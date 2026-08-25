"""Machine-readable gates for Context Queue Portfolio V1 experiments.

This module has no solver authority.  It consumes fresh-process outcome rows,
applies the pre-frozen censoring and Go/No-Go rules, and returns deterministic
JSON-ready decisions.  Repeats are collapsed inside a context; they are never
treated as independent samples.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import hashlib
from math import exp, isfinite, log
import random
from statistics import median
from typing import Iterable, Mapping, Sequence


CORRECTNESS_FIELDS = (
    "objective_mismatch",
    "illegal_route",
    "legal_universe_mismatch",
    "global_minimum_mismatch",
    "reduced_cost_mismatch",
    "certificate_mismatch",
    "exhaustive_with_label_drop",
)
COMPLETED_STATUSES = frozenset({"COMPLETED", "EXACT", "MILESTONE_REACHED"})
CENSORED_STATUSES = frozenset({"TIMEOUT", "MEMORY_LIMIT", "CENSORED"})


@dataclass(frozen=True)
class MatchedContextOutcome:
    context_id: str
    instance_hash: str
    scale: int
    partition: str
    arm: str
    determined: bool
    ratio: float | None
    beneficial: bool
    strong_benefit: bool
    harmful: bool
    adverse: bool
    q0_complete_arm_censored: bool
    q0_censored_arm_completed: bool
    correctness_redlines: tuple[str, ...]


def rotate_blocked_arm_order(
    state_hash: str,
    *,
    arms: Sequence[str] = ("Q0", "QD1", "QB1"),
    repeats: int = 3,
) -> tuple[tuple[str, ...], ...]:
    """Freeze a deterministic, state-bound blocked order with Q0 each block."""

    values = tuple(str(arm) for arm in arms)
    if not values or values[0] != "Q0" or len(set(values)) != len(values):
        raise ValueError("blocked arm universe must start with unique literal Q0")
    digest = hashlib.sha256(str(state_hash).encode("utf-8")).digest()
    schedule = []
    for repeat in range(int(repeats)):
        offset = (digest[repeat % len(digest)] + repeat) % len(values)
        schedule.append(values[offset:] + values[:offset])
    return tuple(schedule)


def collapse_matched_matrix(
    rows: Sequence[Mapping[str, object]],
    *,
    caps_by_scale: Mapping[int | str, float],
    required_repeats: int = 3,
) -> tuple[MatchedContextOutcome, ...]:
    grouped: dict[tuple[str, str], list[Mapping[str, object]]] = defaultdict(list)
    context_meta: dict[str, tuple[str, int, str]] = {}
    for row in rows:
        context_id = str(row.get("context_id") or "")
        arm = str(row.get("arm") or "")
        instance_hash = str(row.get("instance_hash") or "")
        scale = int(row.get("scale") or 0)
        partition = str(row.get("partition") or "")
        if not all((context_id, arm, instance_hash, partition)) or scale not in {30, 50}:
            raise ValueError("matched outcome row has incomplete identity")
        identity = (instance_hash, scale, partition)
        if context_id in context_meta and context_meta[context_id] != identity:
            raise ValueError("context identity drift across repeats")
        context_meta[context_id] = identity
        grouped[(context_id, arm)].append(row)

    results = []
    for context_id, (instance_hash, scale, partition) in sorted(context_meta.items()):
        q0 = grouped.get((context_id, "Q0"), [])
        if len(q0) != required_repeats:
            raise ValueError("every context requires exactly three fresh Q0 repeats")
        for arm in sorted(
            value for cid, value in grouped if cid == context_id and value != "Q0"
        ):
            arm_rows = grouped[(context_id, arm)]
            if len(arm_rows) != required_repeats:
                raise ValueError("every arm requires exactly three fresh repeats")
            cap = float(caps_by_scale.get(scale, caps_by_scale.get(str(scale), 0.0)))
            results.append(_collapse_pair(
                context_id=context_id,
                instance_hash=instance_hash,
                scale=scale,
                partition=partition,
                arm=arm,
                q0_rows=q0,
                arm_rows=arm_rows,
                cap=cap,
            ))
    return tuple(results)


def _collapse_pair(
    *, context_id, instance_hash, scale, partition, arm, q0_rows, arm_rows, cap
) -> MatchedContextOutcome:
    if not isfinite(cap) or cap <= 0.0:
        raise ValueError("scale replay cap is invalid")
    redlines = sorted(set(
        value
        for row in (*q0_rows, *arm_rows)
        for value in _redlines(row)
    ))
    q0_complete = all(_completed(row) for row in q0_rows)
    arm_complete = all(_completed(row) for row in arm_rows)
    q0_censored = all(_censored(row) for row in q0_rows)
    arm_censored = all(_censored(row) for row in arm_rows)
    ratio = None
    adverse = False
    q0_censored_arm_completed = False
    if q0_complete and arm_complete:
        ratio = median(_walls(arm_rows)) / median(_walls(q0_rows))
    elif q0_complete and arm_censored:
        ratio = cap / median(_walls(q0_rows))
        adverse = True
    elif q0_censored and arm_complete:
        ratio = median(_walls(arm_rows)) / cap
        q0_censored_arm_completed = True
    elif not (q0_censored and arm_censored):
        raise ValueError("mixed completion/censor status inside repeat block")
    if ratio is not None and (not isfinite(ratio) or ratio < 0.0):
        raise ValueError("matched wall ratio is invalid")
    return MatchedContextOutcome(
        context_id=context_id,
        instance_hash=instance_hash,
        scale=scale,
        partition=partition,
        arm=arm,
        determined=ratio is not None,
        ratio=ratio,
        beneficial=bool(ratio is not None and ratio <= 0.98),
        strong_benefit=bool(ratio is not None and ratio <= 0.95),
        harmful=bool(ratio is not None and ratio >= 1.05),
        adverse=bool(adverse or (ratio is not None and ratio >= 1.05)),
        q0_complete_arm_censored=bool(q0_complete and arm_censored),
        q0_censored_arm_completed=q0_censored_arm_completed,
        correctness_redlines=tuple(redlines),
    )


def _completed(row: Mapping[str, object]) -> bool:
    return bool(row.get("milestone_reached")) and str(row.get("status")) in (
        COMPLETED_STATUSES
    )


def _censored(row: Mapping[str, object]) -> bool:
    return str(row.get("status")) in CENSORED_STATUSES


def _walls(rows: Iterable[Mapping[str, object]]) -> list[float]:
    values = [float(row.get("wall_sec") or 0.0) for row in rows]
    if any(not isfinite(value) or value <= 0.0 for value in values):
        raise ValueError("completed wall must be finite and positive")
    return values


def _redlines(row: Mapping[str, object]) -> tuple[str, ...]:
    explicit = tuple(str(value) for value in row.get("correctness_redlines") or ())
    inferred = tuple(field for field in CORRECTNESS_FIELDS if bool(row.get(field)))
    incomplete = (
        ("correctness_audit_incomplete",)
        if row.get("correctness_audit_complete") is False else ()
    )
    return (*explicit, *inferred, *incomplete)


def assess_arm_scale_admission(
    outcomes: Sequence[MatchedContextOutcome], *, arm: str, scale: int
) -> dict[str, object]:
    rows = [
        row for row in outcomes
        if row.arm == arm and row.scale == scale and row.partition == "train"
    ]
    determined = [row for row in rows if row.determined]
    strong = [row for row in determined if row.strong_benefit]
    neutral_harm = [row for row in determined if not row.strong_benefit]
    redlines = sorted({value for row in rows for value in row.correctness_redlines})
    violations = []
    if redlines:
        violations.append("CORRECTNESS_REDLINE")
    if len(determined) < 12:
        violations.append("DETERMINED_TRAIN_CONTEXTS_LT_12")
    if len({row.instance_hash for row in determined}) < 6:
        violations.append("TRAIN_INSTANCES_LT_6")
    if len(strong) < 2 or len({row.instance_hash for row in strong}) < 2:
        violations.append("STRONG_BENEFIT_DIVERSITY_LT_2")
    if len(neutral_harm) < 2:
        violations.append("NEUTRAL_OR_HARM_EXAMPLES_LT_2")
    return {
        "arm": arm,
        "scale": scale,
        "admitted": not violations,
        "forced_veto": bool(violations),
        "determined_contexts": len(determined),
        "determined_instances": len({row.instance_hash for row in determined}),
        "strong_benefit_contexts": len(strong),
        "strong_benefit_instances": len({row.instance_hash for row in strong}),
        "neutral_or_harm_contexts": len(neutral_harm),
        "correctness_redlines": redlines,
        "violations": violations,
    }


def assess_qgr1_force_on(
    outcomes: Sequence[MatchedContextOutcome],
) -> dict[str, object]:
    rows = [row for row in outcomes if row.arm == "QGR1"]
    determined = [row for row in rows if row.determined]
    violations = []
    redlines = sorted({value for row in rows for value in row.correctness_redlines})
    if len(determined) != 8 or len({row.instance_hash for row in determined}) != 8:
        violations.append("QGR1_FORCE_ON_NOT_8_DISTINCT_INSTANCES")
    if redlines:
        violations.append("CORRECTNESS_REDLINE")
    ratios = [float(row.ratio) for row in determined]
    if len(ratios) == 8 and geometric_mean(ratios) >= 0.98:
        violations.append("QGR1_OVERALL_GM_NOT_LT_0_98")
    scale_summary = {}
    for scale in (30, 50):
        selected = [row for row in determined if row.scale == scale]
        gm = geometric_mean([float(row.ratio) for row in selected]) if selected else None
        beneficial_instances = len({
            row.instance_hash for row in selected if row.beneficial
        })
        scale_summary[str(scale)] = {
            "contexts": len(selected), "gm": gm,
            "beneficial_instances": beneficial_instances,
        }
        if len(selected) != 4 or gm is None or gm > 1.02:
            violations.append(f"QGR1_SCALE{scale}_GM_OR_COUNT_FAILED")
        if beneficial_instances < 1:
            violations.append(f"QGR1_SCALE{scale}_NO_BENEFICIAL_INSTANCE")
    if sum(row.harmful for row in determined) > 1:
        violations.append("QGR1_HARMFUL_CONTEXTS_GT_1")
    if any(row.q0_complete_arm_censored for row in rows):
        violations.append("QGR1_Q0_COMPLETE_ARM_CENSORED")
    return {
        "admitted": not violations,
        "hard_veto": bool(violations),
        "overall_gm": geometric_mean(ratios) if ratios else None,
        "scale_summary": scale_summary,
        "harmful_contexts": sum(row.harmful for row in determined),
        "correctness_redlines": redlines,
        "violations": sorted(set(violations)),
    }


def measured_portfolio_oracle(
    outcomes: Sequence[MatchedContextOutcome],
    *, admitted_arms_by_scale: Mapping[int | str, Sequence[str]],
) -> dict[str, object]:
    result = {}
    overall_pass = True
    terminal_reasons = []
    for scale in (30, 50):
        allowed = set(admitted_arms_by_scale.get(
            scale, admitted_arms_by_scale.get(str(scale), ())
        ))
        by_context: dict[str, list[MatchedContextOutcome]] = defaultdict(list)
        for row in outcomes:
            if row.scale == scale and row.arm in allowed:
                by_context[row.context_id].append(row)
        ratios = []
        winners = []
        redlines = sorted({
            value for rows in by_context.values() for row in rows
            for value in row.correctness_redlines
        })
        for context_id, rows in sorted(by_context.items()):
            determined = [row for row in rows if row.determined]
            winner = (
                min(determined, key=lambda row: (float(row.ratio), row.arm))
                if determined else None
            )
            ratio = min(1.0, float(winner.ratio)) if winner else 1.0
            ratios.append(ratio)
            if ratio < 1.0 and winner is not None:
                winners.append(winner)
        gm = geometric_mean(ratios) if ratios else None
        winner_instances = len({row.instance_hash for row in winners})
        passed = bool(
            gm is not None and gm <= 0.95 and winner_instances >= 3
            and not redlines
        )
        result[str(scale)] = {
            "context_count": len(ratios),
            "oracle_gm": gm,
            "non_q0_winner_instances": winner_instances,
            "winner_distribution": _counts(row.arm for row in winners),
            "correctness_redlines": redlines,
            "passed": passed,
        }
        if not passed:
            overall_pass = False
            terminal_reasons.append(f"NO_SCALE{scale}_PORTFOLIO_HEADROOM")
    return {
        "selector_training_authorized": overall_pass,
        "scales": result,
        "terminal_reasons": terminal_reasons,
    }


def assess_heldout_fresh(
    outcomes: Sequence[MatchedContextOutcome],
    *, preparation_p99_ms_by_scale: Mapping[int | str, float],
) -> dict[str, object]:
    violations = []
    scales = {}
    for scale in (30, 50):
        rows = [row for row in outcomes if row.scale == scale]
        activated = [
            row for row in rows
            if row.arm in {"QD1", "QB1", "QGR1"} and row.determined
        ]
        gm = geometric_mean([float(row.ratio) for row in rows if row.determined])
        prep = float(preparation_p99_ms_by_scale.get(
            scale, preparation_p99_ms_by_scale.get(str(scale), float("inf"))
        ))
        redlines = sorted({value for row in rows for value in row.correctness_redlines})
        scales[str(scale)] = {
            "activated_instances": len({row.instance_hash for row in activated}),
            "gm": gm,
            "harmful_activations": sum(row.harmful for row in activated),
            "adverse_activations": sum(row.adverse for row in activated),
            "preparation_p99_ms": prep,
            "correctness_redlines": redlines,
        }
        if len({row.instance_hash for row in activated}) < 2:
            violations.append(f"SCALE{scale}_ACTIVATION_INSTANCES_LT_2")
        if gm is None or gm >= 1.0:
            violations.append(f"SCALE{scale}_NET_GM_NOT_LT_1")
        if any(row.harmful or row.adverse for row in activated):
            violations.append(f"SCALE{scale}_HARMFUL_OR_ADVERSE_ACTIVATION")
        if prep > 10.0:
            violations.append(f"SCALE{scale}_PREPARATION_P99_GT_10MS")
        if redlines:
            violations.append("CORRECTNESS_REDLINE")
    return {
        "passed": not violations,
        "terminal_reason": None if not violations else "HELDOUT_FRESH_FAILED",
        "scales": scales,
        "violations": sorted(set(violations)),
    }


def assess_development_e2e(
    outcomes: Sequence[MatchedContextOutcome],
    *, q0_exact_count_by_scale: Mapping[int | str, int],
    candidate_exact_count_by_scale: Mapping[int | str, int],
) -> dict[str, object]:
    violations = []
    scales = {}
    for scale in (30, 50):
        rows = [row for row in outcomes if row.scale == scale and row.determined]
        ratios = [float(row.ratio) for row in rows]
        gm = geometric_mean(ratios)
        worst = max(ratios) if ratios else None
        q0_exact = int(q0_exact_count_by_scale.get(
            scale, q0_exact_count_by_scale.get(str(scale), 0)
        ))
        candidate_exact = int(candidate_exact_count_by_scale.get(
            scale, candidate_exact_count_by_scale.get(str(scale), 0)
        ))
        redlines = sorted({value for row in rows for value in row.correctness_redlines})
        scales[str(scale)] = {
            "gm": gm,
            "worst_context_median_ratio": worst,
            "q0_exact_count": q0_exact,
            "candidate_exact_count": candidate_exact,
            "correctness_redlines": redlines,
        }
        if gm is None or gm >= 1.0:
            violations.append(f"SCALE{scale}_E2E_GM_NOT_LT_1")
        if candidate_exact < q0_exact:
            violations.append("DEVELOPMENT_E2E_EXACT_COUNT_DECREASED")
        if worst is None or worst > 1.10:
            violations.append(f"SCALE{scale}_E2E_WORST_RATIO_GT_1_10")
        if redlines:
            violations.append("CORRECTNESS_REDLINE")
    return {
        "passed": not violations,
        "research_candidate_freeze_authorized": not violations,
        "scales": scales,
        "violations": sorted(set(violations)),
    }


def assess_formal_full100(
    rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Apply the immutable full100 acceptance rules at instance granularity."""

    grouped: dict[tuple[int, str], dict[str, Mapping[str, object]]] = defaultdict(dict)
    for row in rows:
        scale = int(row.get("scale") or 0)
        instance_hash = str(row.get("instance_hash") or "")
        side = str(row.get("side") or "")
        if scale not in {5, 10, 20, 30, 50} or not instance_hash:
            raise ValueError("formal row identity is invalid")
        if side not in {"Q0", "candidate"} or side in grouped[(scale, instance_hash)]:
            raise ValueError("formal pair must contain unique Q0/candidate rows")
        grouped[(scale, instance_hash)][side] = row
    if any(set(pair) != {"Q0", "candidate"} for pair in grouped.values()):
        raise ValueError("formal pair is incomplete")

    violations = []
    scales = {}
    strong = {}
    bootstrap_upper = {}
    for scale in (5, 10, 20, 30, 50):
        pairs = [pair for (value, _), pair in grouped.items() if value == scale]
        q0_exact = sum(bool(pair["Q0"].get("exact")) for pair in pairs)
        candidate_exact = sum(bool(pair["candidate"].get("exact")) for pair in pairs)
        ratios = []
        model_calls = 0
        redlines = set()
        q0_par2 = []
        candidate_par2 = []
        for pair in pairs:
            q0, candidate = pair["Q0"], pair["candidate"]
            model_calls += sum(int(candidate.get(field) or 0) for field in (
                "selector_calls", "model_calls", "ranker_calls"
            ))
            redlines.update(_redlines(q0))
            redlines.update(_redlines(candidate))
            q0_par2.append(float(q0.get("par2_wall_sec") or q0.get("wall_sec") or 0.0))
            candidate_par2.append(float(
                candidate.get("par2_wall_sec") or candidate.get("wall_sec") or 0.0
            ))
            if bool(q0.get("exact")) and bool(candidate.get("exact")):
                q0_wall = float(q0.get("wall_sec") or 0.0)
                candidate_wall = float(candidate.get("wall_sec") or 0.0)
                if q0_wall <= 0.0 or candidate_wall <= 0.0:
                    raise ValueError("formal common-exact wall is invalid")
                ratios.append(candidate_wall / q0_wall)
        gm = geometric_mean(ratios)
        p90 = percentile(ratios, 0.90)
        worst = max(ratios) if ratios else None
        q0_par2_mean = sum(q0_par2) / len(q0_par2) if q0_par2 else None
        candidate_par2_mean = (
            sum(candidate_par2) / len(candidate_par2) if candidate_par2 else None
        )
        scales[str(scale)] = {
            "instance_pairs": len(pairs),
            "q0_exact_count": q0_exact,
            "candidate_exact_count": candidate_exact,
            "common_exact_count": len(ratios),
            "common_exact_gm": gm,
            "p90_ratio": p90,
            "worst_ratio": worst,
            "q0_par2_mean": q0_par2_mean,
            "candidate_par2_mean": candidate_par2_mean,
            "candidate_model_calls": model_calls,
            "correctness_redlines": sorted(redlines),
        }
        strong[str(scale)] = bool(gm is not None and gm <= 0.95)
        if scale in {30, 50}:
            bootstrap = _instance_bootstrap_ratio_ci(
                pairs, seed=61635 + scale, replicates=2000
            )
            scales[str(scale)]["instance_bootstrap_gm_ci95"] = bootstrap
            bootstrap_upper[str(scale)] = (
                None if bootstrap is None else bootstrap["upper"]
            )
        if len(pairs) != 20:
            violations.append(f"SCALE{scale}_FORMAL_PAIR_COUNT_NOT_20")
        if redlines:
            violations.append("CORRECTNESS_REDLINE")
        if scale in {5, 10, 20}:
            if q0_exact != 20 or candidate_exact != 20:
                violations.append(f"SCALE{scale}_EXACT_NOT_20")
            if model_calls != 0:
                violations.append("FORMAL_SMALL_SCALE_MODEL_CALL")
            if gm is None or gm > 1.01:
                violations.append(f"SCALE{scale}_GM_GT_1_01")
        else:
            if scale == 30 and candidate_exact != 20:
                violations.append("SCALE30_EXACT_NOT_20")
            if scale == 50 and (candidate_exact < q0_exact or candidate_exact < 15):
                violations.append("SCALE50_EXACT_GATE_FAILED")
            if gm is None or gm >= 1.0:
                violations.append(f"SCALE{scale}_COMMON_EXACT_GM_NOT_LT_1")
            if (
                q0_par2_mean is None or candidate_par2_mean is None
                or candidate_par2_mean > q0_par2_mean
            ):
                violations.append(f"SCALE{scale}_PAR2_INCREASED")
            if p90 is None or p90 > 1.05:
                violations.append(f"SCALE{scale}_P90_GT_1_05")
            if worst is None or worst > 1.20:
                violations.append(f"SCALE{scale}_WORST_GT_1_20")
    passed = not violations
    return {
        "passed": passed,
        "decision": "PASS" if passed else "FAIL",
        "research_candidate_only": True,
        "production_switch_authorized": False,
        "strong_speedup_by_scale": strong,
        "promotion_review_metric_gate": bool(
            strong["30"] and strong["50"]
            and bootstrap_upper.get("30") is not None
            and bootstrap_upper.get("50") is not None
            and bootstrap_upper["30"] < 1.0
            and bootstrap_upper["50"] < 1.0
        ),
        "bootstrap_review_still_required": False,
        "scales": scales,
        "violations": sorted(set(violations)),
    }


