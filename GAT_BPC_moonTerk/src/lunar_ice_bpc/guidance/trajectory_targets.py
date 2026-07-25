"""Leakage-safe counterfactual trajectory targets for pricing guidance.

The learning unit is an immutable pricing context.  A record contains a P0
control and ordering-only interventions that differ solely in which legal
candidate receives the next-work priority.  Missing interventions are never
interpreted as negative examples.

This module deliberately has no torch dependency.  It is shared by collectors,
materializers, audits, and tests before the training runtime is imported.
"""

from __future__ import annotations

from collections import defaultdict
from math import exp, isfinite
import random
from statistics import mean
from typing import Any, Iterable, Mapping, Sequence

from lunar_ice_bpc.exact.bpc.guidance.contracts import canonical_universe_hash
from lunar_ice_bpc.exact.core.cuts import stable_payload_hash


COUNTERFACTUAL_TRAJECTORY_SCHEMA_V2 = (
    "lunar_ice_bpc.gat_counterfactual_trajectory.v2"
)
COUNTERFACTUAL_TRAINING_OBJECTIVE_V2 = "counterfactual_trajectory_v2"
FIXED_POOL_PRICING_PRESSURE_OBJECTIVE_SPEC_V1 = (
    "fixed_pool_pricing_pressure_auc."
    "equal_mass_count.current_state.normalized.v1"
)
P0_CONTROL_ACTION_ID = "P0_KEEP_ORDER"
SUPPORTED_CANDIDATE_KINDS = frozenset({"task", "arc", "harvest"})
SUPPORTED_UTILITY_KINDS = frozenset(
    {
        "negative_discovery_auc",
        "addable_discovery_auc",
        "rmp_progress_auc",
        "fixed_pool_pricing_pressure_auc",
    }
)
MIN_BLOCKED_REPLICATES = 3
DEFAULT_ADVANTAGE_RISK_KAPPA = 1.96
DEFAULT_SOFT_TARGET_TEMPERATURE = 0.05
MIN_PRACTICAL_ADVANTAGE = 0.005
MEMORY_COMPETING_RISK_REASONS = frozenset(
    {
        "MEMORY_LIMIT",
        "FRONTIER_EXPLOSION",
        "RESOURCE_SAFETY_TERMINATION",
    }
)
ORACLE_HEADROOM_AUDIT_SCHEMA_V1 = (
    "lunar_ice_bpc.gat_oracle_headroom_audit.v1"
)


def pre_action_feature_hash(
    *,
    binding_hash: str,
    static_tensor_cache_hash: str,
    dynamic_node_features: Sequence[Sequence[float]],
    resource_context: Sequence[float],
) -> str:
    """Hash only fields available before an ordering intervention runs."""

    return stable_payload_hash(
        {
            "schema_version": (
                "lunar_ice_bpc.gat_pre_action_feature_payload.v1"
            ),
            "binding_hash": str(binding_hash),
            "static_tensor_cache_hash": str(static_tensor_cache_hash),
            "dynamic_node_features": [
                [float(value) for value in row]
                for row in dynamic_node_features
            ],
            "resource_context": [
                float(value) for value in resource_context
            ],
        }
    )


