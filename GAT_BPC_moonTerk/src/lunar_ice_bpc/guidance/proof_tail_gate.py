"""Exact-safe paired targets for the proof-tail policy gate.

The learning action is deliberately binary: keep the cached P0 ordering
(``QC0``) or install the fixed deeper-first ordering (``QD1``) once for one
exact-pricing context.  No model score is evaluated inside the label loop.
"""

from __future__ import annotations

from math import isfinite, log
import random
from statistics import median
from typing import Any, Iterable, Mapping

from lunar_ice_bpc.exact.core.cuts import stable_payload_hash


PROOF_TAIL_POLICY_PAIR_SCHEMA_V1 = (
    "lunar_ice_bpc.proof_tail_policy_pair.v1"
)
PROOF_TAIL_GATE_DATASET_SCHEMA_V1 = (
    "lunar_ice_bpc.proof_tail_gate_dataset.v1"
)
PROOF_TAIL_CONTROL_POLICY = "QC0"
PROOF_TAIL_ACTION_POLICY = "QD1"
PROOF_TAIL_POLICIES = frozenset(
    {PROOF_TAIL_CONTROL_POLICY, PROOF_TAIL_ACTION_POLICY}
)


def proof_tail_context_payload(
    arm: Mapping[str, Any],
) -> dict[str, Any]:
    """Return the policy-independent mathematical and budget identity."""

    binding = dict(arm.get("replay_binding") or {})
    telemetry = dict(arm.get("proof_telemetry") or {})
    required_binding = (
        "instance_hash",
        "pricing_mode",
        "phase",
        "objective_mode",
        "mathematical_dual_hash",
        "branch_context_hash",
        "full_cut_context_hash",
        "projected_pricing_cut_context_hash",
        "cut_lineage_hash",
        "live_cut_policy_hash",
        "separator_policy_version",
        "cut_state_schema_version",
    )
    missing = [
        field for field in required_binding if field not in binding
    ]
    if missing:
        raise ValueError(
            "proof-tail replay binding is incomplete: "
            + ",".join(missing)
        )
    if str(binding["pricing_mode"]) != "exact_proof":
        raise ValueError("proof-tail gate requires exact-proof arms")
    return {
        "instance_hash": str(binding["instance_hash"]),
        "scale": int(arm.get("scale") or 0),
        "phase": str(binding["phase"]),
        "objective_mode": str(binding["objective_mode"]),
        "mathematical_dual_hash": str(
            binding["mathematical_dual_hash"]
        ),
        "branch_context_hash": str(binding["branch_context_hash"]),
        "full_cut_context_hash": str(
            binding["full_cut_context_hash"]
        ),
        "projected_pricing_cut_context_hash": str(
            binding["projected_pricing_cut_context_hash"]
        ),
        "cut_lineage_hash": str(binding["cut_lineage_hash"]),
        "live_cut_policy_hash": str(
            binding["live_cut_policy_hash"]
        ),
        "separator_policy_version": str(
            binding["separator_policy_version"]
        ),
        "cut_state_schema_version": str(
            binding["cut_state_schema_version"]
        ),
        "completion_bound_enabled": bool(
            arm.get("completion_bound_enabled")
        ),
        "subset_dominance_enabled": bool(
            arm.get("subset_dominance_enabled")
        ),
        "negative_eps": float(arm.get("negative_eps") or 1.0e-6),
        "dominance_eps": float(
            arm.get("dominance_eps") or 1.0e-12
        ),
        "resource_eps": float(arm.get("resource_eps") or 1.0e-9),
        "wall_time_limit_sec": float(
            arm.get("wall_time_limit_sec") or 0.0
        ),
        "memory_limit_gb": float(
            arm.get("memory_limit_gb") or 0.0
        ),
        "native_engine_build_hash": str(
            telemetry.get("native_engine_build_hash")
            or arm.get("native_engine_build_hash")
            or ""
        ),
    }


def proof_tail_context_hash(arm: Mapping[str, Any]) -> str:
    return stable_payload_hash(proof_tail_context_payload(arm))


