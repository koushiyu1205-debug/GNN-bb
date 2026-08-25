"""Machine-readable V2 gates for the GAT-only research chain."""

from __future__ import annotations

from collections import defaultdict
from math import isfinite
from typing import Mapping, Sequence

from lunar_ice_bpc.guidance.context_queue_portfolio_gates import (
    MatchedContextOutcome,
    geometric_mean,
)


def assess_v2_arm_scale_admission(
    outcomes: Sequence[MatchedContextOutcome], *, arm: str, scale: int
):
    rows = [
        row for row in outcomes
        if row.arm == arm and row.scale == int(scale) and row.partition == "train"
    ]
    determined = [row for row in rows if row.determined]
    strong = [row for row in determined if row.strong_benefit]
    neutral_harm = [row for row in determined if not row.strong_benefit]
    redlines = sorted({value for row in rows for value in row.correctness_redlines})
    violations = []
    if redlines:
        violations.append("CORRECTNESS_REDLINE")
    if len(determined) < 18:
        violations.append("DETERMINED_TRAIN_CONTEXTS_LT_18")
    if len({row.instance_hash for row in determined}) < 9:
        violations.append("DETERMINED_TRAIN_INSTANCES_LT_9")
    if len(strong) < 3 or len({row.instance_hash for row in strong}) < 3:
        violations.append("STRONG_BENEFIT_DIVERSITY_LT_3")
    if len(neutral_harm) < 4 or len({row.instance_hash for row in neutral_harm}) < 3:
        violations.append("NEUTRAL_HARM_DIVERSITY_FAILED")
    return {
        "arm": str(arm), "scale": int(scale), "admitted": not violations,
        "forced_veto": bool(violations),
        "determined_contexts": len(determined),
        "determined_instances": len({row.instance_hash for row in determined}),
        "strong_benefit_contexts": len(strong),
        "strong_benefit_instances": len({row.instance_hash for row in strong}),
        "neutral_or_harm_contexts": len(neutral_harm),
        "neutral_or_harm_instances": len({row.instance_hash for row in neutral_harm}),
        "correctness_redlines": redlines,
        "violations": violations,
    }


def assess_v2_qgr1_force_on(
    outcomes: Sequence[MatchedContextOutcome],
    telemetry_by_context: Mapping[str, Mapping[str, float]],
):
    rows = [row for row in outcomes if row.arm == "QGR1"]
    determined = [row for row in rows if row.determined]
    redlines = sorted({value for row in rows for value in row.correctness_redlines})
    violations = []
    if len(determined) != 8 or len({row.instance_hash for row in determined}) != 8:
        violations.append("QGR1_FORCE_ON_NOT_8_DISTINCT_INSTANCES")
    if redlines:
        violations.append("CORRECTNESS_REDLINE")
    ratios = [float(row.ratio) for row in determined]
    overall = geometric_mean(ratios) if len(ratios) == 8 else None
    if overall is None or overall >= 0.98:
        violations.append("QGR1_OVERALL_GM_NOT_LT_0_98")
    scales = {}
    for scale in (30, 50):
        selected = [row for row in determined if row.scale == scale]
        gm = geometric_mean([float(row.ratio) for row in selected])
        beneficial = len({row.instance_hash for row in selected if row.beneficial})
        scales[str(scale)] = {
            "contexts": len(selected), "gm": gm,
            "beneficial_instances": beneficial,
        }
        if len(selected) != 4 or gm is None or gm >= 1.0:
            violations.append(f"QGR1_SCALE{scale}_GM_OR_COUNT_FAILED")
        if beneficial < 2:
            violations.append(f"QGR1_SCALE{scale}_BENEFICIAL_INSTANCES_LT_2")
    if any(row.harmful for row in determined):
        violations.append("QGR1_HARMFUL_CONTEXT")
    if any(row.q0_complete_arm_censored for row in rows):
        violations.append("QGR1_Q0_COMPLETE_ARM_CENSORED")
    telemetry_violations = []
    for row in determined:
        values = dict(telemetry_by_context.get(row.context_id) or {})
        reorder = float(values.get("reordered_label_fraction", float("inf")))
        scoring = float(values.get("scoring_wall_sec", float("inf")))
        proof = float(values.get("proof_wall_sec", 0.0))
        if not isfinite(reorder) or reorder > 0.15:
            telemetry_violations.append(f"{row.context_id}:REORDER_FRACTION_GT_0_15")
        if not all(isfinite(value) for value in (scoring, proof)) or proof <= 0.0 or scoring / proof > 0.02:
            telemetry_violations.append(f"{row.context_id}:SCORING_FRACTION_GT_0_02")
    if telemetry_violations:
        violations.append("QGR1_TELEMETRY_GATE_FAILED")
    return {
        "admitted": not violations,
        "hard_veto": bool(violations),
        "overall_gm": overall,
        "scale_summary": scales,
        "correctness_redlines": redlines,
        "telemetry_violations": telemetry_violations,
        "violations": sorted(set(violations)),
    }


