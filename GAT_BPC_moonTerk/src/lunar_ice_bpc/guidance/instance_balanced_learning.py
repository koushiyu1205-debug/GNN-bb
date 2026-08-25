"""Deterministic instance-balanced sampling and evaluation helpers.

The QG2 real-map corpus can contain several fallback contexts from one
logical instance.  Instance-disjoint splits prevent leakage, but they do not
prevent a context-rich instance from dominating optimizer steps, early
stopping, or headline accuracy.  These helpers make the experimental unit
explicit without discarding the additional contexts.
"""

from __future__ import annotations

from collections import defaultdict
import hashlib
import math
import random
import statistics
from typing import Callable, Mapping, Sequence, TypeVar


T = TypeVar("T")
INSTANCE_BALANCING_POLICY_V1 = (
    "uniform_instance_steps_rotating_contexts.v1"
)


def instance_balanced_epoch_order(
    rows: Sequence[T],
    *,
    instance_key: Callable[[T], str],
    context_key: Callable[[T], str],
    seed: int,
    epoch: int,
    steps: int | None = None,
) -> tuple[T, ...]:
    """Return a deterministic order with near-equal steps per instance.

    The epoch keeps the original number of optimizer steps by default.  The
    instance selected at each step is round-robin balanced (counts differ by
    at most one), while the starting context within each instance rotates
    deterministically across epochs.  Context-rich instances therefore retain
    coverage over training without receiving more total gradient steps.
    """

    values = tuple(rows)
    if not values:
        return tuple()
    target_steps = len(values) if steps is None else int(steps)
    if target_steps <= 0:
        return tuple()
    groups: dict[str, list[T]] = defaultdict(list)
    for row in values:
        key = str(instance_key(row))
        if not key:
            raise ValueError("instance-balanced sampling requires instance ids")
        groups[key].append(row)
    for key in groups:
        groups[key].sort(key=lambda row: str(context_key(row)))

    instances = sorted(groups)
    rng = random.Random(_stable_seed(seed, epoch, "instance-order"))
    rng.shuffle(instances)
    offsets = {
        key: _stable_seed(seed, epoch, key) % len(groups[key])
        for key in instances
    }
    cursors = {key: 0 for key in instances}
    result: list[T] = []
    for step in range(target_steps):
        if step and step % len(instances) == 0:
            rng.shuffle(instances)
        instance = instances[step % len(instances)]
        group = groups[instance]
        index = (offsets[instance] + cursors[instance]) % len(group)
        result.append(group[index])
        cursors[instance] += 1
    return tuple(result)


def instance_balanced_metric(
    rows: Sequence[Mapping[str, object]],
    *,
    value_key: str,
    instance_key: str = "instance_hash",
) -> dict[str, object]:
    """Aggregate context values by instance, then average instances equally."""

    groups: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        instance = str(row.get(instance_key) or "")
        if not instance:
            raise ValueError("instance-balanced metric requires instance ids")
        try:
            value = float(row[value_key])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                f"instance-balanced metric lacks finite {value_key}"
            ) from exc
        if not math.isfinite(value):
            raise ValueError(
                f"instance-balanced metric lacks finite {value_key}"
            )
        groups[instance].append(value)
    if not groups:
        return {
            "context_count": 0,
            "instance_count": 0,
            "mean_context_value": None,
            "mean_instance_value": None,
            "maximum_context_fraction_by_instance": None,
            "per_instance_mean": {},
            "per_instance_context_count": {},
        }
    per_instance = {
        key: statistics.fmean(values)
        for key, values in sorted(groups.items())
    }
    counts = {key: len(values) for key, values in sorted(groups.items())}
    context_count = sum(counts.values())
    return {
        "context_count": context_count,
        "instance_count": len(groups),
        "mean_context_value": statistics.fmean(
            value for values in groups.values() for value in values
        ),
        "mean_instance_value": statistics.fmean(per_instance.values()),
        "maximum_context_fraction_by_instance": (
            max(counts.values()) / context_count
        ),
        "per_instance_mean": per_instance,
        "per_instance_context_count": counts,
    }


def instance_balanced_geomean(
    rows: Sequence[Mapping[str, object]],
    *,
    ratio_key: str,
    instance_key: str = "instance_hash",
) -> dict[str, object]:
    """Return context- and instance-balanced geometric means of ratios."""

    log_rows = []
    for row in rows:
        try:
            ratio = float(row[ratio_key])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                f"instance-balanced geomean lacks positive {ratio_key}"
            ) from exc
        if not math.isfinite(ratio) or ratio <= 0.0:
            raise ValueError(
                f"instance-balanced geomean lacks positive {ratio_key}"
            )
        log_rows.append({
            "instance_hash": str(row.get(instance_key) or ""),
            "log_ratio": math.log(ratio),
        })
    metric = instance_balanced_metric(log_rows, value_key="log_ratio")
    if not log_rows:
        return {
            **metric,
            "context_geomean_ratio": None,
            "instance_balanced_geomean_ratio": None,
            "per_instance_geomean_ratio": {},
        }
    return {
        **metric,
        "context_geomean_ratio": math.exp(
            float(metric["mean_context_value"])
        ),
        "instance_balanced_geomean_ratio": math.exp(
            float(metric["mean_instance_value"])
        ),
        "per_instance_geomean_ratio": {
            key: math.exp(value)
            for key, value in dict(metric["per_instance_mean"]).items()
        },
    }


def _stable_seed(seed: int, epoch: int, salt: str) -> int:
    digest = hashlib.sha256(
        f"{int(seed)}|{int(epoch)}|{salt}".encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], "big", signed=False)
