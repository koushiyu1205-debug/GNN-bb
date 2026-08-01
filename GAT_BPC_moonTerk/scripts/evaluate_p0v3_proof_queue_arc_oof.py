#!/usr/bin/env python3
"""Fresh-process exact replay of grouped out-of-fold arc potentials."""

from __future__ import annotations

import argparse
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
SCHEMA = "lunar_ice_bpc.p0v3_proof_queue_arc_oof_exact_evaluation.v1"


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


def _run(command: list[str], env: dict[str, str]) -> None:
    subprocess.run(command, cwd=ROOT, env=env, check=True)


def _bootstrap(values: list[float]) -> tuple[float, float]:
    rng = random.Random(20260726)
    samples = []
    for _ in range(10000):
        selected = [values[rng.randrange(len(values))] for _ in values]
        samples.append(
            math.exp(statistics.fmean(math.log(value) for value in selected))
        )
    samples.sort()
    return samples[250], samples[9750]


def _match_exact(arms: dict[str, dict]) -> bool:
    minima = [arms[key].get("global_min_rc") for key in arms]
    thresholds = [arms[key].get("proved_no_rc_below") for key in arms]
    if all(value is not None for value in minima):
        return (
            max(float(value) for value in minima)
            - min(float(value) for value in minima)
            <= 2.0e-6
        )
    return bool(
        all(value is None for value in minima)
        and all(value is not None for value in thresholds)
        and max(float(value) for value in thresholds)
        - min(float(value) for value in thresholds)
        <= 1.0e-12
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cv-summary", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--scale", action="append", type=int, required=True)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--wall-time-limit-sec", type=float, default=180.0)
    parser.add_argument("--memory-limit-gb", type=float, default=10.0)
    parser.add_argument(
        "--inference-overhead-sec",
        type=float,
        default=0.02,
    )
    parser.add_argument(
        "--guidance-bucket-width",
        type=float,
        default=0.01,
    )
    parser.add_argument(
        "--native-build-dir",
        default="build/native-spprc",
        help=(
            "Native extension build used by fresh replay processes. "
            "This is part of the reported evaluation binding."
        ),
    )
    args = parser.parse_args()

    cv_path = (ROOT / args.cv_summary).resolve()
    output_dir = (ROOT / args.output_dir).resolve()
    output_path = (ROOT / args.output).resolve()
    allowed_scales = {int(value) for value in args.scale}
    cv = _load(cv_path)
    env = dict(os.environ)
    native_build_dir = (ROOT / args.native_build_dir).resolve()
    env["PYTHONPATH"] = (
        f"{ROOT / 'src'}:{native_build_dir}"
    )
    records = []
    rows = [
        dict(row) for row in cv.get("rows") or ()
        if int(row["scale"]) in allowed_scales
    ]
    for source_index, row in enumerate(rows):
        state_dir = output_dir / (
            f"{int(row['scale'])}_{str(row['source_state_hash'])[:16]}"
        )
        state_dir.mkdir(parents=True, exist_ok=True)
        for repeat in range(1, max(1, int(args.repeats)) + 1):
            order = ["QC0", "QD1", "QG1"]
            random.Random(
                20260726 + source_index * 101 + repeat
            ).shuffle(order)
            for policy in order:
                target = state_dir / f"{policy.lower()}_rep{repeat}.json"
                if target.exists():
                    continue
                command = [
                    sys.executable,
                    str(REPLAY),
                    "--instance",
                    str(row["instance_path"]),
                    "--snapshot",
                    str(row["snapshot_path"]),
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
                    command.extend(
                        ["--potential", str(row["potential_path"])]
                    )
                _run(command, env)
            arms = {
                policy: _load(
                    state_dir / f"{policy.lower()}_rep{repeat}.json"
                )
                for policy in ("QC0", "QD1", "QG1")
            }
            fixed_best = min(
                float(arms["QC0"]["total_fresh_process_wall_sec"]),
                float(arms["QD1"]["total_fresh_process_wall_sec"]),
            )
            guided = (
                float(arms["QG1"]["total_fresh_process_wall_sec"])
                + max(0.0, float(args.inference_overhead_sec))
            )
            task_hashes = {
                arms[key]["proof_telemetry"][
                    "legal_action_universe_hash_before_sort"
                ]
                for key in arms
            }
            arc_hashes = {
                arms[key]["proof_telemetry"][
                    "legal_arc_universe_hash_before_sort"
                ]
                for key in arms
            }
            records.append(
                {
                    "instance_id": row["instance_id"],
                    "instance_content_hash": row[
                        "instance_content_hash"
                    ],
                    "source_state_hash": row["source_state_hash"],
                    "fold": int(row["fold"]),
                    "scale": int(row["scale"]),
                    "repeat": repeat,
                    "qc0_wall_sec": float(
                        arms["QC0"]["total_fresh_process_wall_sec"]
                    ),
                    "qd1_wall_sec": float(
                        arms["QD1"]["total_fresh_process_wall_sec"]
                    ),
                    "qg1_measured_wall_sec": float(
                        arms["QG1"]["total_fresh_process_wall_sec"]
                    ),
                    "inference_overhead_sec": max(
                        0.0, float(args.inference_overhead_sec)
                    ),
                    "qg1_net_wall_sec": guided,
                    "qg1_net_vs_fixed_best_ratio": guided / fixed_best,
                    "exact_match": _match_exact(arms),
                    "exact_safe": all(
                        bool(
                            arms[key]["exact_safe_ordering_audit"][
                                "passed"
                            ]
                        )
                        for key in arms
                    ),
                    "legal_universe_match": (
                        len(task_hashes) == 1 and len(arc_hashes) == 1
                    ),
                    "zero_filter_drop": all(
                        not bool(arms[key]["labels_dropped"])
                        and all(
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
                        for key in arms
                    ),
                    "potential_path": row["potential_path"],
                    "paths": {
                        key.lower(): str(
                            state_dir / f"{key.lower()}_rep{repeat}.json"
                        )
                        for key in arms
                    },
                }
            )
            print(
                json.dumps(
                    {
                        "completed": len(records),
                        "instance_id": row["instance_id"],
                        "repeat": repeat,
                        "net_ratio": records[-1][
                            "qg1_net_vs_fixed_best_ratio"
                        ],
                    },
                    sort_keys=True,
                ),
                flush=True,
            )

    by_state = {}
    for record in records:
        by_state.setdefault(record["source_state_hash"], []).append(record)
    state_rows = []
    for state_hash, state_records in by_state.items():
        state_rows.append(
            {
                "source_state_hash": state_hash,
                "instance_id": state_records[0]["instance_id"],
                "scale": state_records[0]["scale"],
                "median_qc0_wall_sec": statistics.median(
                    row["qc0_wall_sec"] for row in state_records
                ),
                "median_qd1_wall_sec": statistics.median(
                    row["qd1_wall_sec"] for row in state_records
                ),
                "median_qg1_measured_wall_sec": statistics.median(
                    row["qg1_measured_wall_sec"] for row in state_records
                ),
                "qg1_net_vs_fixed_best_ratio": (
                    statistics.median(
                        row["qg1_measured_wall_sec"]
                        for row in state_records
                    )
                    + max(0.0, float(args.inference_overhead_sec))
                )
                / min(
                    statistics.median(
                        row["qc0_wall_sec"] for row in state_records
                    ),
                    statistics.median(
                        row["qd1_wall_sec"] for row in state_records
                    ),
                ),
                "all_safe": all(
                    row["exact_match"]
                    and row["exact_safe"]
                    and row["legal_universe_match"]
                    and row["zero_filter_drop"]
                    for row in state_records
                ),
            }
        )
    ratios = [
        float(row["qg1_net_vs_fixed_best_ratio"]) for row in state_rows
    ]
    ci_low, ci_high = _bootstrap(ratios)
    aggregate = {
        "state_count": len(state_rows),
        "repeat_count": len(records),
        "win_count": sum(value < 1.0 for value in ratios),
        "median_net_ratio": statistics.median(ratios),
        "paired_geometric_mean_net_ratio": math.exp(
            statistics.fmean(math.log(value) for value in ratios)
        ),
        "bootstrap_95_interval_geomean_net_ratio": [ci_low, ci_high],
        "all_safe": all(row["all_safe"] for row in state_rows),
    }
    gate = {
        "passes_linear_realizability_gate": bool(
            aggregate["state_count"] >= 8
            and aggregate["all_safe"]
            and aggregate["win_count"] >= 6
            and aggregate["median_net_ratio"] <= 0.98
            and aggregate["paired_geometric_mean_net_ratio"] <= 0.98
            and ci_high <= 1.0
        ),
        "permits_gat_training": False,
        "permits_online_deployment": False,
        "reason": (
            "GAT may train only if the smallest linear model passes; online "
            "deployment still requires independent held-out end-to-end gain"
        ),
    }
    payload = {
        "schema_version": SCHEMA,
        "development_only": True,
        "deployable": False,
        "source_cv_summary": str(cv_path),
        "scales": sorted(allowed_scales),
        "inference_overhead_sec": max(
            0.0, float(args.inference_overhead_sec)
        ),
        "guidance_bucket_width": float(args.guidance_bucket_width),
        "native_build_dir": str(native_build_dir),
        "records": records,
        "state_rows": state_rows,
        "aggregate": aggregate,
        "gate": gate,
    }
    _write(output_path, payload)
    print(json.dumps({"aggregate": aggregate, "gate": gate}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