def validate_proof_tail_arm(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    arm = dict(payload)
    policy = str(arm.get("proof_queue_policy_id") or "")
    if policy not in PROOF_TAIL_POLICIES:
        raise ValueError("proof-tail arm must be QC0 or QD1")
    if not bool(arm.get("fresh_process_arm")):
        raise ValueError("proof-tail arm must run in a fresh process")
    if str(arm.get("engine_status") or "") != "COMPLETE":
        raise ValueError("proof-tail arm is not complete")
    if (
        not bool(arm.get("search_exhaustive"))
        or not bool(arm.get("frontier_empty"))
        or bool(arm.get("labels_dropped"))
    ):
        raise ValueError("proof-tail arm lacks exhaustive safe closure")
    if tuple(arm.get("certificate_blockers") or ()):
        raise ValueError("proof-tail arm has certificate blockers")
    if not bool(arm.get("can_enter_certificate_audit")):
        raise ValueError("proof-tail arm cannot enter certificate audit")
    matching = dict(
        arm.get("same_mathematical_request_as_source") or {}
    )
    if not matching or not all(bool(value) for value in matching.values()):
        raise ValueError("proof-tail source mathematical binding differs")
    native_wall = float(
        (arm.get("proof_telemetry") or {}).get("wall_time_seconds")
        or 0.0
    )
    fresh_wall = float(arm.get("total_fresh_process_wall_sec") or 0.0)
    if (
        not isfinite(native_wall)
        or native_wall <= 0.0
        or not isfinite(fresh_wall)
        or fresh_wall <= 0.0
    ):
        raise ValueError("proof-tail arm wall time is invalid")
    context = proof_tail_context_payload(arm)
    if context["scale"] not in {5, 10, 20, 30, 50, 100}:
        raise ValueError("proof-tail arm scale is unsupported")
    arm["proof_tail_context_hash"] = stable_payload_hash(context)
    return arm


def build_proof_tail_policy_pair(
    qc0_payload: Mapping[str, Any],
    qd1_payload: Mapping[str, Any],
    *,
    replicate_id: str,
    pair_run_order: str,
    gate_wall_sec_upper_bound: float = 0.0,
    promotion_margin_sec: float = 0.0,
    rc_tolerance: float = 1.0e-9,
) -> dict[str, Any]:
    """Create one no-leakage QC0/QD1 paired training observation."""

    qc0 = validate_proof_tail_arm(qc0_payload)
    qd1 = validate_proof_tail_arm(qd1_payload)
    if qc0["proof_queue_policy_id"] != PROOF_TAIL_CONTROL_POLICY:
        raise ValueError("first proof-tail arm is not QC0")
    if qd1["proof_queue_policy_id"] != PROOF_TAIL_ACTION_POLICY:
        raise ValueError("second proof-tail arm is not QD1")
    context_hash = str(qc0["proof_tail_context_hash"])
    if str(qd1["proof_tail_context_hash"]) != context_hash:
        raise ValueError("proof-tail pair context binding mismatch")
    replicate = str(replicate_id)
    if not replicate:
        raise ValueError("proof-tail replicate_id is required")
    order = str(pair_run_order)
    if order not in {"QC0_THEN_QD1", "QD1_THEN_QC0"}:
        raise ValueError("proof-tail pair run order is invalid")
    gate_cost = float(gate_wall_sec_upper_bound)
    margin = float(promotion_margin_sec)
    if (
        not isfinite(gate_cost)
        or gate_cost < 0.0
        or not isfinite(margin)
        or margin < 0.0
    ):
        raise ValueError("proof-tail gate cost/margin is invalid")
    _validate_exact_outcome_match(qc0, qd1, tolerance=rc_tolerance)
    qc0_features = dict(qc0.get("pre_call_features") or {})
    qd1_features = dict(qd1.get("pre_call_features") or {})
    if qc0_features != qd1_features:
        raise ValueError("proof-tail pair pre-call features differ")
    qc0_native = _native_wall(qc0)
    qd1_native = _native_wall(qd1)
    qc0_fresh = float(qc0["total_fresh_process_wall_sec"])
    qd1_fresh = float(qd1["total_fresh_process_wall_sec"])
    native_delta = qd1_native - qc0_native
    fresh_delta = qd1_fresh - qc0_fresh
    net_delta = native_delta + gate_cost
    target_policy = (
        PROOF_TAIL_ACTION_POLICY
        if net_delta < -margin
        else PROOF_TAIL_CONTROL_POLICY
    )
    pair = {
        "schema_version": PROOF_TAIL_POLICY_PAIR_SCHEMA_V1,
        "proof_tail_context_hash": context_hash,
        "context": proof_tail_context_payload(qc0),
        "pre_call_features": qc0_features,
        "replicate_id": replicate,
        "pair_run_order": order,
        "pair_order_randomized_pre_outcome": True,
        "control_policy_id": PROOF_TAIL_CONTROL_POLICY,
        "action_policy_id": PROOF_TAIL_ACTION_POLICY,
        "qc0_native_wall_sec": qc0_native,
        "qd1_native_wall_sec": qd1_native,
        "qc0_fresh_wall_sec": qc0_fresh,
        "qd1_fresh_wall_sec": qd1_fresh,
        "native_delta_qd1_minus_qc0_sec": native_delta,
        "fresh_delta_qd1_minus_qc0_sec": fresh_delta,
        "gate_wall_sec_upper_bound": gate_cost,
        "net_delta_qd1_minus_qc0_sec": net_delta,
        "promotion_margin_sec": margin,
        "native_log_cost_ratio_qd1_over_qc0": log(
            (qd1_native + gate_cost) / qc0_native
        ),
        "target_policy_id": target_policy,
        "qd1_net_beneficial": target_policy == PROOF_TAIL_ACTION_POLICY,
        "exact_result_equal": True,
        "guidance_filter_count": 0,
        "labels_dropped": False,
        "extra_incomplete": False,
        "qc0_extended_labels": _telemetry_int(
            qc0, "extended_labels"
        ),
        "qd1_extended_labels": _telemetry_int(
            qd1, "extended_labels"
        ),
        "qc0_dominance_wall_sec": _telemetry_float(
            qc0, "dominance_wall_time_seconds"
        ),
        "qd1_dominance_wall_sec": _telemetry_float(
            qd1, "dominance_wall_time_seconds"
        ),
    }
    pair["pair_hash"] = stable_payload_hash(pair)
    return pair


def build_proof_tail_gate_dataset(
    pairs: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Aggregate repetitions without pretending they are new contexts."""

    normalized = [dict(row) for row in pairs]
    if not normalized:
        raise ValueError("proof-tail gate dataset is empty")
    by_context: dict[str, list[dict[str, Any]]] = {}
    seen_replicates: set[tuple[str, str]] = set()
    for row in normalized:
        if str(row.get("schema_version") or "") != (
            PROOF_TAIL_POLICY_PAIR_SCHEMA_V1
        ):
            raise ValueError("proof-tail pair schema mismatch")
        context_hash = str(row.get("proof_tail_context_hash") or "")
        replicate_id = str(row.get("replicate_id") or "")
        key = (context_hash, replicate_id)
        if not context_hash or not replicate_id or key in seen_replicates:
            raise ValueError("duplicate or missing proof-tail replicate")
        seen_replicates.add(key)
        by_context.setdefault(context_hash, []).append(row)
    contexts = []
    for context_hash, rows in sorted(by_context.items()):
        context_payloads = {
            stable_payload_hash(dict(row.get("context") or {}))
            for row in rows
        }
        if len(context_payloads) != 1:
            raise ValueError("proof-tail context payloads conflict")
        feature_payloads = {
            stable_payload_hash(dict(row.get("pre_call_features") or {}))
            for row in rows
        }
        if len(feature_payloads) != 1:
            raise ValueError("proof-tail pre-call features conflict")
        pre_call_features = dict(rows[0].get("pre_call_features") or {})
        if not pre_call_features:
            raise ValueError("proof-tail pre-call features are missing")
        qc0_native = [float(row["qc0_native_wall_sec"]) for row in rows]
        qd1_native = [float(row["qd1_native_wall_sec"]) for row in rows]
        gate_cost = max(
            float(row["gate_wall_sec_upper_bound"]) for row in rows
        )
        margin = max(float(row["promotion_margin_sec"]) for row in rows)
        median_delta = median(qd1_native) + gate_cost - median(qc0_native)
        contexts.append(
            {
                "proof_tail_context_hash": context_hash,
                "context": dict(rows[0]["context"]),
                "pre_call_features": pre_call_features,
                "replicate_count": len(rows),
                "median_qc0_native_wall_sec": median(qc0_native),
                "median_qd1_native_wall_sec": median(qd1_native),
                "gate_wall_sec_upper_bound": gate_cost,
                "median_net_delta_qd1_minus_qc0_sec": median_delta,
                "target_policy_id": (
                    PROOF_TAIL_ACTION_POLICY
                    if median_delta < -margin
                    else PROOF_TAIL_CONTROL_POLICY
                ),
            }
        )
    payload = {
        "schema_version": PROOF_TAIL_GATE_DATASET_SCHEMA_V1,
        "pair_count": len(normalized),
        "independent_context_count": len(contexts),
        "contexts": contexts,
        "pairs": normalized,
        "repeat_rows_count_as_independent_contexts": False,
    }
    payload["dataset_hash"] = stable_payload_hash(payload)
    return payload


def audit_static_proof_tail_scale_rule(
    dataset: Mapping[str, Any],
    *,
    qd1_scales: Iterable[int] = (30,),
    minimum_contexts_per_scale: int = 20,
    bootstrap_samples: int = 4000,
    bootstrap_seed: int = 629031,
) -> dict[str, Any]:
    """Audit the no-model rule before authorizing any learned gate."""

    payload = dict(dataset)
    if str(payload.get("schema_version") or "") != (
        PROOF_TAIL_GATE_DATASET_SCHEMA_V1
    ):
        raise ValueError("proof-tail gate dataset schema mismatch")
    selected_scales = {int(value) for value in qd1_scales}
    if not selected_scales.issubset({5, 10, 20, 30, 50, 100}):
        raise ValueError("static proof-tail rule has unsupported scale")
    if minimum_contexts_per_scale <= 0 or bootstrap_samples <= 0:
        raise ValueError("static proof-tail audit budget is invalid")
    rows = []
    by_scale: dict[int, list[dict[str, float]]] = {}
    for context in payload.get("contexts", ()):
        row = dict(context)
        scale = int((row.get("context") or {}).get("scale") or 0)
        qc0 = float(row["median_qc0_native_wall_sec"])
        qd1 = float(row["median_qd1_native_wall_sec"])
        gate_cost = float(row.get("gate_wall_sec_upper_bound") or 0.0)
        choose_qd1 = scale in selected_scales
        selected_wall = qd1 + gate_cost if choose_qd1 else qc0
        evaluated = {
            "scale": scale,
            "qc0_wall_sec": qc0,
            "selected_wall_sec": selected_wall,
            "saving_sec": qc0 - selected_wall,
            "selected_policy_id": (
                PROOF_TAIL_ACTION_POLICY
                if choose_qd1
                else PROOF_TAIL_CONTROL_POLICY
            ),
        }
        rows.append(evaluated)
        by_scale.setdefault(scale, []).append(evaluated)
    if not rows:
        raise ValueError("static proof-tail audit has no contexts")
    scale_rows = {}
    for scale, values in sorted(by_scale.items()):
        baseline = sum(row["qc0_wall_sec"] for row in values)
        selected = sum(row["selected_wall_sec"] for row in values)
        scale_savings = [row["saving_sec"] for row in values]
        scale_bootstrap = _bootstrap_means(
            scale_savings,
            samples=bootstrap_samples,
            seed=bootstrap_seed + scale,
        )
        scale_rows[str(scale)] = {
            "context_count": len(values),
            "selected_policy_id": (
                PROOF_TAIL_ACTION_POLICY
                if scale in selected_scales
                else PROOF_TAIL_CONTROL_POLICY
            ),
            "total_qc0_wall_sec": baseline,
            "total_selected_wall_sec": selected,
            "total_saving_sec": baseline - selected,
            "wall_ratio_selected_over_qc0": selected / baseline,
            "worst_context_saving_sec": min(
                row["saving_sec"] for row in values
            ),
            "bootstrap_mean_saving_lcb95_sec": _percentile_lower(
                scale_bootstrap
            ),
            "bootstrap_mean_saving_ucb95_sec": _percentile_upper(
                scale_bootstrap
            ),
        }
    savings = [row["saving_sec"] for row in rows]
    bootstrap_means = _bootstrap_means(
        savings,
        samples=bootstrap_samples,
        seed=bootstrap_seed,
    )
    required_scales = {20, 30}
    quota_met = all(
        len(by_scale.get(scale, ())) >= int(minimum_contexts_per_scale)
        for scale in required_scales
    )
    total_qc0 = sum(row["qc0_wall_sec"] for row in rows)
    total_selected = sum(row["selected_wall_sec"] for row in rows)
    safety_gate_passed = all(
        bool(pair.get("exact_result_equal"))
        and not bool(pair.get("labels_dropped"))
        and not bool(pair.get("extra_incomplete"))
        and int(pair.get("guidance_filter_count") or 0) == 0
        for pair in payload.get("pairs", ())
    )
    active_scale_lcbs = [
        float(scale_rows[str(scale)][
            "bootstrap_mean_saving_lcb95_sec"
        ])
        for scale in sorted(selected_scales)
        if str(scale) in scale_rows
    ]
    statistical_benefit_passed = bool(active_scale_lcbs) and all(
        value > 0.0 for value in active_scale_lcbs
    )
    promotion_passed = bool(
        quota_met
        and safety_gate_passed
        and statistical_benefit_passed
        and _percentile_lower(bootstrap_means) > 0.0
    )
    return {
        "schema_version": (
            "lunar_ice_bpc.proof_tail_static_scale_rule_audit.v1"
        ),
        "rule_id": "scale30_qd1_else_qc0_v1",
        "qd1_scales": sorted(selected_scales),
        "context_count": len(rows),
        "minimum_contexts_per_scale": int(
            minimum_contexts_per_scale
        ),
        "minimum_context_quota_met": quota_met,
        "safety_gate_passed": safety_gate_passed,
        "statistical_benefit_passed": statistical_benefit_passed,
        "by_scale": scale_rows,
        "total_qc0_wall_sec": total_qc0,
        "total_selected_wall_sec": total_selected,
        "wall_ratio_selected_over_qc0": total_selected / total_qc0,
        "mean_saving_sec": sum(savings) / float(len(savings)),
        "bootstrap_mean_saving_lcb95_sec": _percentile_lower(
            bootstrap_means
        ),
        "bootstrap_mean_saving_ucb95_sec": _percentile_upper(
            bootstrap_means
        ),
        "promotion_evaluable": quota_met,
        "promotion_passed": promotion_passed,
        "production_policy_changed": False,
        "learned_model_needed": False if promotion_passed else None,
        "note": (
            "A learned gate is unnecessary if this frozen static rule "
            "passes the full independent-context promotion gate."
        ),
    }


def _bootstrap_means(
    values: list[float],
    *,
    samples: int,
    seed: int,
) -> list[float]:
    if not values:
        raise ValueError("bootstrap requires at least one value")
    randomizer = random.Random(int(seed))
    return sorted(
        sum(
            values[randomizer.randrange(len(values))]
            for _ in values
        )
        / float(len(values))
        for _ in range(int(samples))
    )


def _percentile_lower(values: list[float]) -> float:
    return values[max(0, int(0.025 * len(values)) - 1)]


def _percentile_upper(values: list[float]) -> float:
    return values[
        min(len(values) - 1, int(0.975 * len(values)))
    ]


def _validate_exact_outcome_match(
    qc0: Mapping[str, Any],
    qd1: Mapping[str, Any],
    *,
    tolerance: float,
) -> None:
    qc0_proved = qc0.get("proved_no_rc_below")
    qd1_proved = qd1.get("proved_no_rc_below")
    if (qc0_proved is None) != (qd1_proved is None):
        raise ValueError("proof-tail threshold outcomes differ")
    if qc0_proved is not None and abs(
        float(qc0_proved) - float(qd1_proved)
    ) > float(tolerance):
        raise ValueError("proof-tail proved thresholds differ")
    qc0_exact = bool(qc0.get("global_min_rc_is_exact"))
    qd1_exact = bool(qd1.get("global_min_rc_is_exact"))
    if qc0_exact != qd1_exact:
        raise ValueError("proof-tail global-min exactness differs")
    qc0_min = qc0.get("global_min_rc")
    qd1_min = qd1.get("global_min_rc")
    if (qc0_min is None) != (qd1_min is None):
        raise ValueError("proof-tail global-min outcomes differ")
    if qc0_min is not None and abs(
        float(qc0_min) - float(qd1_min)
    ) > float(tolerance):
        raise ValueError("proof-tail exact global minima differ")


def _native_wall(arm: Mapping[str, Any]) -> float:
    return float(
        (arm.get("proof_telemetry") or {})["wall_time_seconds"]
    )


def _telemetry_int(arm: Mapping[str, Any], key: str) -> int:
    return int((arm.get("proof_telemetry") or {}).get(key) or 0)


def _telemetry_float(arm: Mapping[str, Any], key: str) -> float:
    return float((arm.get("proof_telemetry") or {}).get(key) or 0.0)
