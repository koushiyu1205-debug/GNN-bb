"""Instance-first gates for Interaction-GAT Queue Selector V3.

Fresh repeats are collapsed by the shared exact-safe matrix code.  This module
then gives every instance total weight one, irrespective of how many natural
root contexts it contributes.
"""

from __future__ import annotations

from collections import defaultdict
from math import exp, isfinite, log
from typing import Mapping, Sequence

from lunar_ice_bpc.guidance.context_queue_portfolio_gates import (
    MatchedContextOutcome,
    geometric_mean,
)


def context_weights_by_instance(rows: Sequence[Mapping[str, object]]):
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        counts[str(row["instance_hash"])] += 1
    if not counts:
        raise ValueError("V3 weighting requires at least one context")
    return {
        str(row["context_id"]): 1.0 / counts[str(row["instance_hash"])]
        for row in rows
    }


def instance_geometric_means(
    ratios: Sequence[tuple[str, str, float]],
) -> dict[str, float]:
    """Fold ``(instance, context, ratio)`` rows inside instances first."""

    grouped: dict[str, list[float]] = defaultdict(list)
    seen: set[tuple[str, str]] = set()
    for instance_hash, context_id, ratio in ratios:
        identity = (str(instance_hash), str(context_id))
        value = float(ratio)
        if identity in seen:
            raise ValueError("duplicate context ratio in V3 instance fold")
        if not isfinite(value) or value <= 0.0:
            raise ValueError("V3 ratio must be finite and positive")
        seen.add(identity)
        grouped[identity[0]].append(value)
    return {
        instance_hash: float(geometric_mean(values))
        for instance_hash, values in sorted(grouped.items())
    }


def macro_instance_geometric_mean(
    ratios: Sequence[tuple[str, str, float]],
) -> float | None:
    folded = instance_geometric_means(ratios)
    return geometric_mean(tuple(folded.values()))


def assess_v3_arm_scale_admission(
    outcomes: Sequence[MatchedContextOutcome], *, arm: str, scale: int,
):
    rows = [
        row for row in outcomes
        if row.arm == str(arm) and row.scale == int(scale)
        and row.partition == "train"
    ]
    expected_contexts = len(rows)
    determined = [row for row in rows if row.determined]
    strong_instances = {row.instance_hash for row in determined if row.strong_benefit}
    neutral_harm_instances = {
        row.instance_hash for row in determined if not row.strong_benefit
    }
    redlines = sorted({value for row in rows for value in row.correctness_redlines})
    fraction = len(determined) / expected_contexts if expected_contexts else 0.0
    violations = []
    if redlines:
        violations.append("CORRECTNESS_REDLINE")
    if fraction < 0.75:
        violations.append("DETERMINED_TRAIN_CONTEXT_FRACTION_LT_0_75")
    if len({row.instance_hash for row in determined}) < 11:
        violations.append("DETERMINED_TRAIN_INSTANCES_LT_11")
    if len(strong_instances) < 3:
        violations.append("STRONG_BENEFIT_INSTANCES_LT_3")
    if len(neutral_harm_instances) < 4:
        violations.append("NEUTRAL_HARM_INSTANCES_LT_4")
    return {
        "arm": str(arm),
        "scale": int(scale),
        "admitted": not violations,
        "forced_veto": bool(violations),
        "train_contexts": expected_contexts,
        "determined_contexts": len(determined),
        "determined_context_fraction": fraction,
        "determined_instances": len({row.instance_hash for row in determined}),
        "strong_benefit_instances": len(strong_instances),
        "neutral_or_harm_instances": len(neutral_harm_instances),
        "correctness_redlines": redlines,
        "violations": violations,
    }


