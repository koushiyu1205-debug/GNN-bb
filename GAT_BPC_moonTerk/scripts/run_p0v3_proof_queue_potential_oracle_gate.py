#!/usr/bin/env python3
"""Run a resumable matched QC0/QD1/QG1 task-potential oracle gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import random
import statistics
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
REPLAY = ROOT / "scripts/replay_p0v3_proof_queue_potential_snapshot.py"
BUILD_ORACLE = ROOT / "scripts/build_p0v3_proof_queue_potential_oracle.py"
SCHEMA = "lunar_ice_bpc.p0v3_proof_queue_potential_oracle_gate.v1"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _instance_index(roots: tuple[Path, ...]) -> dict[str, list[Path]]:
    index: dict[str, list[Path]] = {}
    for root in roots:
        for path in root.rglob("*_logical_graph.json"):
            payload = _load(path)
            instance_id = str(payload.get("instance_id") or "")
            if instance_id:
                index.setdefault(instance_id, []).append(path.resolve())
    return index


def _run(command: list[str], env: dict[str, str]) -> None:
    subprocess.run(command, cwd=ROOT, env=env, check=True)


def _bootstrap_ratio_interval(
    numerator: list[float],
    denominator: list[float],
    *,
    seed: int = 20260726,
    samples: int = 10000,
) -> tuple[float, float]:
    if not numerator or len(numerator) != len(denominator):
        return math.nan, math.nan
    rng = random.Random(seed)
    values = []
    count = len(numerator)
    for _ in range(samples):
        indices = [rng.randrange(count) for _ in range(count)]
        ratio_logs = [
            math.log(max(1.0e-12, numerator[index]))
            - math.log(max(1.0e-12, denominator[index]))
            for index in indices
        ]
        values.append(math.exp(sum(ratio_logs) / count))
    values.sort()
    return values[int(0.025 * samples)], values[int(0.975 * samples)]


def _aggregate(rows: list[dict]) -> dict:
    if not rows:
        return {}
    qg = [float(row["qg1_wall_sec"]) for row in rows]
    qc = [float(row["qc0_wall_sec"]) for row in rows]
    qd = [float(row["qd1_wall_sec"]) for row in rows]
    fixed_best = [min(left, right) for left, right in zip(qc, qd)]
    ratios = [
        candidate / max(1.0e-12, control)
        for candidate, control in zip(qg, fixed_best)
    ]
    geometric_mean = math.exp(
        statistics.fmean(math.log(max(1.0e-12, value)) for value in ratios)
    )
    ci_low, ci_high = _bootstrap_ratio_interval(qg, fixed_best)
    return {
        "state_count": len(rows),
        "scale_counts": {
            str(scale): sum(int(row["scale"]) == scale for row in rows)
            for scale in sorted({int(row["scale"]) for row in rows})
        },
        "qg1_better_than_qc0_count": sum(
            candidate < control for candidate, control in zip(qg, qc)
        ),
        "qg1_better_than_qd1_count": sum(
            candidate < control for candidate, control in zip(qg, qd)
        ),
        "qg1_better_than_fixed_best_count": sum(
            candidate < control
            for candidate, control in zip(qg, fixed_best)
        ),
        "median_qg1_vs_qc0_ratio": statistics.median(
            candidate / max(1.0e-12, control)
            for candidate, control in zip(qg, qc)
        ),
        "median_qg1_vs_qd1_ratio": statistics.median(
            candidate / max(1.0e-12, control)
            for candidate, control in zip(qg, qd)
        ),
        "median_qg1_vs_fixed_best_ratio": statistics.median(ratios),
        "paired_geometric_mean_qg1_vs_fixed_best": geometric_mean,
        "bootstrap_95_interval_geomean_qg1_vs_fixed_best": [
            ci_low,
            ci_high,
        ],
        "all_exact_safe": all(bool(row["exact_safe"]) for row in rows),
        "all_global_min_match": all(
            bool(row["global_min_match"]) for row in rows
        ),
        "all_legal_universe_match": all(
            bool(row["legal_universe_match"]) for row in rows
        ),
        "all_zero_filter_drop": all(
            bool(row["zero_filter_drop"]) for row in rows
        ),
        "mean_positive_oracle_task_count": statistics.fmean(
            float(row["positive_oracle_task_count"]) for row in rows
        ),
        "mean_positive_oracle_action_count": statistics.fmean(
            float(row["positive_oracle_action_count"]) for row in rows
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--wall-time-limit-sec", type=float, default=180.0)
    parser.add_argument("--memory-limit-gb", type=float, default=10.0)
    parser.add_argument(
        "--guidance-bucket-width",
        type=float,
        default=0.01,
    )
    parser.add_argument(
        "--oracle-method",
        choices=(
            "best_route_binary",
            "negative_route_reciprocal_rank",
            "negative_route_abs_rc",
            "cover_dual",
            "dominance_wins_log",
            "dominance_net_log",
            "dominance_leverage",
            "arc_dominance_wins_log",
            "arc_dominance_net_log",
            "arc_dominance_leverage",
        ),
        default="negative_route_reciprocal_rank",
    )
    parser.add_argument(
        "--oracle-sign",
        choices=("forward", "reverse"),
        default="forward",
    )
    parser.add_argument("--instance-root", action="append", required=True)
    args = parser.parse_args()

    label_path = (ROOT / args.labels).resolve()
    output_dir = (ROOT / args.output_dir).resolve()
    summary_path = (ROOT / args.summary).resolve()
    roots = tuple((ROOT / value).resolve() for value in args.instance_root)
    index = _instance_index(roots)
    outer = _load(label_path)
    source_rows = list(outer.get("rows") or outer.get("labels") or ())
    if not source_rows:
        raise SystemExit("label artifact has no rows")
    env = dict(os.environ)
    env["PYTHONPATH"] = (
        f"{ROOT / 'src'}:{ROOT / 'build/native-spprc'}"
    )
    python = sys.executable
    records: list[dict] = []
    for source_index, source in enumerate(source_rows):
        instance_id = str(source["instance_id"])
        candidates = index.get(instance_id) or []
        if len(candidates) != 1:
            raise SystemExit(
                f"instance path is not unique for {instance_id}: {candidates}"
            )
        instance = candidates[0]
        proof_fork = Path(
            source["fork_paths_by_action"]["proof_only"][0]
        ).resolve()
        snapshot = Path(_load(proof_fork)["source_snapshot_path"]).resolve()
        state_hash = str(source["source_state_hash"])
        short_hash = state_hash[:16]
        state_dir = output_dir / f"{int(source['scale'])}_{short_hash}"
        state_dir.mkdir(parents=True, exist_ok=True)
        control_first = state_dir / "qc0_rep1.json"
        if not control_first.exists():
            control_env = dict(env)
            if "dominance_" in str(args.oracle_method):
                control_env[
                    "LUNAR_ICE_PROOF_QUEUE_POTENTIAL_TRACE"
                ] = "1"
            _run(
                [
                    python,
                    str(REPLAY),
                    "--instance",
                    str(instance),
                    "--snapshot",
                    str(snapshot),
                    "--output",
                    str(control_first),
                    "--policy",
                    "QC0",
                    "--repeat-index",
                    "1",
                    "--wall-time-limit-sec",
                    str(float(args.wall_time_limit_sec)),
                    "--memory-limit-gb",
                    str(float(args.memory_limit_gb)),
                    "--guidance-bucket-width",
                    str(float(args.guidance_bucket_width)),
                ],
                control_env,
            )
        potential = state_dir / f"{args.oracle_method}_potential.json"
        if not potential.exists():
            _run(
                [
                    python,
                    str(BUILD_ORACLE),
                    "--instance",
                    str(instance),
                    "--snapshot",
                    str(snapshot),
                    "--control-replay",
                    str(control_first),
                    "--method",
                    str(args.oracle_method),
                    "--sign",
                    str(args.oracle_sign),
                    "--output",
                    str(potential),
                ],
                env,
            )
        for repeat in range(1, max(1, int(args.repeats)) + 1):
            arm_order = ["QC0", "QD1", "QG1"]
            random.Random(
                20260726 + source_index * 101 + repeat
            ).shuffle(arm_order)
            for policy in arm_order:
                target = state_dir / f"{policy.lower()}_rep{repeat}.json"
                if target.exists():
                    continue
                command = [
                    python,
                    str(REPLAY),
                    "--instance",
                    str(instance),
                    "--snapshot",
                    str(snapshot),
                    "--output",
                    str(target),
                    "--policy",
                    policy,
                    "--repeat-index",
                    str(repeat),
                    "--wall-time-limit-sec",
                    str(float(args.wall_time_limit_sec)),
                    "--memory-limit-gb",
                    str(float(args.memory_limit_gb)),
                    "--guidance-bucket-width",
                    str(float(args.guidance_bucket_width)),
                ]
                if policy == "QG1":
                    command.extend(["--potential", str(potential)])
                _run(command, env)
            arms = {
                policy: _load(
                    state_dir / f"{policy.lower()}_rep{repeat}.json"
                )
                for policy in ("QC0", "QD1", "QG1")
            }
            potential_payload = _load(potential)
            globals_ = [arms[key].get("global_min_rc") for key in arms]
            proved_thresholds = [
                arms[key].get("proved_no_rc_below") for key in arms
            ]
            task_hashes = [
                (arms[key].get("proof_telemetry") or {}).get(
                    "legal_action_universe_hash_before_sort"
                )
                for key in arms
            ]
            arc_hashes = [
                (arms[key].get("proof_telemetry") or {}).get(
                    "legal_arc_universe_hash_before_sort"
                )
                for key in arms
            ]
            records.append(
                {
                    "source_index": source_index,
                    "instance_id": instance_id,
                    "instance_content_hash": str(
                        source["instance_content_hash"]
                    ),
                    "source_state_hash": state_hash,
                    "scale": int(source["scale"]),
                    "repeat": repeat,
                    "qc0_wall_sec": float(
                        arms["QC0"]["total_fresh_process_wall_sec"]
                    ),
                    "qd1_wall_sec": float(
                        arms["QD1"]["total_fresh_process_wall_sec"]
                    ),
                    "qg1_wall_sec": float(
                        arms["QG1"]["total_fresh_process_wall_sec"]
                    ),
                    "qc0_native_wall_sec": float(
                        arms["QC0"]["proof_telemetry"]["wall_time_seconds"]
                    ),
                    "qd1_native_wall_sec": float(
                        arms["QD1"]["proof_telemetry"]["wall_time_seconds"]
                    ),
                    "qg1_native_wall_sec": float(
                        arms["QG1"]["proof_telemetry"]["wall_time_seconds"]
                    ),
                    "qg1_vs_fixed_best_ratio": float(
                        arms["QG1"]["total_fresh_process_wall_sec"]
                    )
                    / max(
                        1.0e-12,
                        min(
                            float(
                                arms["QC0"][
                                    "total_fresh_process_wall_sec"
                                ]
                            ),
                            float(
                                arms["QD1"][
                                    "total_fresh_process_wall_sec"
                                ]
                            ),
                        ),
                    ),
                    "positive_oracle_task_count": sum(
                        float(value) > 0.0
                        for value in potential_payload[
                            "task_potentials"
                        ].values()
                    ),
                    "positive_oracle_action_count": sum(
                        float(value) > 0.0
                        for field in (
                            "task_potentials",
                            "arc_potentials",
                        )
                        for value in potential_payload.get(field, {}).values()
                    ),
                    "exact_safe": all(
                        bool(arms[key]["exact_safe_ordering_audit"]["passed"])
                        for key in arms
                    ),
                    "global_min_match": (
                        (
                            all(value is not None for value in globals_)
                            and max(float(value) for value in globals_)
                            - min(float(value) for value in globals_)
                            <= 2.0e-6
                        )
                        or (
                            all(value is None for value in globals_)
                            and all(
                                value is not None
                                for value in proved_thresholds
                            )
                            and max(
                                float(value)
                                for value in proved_thresholds
                            )
                            - min(
                                float(value)
                                for value in proved_thresholds
                            )
                            <= 1.0e-12
                        )
                    ),
                    "legal_universe_match": (
                        len(set(task_hashes)) == 1
                        and len(set(arc_hashes)) == 1
                    ),
                    "zero_filter_drop": all(
                        all(
                            int(
                                arms[key]["proof_telemetry"].get(field)
                                or 0
                            )
                            == 0
                            for field in (
                                "guidance_filter_count",
                                "guidance_arc_drop_count",
                                "guidance_label_drop_count",
                                "guidance_branch_pair_drop_count",
                            )
                        )
                        and not bool(arms[key]["labels_dropped"])
                        for key in arms
                    ),
                    "paths": {
                        key.lower(): str(
                            state_dir / f"{key.lower()}_rep{repeat}.json"
                        )
                        for key in arms
                    },
                    "potential_path": str(potential),
                }
            )
            partial = {
                "schema_version": SCHEMA,
                "development_only": True,
                "deployable": False,
                "source_labels": str(label_path),
                "oracle_method": str(args.oracle_method),
                "oracle_sign": str(args.oracle_sign),
                "oracle_future_leakage": (
                    str(args.oracle_method) != "cover_dual"
                ),
                "guidance_bucket_width": float(
                    args.guidance_bucket_width
                ),
                "records": records,
                "aggregate": _aggregate(records),
            }
            _write(summary_path, partial)
            print(
                json.dumps(
                    {
                        "completed": len(records),
                        "instance_id": instance_id,
                        "repeat": repeat,
                        "qg1_vs_fixed_best_ratio": records[-1][
                            "qg1_vs_fixed_best_ratio"
                        ],
                    },
                    sort_keys=True,
                ),
                flush=True,
            )

    aggregate = _aggregate(records)
    minimum_states = 12
    gate = {
        "minimum_state_count": minimum_states,
        "passes_reachability_gate": bool(
            len(records) >= minimum_states
            and bool(aggregate.get("all_exact_safe"))
            and bool(aggregate.get("all_global_min_match"))
            and bool(aggregate.get("all_legal_universe_match"))
            and bool(aggregate.get("all_zero_filter_drop"))
            and float(
                aggregate.get(
                    "paired_geometric_mean_qg1_vs_fixed_best",
                    math.inf,
                )
            )
            <= 0.95
            and float(
                aggregate.get(
                    "median_qg1_vs_fixed_best_ratio",
                    math.inf,
                )
            )
            <= 0.95
            and int(
                aggregate.get(
                    "qg1_better_than_fixed_best_count",
                    0,
                )
            )
            >= math.ceil(0.6 * len(records))
        ),
        "permits_model_training": False,
        "reason": (
            "oracle headroom is necessary but no-leak predictability and "
            "held-out transfer remain untested"
        ),
    }
    final = {
        "schema_version": SCHEMA,
        "development_only": True,
        "deployable": False,
        "source_labels": str(label_path),
        "oracle_method": str(args.oracle_method),
        "oracle_sign": str(args.oracle_sign),
        "oracle_future_leakage": str(args.oracle_method) != "cover_dual",
        "guidance_bucket_width": float(args.guidance_bucket_width),
        "records": records,
        "aggregate": aggregate,
        "gate": gate,
    }
    _write(summary_path, final)
    print(json.dumps({"aggregate": aggregate, "gate": gate}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
