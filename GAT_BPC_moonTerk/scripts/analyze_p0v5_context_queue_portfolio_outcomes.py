#!/usr/bin/env python3
"""Report fixed-arm/oracle wall evidence and queue-mechanism decomposition."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from math import exp, log
from pathlib import Path
import random
from statistics import median
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import (  # noqa: E402
    verify_portfolio_freezes,
)
from lunar_ice_bpc.guidance.context_queue_portfolio_gates import (  # noqa: E402
    collapse_matched_matrix, geometric_mean, percentile,
)


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_context_queue_portfolio_v1_20260807_r1"
MECHANISM_FIELDS = (
    "processed_labels", "dominance_candidate_checks", "dominance_wall_sec",
    "max_visited_bucket_size", "ordering_decisions", "guidance_scored_labels",
    "guidance_nonzero_labels", "native_scoring_wall_sec", "wall_sec",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--bootstrap-replicates", type=int, default=2000)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    try:
        verify_portfolio_freezes(run_root, ROOT)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    source = args.input.resolve()
    payload = _load(source)
    rows = [dict(row) for row in payload.get("rows") or ()]
    config = _load(run_root / "config.freeze.json")
    outcomes = collapse_matched_matrix(
        rows,
        caps_by_scale=config["execution"]["replay_caps_sec"],
        required_repeats=config["execution"]["blocked_fresh_process_repeats"],
    )
    mask = _admitted_mask(run_root)
    report = {
        "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_outcome_analysis.v1",
        "source": str(source), "source_sha256": _sha256(source),
        "repeat_is_not_sample": True,
        "bootstrap_unit": "instance_content_hash",
        "bootstrap_replicates": int(args.bootstrap_replicates),
        "scales": {},
        "mechanism_decomposition": _mechanism(rows),
        "correctness_redlines": sorted({
            value for row in outcomes for value in row.correctness_redlines
        }),
    }
    for scale in (30, 50):
        selected = [row for row in outcomes if row.scale == scale]
        cap = float(config["execution"]["replay_caps_sec"][str(scale)])
        q0_par2 = _par2_by_context(rows, scale=scale, arm="Q0", cap=cap)
        fixed = {}
        for arm in ("QD1", "QB1", "QGR1"):
            arm_rows = [row for row in selected if row.arm == arm]
            determined = [row for row in arm_rows if row.determined]
            ratios = [float(row.ratio) for row in determined]
            arm_par2 = _par2_by_context(rows, scale=scale, arm=arm, cap=cap)
            fixed[arm] = {
                "admitted": arm in mask[scale],
                "context_count": len(arm_rows),
                "determined_contexts": len(determined),
                "determined_instances": len({row.instance_hash for row in determined}),
                "gm": geometric_mean(ratios),
                "p90_ratio": percentile(ratios, 0.90),
                "worst_ratio": max(ratios) if ratios else None,
                "harmful_contexts": sum(row.harmful for row in determined),
                "adverse_contexts": sum(row.adverse for row in arm_rows),
                "q0_complete_arm_censored": sum(
                    row.q0_complete_arm_censored for row in arm_rows
                ),
                "double_censored_or_undetermined": sum(
                    not row.determined for row in arm_rows
                ),
                "instance_bootstrap_gm_ci95": _bootstrap_ci(
                    determined, int(args.bootstrap_replicates), f"fixed:{scale}:{arm}"
                ),
                "q0_par2_mean_sec": _mean(q0_par2.values()),
                "arm_par2_mean_sec": _mean(arm_par2.values()),
                "par2_mean_ratio": (
                    _mean(arm_par2.values()) / _mean(q0_par2.values())
                    if arm_par2 and q0_par2 else None
                ),
            }
        by_context = defaultdict(list)
        for row in selected:
            if row.arm in mask[scale]:
                by_context[row.context_id].append(row)
        oracle_ratios, winners, instance_ratios = [], [], defaultdict(list)
        oracle_par2 = []
        for context_id, values in by_context.items():
            determined = [row for row in values if row.determined]
            winner = min(
                determined, key=lambda row: (float(row.ratio), row.arm)
            ) if determined else None
            ratio = min(1.0, float(winner.ratio)) if winner else 1.0
            oracle_ratios.append(ratio)
            instance_hash = values[0].instance_hash
            instance_ratios[instance_hash].append(ratio)
            if winner is not None and ratio < 1.0:
                winners.append(winner)
            candidates = [q0_par2.get(context_id, 2.0 * cap)]
            candidates.extend(
                _par2_by_context(rows, scale=scale, arm=arm, cap=cap).get(
                    context_id, 2.0 * cap
                )
                for arm in mask[scale]
            )
            oracle_par2.append(min(candidates))
        report["scales"][str(scale)] = {
            "fixed_arms": fixed,
            "oracle": {
                "context_count": len(oracle_ratios),
                "gm": geometric_mean(oracle_ratios),
                "winner_distribution": dict(sorted(Counter(
                    row.arm for row in winners
                ).items())),
                "non_q0_winner_instances": len({row.instance_hash for row in winners}),
                "instance_bootstrap_gm_ci95": _bootstrap_grouped(
                    instance_ratios, int(args.bootstrap_replicates), f"oracle:{scale}"
                ),
                "q0_par2_mean_sec": _mean(q0_par2.values()),
                "oracle_par2_mean_sec": _mean(oracle_par2),
            },
        }
    target = args.output.resolve() if args.output else run_root / "portfolio_outcome_analysis.json"
    _write_once(target, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def _admitted_mask(run_root):
    path = run_root / "qgr1_force_on.decision.json"
    if not path.is_file():
        return {30: {"QD1", "QB1", "QGR1"}, 50: {"QD1", "QB1", "QGR1"}}
    mask = _load(path)["decision"]["arm_scale_mask"]
    return {
        scale: {
            arm for arm, scales in mask.items()
            if scale in {int(value) for value in scales}
        } for scale in (30, 50)
    }


def _mechanism(rows):
    result = {}
    for scale in (30, 50):
        result[str(scale)] = {}
        for arm in ("Q0", "QD1", "QB1", "QGR1"):
            values = [
                row for row in rows
                if int(row.get("scale") or 0) == scale and row.get("arm") == arm
            ]
            if not values:
                continue
            result[str(scale)][arm] = {
                field: median(float(row.get(field) or 0.0) for row in values)
                for field in MECHANISM_FIELDS
            }
    return result


def _par2_by_context(rows, *, scale, arm, cap):
    grouped = defaultdict(list)
    for row in rows:
        if int(row.get("scale") or 0) == scale and str(row.get("arm")) == arm:
            grouped[str(row["context_id"])].append(row)
    result = {}
    for context_id, values in grouped.items():
        completed = all(
            bool(row.get("milestone_reached"))
            and str(row.get("status")) == "COMPLETED"
            for row in values
        )
        result[context_id] = (
            median(float(row["wall_sec"]) for row in values)
            if completed else 2.0 * cap
        )
    return result


def _mean(values):
    materialized = list(values)
    return sum(materialized) / len(materialized) if materialized else None


def _bootstrap_ci(rows, replicates, salt):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row.instance_hash].append(float(row.ratio))
    return _bootstrap_grouped(grouped, replicates, salt)


def _bootstrap_grouped(grouped, replicates, salt):
    instances = sorted(grouped)
    if not instances:
        return None
    rng = random.Random(int(hashlib.sha256(
        f"61635:{salt}".encode()
    ).hexdigest()[:16], 16))
    values = []
    for _ in range(max(1, int(replicates))):
        sample = [rng.choice(instances) for _ in instances]
        ratios = [ratio for instance in sample for ratio in grouped[instance]]
        values.append(exp(sum(log(value) for value in ratios) / len(ratios)))
    return {
        "lower": percentile(values, 0.025),
        "upper": percentile(values, 0.975),
    }


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _write_once(path, payload):
    path = Path(path)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != text:
        raise SystemExit(f"immutable outcome report drift:{path}")
    if not path.exists():
        path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
