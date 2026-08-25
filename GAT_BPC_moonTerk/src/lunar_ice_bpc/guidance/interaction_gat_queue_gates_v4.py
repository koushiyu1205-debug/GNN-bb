"""Censor-aware, instance-first gates for Interaction-GAT V4.

The module is analysis-only.  It never creates pricing authority and treats
double-censored matched blocks as missing relative-performance observations,
not as correctness failures or fabricated neutral ratios.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from math import isfinite
from statistics import median
from typing import Mapping, Sequence

from lunar_ice_bpc.guidance.context_queue_portfolio_gates import (
    CENSORED_STATUSES,
    COMPLETED_STATUSES,
    geometric_mean,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_gates_v3 import (
    instance_geometric_means,
)


CENSOR_AWARE_MATCHED_SCHEMA_V1 = (
    "lunar_ice_bpc.p0v5_censor_aware_matched_outcome.v1"
)


@dataclass(frozen=True)
class CensorAwareContextOutcome:
    context_id: str
    instance_hash: str
    scale: int
    partition: str
    arm: str
    determined: bool
    ratio: float | None
    comparable_blocks: int
    double_censored_blocks: int
    beneficial: bool
    strong_benefit: bool
    harmful: bool
    adverse: bool
    resource_censor_positive: bool
    q0_complete_arm_censored_blocks: int
    q0_censored_arm_completed_blocks: int
    correctness_redlines: tuple[str, ...]


def collapse_censor_aware_matrix(
    rows: Sequence[Mapping[str, object]],
    *,
    caps_by_scale: Mapping[int | str, float],
    required_repeats: int = 3,
    minimum_comparable_blocks: int = 2,
) -> tuple[CensorAwareContextOutcome, ...]:
    """Collapse matched Q0/arm blocks without failing on resource censoring."""

    if required_repeats <= 0:
        raise ValueError("required repeats must be positive")
    if not 1 <= minimum_comparable_blocks <= required_repeats:
        raise ValueError("minimum comparable blocks is invalid")
    grouped: dict[tuple[str, str, int], Mapping[str, object]] = {}
    context_meta: dict[str, tuple[str, int, str]] = {}
    arms_by_context: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        context_id = str(row.get("context_id") or "")
        arm = str(row.get("arm") or "")
        instance_hash = str(row.get("instance_hash") or "")
        scale = int(row.get("scale") or 0)
        partition = str(row.get("partition") or "")
        block = int(row.get("block", row.get("repeat", -1)))
        if (
            not all((context_id, arm, instance_hash, partition))
            or scale not in {30, 50}
            or block < 0
        ):
            raise ValueError("V4 matched row identity is incomplete")
        identity = (instance_hash, scale, partition)
        if context_id in context_meta and context_meta[context_id] != identity:
            raise ValueError("V4 context identity drift")
        context_meta[context_id] = identity
        key = (context_id, arm, block)
        if key in grouped:
            raise ValueError("duplicate V4 matched block row")
        grouped[key] = row
        arms_by_context[context_id].add(arm)

    outcomes = []
    for context_id, (instance_hash, scale, partition) in sorted(context_meta.items()):
        arms = arms_by_context[context_id]
        if "Q0" not in arms:
            raise ValueError("every V4 context requires literal Q0")
        non_q0 = sorted(arms - {"Q0"})
        cap = float(caps_by_scale.get(scale, caps_by_scale.get(str(scale), 0.0)))
        if not isfinite(cap) or cap <= 0.0:
            raise ValueError("V4 replay cap is invalid")
        for arm in non_q0:
            block_ratios = []
            redlines = set()
            double_censored = 0
            q0_complete_arm_censored = 0
            q0_censored_arm_completed = 0
            block_adverse = False
            for block in range(required_repeats):
                try:
                    q0 = grouped[(context_id, "Q0", block)]
                    candidate = grouped[(context_id, arm, block)]
                except KeyError as exc:
                    raise ValueError("V4 context lacks a matched block") from exc
                redlines.update(_redlines(q0))
                redlines.update(_redlines(candidate))
                q0_complete = _completed(q0)
                arm_complete = _completed(candidate)
                q0_censored = _censored(q0)
                arm_censored = _censored(candidate)
                if q0_complete and arm_complete:
                    block_ratios.append(_wall(candidate) / _wall(q0))
                elif q0_complete and arm_censored:
                    block_ratios.append(cap / _wall(q0))
                    q0_complete_arm_censored += 1
                    block_adverse = True
                elif q0_censored and arm_complete:
                    block_ratios.append(_wall(candidate) / cap)
                    q0_censored_arm_completed += 1
                elif q0_censored and arm_censored:
                    double_censored += 1
                else:
                    raise ValueError("V4 block has unsupported completion state")
            ratio = (
                float(median(block_ratios))
                if len(block_ratios) >= minimum_comparable_blocks
                else None
            )
            if ratio is not None and (not isfinite(ratio) or ratio <= 0.0):
                raise ValueError("V4 matched ratio is invalid")
            outcomes.append(CensorAwareContextOutcome(
                context_id=context_id,
                instance_hash=instance_hash,
                scale=scale,
                partition=partition,
                arm=arm,
                determined=ratio is not None,
                ratio=ratio,
                comparable_blocks=len(block_ratios),
                double_censored_blocks=double_censored,
                beneficial=bool(ratio is not None and ratio <= 0.98),
                strong_benefit=bool(ratio is not None and ratio <= 0.95),
                harmful=bool(ratio is not None and ratio >= 1.05),
                adverse=bool(block_adverse or (ratio is not None and ratio >= 1.05)),
                resource_censor_positive=bool(
                    double_censored or q0_complete_arm_censored
                ),
                q0_complete_arm_censored_blocks=q0_complete_arm_censored,
                q0_censored_arm_completed_blocks=q0_censored_arm_completed,
                correctness_redlines=tuple(sorted(redlines)),
            ))
    return tuple(outcomes)


def assess_v4_qd1_admission(
    outcomes: Sequence[CensorAwareContextOutcome], *, scale: int
):
    rows = [
        row for row in outcomes
        if row.arm == "QD1" and row.scale == int(scale)
        and row.partition == "train"
    ]
    determined = [row for row in rows if row.determined]
    determined_instances = {row.instance_hash for row in determined}
    strong_instances = {row.instance_hash for row in determined if row.strong_benefit}
    harmful_instances = {row.instance_hash for row in determined if row.harmful}
    neutral_harm_instances = {
        row.instance_hash for row in determined if not row.strong_benefit
    }
    redlines = sorted({v for row in rows for v in row.correctness_redlines})
    fraction = len(determined) / len(rows) if rows else 0.0
    universal = bool(
        not redlines
        and len(determined_instances) >= 11
        and len(strong_instances) >= 10
        and len(harmful_instances) <= 1
    )
    selective = bool(
        not redlines
        and fraction >= 0.75
        and len(determined_instances) >= 11
        and len(strong_instances) >= 3
        and len(neutral_harm_instances) >= 4
    )
    mode = "universal_benefit" if universal else (
        "selective" if selective else "forced_veto"
    )
    return {
        "schema_version": "lunar_ice_bpc.p0v5_qd1_admission.v4",
        "scale": int(scale),
        "arm": "QD1",
        "admitted": mode != "forced_veto",
        "mode": mode,
        "train_contexts": len(rows),
        "determined_contexts": len(determined),
        "determined_context_fraction": fraction,
        "determined_instances": len(determined_instances),
        "strong_benefit_instances": len(strong_instances),
        "neutral_or_harm_instances": len(neutral_harm_instances),
        "harmful_instances": len(harmful_instances),
        "resource_censor_contexts": sum(row.resource_censor_positive for row in rows),
        "correctness_redlines": redlines,
    }


def measured_v4_oracle(
    outcomes: Sequence[CensorAwareContextOutcome],
    *,
    admitted_arms_by_scale: Mapping[int | str, Sequence[str]],
    required_gm: float,
    require_scale50_mixture: bool,
):
    scales = {}
    terminal_reasons = []
    for scale in (30, 50):
        allowed = set(str(v) for v in admitted_arms_by_scale.get(
            scale, admitted_arms_by_scale.get(str(scale), ())
        ))
        by_context: dict[str, list[CensorAwareContextOutcome]] = defaultdict(list)
        scale_rows = [
            row for row in outcomes
            if row.scale == scale and row.partition == "train"
            and row.arm in allowed
        ]
        for row in scale_rows:
            by_context[row.context_id].append(row)
        ratios = []
        winners = set()
        beneficial = set()
        neutral = set()
        harmful = set()
        context_winners = {}
        redlines = sorted({v for row in scale_rows for v in row.correctness_redlines})
        for context_id, values in sorted(by_context.items()):
            candidates = [(1.0, "Q0", values[0].instance_hash)] + [
                (float(row.ratio), row.arm, row.instance_hash)
                for row in values if row.determined
            ]
            ratio, winner, instance_hash = min(candidates, key=lambda v: (v[0], v[1]))
            ratios.append((instance_hash, context_id, ratio))
            context_winners[context_id] = {"arm": winner, "ratio": ratio}
            if winner != "Q0":
                winners.add(instance_hash)
            for row in values:
                if not row.determined:
                    continue
                if float(row.ratio) <= 0.98:
                    beneficial.add(row.instance_hash)
                elif float(row.ratio) < 1.05:
                    neutral.add(row.instance_hash)
                else:
                    harmful.add(row.instance_hash)
        instance_ratios = instance_geometric_means(ratios) if ratios else {}
        gm = geometric_mean(tuple(instance_ratios.values()))
        mixture_ok = bool(
            scale != 50 or not require_scale50_mixture
            or (beneficial and neutral and harmful)
        )
        passed = bool(
            allowed and gm is not None and gm <= float(required_gm)
            and len(winners) >= 5 and mixture_ok and not redlines
        )
        scales[str(scale)] = {
            "admitted_arms": sorted(allowed),
            "context_count": len(ratios),
            "instance_count": len(instance_ratios),
            "instance_weighted_gm": gm,
            "non_q0_winner_instances": len(winners),
            "beneficial_instances": len(beneficial),
            "neutral_instances": len(neutral),
            "harmful_instances": len(harmful),
            "context_winners": context_winners,
            "instance_ratios": instance_ratios,
            "correctness_redlines": redlines,
            "passed": passed,
        }
        if not passed:
            terminal_reasons.append(f"NO_SCALE{scale}_V4_PORTFOLIO_HEADROOM")
    return {
        "schema_version": "lunar_ice_bpc.p0v5_censor_aware_oracle.v4",
        "required_gm": float(required_gm),
        "scales": scales,
        "passed": not terminal_reasons,
        "terminal_reasons": terminal_reasons,
    }


def _completed(row: Mapping[str, object]) -> bool:
    return bool(row.get("milestone_reached")) and str(row.get("status")) in (
        COMPLETED_STATUSES
    )


def _censored(row: Mapping[str, object]) -> bool:
    return str(row.get("status")) in CENSORED_STATUSES


def _wall(row: Mapping[str, object]) -> float:
    value = float(row.get("wall_sec") or 0.0)
    if not isfinite(value) or value <= 0.0:
        raise ValueError("V4 matched wall must be finite and positive")
    return value


def _redlines(row: Mapping[str, object]) -> tuple[str, ...]:
    values = {str(v) for v in row.get("correctness_redlines") or () if str(v)}
    for name in (
        "objective_mismatch", "illegal_route", "legal_universe_mismatch",
        "global_minimum_mismatch", "reduced_cost_mismatch",
        "certificate_mismatch", "exhaustive_with_label_drop",
    ):
        if bool(row.get(name)):
            values.add(name)
    return tuple(sorted(values))


__all__ = [
    "CENSOR_AWARE_MATCHED_SCHEMA_V1",
    "CensorAwareContextOutcome",
    "assess_v4_qd1_admission",
    "collapse_censor_aware_matrix",
    "measured_v4_oracle",
]
