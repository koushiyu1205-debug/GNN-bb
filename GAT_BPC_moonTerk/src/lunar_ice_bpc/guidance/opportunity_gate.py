"""Training-before-deployment audit for sparse guidance opportunities.

The audit deliberately separates two data streams:

``sentinel``
    Contexts selected by a pre-action randomized rule.  Only this stream may
    estimate population opportunity density and amortized runtime ROI.

``targeted``
    Enriched contexts used to obtain enough positive counterfactual labels for
    training.  These rows are reported, but never enter population estimates.

The module has no torch dependency and is safe to use before importing a
checkpoint or constructing graph tensors.
"""

from __future__ import annotations

from collections import defaultdict
from math import isfinite, sqrt
import random
from statistics import mean, stdev
from typing import Any, Iterable, Mapping, Sequence


OPPORTUNITY_OBSERVATION_SCHEMA_V1 = (
    "lunar_ice_bpc.gat_opportunity_observation.v1"
)
OPPORTUNITY_ROI_AUDIT_SCHEMA_V1 = (
    "lunar_ice_bpc.gat_opportunity_roi_audit.v1"
)
SUPPORTED_SAMPLING_STREAMS = frozenset({"sentinel", "targeted"})
SUPPORTED_MODEL_COST_SOURCES = frozenset(
    {"fresh_runtime_measured", "frozen_budget_upper_bound"}
)
SUPPORTED_TIME_BENEFIT_SOURCES = frozenset(
    {"matched_end_to_end_counterfactual_lcb"}
)
SUPPORTED_OUTCOME_STATUSES = frozenset(
    {
        "FORMAL_COUNTERFACTUAL",
        "STRUCTURAL_ZERO_NO_LEGAL_ACTION",
        "STRUCTURAL_ZERO_ACTION_EQUIVALENT",
        "CENSORED_RESOURCE_OR_DISCOVERY",
        "NOT_PROBED_RANDOM",
    }
)
MATCHED_END_TO_END_MEASUREMENT_SCHEMA_V2 = (
    "lunar_ice_bpc.gat_matched_end_to_end_measurement.v2"
)
COMPLETE_EXACT_STATUSES = frozenset({"BPC_OPTIMAL", "OPTIMAL"})


