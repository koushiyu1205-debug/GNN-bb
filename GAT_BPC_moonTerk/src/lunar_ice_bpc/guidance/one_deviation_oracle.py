"""Framework-free contracts for matched one-deviation route rollouts."""

from __future__ import annotations

from collections import defaultdict
from math import isfinite
import random
from statistics import mean
from typing import Any, Mapping, Sequence

from lunar_ice_bpc.exact.core.cuts import stable_payload_hash


ONE_DEVIATION_ORACLE_CONTEXT_SCHEMA_V1 = (
    "lunar_ice_bpc.one_deviation_oracle_context.v1"
)
ONE_DEVIATION_ORACLE_RESULT_SCHEMA_V1 = (
    "lunar_ice_bpc.one_deviation_oracle_result.v1"
)
REQUIRED_STATE_HASHES = (
    "active_columns_hash",
    "rmp_basis_hash",
    "true_dual_binding_hash",
    "branch_context_hash",
    "cut_context_hash",
    "cut_policy_binding_hash",
    "worker_state_hash",
    "queue_state_hash",
    "cache_state_hash",
    "thread_state_hash",
    "exact_binary_hash",
    "exact_config_hash",
    "exact_engine_hash",
    "fixed_k_selection_hash",
)
MILESTONE_PRIORITY = {
    "exact_or_root_closure": 1,
    "p0_terminal_rmp_objective": 2,
    "equal_remaining_negative_pressure": 3,
}
ONE_DEVIATION_NOOP_ACTION_ID = "ONE_DEVIATION_NOOP"
ONE_DEVIATION_ROLLOUT_ROW_SCHEMA_V1 = (
    "lunar_ice_bpc.one_deviation_rollout_row.v1"
)


def build_one_deviation_oracle_context(
    *,
    scale: int,
    instance_content_hash: str,
    node_id: str,
    candidate_count: int,
    batch_size: int,
    remaining_solve_budget_sec: float,
    state_hashes: Mapping[str, str],
    action_manifest_hash: str,
) -> dict[str, Any]:
    scale_value = int(scale)
    if scale_value not in {20, 30, 50}:
        raise ValueError("one-deviation oracle supports scale 20/30/50")
    if str(node_id) != "root":
        raise ValueError("one-deviation oracle is root-only")
    if int(candidate_count) <= int(batch_size):
        raise ValueError("one-deviation context has no admission boundary")
    if int(candidate_count) - int(batch_size) < 8:
        raise ValueError(
            "one-deviation context requires at least eight omitted candidates"
        )
    rollout_budget = 300.0 if scale_value == 50 else 120.0
    if float(remaining_solve_budget_sec) < rollout_budget:
        raise ValueError("insufficient remaining matched rollout budget")
    normalized_hashes = {
        key: str(state_hashes.get(key) or "")
        for key in REQUIRED_STATE_HASHES
    }
    missing = [
        key for key, value in normalized_hashes.items() if not value
    ]
    if missing:
        raise ValueError(
            "counterfactual state binding is incomplete: "
            + ",".join(missing)
        )
    payload = {
        "schema_version": ONE_DEVIATION_ORACLE_CONTEXT_SCHEMA_V1,
        "scale": scale_value,
        "instance_content_hash": str(instance_content_hash),
        "node_id": "root",
        "candidate_count": int(candidate_count),
        "batch_size": int(batch_size),
        "omitted_candidate_count": (
            int(candidate_count) - int(batch_size)
        ),
        "matched_rollout_budget_sec": rollout_budget,
        "rollout_horizon_cg_rounds": 3,
        "blocked_replicates": 3,
        "minimum_promotion_arms": 2,
        "intervention_count_limit": 1,
        "next_round_policy": "restore_frozen_exact_p0_order",
        "action_manifest_hash": str(action_manifest_hash),
        "state_hashes": normalized_hashes,
        "certificate_paths_mutated": False,
        "bound_or_pruning_paths_mutated": False,
    }
    payload["context_hash"] = stable_payload_hash(payload)
    return payload