def validate_counterfactual_trajectory_record(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a normalized record or reject confounded/leaky supervision."""

    row = dict(payload)
    if str(row.get("schema_version")) != COUNTERFACTUAL_TRAJECTORY_SCHEMA_V2:
        raise ValueError("counterfactual trajectory schema version mismatch")
    required_text = (
        "snapshot_hash",
        "binding_hash",
        "instance_content_hash",
        "rmp_context_hash",
        "legal_universe_hash_before_sort",
        "pre_action_feature_hash",
    )
    for key in required_text:
        if not str(row.get(key) or ""):
            raise ValueError(f"counterfactual record requires {key}")
    kind = str(row.get("candidate_kind") or "")
    if kind not in SUPPORTED_CANDIDATE_KINDS:
        raise ValueError(f"unsupported counterfactual candidate kind {kind!r}")
    scale = int(row.get("scale") or 0)
    if scale not in {5, 10, 20, 30, 50, 100}:
        raise ValueError("counterfactual record has unsupported scale")
    budget_sec = float(row.get("budget_sec") or 0.0)
    if not isfinite(budget_sec) or budget_sec <= 0.0:
        raise ValueError("counterfactual budget must be finite and positive")
    if bool(row.get("model_cost_included_in_solver_utility")):
        raise ValueError(
            "forced-intervention solver utility must exclude model cost"
        )
    if not bool(row.get("solver_model_cost_separated")):
        raise ValueError("solver benefit/model cost separation is required")
    if bool(row.get("post_action_features_exposed_to_model")):
        raise ValueError("post-action outcome leakage is forbidden")
    if str(row.get("budget_mode") or "") not in {
        "matched_wall_time",
        "matched_label_count",
        "matched_extension_count",
    }:
        raise ValueError("counterfactual record requires an explicit budget mode")
    rc_scale = float(row.get("pre_treatment_rc_scale") or 0.0)
    if not isfinite(rc_scale) or rc_scale <= 0.0:
        raise ValueError(
            "counterfactual record requires a positive pre-treatment RC scale"
        )
    if not str(row.get("pre_treatment_rc_scale_source") or ""):
        raise ValueError("pre-treatment RC scale provenance is required")

    candidate_ids = tuple(str(value) for value in row.get("candidate_ids", ()))
    if len(candidate_ids) < 2 or len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError(
            "counterfactual record needs at least two unique legal candidates"
        )
    expected_universe = canonical_universe_hash(
        candidate_ids, universe_kind=kind
    )
    if expected_universe != str(row["legal_universe_hash_before_sort"]):
        raise ValueError("counterfactual legal universe hash mismatch")

    arms = tuple(
        _normalize_arm(
            arm,
            candidate_ids=candidate_ids,
            budget_sec=budget_sec,
            legal_universe_hash=expected_universe,
        )
        for arm in row.get("arms", ())
    )
    if not arms:
        raise ValueError("counterfactual record has no intervention arms")
    by_replicate: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for arm in arms:
        by_replicate[arm["replicate_id"]].append(arm)
    if len(by_replicate) < MIN_BLOCKED_REPLICATES:
        raise ValueError(
            "counterfactual target requires at least three blocked replicates"
        )
    promotion_sets = []
    for replicate_id, rows in sorted(by_replicate.items()):
        controls = [
            arm for arm in rows if arm["action_id"] == P0_CONTROL_ACTION_ID
        ]
        if len(controls) != 1:
            raise ValueError(
                f"replicate {replicate_id!r} needs exactly one P0 control"
            )
        promoted = tuple(
            sorted(
                arm["action_id"]
                for arm in rows
                if arm["action_id"] != P0_CONTROL_ACTION_ID
            )
        )
        if len(promoted) < 2 or len(promoted) != len(set(promoted)):
            raise ValueError(
                f"replicate {replicate_id!r} needs at least two promotions"
            )
        promotion_sets.append(promoted)
    if any(values != promotion_sets[0] for values in promotion_sets[1:]):
        raise ValueError(
            "all replicates must probe the same candidate intervention set"
        )

    utility_kind = str(row.get("utility_kind") or "")
    if utility_kind not in SUPPORTED_UTILITY_KINDS:
        raise ValueError(f"unsupported utility kind {utility_kind!r}")
    objective_spec_id = str(
        row.get("trajectory_objective_spec_id") or ""
    )
    if utility_kind == "fixed_pool_pricing_pressure_auc":
        if objective_spec_id != (
            FIXED_POOL_PRICING_PRESSURE_OBJECTIVE_SPEC_V1
        ):
            raise ValueError(
                "fixed-pool pressure trajectory objective spec mismatch"
            )
        _validate_fixed_pool_pressure_points(arms)
    elif objective_spec_id:
        raise ValueError(
            "trajectory objective spec is only defined for fixed-pool "
            "pricing pressure"
        )
    if utility_kind in {
        "rmp_progress_auc",
        "fixed_pool_pricing_pressure_auc",
    }:
        required_rollout_fields = (
            "p0_rollout_policy_hash",
            "rollout_horizon",
            "phase_objective_mode",
            "initial_active_columns_hash",
            "initial_basis_hash",
            "dual_stabilization_state_hash",
            "worker_policy_hash",
            "queue_policy_id",
            "column_pool_hash",
            "cache_state_hash",
            "thread_count",
        )
        missing_rollout_fields = [
            field
            for field in required_rollout_fields
            if row.get(field) is None or row.get(field) == ""
        ]
        if missing_rollout_fields:
            raise ValueError(
                "RMP utility requires a frozen P0 rollout contract: "
                + ",".join(missing_rollout_fields)
            )
        if any(
            point.get("rmp_progress") is None
            for arm in arms
            for point in arm["trajectory"]
        ):
            raise ValueError("RMP utility requires progress on every point")

    normalized = {
        **row,
        "scale": scale,
        "candidate_kind": kind,
        "candidate_ids": list(candidate_ids),
        "budget_sec": budget_sec,
        "utility_kind": utility_kind,
        "trajectory_objective_spec_id": objective_spec_id,
        "pre_treatment_rc_scale": rc_scale,
        "arms": list(arms),
    }
    return normalized


def materialize_counterfactual_targets(
    payload: Mapping[str, Any],
    *,
    candidate_ids: Sequence[str],
    bootstrap_samples: int = 512,
    seed: int = 20260724,
) -> dict[str, Any]:
    """Build conservative no-op-aware listwise and survival targets.

    ``bootstrap_samples`` and ``seed`` remain accepted for artifact/API
    compatibility but are intentionally unused.  Repeated interventions form
    real paired standard errors; trajectory time points are never bootstrapped
    as if they were independent replicates.
    """

    row = validate_counterfactual_trajectory_record(payload)
    expected_ids = tuple(str(value) for value in candidate_ids)
    if tuple(row["candidate_ids"]) != expected_ids:
        raise ValueError("training row/counterfactual candidate order mismatch")
    index_by_id = {
        candidate_id: index
        for index, candidate_id in enumerate(expected_ids)
    }
    by_replicate: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for arm in row["arms"]:
        by_replicate[str(arm["replicate_id"])][str(arm["action_id"])] = arm

    promoted_ids = tuple(
        sorted(
            action_id
            for action_id in next(iter(by_replicate.values()))
            if action_id != P0_CONTROL_ACTION_ID
        )
    )
    advantages_by_action: dict[str, list[float]] = {
        action_id: [] for action_id in promoted_ids
    }
    # Survival index zero is the explicit P0_KEEP_ORDER action. Promotion i is
    # offset by one relative to the model's legal-candidate vector.
    survival_rows: list[tuple[int, float, bool]] = []
    for replicate_id, arms in sorted(by_replicate.items()):
        control_arm = arms[P0_CONTROL_ACTION_ID]
        control_utility = trajectory_utility(
            control_arm,
            budget_sec=float(row["budget_sec"]),
            utility_kind=str(row["utility_kind"]),
            rc_scale=float(row["pre_treatment_rc_scale"]),
        )
        if not bool(control_arm["memory_adverse_event"]):
            event_time, event_observed = first_event_observation(
                control_arm,
                budget_sec=float(row["budget_sec"]),
                utility_kind=str(row["utility_kind"]),
            )
            survival_rows.append(
                (
                    0,
                    event_time / float(row["budget_sec"]),
                    event_observed,
                )
            )
        for action_id in promoted_ids:
            arm = arms[action_id]
            utility = trajectory_utility(
                arm,
                budget_sec=float(row["budget_sec"]),
                utility_kind=str(row["utility_kind"]),
                rc_scale=float(row["pre_treatment_rc_scale"]),
            )
            advantages_by_action[action_id].append(
                float(utility - control_utility)
            )
            if not bool(arm["memory_adverse_event"]):
                event_time, event_observed = first_event_observation(
                    arm,
                    budget_sec=float(row["budget_sec"]),
                    utility_kind=str(row["utility_kind"]),
                )
                survival_rows.append(
                    (
                        index_by_id[action_id] + 1,
                        event_time / float(row["budget_sec"]),
                        event_observed,
                    )
                )

    advantage_standard_error_by_action = {
        action_id: _standard_error(values)
        for action_id, values in advantages_by_action.items()
    }
    risk_kappa = float(
        row.get("advantage_risk_kappa")
        or DEFAULT_ADVANTAGE_RISK_KAPPA
    )
    temperature = float(
        row.get("soft_target_temperature")
        or DEFAULT_SOFT_TARGET_TEMPERATURE
    )
    if not isfinite(risk_kappa) or risk_kappa < 0.0:
        raise ValueError("advantage risk kappa must be finite and nonnegative")
    if not isfinite(temperature) or temperature <= 0.0:
        raise ValueError("soft target temperature must be finite and positive")
    conservative_advantages = {
        action_id: (
            mean(values)
            - risk_kappa * advantage_standard_error_by_action[action_id]
        )
        for action_id, values in advantages_by_action.items()
    }
    probabilities = _conservative_soft_targets(
        conservative_advantages,
        temperature=temperature,
    )
    conservative_values = [0.0, *conservative_advantages.values()]
    action_value_range = max(conservative_values) - min(conservative_values)
    indifference_margin = max(
        MIN_PRACTICAL_ADVANTAGE,
        risk_kappa
        * max(advantage_standard_error_by_action.values(), default=0.0),
    )
    target_probabilities = [0.0] * len(expected_ids)
    advantages = [0.0] * len(expected_ids)
    probe_mask = [False] * len(expected_ids)
    advantage_standard_errors = [0.0] * len(expected_ids)
    conservative_action_values = [0.0] * len(expected_ids)
    memory_adverse_event_rates = [0.0] * len(expected_ids)
    inverse_propensity_weights = [0.0] * len(expected_ids)
    for action_id in promoted_ids:
        index = index_by_id[action_id]
        values = advantages_by_action[action_id]
        target_probabilities[index] = probabilities[action_id]
        advantages[index] = mean(values)
        probe_mask[index] = True
        advantage_standard_errors[index] = (
            advantage_standard_error_by_action[action_id]
        )
        conservative_action_values[index] = (
            conservative_advantages[action_id]
        )
        memory_adverse_event_rates[index] = mean(
            float(
                by_replicate[replicate_id][action_id][
                    "memory_adverse_event"
                ]
            )
            for replicate_id in sorted(by_replicate)
        )
        inverse_propensity_weights[index] = mean(
            min(
                10.0,
                1.0
                / float(
                    by_replicate[replicate_id][action_id]["propensity"]
                ),
            )
            for replicate_id in sorted(by_replicate)
        )

    return {
        "training_objective": COUNTERFACTUAL_TRAINING_OBJECTIVE_V2,
        "counterfactual_utility_kind": str(row["utility_kind"]),
        "counterfactual_trajectory_objective_spec_id": str(
            row.get("trajectory_objective_spec_id") or ""
        ),
        "counterfactual_target_probabilities": target_probabilities,
        "counterfactual_advantages": advantages,
        "counterfactual_solver_advantages": advantages,
        "counterfactual_advantage_standard_errors": (
            advantage_standard_errors
        ),
        "counterfactual_conservative_action_values": (
            conservative_action_values
        ),
        "counterfactual_probe_mask": probe_mask,
        "counterfactual_noop_target_probability": probabilities[
            P0_CONTROL_ACTION_ID
        ],
        "counterfactual_noop_advantage": 0.0,
        "counterfactual_noop_conservative_action_value": 0.0,
        "counterfactual_noop_probe_mask": True,
        "counterfactual_noop_inverse_propensity_weight": 1.0,
        "counterfactual_inverse_propensity_weights": (
            inverse_propensity_weights
        ),
        "survival_candidate_indices": [
            candidate_index
            for candidate_index, _, _ in survival_rows
        ],
        "survival_time_fractions": [
            fraction for _, fraction, _ in survival_rows
        ],
        "survival_event_observed": [
            observed for _, _, observed in survival_rows
        ],
        "counterfactual_replicate_count": len(by_replicate),
        "counterfactual_promoted_candidate_count": len(promoted_ids),
        "counterfactual_action_value_range": action_value_range,
        "counterfactual_indifference_margin": indifference_margin,
        "counterfactual_action_value_identifiable": (
            action_value_range > indifference_margin
        ),
        "counterfactual_advantage_risk_kappa": risk_kappa,
        "counterfactual_soft_target_temperature": temperature,
        "counterfactual_target_method": (
            "conservative_advantage_softmax_with_explicit_p0_noop"
        ),
        "counterfactual_effect_estimand": "intention_to_treat",
        "counterfactual_candidate_kind": str(row["candidate_kind"]),
        "counterfactual_formal_first_stage_eligible": bool(
            row.get("formal_first_stage_eligible")
            and str(row["candidate_kind"]) == "harvest"
            and str(row["utility_kind"])
            == "fixed_pool_pricing_pressure_auc"
            and str(row.get("trajectory_objective_spec_id") or "")
            == FIXED_POOL_PRICING_PRESSURE_OBJECTIVE_SPEC_V1
            and bool(row.get("online_admission_semantics_match"))
            and all(
                (
                    str(arm["action_id"]) == P0_CONTROL_ACTION_ID
                    or arm.get("promotion_executed") is not None
                )
                for arm in row["arms"]
            )
        ),
        "counterfactual_budget_mode": str(row["budget_mode"]),
        "counterfactual_propensity_use": (
            "recorded_and_clipped_for_support_audit; "
            "not_applied_to_randomized_first_stage_loss"
        ),
        "counterfactual_noop_available": True,
        "counterfactual_memory_adverse_event_rates": (
            memory_adverse_event_rates
        ),
        "counterfactual_noop_memory_adverse_event_rate": mean(
            float(
                arms[P0_CONTROL_ACTION_ID]["memory_adverse_event"]
            )
            for arms in by_replicate.values()
        ),
        "unexplored_candidates_used_as_negative": False,
        "p0_control_used_as_model_candidate": True,
        "post_action_features_exposed_to_model": False,
    }


def audit_oracle_headroom(
    records: Iterable[Mapping[str, Any]],
    *,
    required_scales: Sequence[int] = (20, 30),
    minimum_contexts_per_scale: int = 20,
    minimum_mean_oracle_gain_lcb: float = 0.005,
    minimum_positive_context_fraction_lcb: float = 0.10,
    bootstrap_samples: int = 2000,
    seed: int = 20260724,
    require_native_event_trace: bool = True,
) -> dict[str, Any]:
    """Measure whether any legal ordering action can beat P0 before training.

    The resampling unit is an instance.  Contexts within one instance are
    averaged first so a slow instance with many snapshots cannot dominate the
    gate.  Only route-level, formally compliant interventions are accepted.
    """

    required = tuple(sorted({int(scale) for scale in required_scales}))
    if not required:
        raise ValueError("oracle headroom audit requires at least one scale")
    if minimum_contexts_per_scale <= 0:
        raise ValueError("minimum contexts per scale must be positive")
    if bootstrap_samples < 100:
        raise ValueError("oracle headroom audit requires at least 100 bootstraps")
    normalized_rows: list[dict[str, Any]] = []
    rejection_reasons: dict[str, int] = defaultdict(int)
    seen_contexts: dict[tuple[str, str, int], str] = {}
    duplicate_context_count = 0
    received_count = 0
    for payload in records:
        received_count += 1
        try:
            row = validate_counterfactual_trajectory_record(payload)
        except Exception:
            rejection_reasons["invalid_counterfactual_record"] += 1
            continue
        targets = materialize_counterfactual_targets(
            row,
            candidate_ids=row["candidate_ids"],
        )
        if not bool(
            targets["counterfactual_formal_first_stage_eligible"]
        ):
            rejection_reasons["not_formal_route_intervention"] += 1
            continue
        if bool(row.get("calibration_used")) or bool(
            row.get("protected_final_test_used")
        ):
            rejection_reasons["protected_or_calibration_data"] += 1
            continue
        is_rmp_rollout = str(
            row.get("utility_kind") or ""
        ) in {
            "rmp_progress_auc",
            "fixed_pool_pricing_pressure_auc",
        }
        if is_rmp_rollout:
            if not bool(row.get("rmp_rollout_trace_valid")):
                rejection_reasons["rmp_rollout_trace_missing_or_invalid"] += 1
                continue
            if str(row.get("event_time_source") or "") != (
                "fixed_p0_rmp_rollout_v1"
            ):
                rejection_reasons["event_time_source_not_fixed_rmp"] += 1
                continue
        elif require_native_event_trace:
            if not bool(row.get("native_event_trace_valid")):
                rejection_reasons[
                    "native_event_trace_missing_or_invalid"
                ] += 1
                continue
            if str(row.get("event_time_source") or "") != (
                "native_best_reduced_cost_events_v1"
            ):
                rejection_reasons["event_time_source_not_native"] += 1
                continue
        context_key = (
            str(row["instance_content_hash"]),
            str(row["rmp_context_hash"]),
            int(row["scale"]),
        )
        content_hash = stable_payload_hash(row)
        previous_hash = seen_contexts.get(context_key)
        if previous_hash is not None:
            duplicate_context_count += 1
            if previous_hash != content_hash:
                rejection_reasons["conflicting_duplicate_context"] += 1
            continue
        seen_contexts[context_key] = content_hash
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
        normalized_rows.append(
            {
                "scale": int(row["scale"]),
                "instance_content_hash": str(
                    row["instance_content_hash"]
                ),
                "rmp_context_hash": str(row["rmp_context_hash"]),
                "oracle_gain": oracle_gain,
                "positive": oracle_gain >= MIN_PRACTICAL_ADVANTAGE,
                "candidate_count": len(row["candidate_ids"]),
                "probed_candidate_count": sum(
                    bool(value)
                    for value in targets[
                        "counterfactual_probe_mask"
                    ]
                ),
            }
        )

    by_scale_instance: dict[int, dict[str, list[dict[str, Any]]]] = (
        defaultdict(lambda: defaultdict(list))
    )
    for row in normalized_rows:
        by_scale_instance[row["scale"]][
            row["instance_content_hash"]
        ].append(row)
    rng = random.Random(int(seed))
    scale_reports: dict[str, dict[str, Any]] = {}
    for scale in sorted(set(by_scale_instance) | set(required)):
        instances = by_scale_instance.get(scale, {})
        context_count = sum(len(values) for values in instances.values())
        instance_summaries = [
            {
                "oracle_gain": mean(
                    float(row["oracle_gain"]) for row in rows
                ),
                "positive_fraction": mean(
                    float(bool(row["positive"])) for row in rows
                ),
            }
            for _, rows in sorted(instances.items())
        ]
        mean_gain = (
            0.0
            if not instance_summaries
            else mean(row["oracle_gain"] for row in instance_summaries)
        )
        positive_fraction = (
            0.0
            if not instance_summaries
            else mean(
                row["positive_fraction"] for row in instance_summaries
            )
        )
        gain_bootstrap: list[float] = []
        fraction_bootstrap: list[float] = []
        for _ in range(bootstrap_samples):
            if not instance_summaries:
                gain_bootstrap.append(0.0)
                fraction_bootstrap.append(0.0)
                continue
            sampled = [
                instance_summaries[
                    rng.randrange(len(instance_summaries))
                ]
                for _ in range(len(instance_summaries))
            ]
            gain_bootstrap.append(
                mean(row["oracle_gain"] for row in sampled)
            )
            fraction_bootstrap.append(
                mean(row["positive_fraction"] for row in sampled)
            )
        gain_lcb = _empirical_quantile(gain_bootstrap, 0.025)
        fraction_lcb = _empirical_quantile(
            fraction_bootstrap, 0.025
        )
        enough_contexts = context_count >= minimum_contexts_per_scale
        scale_reports[str(scale)] = {
            "scale": scale,
            "context_count": context_count,
            "instance_count": len(instance_summaries),
            "instance_balanced_mean_oracle_gain": mean_gain,
            "instance_bootstrap_mean_oracle_gain_lcb95": gain_lcb,
            "instance_balanced_positive_context_fraction": (
                positive_fraction
            ),
            "instance_bootstrap_positive_context_fraction_lcb95": (
                fraction_lcb
            ),
            "minimum_context_count_gate": enough_contexts,
            "mean_oracle_gain_lcb_gate": (
                gain_lcb >= minimum_mean_oracle_gain_lcb
            ),
            "positive_context_fraction_lcb_gate": (
                fraction_lcb
                >= minimum_positive_context_fraction_lcb
            ),
            "eligible": bool(
                enough_contexts
                and gain_lcb >= minimum_mean_oracle_gain_lcb
                and fraction_lcb
                >= minimum_positive_context_fraction_lcb
            ),
        }
    missing_or_failed = [
        scale
        for scale in required
        if not bool(scale_reports.get(str(scale), {}).get("eligible"))
    ]
    invalid_or_leaky_count = sum(rejection_reasons.values())
    passed = bool(
        not missing_or_failed
        and normalized_rows
        and invalid_or_leaky_count == 0
    )
    required_gain_lcbs = [
        float(
            scale_reports[str(scale)][
                "instance_bootstrap_mean_oracle_gain_lcb95"
            ]
        )
        for scale in required
        if str(scale) in scale_reports
    ]
    return {
        "schema_version": ORACLE_HEADROOM_AUDIT_SCHEMA_V1,
        "passed": passed,
        "training_authorized": passed,
        "required_scales": list(required),
        "required_scale_failures": missing_or_failed,
        "record_count_received": received_count,
        "formal_context_count_accepted": len(normalized_rows),
        "duplicate_context_count": duplicate_context_count,
        "rejection_reasons": dict(sorted(rejection_reasons.items())),
        "scale_reports": scale_reports,
        "worst_required_scale_mean_oracle_gain_lcb95": (
            None if not required_gain_lcbs else min(required_gain_lcbs)
        ),
        "minimum_contexts_per_scale": minimum_contexts_per_scale,
        "minimum_mean_oracle_gain_lcb": (
            minimum_mean_oracle_gain_lcb
        ),
        "minimum_positive_context_fraction_lcb": (
            minimum_positive_context_fraction_lcb
        ),
        "bootstrap_unit": "instance_after_context_averaging",
        "bootstrap_samples": bootstrap_samples,
        "seed": int(seed),
        "require_native_event_trace": require_native_event_trace,
        "calibration_used": False,
        "protected_final_test_used": False,
        "unexplored_candidates_used_as_negative": False,
        "failure_action": (
            ""
            if passed
            else "stop_model_training_and_revise_ordering_action"
        ),
    }


def _empirical_quantile(values: Sequence[float], probability: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(float(value) for value in values)
    index = max(
        0,
        min(
            len(ordered) - 1,
            int(probability * (len(ordered) - 1)),
        ),
    )
    return ordered[index]


def trajectory_utility(
    arm: Mapping[str, Any],
    *,
    budget_sec: float,
    utility_kind: str,
    rc_scale: float,
) -> float:
    """Integrate a conservative step curve over the matched wall budget."""

    points = tuple(dict(point) for point in arm["trajectory"])
    previous_time = 0.0
    current_value = 0.0
    area = 0.0
    for point in points:
        elapsed = float(point["elapsed_sec"])
        area += max(0.0, elapsed - previous_time) * current_value
        if utility_kind in {
            "rmp_progress_auc",
            "fixed_pool_pricing_pressure_auc",
        }:
            # This is a state trajectory, not a best-so-far discovery
            # trajectory.  Taking a running max hid later dual-pressure
            # regressions and overstated one-step promotions.
            current_value = float(point["rmp_progress"])
        else:
            true_rc = point.get("best_true_rc")
            if true_rc is not None:
                current_value = max(
                    current_value,
                    min(1.0, max(0.0, -float(true_rc) / rc_scale)),
                )
        previous_time = elapsed
    area += max(0.0, float(budget_sec) - previous_time) * current_value
    return float(area / float(budget_sec))


def first_event_observation(
    arm: Mapping[str, Any],
    *,
    budget_sec: float,
    utility_kind: str = "negative_discovery_auc",
) -> tuple[float, bool]:
    for point in arm["trajectory"]:
        if (
            utility_kind
            in {
                "rmp_progress_auc",
                "fixed_pool_pricing_pressure_auc",
            }
            and float(point.get("rmp_progress") or 0.0) > 0.0
        ):
            return float(point["elapsed_sec"]), True
        if (
            utility_kind
            not in {
                "rmp_progress_auc",
                "fixed_pool_pricing_pressure_auc",
            }
            and point.get("best_true_rc") is not None
        ):
            return float(point["elapsed_sec"]), True
    followup = min(
        float(budget_sec),
        max(float(point["elapsed_sec"]) for point in arm["trajectory"]),
    )
    return followup, False


def _normalize_arm(
    payload: Mapping[str, Any],
    *,
    candidate_ids: tuple[str, ...],
    budget_sec: float,
    legal_universe_hash: str,
) -> dict[str, Any]:
    arm = dict(payload)
    action_id = str(arm.get("action_id") or "")
    if action_id != P0_CONTROL_ACTION_ID and action_id not in candidate_ids:
        raise ValueError("intervention action is outside the legal universe")
    kind = str(arm.get("intervention_kind") or "")
    expected_kind = (
        "control" if action_id == P0_CONTROL_ACTION_ID else "promote_next"
    )
    if kind != expected_kind:
        raise ValueError("counterfactual intervention kind/action mismatch")
    replicate_id = str(arm.get("replicate_id") or "")
    if not replicate_id:
        raise ValueError("counterfactual arm requires replicate_id")
    propensity = float(arm.get("propensity") or 0.0)
    if not isfinite(propensity) or propensity <= 0.0 or propensity > 1.0:
        raise ValueError("counterfactual arm requires propensity in (0, 1]")
    if float(arm.get("action_sampling_probability") or 0.0) != propensity:
        raise ValueError("action propensity fields must agree")
    for field in (
        "probe_policy_id",
        "action_selection_reason",
        "run_order",
        "machine_block_id",
    ):
        value = arm.get(field)
        if value is None or value == "":
            raise ValueError(f"counterfactual arm requires {field}")
    if int(arm.get("candidate_pool_size") or 0) != len(candidate_ids):
        raise ValueError("counterfactual candidate pool size mismatch")
    if action_id == P0_CONTROL_ACTION_ID:
        if arm.get("candidate_position_under_p0") is not None:
            raise ValueError("P0 no-op has no candidate position")
    else:
        position = int(arm.get("candidate_position_under_p0") or 0)
        if position < 1 or position > len(candidate_ids):
            raise ValueError("candidate P0 position is out of range")
    for field in (
        "promotion_requested",
        "promotion_candidate_id",
        "promotion_installed",
        "promotion_executed",
        "actual_execution_rank",
        "first_effective_action_id",
        "treatment_compliance",
        "noncompliance_reason",
    ):
        if field not in arm:
            raise ValueError(
                f"counterfactual arm requires treatment field {field}"
            )
    if action_id == P0_CONTROL_ACTION_ID and bool(
        arm["promotion_requested"]
    ):
        raise ValueError("P0 no-op cannot request a promotion")
    if action_id == P0_CONTROL_ACTION_ID:
        if arm["promotion_candidate_id"] not in {None, ""}:
            raise ValueError("P0 no-op cannot name a promotion candidate")
    elif str(arm["promotion_candidate_id"] or "") != action_id:
        raise ValueError(
            "promotion candidate must equal the interventional action"
        )
    termination_reason = str(arm.get("termination_reason") or "")
    if not termination_reason:
        raise ValueError("counterfactual arm requires termination_reason")
    memory_adverse_event = bool(arm.get("memory_adverse_event"))
    if memory_adverse_event != (
        termination_reason in MEMORY_COMPETING_RISK_REASONS
    ):
        raise ValueError("memory competing-risk semantics mismatch")
    if str(arm.get("legal_universe_hash_before_sort") or "") != (
        legal_universe_hash
    ):
        raise ValueError("intervention legal universe differs from control")
    if str(
        arm.get("legal_universe_hash_after_sort")
        or arm.get("legal_universe_hash_before_sort")
        or ""
    ) != legal_universe_hash:
        raise ValueError("intervention changed the legal universe")
    for field in (
        "guidance_filter_count",
        "guidance_arc_drop_count",
        "guidance_label_drop_count",
        "guidance_branch_pair_drop_count",
    ):
        if int(arm.get(field) or 0) != 0:
            raise ValueError(f"counterfactual intervention filtered work: {field}")
    if bool(arm.get("labels_dropped")):
        raise ValueError("counterfactual intervention dropped labels")
    if not bool(arm.get("binding_match", True)):
        raise ValueError("counterfactual intervention binding mismatch")

    raw_points = tuple(dict(point) for point in arm.get("trajectory", ()))
    if not raw_points:
        raise ValueError("counterfactual arm has no trajectory points")
    points: list[dict[str, Any]] = []
    previous_time = -1.0
    previous_rc: float | None = None
    for raw_point in raw_points:
        elapsed = float(raw_point.get("elapsed_sec") or 0.0)
        if (
            not isfinite(elapsed)
            or elapsed <= previous_time
            or elapsed <= 0.0
            or elapsed > budget_sec + 1.0e-9
        ):
            raise ValueError(
                "trajectory times must be finite, increasing, and within budget"
            )
        true_rc = raw_point.get("best_true_rc")
        if true_rc is not None:
            true_rc = float(true_rc)
            if not isfinite(true_rc) or true_rc >= 0.0:
                raise ValueError("trajectory discovery RC must be finite and negative")
            if previous_rc is not None and true_rc > previous_rc + 1.0e-12:
                raise ValueError("best-RC trajectory must be monotone")
            previous_rc = true_rc
        progress = raw_point.get("rmp_progress")
        if progress is not None:
            progress = float(progress)
            if not isfinite(progress) or progress < 0.0:
                raise ValueError("RMP progress must be finite and nonnegative")
        points.append(
            {
                **raw_point,
                "elapsed_sec": elapsed,
                "best_true_rc": true_rc,
                "rmp_progress": progress,
            }
        )
        previous_time = elapsed
    return {
        **arm,
        "action_id": action_id,
        "intervention_kind": kind,
        "replicate_id": replicate_id,
        "propensity": propensity,
        "memory_adverse_event": memory_adverse_event,
        "termination_reason": termination_reason,
        "trajectory": points,
    }


def _validate_fixed_pool_pressure_points(
    arms: Sequence[Mapping[str, Any]],
) -> None:
    """Bind the formal pressure target to one unambiguous formula."""

    for arm in arms:
        for point in arm["trajectory"]:
            mass = float(
                point.get("fixed_pool_negative_mass_reduction")
            )
            count = float(
                point.get("fixed_pool_negative_count_reduction")
            )
            progress = float(point.get("rmp_progress"))
            if any(
                not isfinite(value) or value < 0.0 or value > 1.0
                for value in (mass, count, progress)
            ):
                raise ValueError(
                    "fixed-pool pressure components must be finite in [0,1]"
                )
            expected = 0.5 * mass + 0.5 * count
            if abs(progress - expected) > 1.0e-9:
                raise ValueError(
                    "fixed-pool pressure does not match equal-mass/count spec"
                )


def _conservative_soft_targets(
    conservative_advantages: Mapping[str, float],
    *,
    temperature: float,
) -> dict[str, float]:
    values = {
        P0_CONTROL_ACTION_ID: 0.0,
        **{
            str(action_id): float(value)
            for action_id, value in conservative_advantages.items()
        },
    }
    maximum = max(values.values())
    exponentials = {
        action_id: exp((value - maximum) / float(temperature))
        for action_id, value in values.items()
    }
    denominator = sum(exponentials.values())
    if denominator <= 0.0 or not isfinite(denominator):
        raise ValueError("conservative soft target normalization failed")
    return {
        action_id: value / denominator
        for action_id, value in exponentials.items()
    }


def _standard_error(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    observed_mean = mean(values)
    variance = sum(
        (float(value) - observed_mean) ** 2 for value in values
    ) / float(len(values) - 1)
    return float((variance / len(values)) ** 0.5)