def measured_v3_base_portfolio_oracle(
    outcomes: Sequence[MatchedContextOutcome],
    *, admitted_arms_by_scale: Mapping[int | str, Sequence[str]],
):
    """Measure the Q0/QD1/QB1 train-only ceiling in the frozen order."""

    summaries: dict[str, object] = {}
    terminal_reasons = []
    for scale in (30, 50):
        allowed = {
            str(value) for value in admitted_arms_by_scale.get(
                scale, admitted_arms_by_scale.get(str(scale), ())
            )
        }.intersection({"QD1", "QB1"})
        by_context: dict[str, list[MatchedContextOutcome]] = defaultdict(list)
        scale_rows = [
            row for row in outcomes
            if row.scale == scale and row.partition == "train" and row.arm in allowed
        ]
        for row in scale_rows:
            by_context[row.context_id].append(row)
        redlines = sorted({
            value for row in scale_rows for value in row.correctness_redlines
        })
        oracle_rows = []
        winner_instances = set()
        beneficial_instances = set()
        neutral_instances = set()
        harm_instances = set()
        context_winners = {}
        for context_id, rows in sorted(by_context.items()):
            determined = [row for row in rows if row.determined]
            candidates = [(1.0, "Q0", None)] + [
                (float(row.ratio), row.arm, row) for row in determined
            ]
            ratio, winner, winner_row = min(candidates, key=lambda item: (item[0], item[1]))
            instance_hash = rows[0].instance_hash
            oracle_rows.append((instance_hash, context_id, ratio))
            context_winners[context_id] = {"arm": winner, "ratio": ratio}
            if winner != "Q0":
                winner_instances.add(instance_hash)
            for row in determined:
                value = float(row.ratio)
                if value <= 0.98:
                    beneficial_instances.add(row.instance_hash)
                elif value < 1.05:
                    neutral_instances.add(row.instance_hash)
                else:
                    harm_instances.add(row.instance_hash)
        instance_ratios = instance_geometric_means(oracle_rows) if oracle_rows else {}
        gm = geometric_mean(tuple(instance_ratios.values()))
        passed = bool(
            allowed and gm is not None and gm <= 0.95
            and len(winner_instances) >= 5
            and beneficial_instances and neutral_instances and harm_instances
            and not redlines
        )
        summaries[str(scale)] = {
            "admitted_arms": sorted(allowed),
            "context_count": len(oracle_rows),
            "instance_count": len(instance_ratios),
            "context_winners": context_winners,
            "instance_oracle_ratios": instance_ratios,
            "oracle_instance_weighted_gm": gm,
            "non_q0_winner_instances": len(winner_instances),
            "beneficial_instances": len(beneficial_instances),
            "neutral_instances": len(neutral_instances),
            "harm_instances": len(harm_instances),
            "correctness_redlines": redlines,
            "passed": passed,
        }
        if not passed:
            terminal_reasons.append(f"NO_SCALE{scale}_GAT_PORTFOLIO_HEADROOM")
    return {
        "selector_training_authorized": not terminal_reasons,
        "scales": summaries,
        "terminal_reasons": terminal_reasons,
    }


def assess_v3_qgr1_force_on(
    outcomes: Sequence[MatchedContextOutcome],
    telemetry_by_context: Mapping[str, Mapping[str, float]],
    *, scale: int,
):
    rows = [
        row for row in outcomes
        if row.arm == "QGR1" and row.scale == int(scale)
        and row.partition == "calibration"
    ]
    determined = [row for row in rows if row.determined]
    redlines = sorted({value for row in rows for value in row.correctness_redlines})
    ratios = [float(row.ratio) for row in determined]
    gm = geometric_mean(ratios)
    violations = []
    if len(determined) != 4 or len({row.instance_hash for row in determined}) != 4:
        violations.append("QGR1_FORCE_ON_NOT_4_DISTINCT_INSTANCES")
    if redlines:
        violations.append("CORRECTNESS_REDLINE")
    if gm is None or gm >= 1.0:
        violations.append("QGR1_SCALE_GM_NOT_LT_1")
    if len({row.instance_hash for row in determined if row.beneficial}) < 2:
        violations.append("QGR1_BENEFICIAL_INSTANCES_LT_2")
    if any(row.harmful for row in determined):
        violations.append("QGR1_RATIO_GE_1_05")
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
        if (
            not all(isfinite(value) for value in (scoring, proof))
            or proof <= 0.0 or scoring / proof > 0.02
        ):
            telemetry_violations.append(f"{row.context_id}:SCORING_FRACTION_GT_0_02")
    if telemetry_violations:
        violations.append("QGR1_TELEMETRY_GATE_FAILED")
    return {
        "scale": int(scale),
        "admitted": not violations,
        "hard_veto": bool(violations),
        "determined_contexts": len(determined),
        "determined_instances": len({row.instance_hash for row in determined}),
        "instance_weighted_gm": gm,
        "beneficial_instances": len({
            row.instance_hash for row in determined if row.beneficial
        }),
        "correctness_redlines": redlines,
        "telemetry_violations": telemetry_violations,
        "violations": sorted(set(violations)),
    }