def validate_one_deviation_rollouts(
    context: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    if (
        str(context.get("schema_version"))
        != ONE_DEVIATION_ORACLE_CONTEXT_SCHEMA_V1
    ):
        raise ValueError("one-deviation oracle context schema mismatch")
    expected_context_hash = stable_payload_hash(
        {
            key: value
            for key, value in context.items()
            if key != "context_hash"
        }
    )
    if str(context.get("context_hash")) != expected_context_hash:
        raise ValueError("one-deviation oracle context hash mismatch")
    by_replicate: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        if (
            str(row.get("schema_version") or "")
            != ONE_DEVIATION_ROLLOUT_ROW_SCHEMA_V1
        ):
            raise ValueError("one-deviation rollout row schema mismatch")
        if str(row.get("context_hash")) != expected_context_hash:
            raise ValueError("rollout/context hash mismatch")
        if float(row.get("budget_sec") or 0.0) != float(
            context["matched_rollout_budget_sec"]
        ):
            raise ValueError("rollout budget mismatch")
        if int(row.get("rollout_horizon_cg_rounds") or 0) > 3:
            raise ValueError("rollout exceeded three CG rounds")
        if not bool(row.get("next_round_exact_order_restored")):
            raise ValueError("promotion did not restore Exact order")
        if int(row.get("intervention_count") or 0) > 1:
            raise ValueError("more than one route intervention was used")
        if bool(row.get("certificate_paths_mutated")):
            raise ValueError("rollout mutated certificate paths")
        if bool(row.get("bound_or_pruning_paths_mutated")):
            raise ValueError("rollout mutated bound/pruning paths")
        if dict(row.get("state_hashes") or {}) != dict(
            context["state_hashes"]
        ):
            raise ValueError("matched rollout state binding mismatch")
        replicate_id = str(row.get("replicate_id") or "")
        if not replicate_id:
            raise ValueError("rollout replicate id is missing")
        action_kind = str(row.get("action_kind") or "")
        action_id = str(row.get("action_id") or "")
        if action_kind not in {"noop", "promotion"} or not action_id:
            raise ValueError("rollout action identity is invalid")
        if (
            (action_kind == "noop")
            != (action_id == ONE_DEVIATION_NOOP_ACTION_ID)
        ):
            raise ValueError("rollout no-op action identity mismatch")
        by_replicate[replicate_id].append(row)
    if len(by_replicate) != 3:
        raise ValueError("exactly three blocked replicates are required")
    promotion_sets = []
    complete_action_sets = []
    for replicate, replicate_rows in by_replicate.items():
        action_ids = [
            str(row["action_id"]) for row in replicate_rows
        ]
        if len(action_ids) != len(set(action_ids)):
            raise ValueError(
                f"replicate {replicate!r} repeats an action"
            )
        controls = [
            row
            for row in replicate_rows
            if str(row.get("action_kind")) == "noop"
        ]
        promotions = [
            row
            for row in replicate_rows
            if str(row.get("action_kind")) == "promotion"
        ]
        if len(controls) != 1 or len(promotions) < 2:
            raise ValueError(
                f"replicate {replicate!r} requires one no-op and two promotions"
            )
        promotion_sets.append(
            tuple(
                sorted(str(row["action_id"]) for row in promotions)
            )
        )
        complete_action_sets.append(tuple(sorted(action_ids)))
    if any(value != promotion_sets[0] for value in promotion_sets[1:]):
        raise ValueError("blocked replicates probed different promotion arms")
    if any(
        value != complete_action_sets[0]
        for value in complete_action_sets[1:]
    ):
        raise ValueError("blocked replicates probed different action sets")
    return {
        "context_hash": expected_context_hash,
        "replicate_count": 3,
        "promotion_arm_count": len(promotion_sets[0]),
        "validation_pass": True,
    }


def materialize_one_deviation_time_labels(
    context: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    validation = validate_one_deviation_rollouts(context, rows)
    by_replicate: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        by_replicate[str(row["replicate_id"])].append(row)
    arm_values: dict[str, list[float]] = defaultdict(list)
    arm_relative_values: dict[str, list[float]] = defaultdict(list)
    arm_censored: dict[str, int] = defaultdict(int)
    arm_censor_delay_lower_bounds: dict[str, list[float]] = (
        defaultdict(list)
    )
    arm_censor_delay_relative_lower_bounds: dict[str, list[float]] = (
        defaultdict(list)
    )
    arm_memory_adverse: dict[str, int] = defaultdict(int)
    for replicate_rows in by_replicate.values():
        control = next(
            row
            for row in replicate_rows
            if str(row["action_kind"]) == "noop"
        )
        control_time = _observed_milestone_time(control)
        if control_time is None:
            raise ValueError("P0 control milestone must be observed")
        control_milestone = str(control["milestone_kind"])
        for row in replicate_rows:
            if str(row["action_kind"]) != "promotion":
                continue
            if bool(row.get("memory_adverse_event")):
                arm_memory_adverse[str(row["action_id"])] += 1
            if str(row.get("milestone_kind")) != control_milestone:
                arm_censored[str(row["action_id"])] += 1
                arm_censor_delay_lower_bounds[
                    str(row["action_id"])
                ].append(
                    max(
                        0.0,
                        float(row.get("budget_sec") or 0.0)
                        - control_time,
                    )
                )
                arm_censor_delay_relative_lower_bounds[
                    str(row["action_id"])
                ].append(
                    max(
                        0.0,
                        float(row.get("budget_sec") or 0.0)
                        - control_time,
                    )
                    / max(1.0e-9, control_time)
                )
                continue
            action_time = _observed_milestone_time(row)
            if action_time is None:
                arm_censored[str(row["action_id"])] += 1
                arm_censor_delay_lower_bounds[
                    str(row["action_id"])
                ].append(
                    max(
                        0.0,
                        float(row.get("budget_sec") or 0.0)
                        - control_time,
                    )
                )
                arm_censor_delay_relative_lower_bounds[
                    str(row["action_id"])
                ].append(
                    max(
                        0.0,
                        float(row.get("budget_sec") or 0.0)
                        - control_time,
                    )
                    / max(1.0e-9, control_time)
                )
                continue
            delta_time = control_time - action_time
            arm_values[str(row["action_id"])].append(delta_time)
            arm_relative_values[str(row["action_id"])].append(
                delta_time / max(1.0e-9, control_time)
            )
    labels = []
    action_ids = sorted(set(arm_values) | set(arm_censored))
    for action_id in action_ids:
        values = arm_values.get(action_id, [])
        relative_values = arm_relative_values.get(action_id, [])
        advantage = None if not values else mean(values)
        relative_advantage = (
            None if not relative_values else mean(relative_values)
        )
        memory_adverse = bool(arm_memory_adverse.get(action_id, 0))
        censored_count = int(arm_censored.get(action_id, 0))
        fully_observed = bool(
            len(values) == int(validation["replicate_count"])
            and censored_count == 0
        )
        labels.append(
            {
                "action_id": action_id,
                "delta_time_sec": advantage,
                "relative_time_gain": relative_advantage,
                "beneficial": (
                    False
                    if memory_adverse
                    else None
                    if not fully_observed
                    else bool(
                        advantage is not None
                        and relative_advantage is not None
                        and relative_advantage > 0.0
                    )
                ),
                "observed_replicate_count": len(values),
                "right_censored_replicate_count": censored_count,
                "probability_head_mask": fully_observed,
                "positive_magnitude_head_mask": bool(
                    fully_observed
                    and not memory_adverse
                    and advantage is not None
                    and relative_advantage is not None
                    and relative_advantage > 0.0
                ),
                "survival_mask": bool(censored_count),
                "censor_lower_bound_sec": (
                    0.0
                    if not arm_censor_delay_lower_bounds.get(action_id)
                    else mean(
                        arm_censor_delay_lower_bounds[action_id]
                    )
                ),
                "censor_lower_bound_relative": (
                    0.0
                    if not arm_censor_delay_relative_lower_bounds.get(
                        action_id
                    )
                    else mean(
                        arm_censor_delay_relative_lower_bounds[action_id]
                    )
                ),
                "memory_adverse_event": memory_adverse,
            }
        )
    return {
        "schema_version": ONE_DEVIATION_ORACLE_RESULT_SCHEMA_V1,
        **validation,
        "labels": labels,
        "right_censored_never_forced_negative": True,
    }


def audit_one_deviation_oracle(
    context_rows: Sequence[Mapping[str, Any]],
    *,
    required_scales: Sequence[int] = (30, 50),
    minimum_contexts_per_scale: int = 20,
    minimum_instances_per_scale: int = 5,
    minimum_mean_gain: float = 0.10,
    minimum_mean_gain_lcb: float = 0.08,
    minimum_positive_fraction_lcb: float = 0.20,
    bootstrap_samples: int = 2000,
    seed: int = 629_041,
) -> dict[str, Any]:
    normalized = []
    redline_count = 0
    for row in context_rows:
        scale = int(row["scale"])
        gain_fraction = float(row["oracle_gain_fraction"])
        if not isfinite(gain_fraction) or gain_fraction < 0.0:
            raise ValueError("invalid oracle gain fraction")
        redline_count += int(row.get("redline_count") or 0)
        normalized.append(
            {
                "scale": scale,
                "instance": str(row["instance_content_hash"]),
                "gain": gain_fraction,
                "positive": gain_fraction > 0.0,
            }
        )
    generator = random.Random(int(seed))
    scale_reports = {}
    gate = redline_count == 0
    for scale in tuple(int(value) for value in required_scales):
        scale_rows = [row for row in normalized if row["scale"] == scale]
        by_instance: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in scale_rows:
            by_instance[row["instance"]].append(row)
        summaries = [
            {
                "gain": mean(item["gain"] for item in rows),
                "positive": mean(
                    float(item["positive"]) for item in rows
                ),
            }
            for rows in by_instance.values()
        ]
        gain_bootstrap = []
        positive_bootstrap = []
        for _index in range(max(100, int(bootstrap_samples))):
            sampled = [
                generator.choice(summaries) for _row in summaries
            ] if summaries else []
            gain_bootstrap.append(
                0.0 if not sampled else mean(row["gain"] for row in sampled)
            )
            positive_bootstrap.append(
                0.0
                if not sampled
                else mean(row["positive"] for row in sampled)
            )
        gain_lcb = _quantile(gain_bootstrap, 0.025)
        positive_lcb = _quantile(positive_bootstrap, 0.025)
        mean_gain = (
            0.0
            if not summaries
            else mean(row["gain"] for row in summaries)
        )
        scale_gate = bool(
            len(scale_rows) >= int(minimum_contexts_per_scale)
            and len(by_instance) >= int(minimum_instances_per_scale)
            and mean_gain >= float(minimum_mean_gain)
            and gain_lcb >= float(minimum_mean_gain_lcb)
            and positive_lcb >= float(minimum_positive_fraction_lcb)
        )
        gate = gate and scale_gate
        scale_reports[str(scale)] = {
            "context_count": len(scale_rows),
            "instance_count": len(by_instance),
            "minimum_instance_count": int(
                minimum_instances_per_scale
            ),
            "mean_oracle_gain_fraction": mean_gain,
            "mean_gain_unit": "instance_after_context_averaging",
            "mean_oracle_gain_fraction_lcb95": gain_lcb,
            "positive_context_fraction_lcb95": positive_lcb,
            "gate_pass": scale_gate,
        }
    return {
        "schema_version": "lunar_ice_bpc.one_deviation_oracle_gate.v1",
        "gate_pass": gate,
        "gat_training_authorized": gate,
        "scales": scale_reports,
        "minimum_mean_gain_lcb": float(minimum_mean_gain_lcb),
        "minimum_mean_gain": float(minimum_mean_gain),
        "minimum_positive_fraction_lcb": float(
            minimum_positive_fraction_lcb
        ),
        "bootstrap_unit": "instance_after_context_averaging",
        "correctness_redline_count": redline_count,
        "failure_policy": "do_not_train_gat",
    }


def _observed_milestone_time(row: Mapping[str, Any]) -> float | None:
    if bool(row.get("right_censored")):
        return None
    milestone = str(row.get("milestone_kind") or "")
    if milestone not in MILESTONE_PRIORITY:
        raise ValueError("unsupported matched rollout milestone")
    value = float(row.get("milestone_time_sec"))
    if not isfinite(value) or value < 0.0:
        raise ValueError("invalid milestone time")
    return value


def _quantile(values: Sequence[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(float(value) for value in values)
    index = max(
        0,
        min(len(ordered) - 1, int(fraction * (len(ordered) - 1))),
    )
    return ordered[index]
