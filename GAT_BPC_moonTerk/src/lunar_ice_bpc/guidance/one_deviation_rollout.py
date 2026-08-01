"""Executable matched counterfactual rollouts for one route promotion.

The P0V4 journey master does not retain a live HiGHS object or basis between
column-generation rounds.  A replay therefore binds the exact ordered active
column state and performs the same deterministic cold RMP rebuild in every
fresh arm process.  It never fabricates a persistent warm basis.
"""

from __future__ import annotations

from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
from time import perf_counter
from typing import Any, Iterable, Mapping, Sequence

import yaml

from lunar_ice_bpc.exact.bpc.core.column_signature import (
    column_signature_from_journey,
)
from lunar_ice_bpc.exact.bpc.solver.pricing_tail_solver import (
    solve_node_pricing_with_b2b_r3,
)
from lunar_ice_bpc.exact.core.branching import (
    branch_context_from_payload,
)
from lunar_ice_bpc.exact.core.cuts import (
    CutLineage,
    CutLineageEntry,
    cut_context_from_payload,
    stable_payload_hash,
)
from lunar_ice_bpc.exact.core.data import LunarIceData
from lunar_ice_bpc.exact.core.journey import (
    JourneyColumn,
    journey_column_from_solution_payload,
)
from lunar_ice_bpc.guidance.one_deviation_oracle import (
    REQUIRED_STATE_HASHES,
    build_one_deviation_oracle_context,
)
from lunar_ice_bpc.guidance.one_deviation import (
    augment_one_deviation_candidate_contexts,
)
from lunar_ice_bpc.guidance.route_admission import (
    ONE_DEVIATION_NOOP_ACTION_ID,
    validate_route_admission_snapshot,
)


def selected_exact_runtime_binding(
    fixed_selection: Mapping[str, Any],
    *,
    scale: int,
) -> dict[str, Any]:
    """Resolve the exact runtime from the immutable selected V5 config."""

    if str(fixed_selection.get("status") or "") != "FIXED_K_SELECTED":
        raise ValueError("selected Exact runtime requires frozen fixed E_K")
    config_path = Path(str(fixed_selection.get("selected_config") or ""))
    if not config_path.is_file():
        raise ValueError("selected Exact config is missing")
    expected_sha256 = str(
        fixed_selection.get("selected_config_sha256") or ""
    )
    if not expected_sha256 or _file_sha256(config_path) != expected_sha256:
        raise ValueError("selected Exact config hash mismatch")
    config = dict(
        yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    )
    scale_value = int(scale)
    profile = dict(
        dict(config.get("profiles") or {}).get(str(scale_value)) or {}
    )
    if not profile:
        raise ValueError(f"selected Exact config lacks scale{scale_value}")
    backend_id = str(profile.get("backend_id") or "")
    if not backend_id:
        raise ValueError("selected Exact profile lacks a backend")
    scale_key = str(scale_value)
    pass_policy_by_scale = dict(
        config.get("native_final_judge_pass_policy_by_scale") or {}
    )
    adaptive_cap_by_scale = dict(
        config.get("native_adaptive_harvest_cap_sec_by_scale") or {}
    )
    adaptive_cap = adaptive_cap_by_scale.get(scale_key)
    payload = {
        "schema_version": (
            "lunar_ice_bpc.one_deviation_exact_runtime_binding.v1"
        ),
        "selected_config": str(config_path.resolve()),
        "selected_config_sha256": expected_sha256,
        "scale": scale_value,
        "backend_id": backend_id,
        "graph_cache_entries": max(
            1, int(profile.get("graph_cache_entries") or 1)
        ),
        "completion_bound_enabled": bool(
            config.get("native_completion_bound_enabled", False)
        ),
        "subset_dominance_enabled": bool(
            config.get("native_subset_dominance_enabled", False)
        ),
        "cut_state_enabled": bool(
            config.get("native_cut_state_enabled", False)
        ),
        "negative_escape_enabled": bool(
            config.get("exact_negative_escape_enabled", False)
        ),
        "batch_master_admission_enabled": bool(
            config.get("batch_master_admission_enabled", False)
        ),
        "admission_batch_size": int(profile.get("harvest_target") or 0),
        "raw_negative_pool_multiplier": int(
            config.get("exact_raw_negative_pool_multiplier") or 0
        ),
        "negative_escape_policy_id": str(
            config.get("exact_negative_escape_policy_id") or ""
        ),
        "worker_ng_sizes": [
            int(value) for value in profile.get("ng_sizes", ())
        ],
        "worker_hard_time_cap_sec": float(
            profile.get("worker_time_limit_sec") or 0.0
        ),
        "exact_final_judge_first": True,
        "final_judge_pass_policy": str(
            pass_policy_by_scale.get(
                scale_key,
                config.get(
                    "native_final_judge_pass_policy",
                    "harvest_then_proof",
                ),
            )
        ),
        "adaptive_harvest_cap_sec": (
            None if adaptive_cap is None else float(adaptive_cap)
        ),
        "live_sri_policy": str(config.get("live_sri_policy") or "no_cut"),
    }
    if payload["admission_batch_size"] <= 0:
        raise ValueError("selected Exact admission batch is invalid")
    if payload["raw_negative_pool_multiplier"] != 4:
        raise ValueError("one-deviation requires the frozen 4x raw pool")
    if not payload["negative_escape_enabled"] or not payload[
        "batch_master_admission_enabled"
    ]:
        raise ValueError("selected Exact escape/batch policy is disabled")
    payload["runtime_binding_hash"] = stable_payload_hash(payload)
    return payload