def summarize_selected_actions_instance_first(
    context_rows: Sequence[Mapping[str, object]],
):
    """Summarize already matched selected-action rows for one model."""

    scales = {}
    all_ratios = []
    all_redlines = set()
    for scale in (30, 50):
        rows = [row for row in context_rows if int(row["scale"]) == scale]
        ratio_rows = []
        activated_instances = set()
        harmful = adverse = censored = 0
        for row in rows:
            ratio = row.get("net_ratio", row.get("ratio"))
            if ratio is None:
                continue
            ratio_rows.append((
                str(row["instance_hash"]), str(row["context_id"]), float(ratio)
            ))
            if str(row.get("selected_action") or "Q0") != "Q0":
                activated_instances.add(str(row["instance_hash"]))
                harmful += int(float(ratio) >= 1.05)
                adverse += int(bool(row.get("adverse")))
                censored += int(bool(row.get("censored")))
            all_redlines.update(str(v) for v in row.get("correctness_redlines") or ())
        folded = instance_geometric_means(ratio_rows) if ratio_rows else {}
        gm = geometric_mean(tuple(folded.values()))
        all_ratios.extend((instance_hash, f"{scale}:{instance_hash}", value)
                          for instance_hash, value in folded.items())
        scales[str(scale)] = {
            "context_count": len(rows),
            "instance_count": len(folded),
            "activation_instances": len(activated_instances),
            "instance_ratios": folded,
            "net_gm": gm,
            "harmful_activations": harmful,
            "adverse_activations": adverse,
            "censored_activations": censored,
        }
    combined = geometric_mean([
        value for row in scales.values()
        for value in dict(row["instance_ratios"]).values()
    ])
    values = [row["net_gm"] for row in scales.values() if row["net_gm"] is not None]
    return {
        "scales": scales,
        "combined_gm": combined,
        "worst_scale_gm": max(values) if len(values) == 2 else None,
        "harmful_activations": sum(row["harmful_activations"] for row in scales.values()),
        "correctness_redlines": sorted(all_redlines),
    }


def assess_v3_calibration(
    *, full: Mapping[str, object], no_message: Mapping[str, object],
    shuffled_topology: Mapping[str, object],
):
    violations = []
    if int(full.get("harmful_activations") or 0):
        violations.append("GAT_CALIBRATION_HARMFUL_ACTIVATION")
    for scale in (30, 50):
        row = dict(dict(full.get("scales") or {}).get(str(scale)) or {})
        if int(row.get("activation_instances") or 0) < 2:
            violations.append(f"GAT_SCALE{scale}_ACTIVATION_INSTANCES_LT_2")
        if row.get("net_gm") is None or float(row["net_gm"]) >= 1.0:
            violations.append(f"GAT_SCALE{scale}_GM_NOT_LT_1")
    full_rank = float(full.get("train_oof_macro_rank_accuracy") or 0.0)
    control_ranks = [
        float(no_message.get("train_oof_macro_rank_accuracy") or 0.0),
        float(shuffled_topology.get("train_oof_macro_rank_accuracy") or 0.0),
    ]
    if any(full_rank < value for value in control_ranks):
        violations.append("GAT_RANK_ACCURACY_BELOW_TOPOLOGY_CONTROL")
    if not any(full_rank - value >= 0.02 for value in control_ranks):
        violations.append("GAT_TOPOLOGY_RANK_DROP_LT_0_02")
    full_gm = float(full.get("combined_gm") or float("inf"))
    if any(full_gm > float(row.get("combined_gm") or float("inf"))
           for row in (no_message, shuffled_topology)):
        violations.append("GAT_GM_ABOVE_TOPOLOGY_CONTROL")
    if full.get("correctness_redlines"):
        violations.append("CORRECTNESS_REDLINE")
    return {"passed": not violations, "violations": sorted(set(violations))}


def assess_v3_heldout_advantage(
    summaries: Mapping[str, Mapping[str, object]], *, preparation_p99_ms: float,
):
    required = {"gat", "mlp", "linear", "no_message", "shuffled_topology"}
    if set(summaries) != required:
        raise ValueError("heldout comparison must freeze all five independent models")
    gat = dict(summaries["gat"])
    violations = []
    for scale in (30, 50):
        row = dict(dict(gat.get("scales") or {}).get(str(scale)) or {})
        if int(row.get("activation_instances") or 0) < 2:
            violations.append(f"HELDOUT_SCALE{scale}_ACTIVATION_INSTANCES_LT_2")
        if row.get("net_gm") is None or float(row["net_gm"]) >= 1.0:
            violations.append(f"HELDOUT_SCALE{scale}_GM_NOT_LT_1")
        if any(int(row.get(key) or 0) for key in (
            "harmful_activations", "adverse_activations", "censored_activations"
        )):
            violations.append(f"HELDOUT_SCALE{scale}_HARM_ADVERSE_CENSOR")
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
    no_advantage = any(
        value.startswith("NO_GAT_ADVANTAGE") or value.startswith("GAT_WORSE")
        for value in violations
    )
    return {
        "passed": not violations,
        "terminal_reason": (
            None if not violations else
            "NO_GAT_ADVANTAGE" if no_advantage else "HELDOUT_FRESH_FAILED"
        ),
        "violations": sorted(set(violations)),
    }