def geometric_mean(values: Sequence[float]) -> float | None:
    if not values:
        return None
    if any(not isfinite(value) or value <= 0.0 for value in values):
        raise ValueError("geometric mean requires finite positive values")
    return exp(sum(log(value) for value in values) / len(values))


def percentile(values: Sequence[float], quantile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(float(value) for value in values)
    position = max(0.0, min(1.0, float(quantile))) * (len(ordered) - 1)
    low = int(position)
    high = min(len(ordered) - 1, low + 1)
    fraction = position - low
    return ordered[low] * (1.0 - fraction) + ordered[high] * fraction


def _instance_bootstrap_ratio_ci(pairs, *, seed, replicates):
    values = []
    for pair in pairs:
        q0, candidate = pair["Q0"], pair["candidate"]
        if bool(q0.get("exact")) and bool(candidate.get("exact")):
            q0_wall = float(q0.get("wall_sec") or 0.0)
            candidate_wall = float(candidate.get("wall_sec") or 0.0)
            if q0_wall > 0.0 and candidate_wall > 0.0:
                values.append(candidate_wall / q0_wall)
    if not values:
        return None
    rng = random.Random(int(seed))
    estimates = []
    for _ in range(max(1, int(replicates))):
        sample = [rng.choice(values) for _ in values]
        estimates.append(geometric_mean(sample))
    return {
        "replicates": int(replicates),
        "lower": percentile(estimates, 0.025),
        "upper": percentile(estimates, 0.975),
    }


def _counts(values: Iterable[str]) -> dict[str, int]:
    result: dict[str, int] = defaultdict(int)
    for value in values:
        result[str(value)] += 1
    return dict(sorted(result.items()))