def matched_state_hashes(
    snapshot: Mapping[str, Any],
    *,
    fixed_k_selection_hash: str,
) -> dict[str, str]:
    row = validate_route_admission_snapshot(snapshot)
    binding = dict(row["canonical_solve_binding"])
    state = dict(row["counterfactual_state"])
    values = {
        "active_columns_hash": str(state["active_columns_hash"]),
        "rmp_basis_hash": str(state["rmp_basis_hash"]),
        "true_dual_binding_hash": str(
            state["true_dual_binding_hash"]
        ),
        "branch_context_hash": str(state["branch_context_hash"]),
        "cut_context_hash": str(state["cut_context_hash"]),
        "cut_policy_binding_hash": str(
            state["cut_policy_binding_hash"]
        ),
        "worker_state_hash": stable_payload_hash(
            state["worker_state"]
        ),
        "queue_state_hash": stable_payload_hash(
            state["queue_state"]
        ),
        "cache_state_hash": stable_payload_hash(
            state["cache_state"]
        ),
        "thread_state_hash": stable_payload_hash(
            state["thread_state"]
        ),
        "exact_binary_hash": str(
            state.get("exact_binary_hash")
            or binding.get("engine_hash")
            or ""
        ),
        "exact_config_hash": str(
            state.get("exact_config_hash")
            or binding.get("config_hash")
            or ""
        ),
        "exact_engine_hash": str(
            state.get("exact_engine_hash")
            or binding.get("engine_hash")
            or ""
        ),
        "fixed_k_selection_hash": str(fixed_k_selection_hash),
    }
    missing = [
        key for key in REQUIRED_STATE_HASHES if not values.get(key)
    ]
    if missing:
        raise ValueError(
            "matched counterfactual state is incomplete: "
            + ",".join(missing)
        )
    return values


def build_matched_rollout_context(
    snapshot: Mapping[str, Any],
    action_manifest: Mapping[str, Any],
    *,
    fixed_k_selection_hash: str,
) -> dict[str, Any]:
    row = validate_route_admission_snapshot(snapshot)
    _validate_action_manifest(row, action_manifest)
    return build_one_deviation_oracle_context(
        scale=int(row["scale"]),
        instance_content_hash=str(row["instance_content_hash"]),
        node_id=str(row["node_id"]),
        candidate_count=len(row["legal_candidate_ids"]),
        batch_size=int(row["selection_limit"]),
        remaining_solve_budget_sec=float(
            row.get("remaining_solve_budget_sec") or 0.0
        ),
        state_hashes=matched_state_hashes(
            row,
            fixed_k_selection_hash=fixed_k_selection_hash,
        ),
        action_manifest_hash=stable_payload_hash(
            dict(action_manifest)
        ),
    )