def attach_matched_end_to_end_benefit(
    observation: Mapping[str, Any],
    measurements: Iterable[Mapping[str, Any]],
    *,
    risk_kappa: float = 1.96,
    objective_tolerance: float = 1.0e-8,
) -> dict[str, Any]:
    """Attach a conservative solver-only wall-time benefit to one context.

    Measurements compare the P0 no-op against one frozen oracle action under
    matched seeds and budgets.  Exact status, objective, legal universe and
    no-filter invariants must agree.  Model cost remains separate.
    """

    row = validate_opportunity_observation(observation)
    if not bool(row["formal_label_available"]) or not bool(
        row["action_value_identifiable"]
    ):
        raise ValueError(
            "end-to-end benefit requires an identifiable formal context"
        )
    if not isfinite(risk_kappa) or risk_kappa < 0.0:
        raise ValueError("risk kappa must be finite and nonnegative")
    normalized: list[dict[str, Any]] = []
    seen_replicates: set[str] = set()
    action_ids: set[str] = set()
    action_binding_hashes: set[str] = set()
    matched_budget_ids: set[str] = set()
    objective_spec_ids: set[str] = set()
    for payload in measurements:
        measurement = dict(payload)
        if str(measurement.get("observation_id") or "") != str(
            row["observation_id"]
        ):
            raise ValueError("end-to-end observation binding mismatch")
        if str(measurement.get("schema_version") or "") != (
            MATCHED_END_TO_END_MEASUREMENT_SCHEMA_V2
        ):
            raise ValueError("end-to-end measurement schema mismatch")
        if str(measurement.get("instance_content_hash") or "") != str(
            row["instance_content_hash"]
        ):
            raise ValueError("end-to-end instance binding mismatch")
        if str(measurement.get("rmp_context_hash") or "") != str(
            row["rmp_context_hash"]
        ):
            raise ValueError("end-to-end RMP-context binding mismatch")
        if str(measurement.get("selection_manifest_hash") or "") != str(
            row.get("selection_manifest_hash") or ""
        ):
            raise ValueError("end-to-end sentinel-manifest binding mismatch")
        if not str(measurement.get("executed_objective_spec_id") or ""):
            raise ValueError("end-to-end objective spec is missing")
        if str(measurement["executed_objective_spec_id"]) != str(
            row["executed_objective_spec_id"]
        ):
            raise ValueError("end-to-end objective spec binding mismatch")
        if not bool(measurement.get("action_frozen_before_outcome")):
            raise ValueError("end-to-end action was not frozen pre-outcome")
        if not bool(measurement.get("fresh_process_pair")):
            raise ValueError("end-to-end pair was not run in fresh processes")
        if not bool(measurement.get("pair_order_randomized")):
            raise ValueError("end-to-end pair order was not randomized")
        if str(measurement.get("pair_run_order") or "") not in {
            "P0_THEN_ACTION",
            "ACTION_THEN_P0",
        }:
            raise ValueError("end-to-end pair run order is invalid")
        if not str(measurement.get("matched_budget_id") or ""):
            raise ValueError("end-to-end matched budget is missing")
        if not str(
            measurement.get("canonical_action_binding_hash") or ""
        ):
            raise ValueError("end-to-end action binding is missing")
        for field in (
            "promotion_requested",
            "promotion_installed",
            "promotion_executed",
            "actual_execution_rank",
            "treatment_compliance",
        ):
            if field not in measurement:
                raise ValueError(
                    f"end-to-end treatment compliance lacks {field}"
                )
        if not bool(measurement["promotion_requested"]):
            raise ValueError("end-to-end action did not request promotion")
        action_binding_hashes.add(
            str(measurement["canonical_action_binding_hash"])
        )
        matched_budget_ids.add(str(measurement["matched_budget_id"]))
        objective_spec_ids.add(
            str(measurement["executed_objective_spec_id"])
        )
        replicate_id = str(measurement.get("replicate_id") or "")
        if not replicate_id or replicate_id in seen_replicates:
            raise ValueError("end-to-end replicate IDs must be unique")
        seen_replicates.add(replicate_id)
        action_id = str(measurement.get("oracle_action_id") or "")
        if not action_id or action_id == "P0_KEEP_ORDER":
            raise ValueError("end-to-end measurement requires an action")
        action_ids.add(action_id)
        p0_wall = _positive_finite(
            measurement, "p0_solver_wall_sec"
        )
        action_wall = _positive_finite(
            measurement, "action_solver_wall_sec"
        )
        p0_status = str(measurement.get("p0_exact_status") or "")
        action_status = str(measurement.get("action_exact_status") or "")
        if p0_status != action_status:
            raise ValueError("end-to-end exact statuses differ")
        if p0_status not in COMPLETE_EXACT_STATUSES:
            raise ValueError(
                "end-to-end wall-time benefit requires complete exact runs"
            )
        if not bool(measurement.get("p0_exact_complete")) or not bool(
            measurement.get("action_exact_complete")
        ):
            raise ValueError("end-to-end exact completion flags are false")
        p0_objective = float(measurement["p0_objective"])
        action_objective = float(measurement["action_objective"])
        if (
            not isfinite(p0_objective)
            or not isfinite(action_objective)
            or abs(p0_objective - action_objective)
            > float(objective_tolerance)
        ):
            raise ValueError("end-to-end exact objectives differ")
        universe_hash = str(
            measurement.get("legal_universe_hash_before_sort") or ""
        )
        if (
            not universe_hash
            or universe_hash
            != str(
                measurement.get(
                    "action_legal_universe_hash_before_sort"
                )
                or ""
            )
        ):
            raise ValueError("end-to-end legal universes differ")
        if (
            int(measurement.get("guidance_filter_count") or 0) != 0
            or bool(measurement.get("extra_incomplete"))
            or bool(measurement.get("certificate_semantics_changed"))
        ):
            raise ValueError("end-to-end safety invariant failed")
        normalized.append(
            {
                "replicate_id": replicate_id,
                "p0_solver_wall_sec": p0_wall,
                "action_solver_wall_sec": action_wall,
                "saving_sec": p0_wall - action_wall,
            }
        )
    if len(normalized) < 3:
        raise ValueError(
            "end-to-end benefit requires at least three paired replicates"
        )
    if len(action_ids) != 1:
        raise ValueError("end-to-end replicates must freeze one oracle action")
    if (
        len(action_binding_hashes) != 1
        or len(matched_budget_ids) != 1
        or len(objective_spec_ids) != 1
    ):
        raise ValueError(
            "end-to-end replicates changed action binding, budget, or "
            "objective spec"
        )
    savings = [item["saving_sec"] for item in normalized]
    standard_error = (
        0.0
        if len(savings) < 2
        else stdev(savings) / sqrt(float(len(savings)))
    )
    mean_saving = mean(savings)
    signed_lcb = mean_saving - float(risk_kappa) * standard_error
    signed_ucb = mean_saving + float(risk_kappa) * standard_error
    conservative_lcb = max(0.0, signed_lcb)
    enriched = {
        **row,
        "oracle_solver_time_saved_sec_lcb": conservative_lcb,
        "oracle_solver_time_saved_sec_ucb": max(0.0, signed_ucb),
        "time_benefit_source": (
            "matched_end_to_end_counterfactual_lcb"
        ),
        "solver_time_benefit_measurement": {
            "oracle_action_id": next(iter(action_ids)),
            "canonical_action_binding_hash": next(
                iter(action_binding_hashes)
            ),
            "matched_budget_id": next(iter(matched_budget_ids)),
            "executed_objective_spec_id": next(
                iter(objective_spec_ids)
            ),
            "replicate_count": len(normalized),
            "paired_mean_saving_sec": mean_saving,
            "paired_standard_error_sec": standard_error,
            "paired_saving_sec_lcb95_signed": signed_lcb,
            "paired_saving_sec_ucb95_signed": signed_ucb,
            "risk_kappa": float(risk_kappa),
            "objective_tolerance": float(objective_tolerance),
            "model_cost_included": False,
            "exact_result_equal": True,
            "legal_universe_equal": True,
            "guidance_filter_count": 0,
            "extra_incomplete": False,
        },
    }
    return validate_opportunity_observation(enriched)


