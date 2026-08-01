#!/usr/bin/env python3
"""Paired fresh-process Q0 versus OOF-GAT QG1 exact replay."""

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
SCHEMA = "lunar_ice_bpc.p0v5_proof_queue_gat_exact_replay.v1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cv-summary", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--scale", action="append", type=int, required=True)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--wall-time-limit-sec", type=float, default=180.0)
    parser.add_argument("--memory-limit-gb", type=float, default=10.0)
    parser.add_argument("--inference-overhead-sec", type=float, default=0.01)
    parser.add_argument("--guidance-bucket-width", type=float, default=1.0e-4)
    parser.add_argument(
        "--native-build-dir",
        default="build/native-spprc-bidirectional-feasibility-v1",
    )
    args = parser.parse_args()

    cv_path = _resolve(args.cv_summary)
    output_dir = _resolve(args.output_dir)
    output_path = _resolve(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    native_build = _resolve(args.native_build_dir)
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{ROOT / 'src'}:{native_build}"
    allowed_scales = {int(value) for value in args.scale}
    rows = [
        dict(row)
        for row in _load(cv_path).get("rows") or ()
        if int(row["scale"]) in allowed_scales
    ]
    records = []
    for index, row in enumerate(rows):
        state = str(row["source_state_hash"])
        state_dir = output_dir / f"{int(row['scale'])}_{state[:16]}"
        state_dir.mkdir(parents=True, exist_ok=True)
        for repeat in range(1, max(1, int(args.repeats)) + 1):
            policies = ["Q0", "QG1"]
            random.Random(20260801 + index * 101 + repeat).shuffle(policies)
            for policy in policies:
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
                subprocess.run(
                    command, cwd=ROOT, env=env, check=True
                )
            control = _load(state_dir / f"q0_rep{repeat}.json")
            guided = _load(state_dir / f"qg1_rep{repeat}.json")
            control_wall = float(control["total_fresh_process_wall_sec"])
            guided_wall = float(guided["total_fresh_process_wall_sec"])
            net_guided = guided_wall + max(
                0.0, float(args.inference_overhead_sec)
            )
            exact_match = _exact_match(control, guided)
            safe = bool(
                exact_match
                and _safe(control)
                and _safe(guided)
                and control["proof_telemetry"][
                    "legal_action_universe_hash_before_sort"
                ]
                == guided["proof_telemetry"][
                    "legal_action_universe_hash_before_sort"
                ]
                and control["proof_telemetry"][
                    "legal_arc_universe_hash_before_sort"
                ]
                == guided["proof_telemetry"][
                    "legal_arc_universe_hash_before_sort"
                ]
            )
            record = {
                "instance_id": row["instance_id"],
                "instance_content_hash": row["instance_content_hash"],
                "source_state_hash": state,
                "scale": int(row["scale"]),
                "repeat": repeat,
                "q0_wall_sec": control_wall,
                "qg1_measured_wall_sec": guided_wall,
                "inference_overhead_sec": max(
                    0.0, float(args.inference_overhead_sec)
                ),
                "qg1_net_wall_sec": net_guided,
                "qg1_net_vs_q0_ratio": net_guided / control_wall,
                "exact_match": exact_match,
                "exact_safe": safe,
                "paths": {
                    "q0": str(state_dir / f"q0_rep{repeat}.json"),
                    "qg1": str(state_dir / f"qg1_rep{repeat}.json"),
                },
            }
            records.append(record)
            print(
                json.dumps(
                    {
                        "completed": len(records),
                        "state": state[:16],
                        "ratio": record["qg1_net_vs_q0_ratio"],
                        "safe": safe,
                    },
                    sort_keys=True,
                ),
                flush=True,
            )

    by_state = {}
    for row in records:
        by_state.setdefault(row["source_state_hash"], []).append(row)
    state_rows = []
    for state, values in sorted(by_state.items()):
        q0 = statistics.median(row["q0_wall_sec"] for row in values)
        qg1 = statistics.median(
            row["qg1_measured_wall_sec"] for row in values
        ) + max(0.0, float(args.inference_overhead_sec))
        state_rows.append(
            {
                "source_state_hash": state,
                "instance_id": values[0]["instance_id"],
                "scale": values[0]["scale"],
                "q0_median_wall_sec": q0,
                "qg1_net_median_wall_sec": qg1,
                "qg1_net_vs_q0_ratio": qg1 / q0,
                "all_safe": all(row["exact_safe"] for row in values),
            }
        )
    ratios = [row["qg1_net_vs_q0_ratio"] for row in state_rows]
    ci = _bootstrap(ratios)
    aggregate = {
        "state_count": len(state_rows),
        "repeat_count": len(records),
        "win_count": sum(value < 1.0 for value in ratios),
        "five_percent_win_count": sum(value <= 0.95 for value in ratios),
        "median_net_ratio": statistics.median(ratios),
        "paired_geometric_mean_net_ratio": math.exp(
            statistics.fmean(math.log(value) for value in ratios)
        ),
        "bootstrap_95_interval_geomean_net_ratio": list(ci),
        "all_safe": all(row["all_safe"] for row in state_rows),
    }
    gate_pass = bool(
        aggregate["state_count"] >= 12
        and aggregate["all_safe"]
        and aggregate["paired_geometric_mean_net_ratio"] <= 0.95
        and ci[1] <= 1.0
    )
    payload = {
        "schema_version": SCHEMA,
        "development_only": True,
        "deployable": False,
        "source_cv_summary": str(cv_path),
        "native_build_dir": str(native_build),
        "guidance_bucket_width": float(args.guidance_bucket_width),
        "records": records,
        "state_rows": state_rows,
        "aggregate": aggregate,
        "gate": {
            "passes_oof_exact_replay": gate_pass,
            "permits_online_deployment": False,
            "reason": (
                "held-out V5 end-to-end calibration remains required"
                if gate_pass
                else "OOF exact replay did not meet the 5 percent gate"
            ),
        },
    }
    _write(output_path, payload)
    print(json.dumps({"aggregate": aggregate, "gate": payload["gate"]}))
    return 0


def _safe(row: dict) -> bool:
    telemetry = dict(row.get("proof_telemetry") or {})
    return bool(
        not row.get("labels_dropped")
        and all(
            int(telemetry.get(key) or 0) == 0
            for key in (
                "guidance_filter_count",
                "guidance_arc_drop_count",
                "guidance_label_drop_count",
                "guidance_branch_pair_drop_count",
            )
        )
    )


def _exact_match(left: dict, right: dict) -> bool:
    minima = (left.get("global_min_rc"), right.get("global_min_rc"))
    if all(value is not None for value in minima):
        return abs(float(minima[0]) - float(minima[1])) <= 2.0e-6
    thresholds = (
        left.get("proved_no_rc_below"),
        right.get("proved_no_rc_below"),
    )
    return bool(
        all(value is None for value in minima)
        and all(value is not None for value in thresholds)
        and abs(float(thresholds[0]) - float(thresholds[1])) <= 1.0e-12
    )


def _bootstrap(values: list[float]) -> tuple[float, float]:
    rng = random.Random(20260801)
    samples = []
    for _ in range(10000):
        draw = [values[rng.randrange(len(values))] for _ in values]
        samples.append(
            math.exp(statistics.fmean(math.log(value) for value in draw))
        )
    samples.sort()
    return samples[250], samples[9750]


def _resolve(value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