def action_initial_columns(
    data: LunarIceData,
    snapshot: Mapping[str, Any],
    action: Mapping[str, Any],
) -> tuple[JourneyColumn, ...]:
    row = validate_route_admission_snapshot(snapshot)
    actions = {
        str(value["action_id"]): dict(value)
        for value in _actions_from_snapshot(row)
    }
    action_id = str(action.get("action_id") or "")
    expected = actions.get(action_id)
    if expected is None or dict(action) != expected:
        raise ValueError("rollout action does not match snapshot action")
    candidate_by_id = {
        str(value["candidate_id"]): dict(value["column_payload"])
        for value in row["candidate_rows"]
    }
    active = [
        journey_column_from_solution_payload(data, dict(payload))
        for payload in row["active_column_payloads"]
    ]
    signatures = {
        column_signature_from_journey(column) for column in active
    }
    for candidate_id in expected["admitted_candidate_ids"]:
        payload = candidate_by_id.get(str(candidate_id))
        if payload is None:
            raise ValueError("action candidate payload is missing")
        column = journey_column_from_solution_payload(data, payload)
        signature = column_signature_from_journey(column)
        if signature in signatures:
            raise ValueError(
                "audited addable action duplicates the active master"
            )
        signatures.add(signature)
        active.append(column)
    return tuple(active)