def validate_opportunity_observation(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Normalize one opportunity-funnel observation or reject leakage."""

    row = dict(payload)
    if str(row.get("schema_version") or "") != (
        OPPORTUNITY_OBSERVATION_SCHEMA_V1
    ):
        raise ValueError("opportunity observation schema mismatch")
    for key in (
        "observation_id",
        "instance_content_hash",
        "rmp_context_hash",
        "executed_objective_spec_id",
    ):
        if not str(row.get(key) or ""):
            raise ValueError(f"opportunity observation requires {key}")
    scale = int(row.get("scale") or 0)
    if scale not in {5, 10, 20, 30, 50, 100}:
        raise ValueError("opportunity observation has unsupported scale")
    stream = str(row.get("sampling_stream") or "")
    if stream not in SUPPORTED_SAMPLING_STREAMS:
        raise ValueError("unsupported opportunity sampling stream")
    probability = float(row.get("selection_probability") or 0.0)
    if (
        not isfinite(probability)
        or probability <= 0.0
        or probability > 1.0
    ):
        raise ValueError("selection probability must be in (0, 1]")
    pre_action_randomized = bool(row.get("selection_decision_pre_action"))
    target_used = bool(row.get("target_condition_used_for_selection"))
    if stream == "sentinel" and (
        not pre_action_randomized or target_used
    ):
        raise ValueError(
            "sentinel selection must be pre-action and target-independent"
        )
    if bool(row.get("calibration_used")) or bool(
        row.get("protected_final_test_used")
    ):
        raise ValueError("opportunity audit cannot use protected data")

    sequence_id = int(row.get("context_sequence_id") or 0)
    if sequence_id < 0:
        raise ValueError("context sequence ID must be nonnegative")
    solver_elapsed_sec = float(row.get("solver_elapsed_sec") or 0.0)
    if not isfinite(solver_elapsed_sec) or solver_elapsed_sec < 0.0:
        raise ValueError("solver elapsed time must be finite and nonnegative")
    legal_action_count = int(row.get("legal_action_count") or 0)
    if legal_action_count < 0:
        raise ValueError("legal action count must be nonnegative")

    cheap_gate_eligible = bool(row.get("cheap_gate_eligible"))
    model_would_be_invoked = bool(row.get("model_would_be_invoked"))
    if model_would_be_invoked and not cheap_gate_eligible:
        raise ValueError("model cannot be invoked when cheap gate is closed")
    formal_label = bool(row.get("formal_label_available"))
    identifiable = bool(row.get("action_value_identifiable"))
    outcome_status = str(row.get("opportunity_outcome_status") or "")
    if outcome_status not in SUPPORTED_OUTCOME_STATUSES:
        raise ValueError("unsupported opportunity outcome status")
    if formal_label != (outcome_status == "FORMAL_COUNTERFACTUAL"):
        raise ValueError("formal-label flag and outcome status disagree")
    if (
        outcome_status == "STRUCTURAL_ZERO_NO_LEGAL_ACTION"
        and legal_action_count >= 2
    ):
        raise ValueError("structural zero cannot have two legal actions")
    if (
        outcome_status == "STRUCTURAL_ZERO_ACTION_EQUIVALENT"
        and legal_action_count < 2
    ):
        raise ValueError(
            "action-equivalent structural zero requires legal alternatives"
        )
    if formal_label and legal_action_count < 2:
        raise ValueError("formal label requires at least two legal actions")
    if identifiable and not formal_label:
        raise ValueError("identifiable action value requires a formal label")

    oracle_gain = float(row.get("oracle_solver_gain") or 0.0)
    if not isfinite(oracle_gain) or oracle_gain < 0.0:
        raise ValueError("oracle solver gain must be finite and nonnegative")
    if not formal_label and oracle_gain != 0.0:
        raise ValueError("unlabeled context cannot carry oracle solver gain")

    benefit_raw = row.get("oracle_solver_time_saved_sec_lcb")
    benefit = None if benefit_raw is None else float(benefit_raw)
    if benefit is not None and (
        not isfinite(benefit) or benefit < 0.0
    ):
        raise ValueError("oracle time benefit must be finite and nonnegative")
    benefit_source = str(row.get("time_benefit_source") or "")
    if benefit is None and benefit_source:
        raise ValueError("time benefit source supplied without a benefit")
    if benefit is not None and (
        not identifiable
        or benefit_source not in SUPPORTED_TIME_BENEFIT_SOURCES
    ):
        raise ValueError(
            "time benefit requires an identifiable matched end-to-end LCB"
        )
    benefit_ucb_raw = row.get("oracle_solver_time_saved_sec_ucb")
    benefit_ucb = (
        benefit
        if benefit_ucb_raw is None and benefit is not None
        else (
            None
            if benefit_ucb_raw is None
            else float(benefit_ucb_raw)
        )
    )
    if benefit_ucb is not None and (
        not isfinite(benefit_ucb)
        or benefit_ucb < 0.0
        or benefit is None
        or benefit_ucb + 1.0e-12 < benefit
    ):
        raise ValueError(
            "oracle time-benefit UCB must be finite and not below LCB"
        )

    gate_cost = _nonnegative_cost(row, "cheap_gate_wall_sec")
    startup_share = _nonnegative_cost(
        row, "startup_cost_share_sec"
    )
    model_cost_raw = row.get("model_call_wall_sec_upper_bound")
    model_cost = (
        None if model_cost_raw is None else float(model_cost_raw)
    )
    if model_cost is not None and (
        not isfinite(model_cost) or model_cost < 0.0
    ):
        raise ValueError("model call cost must be finite and nonnegative")
    model_cost_source = str(row.get("model_cost_source") or "")
    if model_would_be_invoked and (
        model_cost is None
        or model_cost_source not in SUPPORTED_MODEL_COST_SOURCES
    ):
        raise ValueError(
            "an invoked model requires a measured or frozen upper-bound cost"
        )
    if not model_would_be_invoked and model_cost is None:
        model_cost = 0.0
    if model_cost is None:
        model_cost = 0.0

    normalized = {
        **row,
        "scale": scale,
        "sampling_stream": stream,
        "selection_probability": probability,
        "context_sequence_id": sequence_id,
        "solver_elapsed_sec": solver_elapsed_sec,
        "legal_action_count": legal_action_count,
        "cheap_gate_eligible": cheap_gate_eligible,
        "model_would_be_invoked": model_would_be_invoked,
        "formal_label_available": formal_label,
        "opportunity_outcome_status": outcome_status,
        "action_value_identifiable": identifiable,
        "oracle_solver_gain": oracle_gain,
        "oracle_solver_time_saved_sec_lcb": benefit,
        "oracle_solver_time_saved_sec_ucb": benefit_ucb,
        "cheap_gate_wall_sec": gate_cost,
        "startup_cost_share_sec": startup_share,
        "model_call_wall_sec_upper_bound": model_cost,
        "model_cost_source": model_cost_source,
        "time_benefit_source": benefit_source,
    }
    return normalized


def audit_opportunity_roi(
    observations: Iterable[Mapping[str, Any]],
    *,
    required_scales: Sequence[int] = (20, 30),
    minimum_sentinel_contexts_per_scale: int = 20,
    minimum_sentinel_instances_per_scale: int = 20,
    minimum_positive_context_fraction_lcb: float = 0.02,
    minimum_net_gain_sec_per_context_lcb: float = 0.0,
    maximum_censored_context_fraction: float = 0.10,
    bootstrap_samples: int = 2000,
    seed: int = 20260724,
) -> dict[str, Any]:
    """Audit opportunity density and a perfect abstaining policy's net ROI.

    The perfect policy may choose the best observed action or P0 no-op, but it
    can only act in contexts admitted by the cheap pre-import gate.  It pays
    the cheap-gate cost on every sentinel context and model/startup cost on
    every context where the model would be invoked.  This is intentionally an
    optimistic upper bound on model decision quality and a conservative bound
    on measured wall-time benefit.
    """

    required = tuple(sorted({int(scale) for scale in required_scales}))
    if not required:
        raise ValueError("opportunity ROI audit requires a scale")
    if minimum_sentinel_contexts_per_scale <= 0:
        raise ValueError("minimum sentinel contexts must be positive")
    if minimum_sentinel_instances_per_scale <= 0:
        raise ValueError("minimum sentinel instances must be positive")
    if bootstrap_samples < 100:
        raise ValueError("opportunity ROI audit requires 100 bootstraps")
    if (
        not isfinite(maximum_censored_context_fraction)
        or maximum_censored_context_fraction < 0.0
        or maximum_censored_context_fraction > 1.0
    ):
        raise ValueError("maximum censored fraction must be in [0,1]")

    accepted: list[dict[str, Any]] = []
    rejection_reasons: dict[str, int] = defaultdict(int)
    received = 0
    seen: set[str] = set()
    duplicates = 0
    context_keys: dict[tuple[str, int, str, str], str] = {}
    duplicate_contexts = 0
    for payload in observations:
        received += 1
        try:
            row = validate_opportunity_observation(payload)
        except Exception:
            rejection_reasons["invalid_opportunity_observation"] += 1
            continue
        observation_id = str(row["observation_id"])
        if observation_id in seen:
            duplicates += 1
            continue
        seen.add(observation_id)
        if str(row["sampling_stream"]) == "sentinel":
            context_key = (
                str(row.get("selection_manifest_hash") or ""),
                int(row["scale"]),
                str(row["instance_content_hash"]),
                str(row["rmp_context_hash"]),
            )
            if context_key in context_keys:
                duplicate_contexts += 1
                rejection_reasons["duplicate_sentinel_context"] += 1
                continue
            context_keys[context_key] = observation_id
        accepted.append(row)

    sentinel = [
        row for row in accepted if row["sampling_stream"] == "sentinel"
    ]
    targeted = [
        row for row in accepted if row["sampling_stream"] == "targeted"
    ]
    sentinel_manifest_hashes = {
        str(row.get("selection_manifest_hash") or "")
        for row in sentinel
    }
    if "" in sentinel_manifest_hashes:
        rejection_reasons["missing_sentinel_manifest_hash"] += 1
    if len(sentinel_manifest_hashes) > 1:
        rejection_reasons["mixed_sentinel_manifests"] += 1
    by_scale_instance: dict[int, dict[str, list[dict[str, Any]]]] = (
        defaultdict(lambda: defaultdict(list))
    )
    for row in sentinel:
        by_scale_instance[int(row["scale"])][
            str(row["instance_content_hash"])
        ].append(row)

    rng = random.Random(int(seed))
    scale_reports: dict[str, dict[str, Any]] = {}
    for scale in sorted(set(by_scale_instance) | set(required)):
        instances = by_scale_instance.get(scale, {})
        rows = [row for values in instances.values() for row in values]
        outcome_observed_rows = [
            row for row in rows if _outcome_observed(row)
        ]
        summaries = [
            _instance_summary(values)
            for _, values in sorted(instances.items())
        ]
        outcome_observed_summaries = [
            item for item in summaries if item["outcome_observed_weight"] > 0
        ]
        positive_fraction = _ratio_of_weighted_sums(
            outcome_observed_rows, numerator_key="_positive"
        )
        funnel = {
            "cheap_gate_eligible_rate": _ratio_of_weighted_sums(
                rows, numerator_key="_cheap_gate"
            ),
            "legal_multi_action_rate": _ratio_of_weighted_sums(
                rows, numerator_key="_legal_multi_action"
            ),
            "formal_label_yield_rate": _ratio_of_weighted_sums(
                rows, numerator_key="_formal_label"
            ),
            "identifiable_label_rate": _ratio_of_weighted_sums(
                rows, numerator_key="_identifiable"
            ),
            "oracle_positive_rate": positive_fraction,
            "model_invocation_rate": _ratio_of_weighted_sums(
                rows, numerator_key="_model_invoked"
            ),
            "censored_or_unprobed_rate": _ratio_of_weighted_sums(
                rows, numerator_key="_censored_or_unprobed"
            ),
        }
        mean_net = (
            0.0
            if not summaries
            else mean(item["net_gain_sec_per_context"] for item in summaries)
        )
        mean_cost = (
            0.0
            if not summaries
            else mean(item["cost_sec_per_context"] for item in summaries)
        )
        positive_benefits = [
            float(row["oracle_solver_time_saved_sec_lcb"])
            for row in rows
            if _is_positive(row)
            and row["oracle_solver_time_saved_sec_lcb"] is not None
            and bool(row["cheap_gate_eligible"])
        ]
        mean_benefit_when_positive = (
            0.0 if not positive_benefits else mean(positive_benefits)
        )
        break_even_rate = (
            None
            if mean_benefit_when_positive <= 0.0
            else mean_cost / mean_benefit_when_positive
        )
        positive_bootstrap: list[float] = []
        net_lower_bootstrap: list[float] = []
        net_upper_bootstrap: list[float] = []
        for _ in range(bootstrap_samples):
            if not summaries:
                positive_bootstrap.append(0.0)
                net_lower_bootstrap.append(-0.0)
                net_upper_bootstrap.append(-0.0)
                continue
            sampled = [
                summaries[rng.randrange(len(summaries))]
                for _ in range(len(summaries))
            ]
            sampled_observed = [
                item
                for item in sampled
                if item["outcome_observed_weight"] > 0
            ]
            positive_bootstrap.append(
                0.0
                if not sampled_observed
                else mean(
                    item["positive_fraction"]
                    for item in sampled_observed
                )
            )
            net_lower_bootstrap.append(
                mean(
                    item["net_gain_sec_per_context_lcb"]
                    for item in sampled
                )
            )
            net_upper_bootstrap.append(
                mean(
                    item["net_gain_sec_per_context_ucb"]
                    for item in sampled
                )
            )
        positive_lcb = _quantile(positive_bootstrap, 0.025)
        positive_ucb = _quantile(positive_bootstrap, 0.975)
        net_lcb = _quantile(net_lower_bootstrap, 0.025)
        net_ucb = _quantile(net_upper_bootstrap, 0.975)
        missing_time_benefit_count = sum(
            bool(row["action_value_identifiable"])
            and float(row["oracle_solver_gain"]) > 0.0
            and row["oracle_solver_time_saved_sec_lcb"] is None
            for row in rows
        )
        unmeasured_effective_action_count = sum(
            int(row.get("route_admission_effective_action_count") or 0)
            > 0
            and row["oracle_solver_time_saved_sec_lcb"] is None
            for row in rows
        )
        missing_model_cost_count = sum(
            bool(row["model_would_be_invoked"])
            and not str(row["model_cost_source"])
            for row in rows
        )
        enough_contexts = (
            len(outcome_observed_rows)
            >= minimum_sentinel_contexts_per_scale
        )
        enough_instances = (
            len(outcome_observed_summaries)
            >= minimum_sentinel_instances_per_scale
        )
        measurement_complete = (
            missing_time_benefit_count == 0
            and unmeasured_effective_action_count == 0
            and missing_model_cost_count == 0
        )
        censored_fraction = funnel["censored_or_unprobed_rate"]
        censor_gate = (
            censored_fraction <= maximum_censored_context_fraction
        )
        density_gate = (
            positive_lcb >= minimum_positive_context_fraction_lcb
        )
        net_gate = (
            net_lcb >= minimum_net_gain_sec_per_context_lcb
            and net_lcb > 0.0
        )
        eligible = bool(
            enough_contexts
            and enough_instances
            and measurement_complete
            and censor_gate
            and density_gate
            and net_gate
        )
        scale_reports[str(scale)] = {
            "scale": scale,
            "sentinel_context_count": len(rows),
            "sentinel_instance_count": len(summaries),
            "outcome_observed_context_count": len(
                outcome_observed_rows
            ),
            "outcome_observed_instance_count": len(
                outcome_observed_summaries
            ),
            "targeted_context_count_excluded_from_population_estimates": sum(
                int(row["scale"]) == scale for row in targeted
            ),
            "estimated_population_context_count_horvitz_thompson": sum(
                1.0 / float(row["selection_probability"])
                for row in rows
            ),
            "funnel": funnel,
            "instance_balanced_positive_context_fraction": (
                0.0
                if not outcome_observed_summaries
                else mean(
                    item["positive_fraction"]
                    for item in outcome_observed_summaries
                )
            ),
            "instance_bootstrap_positive_context_fraction_lcb95": (
                positive_lcb
            ),
            "instance_bootstrap_positive_context_fraction_ucb95": (
                positive_ucb
            ),
            "conservative_perfect_policy_net_gain_sec_per_context": (
                mean_net if measurement_complete else None
            ),
            "instance_bootstrap_net_gain_sec_per_context_lcb95": (
                net_lcb if measurement_complete else None
            ),
            "instance_bootstrap_net_gain_sec_per_context_ucb95": (
                net_ucb if measurement_complete else None
            ),
            "mean_guidance_cost_sec_per_context": mean_cost,
            "mean_reachable_time_benefit_sec_when_positive": (
                mean_benefit_when_positive
            ),
            "break_even_positive_context_fraction": break_even_rate,
            "missing_end_to_end_time_benefit_count": (
                missing_time_benefit_count
            ),
            "unmeasured_effective_action_context_count": (
                unmeasured_effective_action_count
            ),
            "missing_model_cost_count": missing_model_cost_count,
            "minimum_sentinel_context_gate": enough_contexts,
            "minimum_sentinel_instance_gate": enough_instances,
            "measurement_complete_gate": measurement_complete,
            "censoring_rate_gate": censor_gate,
            "positive_opportunity_density_gate": density_gate,
            "perfect_policy_net_benefit_gate": net_gate,
            "eligible": eligible,
            "sequential_decision": (
                "PASS_TO_TRAINING"
                if eligible
                else (
                    "STOP_ACTION_FAMILY_AS_FUTILE"
                    if measurement_complete
                    and censor_gate
                    and enough_contexts
                    and enough_instances
                    and net_ucb <= 0.0
                    else "CONTINUE_SENTINEL_COLLECTION"
                )
            ),
            "positive_arrival_gaps": _positive_arrival_gaps(rows),
        }

    failed = [
        scale
        for scale in required
        if not bool(scale_reports.get(str(scale), {}).get("eligible"))
    ]
    required_reports = [
        scale_reports.get(str(scale), {}) for scale in required
    ]
    required_sample_complete = bool(
        required_reports
        and all(
            bool(report.get("minimum_sentinel_context_gate"))
            and bool(report.get("minimum_sentinel_instance_gate"))
            and bool(report.get("measurement_complete_gate"))
            and bool(report.get("censoring_rate_gate"))
            for report in required_reports
        )
    )
    equal_scale_net_lower_bootstrap: list[float] = []
    equal_scale_net_upper_bootstrap: list[float] = []
    if required_sample_complete:
        instance_summaries_by_scale = {
            scale: [
                _instance_summary(values)
                for _, values in sorted(
                    by_scale_instance.get(scale, {}).items()
                )
            ]
            for scale in required
        }
        for _ in range(bootstrap_samples):
            scale_lower_means = []
            scale_upper_means = []
            for scale in required:
                summaries = instance_summaries_by_scale[scale]
                sampled = [
                    summaries[rng.randrange(len(summaries))]
                    for _ in range(len(summaries))
                ]
                scale_lower_means.append(
                    mean(
                        item["net_gain_sec_per_context_lcb"]
                        for item in sampled
                    )
                )
                scale_upper_means.append(
                    mean(
                        item["net_gain_sec_per_context_ucb"]
                        for item in sampled
                    )
                )
            equal_scale_net_lower_bootstrap.append(
                mean(scale_lower_means)
            )
            equal_scale_net_upper_bootstrap.append(
                mean(scale_upper_means)
            )
    overall_net_lcb = _quantile(
        equal_scale_net_lower_bootstrap, 0.025
    )
    overall_net_ucb = _quantile(
        equal_scale_net_upper_bootstrap, 0.975
    )
    preliminary_pass = bool(
        not failed and sentinel and not rejection_reasons
    )
    passed = bool(
        preliminary_pass
        and overall_net_lcb is not None
        and overall_net_lcb > 0.0
    )
    route_admission_decision = (
        "ALLOW_LINEAR_TRAINING"
        if passed
        else (
            "TERMINATE_ROUTE_ADMISSION"
            if required_sample_complete
            and overall_net_ucb is not None
            and overall_net_ucb <= 0.0
            else "CONTINUE_MATCHED_PAIRED_COLLECTION"
        )
    )
    return {
        "schema_version": OPPORTUNITY_ROI_AUDIT_SCHEMA_V1,
        "passed": passed,
        "training_authorized": passed,
        "linear_training_authorized": passed,
        "route_admission_decision": route_admission_decision,
        "required_sample_complete": required_sample_complete,
        "equal_scale_perfect_policy_net_gain_sec_per_context_lcb95": (
            overall_net_lcb
        ),
        "equal_scale_perfect_policy_net_gain_sec_per_context_ucb95": (
            overall_net_ucb
        ),
        "required_scales": list(required),
        "required_scale_failures": failed,
        "record_count_received": received,
        "record_count_accepted": len(accepted),
        "sentinel_context_count": len(sentinel),
        "targeted_context_count": len(targeted),
        "targeted_rows_excluded_from_population_estimates": True,
        "duplicate_observation_count": duplicates,
        "duplicate_context_count": duplicate_contexts,
        "sentinel_manifest_hashes": sorted(sentinel_manifest_hashes),
        "rejection_reasons": dict(sorted(rejection_reasons.items())),
        "scale_reports": scale_reports,
        "minimum_sentinel_contexts_per_scale": (
            minimum_sentinel_contexts_per_scale
        ),
        "minimum_sentinel_instances_per_scale": (
            minimum_sentinel_instances_per_scale
        ),
        "minimum_positive_context_fraction_lcb": (
            minimum_positive_context_fraction_lcb
        ),
        "minimum_net_gain_sec_per_context_lcb": (
            minimum_net_gain_sec_per_context_lcb
        ),
        "maximum_censored_context_fraction": (
            maximum_censored_context_fraction
        ),
        "bootstrap_unit": "instance_after_context_averaging",
        "bootstrap_samples": bootstrap_samples,
        "seed": int(seed),
        "perfect_policy_definition": (
            "best_reachable_observed_action_or_p0_noop_minus_cheap_gate_"
            "model_call_and_amortized_startup_cost"
        ),
        "failure_action": (
            ""
            if passed
            else "block_training_and_online_promotion_until_unbiased_"
            "opportunity_density_and_net_roi_are_identifiable"
        ),
        "calibration_used": False,
        "protected_final_test_used": False,
    }


def _instance_summary(rows: Sequence[dict[str, Any]]) -> dict[str, float]:
    weights = [1.0 / float(row["selection_probability"]) for row in rows]
    denominator = sum(weights)
    observed = [
        (row, weight)
        for row, weight in zip(rows, weights, strict=True)
        if _outcome_observed(row)
    ]
    observed_denominator = sum(weight for _, weight in observed)
    positive = (
        0.0
        if observed_denominator <= 0.0
        else sum(
            weight * float(_is_positive(row))
            for row, weight in observed
        )
        / observed_denominator
    )
    benefit_lcb = sum(
        weight * _reachable_benefit(row, bound="lcb")
        for row, weight in zip(rows, weights, strict=True)
    ) / denominator
    benefit_ucb = sum(
        weight * _reachable_benefit(row, bound="ucb")
        for row, weight in zip(rows, weights, strict=True)
    ) / denominator
    cost = sum(
        weight * _guidance_cost(row)
        for row, weight in zip(rows, weights, strict=True)
    ) / denominator
    return {
        "positive_fraction": positive,
        "outcome_observed_weight": observed_denominator,
        "benefit_sec_per_context": benefit_lcb,
        "benefit_sec_per_context_lcb": benefit_lcb,
        "benefit_sec_per_context_ucb": benefit_ucb,
        "cost_sec_per_context": cost,
        "net_gain_sec_per_context": benefit_lcb - cost,
        "net_gain_sec_per_context_lcb": benefit_lcb - cost,
        "net_gain_sec_per_context_ucb": benefit_ucb - cost,
    }


def _ratio_of_weighted_sums(
    rows: Sequence[dict[str, Any]],
    *,
    numerator_key: str,
) -> float:
    if not rows:
        return 0.0
    weighted_total = sum(
        1.0 / float(row["selection_probability"]) for row in rows
    )
    if numerator_key == "_positive":
        predicate = _is_positive
    else:
        predicates = {
            "_cheap_gate": lambda row: bool(row["cheap_gate_eligible"]),
            "_legal_multi_action": lambda row: int(
                row["legal_action_count"]
            )
            >= 2,
            "_formal_label": lambda row: bool(
                row["formal_label_available"]
            ),
            "_identifiable": lambda row: bool(
                row["action_value_identifiable"]
            ),
            "_model_invoked": lambda row: bool(
                row["model_would_be_invoked"]
            ),
            "_censored_or_unprobed": lambda row: not _outcome_observed(
                row
            ),
        }
        predicate = predicates[numerator_key]
    return sum(
        (1.0 / float(row["selection_probability"]))
        * float(predicate(row))
        for row in rows
    ) / weighted_total


def _is_positive(row: Mapping[str, Any]) -> bool:
    return bool(
        row["formal_label_available"]
        and row["action_value_identifiable"]
        and float(row["oracle_solver_gain"]) > 0.0
    )


def _outcome_observed(row: Mapping[str, Any]) -> bool:
    return str(row["opportunity_outcome_status"]) in {
        "FORMAL_COUNTERFACTUAL",
        "STRUCTURAL_ZERO_NO_LEGAL_ACTION",
        "STRUCTURAL_ZERO_ACTION_EQUIVALENT",
    }


def _reachable_benefit(
    row: Mapping[str, Any], *, bound: str
) -> float:
    if not bool(row["cheap_gate_eligible"]) or not _is_positive(row):
        return 0.0
    key = (
        "oracle_solver_time_saved_sec_lcb"
        if bound == "lcb"
        else "oracle_solver_time_saved_sec_ucb"
    )
    value = row[key]
    return 0.0 if value is None else float(value)


def _guidance_cost(row: Mapping[str, Any]) -> float:
    return float(row["cheap_gate_wall_sec"]) + (
        float(row["model_call_wall_sec_upper_bound"])
        + float(row["startup_cost_share_sec"])
        if bool(row["model_would_be_invoked"])
        else 0.0
    )


def _positive_arrival_gaps(
    rows: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    """Report observed gaps only; Horvitz-Thompson rates remain authoritative."""

    by_instance: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_instance[str(row["instance_content_hash"])].append(row)
    call_gaps: list[int] = []
    wall_gaps: list[float] = []
    for values in by_instance.values():
        positives = sorted(
            (row for row in values if _is_positive(row)),
            key=lambda row: (
                int(row["context_sequence_id"]),
                float(row["solver_elapsed_sec"]),
            ),
        )
        for left, right in zip(positives, positives[1:]):
            call_gaps.append(
                int(right["context_sequence_id"])
                - int(left["context_sequence_id"])
            )
            wall_gaps.append(
                max(
                    0.0,
                    float(right["solver_elapsed_sec"])
                    - float(left["solver_elapsed_sec"]),
                )
            )
    return {
        "observed_pair_count": len(call_gaps),
        "call_gap_p50": _quantile(call_gaps, 0.5),
        "call_gap_p90": _quantile(call_gaps, 0.9),
        "call_gap_max": max(call_gaps, default=None),
        "wall_sec_gap_p50": _quantile(wall_gaps, 0.5),
        "wall_sec_gap_p90": _quantile(wall_gaps, 0.9),
        "wall_sec_gap_max": max(wall_gaps, default=None),
        "population_rate_estimator": (
            "inverse_probability_weighted_funnel_not_observed_gap"
        ),
    }


def _nonnegative_cost(row: Mapping[str, Any], key: str) -> float:
    value = float(row.get(key) or 0.0)
    if not isfinite(value) or value < 0.0:
        raise ValueError(f"{key} must be finite and nonnegative")
    return value


def _positive_finite(row: Mapping[str, Any], key: str) -> float:
    value = float(row.get(key) or 0.0)
    if not isfinite(value) or value <= 0.0:
        raise ValueError(f"{key} must be finite and positive")
    return value


def _quantile(values: Sequence[float | int], probability: float) -> float | None:
    if not values:
        return None
    ordered = sorted(float(value) for value in values)
    index = max(
        0,
        min(
            len(ordered) - 1,
            int(probability * (len(ordered) - 1)),
        ),
    )
    return ordered[index]