def measured_v2_portfolio_oracle(
    outcomes: Sequence[MatchedContextOutcome],
    *, admitted_arms_by_scale: Mapping[int | str, Sequence[str]],
):
    result = {}
    reasons = []
    for scale in (30, 50):
        allowed = set(admitted_arms_by_scale.get(
            scale, admitted_arms_by_scale.get(str(scale), ())
        ))
        by_context = defaultdict(list)
        for row in outcomes:
            if row.scale == scale and row.arm in allowed:
                by_context[row.context_id].append(row)
        ratios, winners = [], []
        all_determined = [
            row for rows in by_context.values() for row in rows if row.determined
        ]
        redlines = sorted({
            value for rows in by_context.values() for row in rows
            for value in row.correctness_redlines
        })
        for context_id, rows in sorted(by_context.items()):
            determined = [row for row in rows if row.determined]
            winner = min(determined, key=lambda row: (float(row.ratio), row.arm)) if determined else None
            ratio = min(1.0, float(winner.ratio)) if winner else 1.0
            ratios.append(ratio)
            if winner is not None and ratio < 1.0:
                winners.append(winner)
        gm = geometric_mean(ratios)
        winner_instances = len({row.instance_hash for row in winners})
        categories = {
            "beneficial_instances": len({row.instance_hash for row in all_determined if float(row.ratio) < 0.98}),
            "neutral_instances": len({row.instance_hash for row in all_determined if 0.98 <= float(row.ratio) < 1.05}),
            "harm_instances": len({row.instance_hash for row in all_determined if float(row.ratio) >= 1.05}),
        }
        passed = bool(
            gm is not None and gm <= 0.95 and winner_instances >= 5
            and all(value >= 1 for value in categories.values()) and not redlines
        )
        result[str(scale)] = {
            "context_count": len(ratios), "oracle_gm": gm,
            "non_q0_winner_instances": winner_instances,
            **categories, "correctness_redlines": redlines, "passed": passed,
        }
        if not passed:
            reasons.append(f"NO_SCALE{scale}_GAT_PORTFOLIO_HEADROOM")
    return {
        "selector_training_authorized": not reasons,
        "scales": result,
        "terminal_reasons": reasons,
    }


def assess_gat_calibration(
    *, full: Mapping[str, object], no_message: Mapping[str, object],
    shuffled_topology: Mapping[str, object],
):
    violations = []
    if int(full.get("harmful_activations") or 0):
        violations.append("GAT_CALIBRATION_HARMFUL_ACTIVATION")
    scales = dict(full.get("scales") or {})
    for scale in (30, 50):
        row = dict(scales.get(str(scale)) or {})
        if int(row.get("activation_instances") or 0) < 2:
            violations.append(f"GAT_SCALE{scale}_ACTIVATION_INSTANCES_LT_2")
        gm = row.get("selected_action_gm")
        if gm is None or float(gm) >= 1.0:
            violations.append(f"GAT_SCALE{scale}_GM_NOT_LT_1")
    full_rank = float(full.get("rank_accuracy") or 0.0)
    control_ranks = [
        float(no_message.get("rank_accuracy") or 0.0),
        float(shuffled_topology.get("rank_accuracy") or 0.0),
    ]
    if any(full_rank < value for value in control_ranks):
        violations.append("GAT_RANK_ACCURACY_BELOW_TOPOLOGY_CONTROL")
    if not any(full_rank - value >= 0.02 for value in control_ranks):
        violations.append("GAT_TOPOLOGY_RANK_DROP_LT_0_02")
    full_gm = float(full.get("combined_gm") or float("inf"))
    if any(full_gm > float(row.get("combined_gm") or float("inf")) for row in (no_message, shuffled_topology)):
        violations.append("GAT_GM_ABOVE_TOPOLOGY_CONTROL")
    if full.get("correctness_redlines"):
        violations.append("CORRECTNESS_REDLINE")
    return {"passed": not violations, "violations": sorted(set(violations))}


def assess_gat_heldout_advantage(
    summaries: Mapping[str, Mapping[str, object]], *, preparation_p99_ms: float,
):
    required = {"gat", "mlp", "linear", "no_message", "shuffled_topology"}
    if set(summaries) != required:
        raise ValueError("heldout comparison must freeze all five models")
    gat = dict(summaries["gat"])
    violations = []
    for scale in (30, 50):
        row = dict(dict(gat.get("scales") or {}).get(str(scale)) or {})
        if int(row.get("activation_instances") or 0) < 2:
            violations.append(f"HELDOUT_SCALE{scale}_ACTIVATION_INSTANCES_LT_2")
        gm = row.get("net_gm")
        if gm is None or float(gm) >= 1.0:
            violations.append(f"HELDOUT_SCALE{scale}_GM_NOT_LT_1")
        if any(int(row.get(key) or 0) for key in (
            "harmful_activations", "adverse_activations", "censored_activations",
        )):
            violations.append(f"HELDOUT_SCALE{scale}_HARM_CENSOR")
    if float(preparation_p99_ms) > 10.0:
        violations.append("HELDOUT_PREPARATION_P99_GT_10MS")
    for control in ("mlp", "linear"):
        row = summaries[control]
        if not (
            float(gat["worst_scale_gm"]) < float(row["worst_scale_gm"])
            and float(gat["combined_gm"]) < float(row["combined_gm"])
        ):
            violations.append(f"NO_GAT_ADVANTAGE_OVER_{control.upper()}")
    for control in ("no_message", "shuffled_topology"):
        row = summaries[control]
        if (
            float(gat["worst_scale_gm"]) > float(row["worst_scale_gm"])
            or float(gat["combined_gm"]) > float(row["combined_gm"])
        ):
            violations.append(f"GAT_WORSE_THAN_{control.upper()}")
    if gat.get("correctness_redlines"):
        violations.append("CORRECTNESS_REDLINE")
    return {
        "passed": not violations,
        "terminal_reason": (
            None if not violations else
            "NO_GAT_ADVANTAGE" if any("GAT_ADVANTAGE" in row for row in violations)
            else "HELDOUT_FRESH_FAILED"
        ),
        "violations": sorted(set(violations)),
    }