def execute_rollout_arm(
    data: LunarIceData,
    snapshot: Mapping[str, Any],
    action: Mapping[str, Any],
    *,
    budget_sec: float,
    batch_size: int,
    max_rounds: int = 3,
    exact_backend: str | None = None,
    exact_runtime_binding: Mapping[str, Any] | None = None,
    memory_limit_gb: float | None = None,
) -> dict[str, Any]:
    row = validate_route_admission_snapshot(snapshot)
    if int(batch_size) != int(row["selection_limit"]):
        raise ValueError("rollout batch size differs from snapshot")
    initial_columns = action_initial_columns(data, row, action)
    cut_lineage = _matched_cut_lineage(row)
    runtime = dict(exact_runtime_binding or {})
    if not runtime or not str(runtime.get("runtime_binding_hash") or ""):
        raise ValueError("rollout requires the selected Exact runtime binding")
    backend = str(exact_backend or runtime.get("backend_id") or "")
    if not backend:
        raise ValueError("rollout selected Exact backend is missing")
    if runtime and backend != str(runtime.get("backend_id") or ""):
        raise ValueError("rollout backend differs from selected Exact runtime")
    if runtime and int(runtime.get("scale") or 0) != int(row["scale"]):
        raise ValueError("rollout runtime scale differs from snapshot")
    if runtime and int(runtime.get("admission_batch_size") or 0) != int(
        batch_size
    ):
        raise ValueError("rollout runtime admission batch differs from E_K")
    memory = (
        float(memory_limit_gb)
        if memory_limit_gb is not None
        else float(row.get("memory_limit_gb") or 0.0)
    )
    environment = {
        "LUNAR_ICE_SPPRC_EXACT_BACKEND": backend,
        "LUNAR_ICE_SPPRC_MEMORY_LIMIT_GB": str(memory),
        "LUNAR_ICE_SPPRC_GRAPH_CACHE_ENTRIES": str(
            max(1, int(runtime.get("graph_cache_entries") or 1))
        ),
        "LUNAR_ICE_SPPRC_COMPLETION_BOUND": (
            "1" if bool(runtime.get("completion_bound_enabled")) else "0"
        ),
        "LUNAR_ICE_SPPRC_SUBSET_DOMINANCE": (
            "1" if bool(runtime.get("subset_dominance_enabled")) else "0"
        ),
        "LUNAR_ICE_SPPRC_CUT_STATE": (
            "1" if bool(runtime.get("cut_state_enabled")) else "0"
        ),
        "LUNAR_ICE_EXACT_NEGATIVE_ESCAPE_ENABLED": (
            "1" if bool(runtime.get("negative_escape_enabled", True)) else "0"
        ),
        "LUNAR_ICE_BATCH_MASTER_ADMISSION_ENABLED": (
            "1"
            if bool(runtime.get("batch_master_admission_enabled", True))
            else "0"
        ),
        "LUNAR_ICE_LABELING_WORKER_NG_SIZES": ",".join(
            str(value) for value in runtime.get("worker_ng_sizes", ())
        ),
        "LUNAR_ICE_LABELING_WORKER_HARD_TIME_CAP_SEC": str(
            float(runtime.get("worker_hard_time_cap_sec") or 0.0)
        ),
        "LUNAR_ICE_EXACT_FINAL_JUDGE_FIRST": (
            "1" if bool(runtime.get("exact_final_judge_first", True)) else "0"
        ),
        "LUNAR_ICE_LABELING_FINAL_JUDGE_PASS_POLICY": (
            str(runtime.get("final_judge_pass_policy") or "harvest_then_proof")
        ),
        "LUNAR_ICE_ONE_DEVIATION_MANIFEST": None,
        "LUNAR_ICE_GAT_GUIDANCE_MODE": "off",
    }
    adaptive_cap = runtime.get("adaptive_harvest_cap_sec")
    if adaptive_cap is not None:
        environment[
            "LUNAR_ICE_LABELING_FINAL_JUDGE_ADAPTIVE_HARVEST_CAP_SEC"
        ] = str(float(adaptive_cap))
    started = perf_counter()
    with _temporary_environment(environment):
        result = solve_node_pricing_with_b2b_r3(
            data,
            node_id="root",
            branch_context=branch_context_from_payload(
                dict(row["branch_context"])
            ),
            cut_context=cut_context_from_payload(
                dict(row["full_cut_context"])
            ),
            cut_lineage=cut_lineage,
            live_cut_policy_hash=str(
                row.get("live_cut_policy_hash") or ""
            ),
            separator_policy_version=str(
                row.get("separator_policy_version") or ""
            ),
            initial_columns=initial_columns,
            max_direct_tasks=int(row["scale"]),
            max_rounds=max(1, min(3, int(max_rounds))),
            wall_time_limit_sec=float(budget_sec),
            max_columns_per_round=int(batch_size),
            worker_pricer_kind="relaxed_labeling",
            labeling_final_judge_enabled=True,
            labeling_final_judge_max_exact_tasks=int(row["scale"]),
            labeling_final_judge_exact_harvest_target=int(
                batch_size
            ),
            tail_dual_stabilization_enabled=True,
            tail_dual_stabilization_alpha=0.7,
            tail_dual_stabilization_window=5,
            return_active_columns_payload=False,
        )
    elapsed = perf_counter() - started
    history = [dict(value) for value in result.get("history", ())]
    trace = _rollout_trace(history, terminal_elapsed=elapsed)
    terminal_negative_pressure = _last_observed_negative_pressure(
        trace
    )
    root_closed = bool(
        str(result.get("node_status")) == "NODE_LP_CERTIFIED"
        or str(result.get("pricing_state")) == "CERTIFIED_NO_NEGATIVE"
    )
    return {
        "schema_version": (
            "lunar_ice_bpc.one_deviation_raw_arm_result.v1"
        ),
        "exact_runtime_binding": runtime,
        "exact_runtime_binding_hash": str(
            runtime.get("runtime_binding_hash") or ""
        ),
        "action_id": str(action["action_id"]),
        "action_kind": (
            "noop"
            if str(action["action_id"])
            == ONE_DEVIATION_NOOP_ACTION_ID
            else "promotion"
        ),
        "elapsed_sec": elapsed,
        "budget_sec": float(budget_sec),
        "rollout_horizon_cg_rounds": max(
            0, min(3, len(history))
        ),
        "root_closed": root_closed,
        "closure_time_sec": elapsed if root_closed else None,
        "terminal_root_bound": _optional_float(
            result.get("root_lp_bound")
            or result.get("root_rmp_objective")
        ),
        "terminal_negative_pressure": terminal_negative_pressure,
        "terminal_negative_pressure_observed": bool(
            terminal_negative_pressure is not None
        ),
        "trace": trace,
        "algorithm_status": str(
            result.get("algorithm_status") or ""
        ),
        "certificate_scope": str(
            result.get("certificate_scope") or ""
        ),
        "pricing_state": str(result.get("pricing_state") or ""),
        "memory_adverse_event": _memory_adverse_event(result),
        "correctness_redline_count": _correctness_redlines(result),
        "next_round_exact_order_restored": True,
        "intervention_count": (
            0
            if str(action["action_id"])
            == ONE_DEVIATION_NOOP_ACTION_ID
            else 1
        ),
        "certificate_paths_mutated": False,
        "bound_or_pruning_paths_mutated": False,
        "result": _public_exact_result(result),
    }


def _public_exact_result(result: Mapping[str, Any]) -> dict[str, Any]:
    """Drop solver-private Python objects before persisting an arm result."""

    return {
        str(key): value
        for key, value in result.items()
        if not str(key).startswith("_")
    }


def materialize_matched_rollout_rows(
    context: Mapping[str, Any],
    raw_results_by_replicate: Mapping[
        str, Sequence[Mapping[str, Any]]
    ],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    budget = float(context["matched_rollout_budget_sec"])
    state_hashes = dict(context["state_hashes"])
    for replicate_id, raw_rows in raw_results_by_replicate.items():
        raw = [dict(value) for value in raw_rows]
        controls = [
            value
            for value in raw
            if str(value["action_kind"]) == "noop"
        ]
        if len(controls) != 1:
            raise ValueError(
                "each blocked replicate requires one P0 control"
            )
        control = controls[0]
        milestone_kind, target = _control_milestone(control)
        for result in raw:
            milestone_time = _time_to_milestone(
                result,
                milestone_kind=milestone_kind,
                target=target,
            )
            right_censored = milestone_time is None
            rows.append(
                {
                    "schema_version": (
                        "lunar_ice_bpc.one_deviation_rollout_row.v1"
                    ),
                    "context_hash": str(context["context_hash"]),
                    "replicate_id": str(replicate_id),
                    "action_id": str(result["action_id"]),
                    "action_kind": str(result["action_kind"]),
                    "budget_sec": budget,
                    "rollout_horizon_cg_rounds": int(
                        result["rollout_horizon_cg_rounds"]
                    ),
                    "next_round_exact_order_restored": bool(
                        result["next_round_exact_order_restored"]
                    ),
                    "intervention_count": int(
                        result["intervention_count"]
                    ),
                    "certificate_paths_mutated": False,
                    "bound_or_pruning_paths_mutated": False,
                    "state_hashes": state_hashes,
                    "milestone_kind": milestone_kind,
                    "milestone_time_sec": (
                        budget
                        if milestone_time is None
                        else float(milestone_time)
                    ),
                    "right_censored": right_censored,
                    "memory_adverse_event": bool(
                        result.get("memory_adverse_event")
                    ),
                    "raw_algorithm_status": str(
                        result.get("algorithm_status") or ""
                    ),
                }
            )
    return rows


def training_row_from_harvest(
    harvest_row: Mapping[str, Any],
    action_manifest: Mapping[str, Any],
    *,
    instance_content_hash: str,
    split: str,
) -> dict[str, Any]:
    candidate_ids = [
        str(value) for value in harvest_row["harvest_candidate_ids"]
    ]
    index_by_id = {
        candidate_id: index
        for index, candidate_id in enumerate(candidate_ids)
    }
    promotions = [
        dict(value)
        for value in action_manifest["actions"]
        if str(value["action_id"]) != ONE_DEVIATION_NOOP_ACTION_ID
    ]
    indices = [
        index_by_id[str(value["promoted_candidate_id"])]
        for value in promotions
    ]
    noop = next(
        dict(value)
        for value in action_manifest["actions"]
        if str(value["action_id"]) == ONE_DEVIATION_NOOP_ACTION_ID
    )
    selected_indices = [
        index_by_id[str(candidate_id)]
        for candidate_id in noop["admitted_candidate_ids"]
    ]
    candidate_rank_offsets = [
        int(value["promoted_from_rank"])
        - int(action_manifest["p0_batch_size"])
        for value in promotions
    ]
    candidate_masks = [
        list(harvest_row["harvest_task_masks"][index])
        for index in indices
    ]
    candidate_context = augment_one_deviation_candidate_contexts(
        candidate_task_masks=candidate_masks,
        candidate_contexts=[
            list(harvest_row["harvest_context"][index])
            for index in indices
        ],
        candidate_rank_offsets=candidate_rank_offsets,
        selected_task_masks=[
            list(harvest_row["harvest_task_masks"][index])
            for index in selected_indices
        ],
        selected_contexts=[
            list(harvest_row["harvest_context"][index])
            for index in selected_indices
        ],
    )
    return {
        "schema_version": (
            "lunar_ice_bpc.one_deviation_training_features.v1"
        ),
        "scale": int(harvest_row["scale"]),
        "instance_content_hash": str(instance_content_hash),
        "split": str(split),
        "action_ids": [
            str(value["action_id"]) for value in promotions
        ],
        "candidate_rank_offsets": candidate_rank_offsets,
        "node_features": [
            list(value) for value in harvest_row["node_features"]
        ],
        "edge_index": [
            list(value) for value in harvest_row["edge_index"]
        ],
        "edge_features": [
            list(value) for value in harvest_row["edge_features"]
        ],
        "candidate_task_masks": candidate_masks,
        "candidate_context": candidate_context,
        "global_context": list(
            harvest_row.get("resource_context") or []
        ),
        "post_action_features_exposed_to_model": False,
        "certificate_paths_mutated": False,
    }


def _actions_from_snapshot(
    snapshot: Mapping[str, Any],
) -> tuple[dict[str, Any], ...]:
    from lunar_ice_bpc.guidance.route_admission import (
        build_one_deviation_actions,
    )

    return tuple(
        dict(value)
        for value in build_one_deviation_actions(snapshot)["actions"]
    )


def _matched_cut_lineage(
    snapshot: Mapping[str, Any],
) -> CutLineage:
    row = validate_route_admission_snapshot(snapshot)
    context = cut_context_from_payload(
        dict(row["full_cut_context"])
    )
    lineage = CutLineage(
        entries=tuple(
            CutLineageEntry(
                cut_id=cut.cut_id,
                scope="global",
                origin_node_id="root",
                policy_version="explicit_cut_context_v1",
            )
            for cut in context.cuts
        ),
        policy_version="explicit_cut_context_v1",
    )
    source_hash = str(
        dict(row["canonical_solve_binding"]).get(
            "cut_lineage_hash"
        )
        or ""
    )
    if not source_hash and context.empty:
        # Legacy opportunity snapshots recorded the optional public argument
        # instead of the normalized empty lineage used internally by
        # solve_node_pricing_with_b2b_r3.  With no active cuts there are no
        # lineage entries to infer: this is the solver's deterministic root
        # default, not a reconstructed non-empty cut history.  New snapshots
        # record lineage.cut_lineage_hash directly.
        return lineage
    if source_hash != lineage.cut_lineage_hash:
        raise ValueError(
            "source cut lineage cannot be reconstructed exactly"
        )
    return lineage


def _validate_action_manifest(
    snapshot: Mapping[str, Any],
    manifest: Mapping[str, Any],
) -> None:
    if str(manifest.get("snapshot_hash")) != str(
        snapshot["snapshot_hash"]
    ):
        raise ValueError("action manifest snapshot hash mismatch")
    expected = {
        str(value["action_id"]): dict(value)
        for value in _actions_from_snapshot(snapshot)
    }
    observed_rows = [
        dict(value) for value in manifest.get("actions", ())
    ]
    observed_ids = [
        str(value.get("action_id") or "") for value in observed_rows
    ]
    if (
        any(not value for value in observed_ids)
        or len(observed_ids) != len(set(observed_ids))
    ):
        raise ValueError(
            "action manifest contains duplicate action identities"
        )
    observed = {
        str(value["action_id"]): dict(value)
        for value in observed_rows
    }
    if not observed or any(
        action_id not in expected
        or expected[action_id] != action
        for action_id, action in observed.items()
    ):
        raise ValueError(
            "action manifest is not a subset of legal one-deviation actions"
        )
    if ONE_DEVIATION_NOOP_ACTION_ID not in observed:
        raise ValueError("action manifest lacks the Exact no-op")
    if len(observed) < 3:
        raise ValueError(
            "action manifest requires at least two promotion arms"
        )


def _rollout_trace(
    history: Sequence[Mapping[str, Any]],
    *,
    terminal_elapsed: float,
) -> list[dict[str, Any]]:
    trace = []
    previous = 0.0
    count = len(history)
    for index, row in enumerate(history, start=1):
        elapsed = _optional_float(
            row.get("round_elapsed_wall_time_sec")
        )
        if elapsed is None:
            elapsed = (
                float(terminal_elapsed) * index / max(1, count)
            )
        elapsed = max(previous, min(float(terminal_elapsed), elapsed))
        previous = elapsed
        negative_count = int(
            row.get("candidate_negative_count")
            or row.get("negative_column_count")
            or 0
        )
        best_rc = _optional_float(row.get("harvest_best_true_rc"))
        negative_mass = max(
            0.0, negative_count * max(0.0, -(best_rc or 0.0))
        )
        trace.append(
            {
                "elapsed_sec": elapsed,
                "root_bound": _optional_float(
                    row.get("node_lp_bound")
                ),
                "negative_pressure": {
                    "count": max(0, negative_count),
                    "mass": negative_mass,
                    "best_true_rc": best_rc,
                },
                "pricing_state": str(
                    row.get("pricing_state") or ""
                ),
            }
        )
    return trace


def _control_milestone(
    control: Mapping[str, Any],
) -> tuple[str, object]:
    if bool(control.get("root_closed")):
        return "exact_or_root_closure", None
    bound = _optional_float(control.get("terminal_root_bound"))
    trace_bounds = [
        value
        for value in (
            _optional_float(row.get("root_bound"))
            for row in control.get("trace", ())
        )
        if value is not None
    ]
    objective_progressed = bool(
        bound is not None
        and any(
            value > bound + 1.0e-9 for value in trace_bounds
        )
    )
    if objective_progressed:
        return "p0_terminal_rmp_objective", bound
    pressure = control.get("terminal_negative_pressure")
    if isinstance(pressure, dict):
        return "equal_remaining_negative_pressure", dict(pressure)
    if bound is not None:
        # Some contexts have no trustworthy pressure observation.  Retain the
        # plan's objective milestone as a last fail-closed progress proxy
        # rather than inventing a zero-pressure target.
        return "p0_terminal_rmp_objective", bound
    raise ValueError("P0 control did not expose a progress milestone")


def _time_to_milestone(
    result: Mapping[str, Any],
    *,
    milestone_kind: str,
    target: object,
) -> float | None:
    if milestone_kind == "exact_or_root_closure":
        return (
            _optional_float(result.get("closure_time_sec"))
            if bool(result.get("root_closed"))
            else None
        )
    if milestone_kind == "p0_terminal_rmp_objective":
        threshold = float(target)
        for row in result.get("trace", ()):
            bound = _optional_float(row.get("root_bound"))
            if bound is not None and bound <= threshold + 1.0e-9:
                return float(row["elapsed_sec"])
        return None
    if milestone_kind == "equal_remaining_negative_pressure":
        threshold = dict(target)
        for row in result.get("trace", ()):
            if not _negative_pressure_observed(row):
                continue
            pressure = dict(row.get("negative_pressure") or {})
            if _pressure_key(pressure) <= _pressure_key(threshold):
                return float(row["elapsed_sec"])
        return None
    raise ValueError("unsupported matched rollout milestone")


def _pressure_key(value: Mapping[str, Any]) -> tuple[float, float, float]:
    best_rc = _optional_float(value.get("best_true_rc"))
    return (
        float(value.get("count") or 0.0),
        float(value.get("mass") or 0.0),
        max(0.0, -(best_rc or 0.0)),
    )


def _negative_pressure_observed(row: Mapping[str, Any]) -> bool:
    """Return whether a trace row exposes sound negative-pressure evidence.

    An incomplete pricing call that happened to return no candidate is not
    evidence of zero remaining pressure.  Only a found-negative result or an
    exhaustive no-negative closure is usable for the matched milestone.
    """

    return str(row.get("pricing_state") or "") in {
        "FOUND_NEGATIVE",
        "CERTIFIED_NO_NEGATIVE",
    }


def _last_observed_negative_pressure(
    trace: Sequence[Mapping[str, Any]],
) -> dict[str, Any] | None:
    for row in reversed(trace):
        if not _negative_pressure_observed(row):
            continue
        pressure = row.get("negative_pressure")
        if isinstance(pressure, dict):
            return dict(pressure)
    return None


def _memory_adverse_event(result: Mapping[str, Any]) -> bool:
    final_judge = dict(result.get("final_judge") or {})
    telemetry = dict(final_judge.get("telemetry") or {})
    return bool(
        telemetry.get("host_memory_killed")
        or telemetry.get("memory_pressure_triggered")
        or str(result.get("algorithm_status"))
        in {"BPC_MEMORY_LIMIT", "MEMORY_LIMIT"}
    )


def _correctness_redlines(result: Mapping[str, Any]) -> int:
    final_judge = dict(result.get("final_judge") or {})
    return sum(
        int(not bool(final_judge.get(key, True)))
        for key in (
            "pricing_rc_audit_pass",
            "manual_rc_audit_pass",
        )
        if key in final_judge
    ) + int(
        bool(final_judge.get("can_certify_no_negative"))
        and str(final_judge.get("pricing_state"))
        != "CERTIFIED_NO_NEGATIVE"
    )


def _optional_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@contextmanager
def _temporary_environment(
    updates: Mapping[str, str | None],
) -> Iterable[None]:
    previous = {key: os.environ.get(key) for key in updates}
    try:
        for key, value in updates.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = str(value)
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
