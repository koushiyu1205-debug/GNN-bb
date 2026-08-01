#!/usr/bin/env python3
"""Evaluate the precommitted DSSR V2 pressure grid on sentinels."""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REPLAY = ROOT / "scripts" / "replay_large_exact_pricer_tail.py"
SCHEMA_VERSION = "lunar_ice_bpc.dssr_v2_snapshot_grid.v1"
BUCKET_GRID = (4096, 8192, 16384)
CHECK_GRID = (50_000_000, 200_000_000, 800_000_000)
DEFAULT_SENTINELS = (
    ROOT
    / "runs"
    / "p0v3_six_scale_full120_baseline_20260727"
    / "slots"
    / "scale_020"
    / "instance_011"
    / "attempt_01"
    / "scale_020"
    / "pools"
    / "scale_020"
    / "instance_011"
    / "stage_001"
    / "probe.json",
    *tuple(
        ROOT
        / "runs"
        / "p0v3_six_scale_full120_baseline_20260727"
        / "slots"
        / "scale_030"
        / f"instance_{index:03d}"
        / "attempt_01"
        / "scale_030"
        / "pools"
        / "scale_030"
        / f"instance_{index:03d}"
        / "stage_001"
        / "probe.json"
        for index in (1, 5, 13, 16, 17)
    ),
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe-json", type=Path, action="append")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--time-limit-sec", type=float, default=3600.0)
    parser.add_argument("--memory-limit-gb", type=float, default=8.0)
    parser.add_argument("--negative-batch-target", type=int, default=16)
    parser.add_argument(
        "--bucket-limit",
        type=int,
        action="append",
        choices=BUCKET_GRID,
        help="run only selected precommitted bucket values",
    )
    parser.add_argument(
        "--candidate-check-limit",
        type=int,
        action="append",
        choices=CHECK_GRID,
        help="run only selected precommitted dominance-check values",
    )
    parser.add_argument(
        "--native-build",
        type=Path,
        default=ROOT / "build" / "native-spprc-dssr-v2",
    )
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    bucket_grid = tuple(dict.fromkeys(args.bucket_limit or BUCKET_GRID))
    check_grid = tuple(
        dict.fromkeys(args.candidate_check_limit or CHECK_GRID)
    )

    probes = tuple(
        path.resolve()
        for path in (args.probe_json or DEFAULT_SENTINELS)
    )
    missing = [str(path) for path in probes if not path.is_file()]
    if missing:
        raise SystemExit("missing sentinel probes: " + ",".join(missing))
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join(
        (
            str(ROOT / "src"),
            str(args.native_build.resolve()),
            environment.get("PYTHONPATH", ""),
        )
    )
    environment["LUNAR_ICE_SPPRC_GRAPH_CACHE_ENTRIES"] = "0"

    rows: list[dict] = []
    for bucket in bucket_grid:
        for checks in check_grid:
            config_id = f"b{bucket}_c{checks}"
            for probe in probes:
                probe_payload = _read_json(probe)
                scale, instance_id = _probe_identity(probe_payload)
                row_path = (
                    output
                    / config_id
                    / f"scale_{scale:03d}_{instance_id}.json"
                )
                command = [
                    sys.executable,
                    str(REPLAY),
                    "--probe-json",
                    str(probe),
                    "--time-limit-sec",
                    str(float(args.time_limit_sec)),
                    "--memory-limit-gb",
                    str(float(args.memory_limit_gb)),
                    "--execution-mode",
                    "host",
                    "--dssr-policy",
                    "v2",
                    "--dssr-negative-batch-target",
                    str(
                        max(
                            1,
                            min(64, int(args.negative_batch_target)),
                        )
                    ),
                    "--dssr-pressure-max-bucket-size",
                    str(bucket),
                    "--dssr-pressure-max-candidate-checks",
                    str(checks),
                    "--output",
                    str(row_path),
                ]
                if args.dry_run:
                    rows.append(
                        {
                            "config_id": config_id,
                            "scale": scale,
                            "instance_id": instance_id,
                            "probe_json": str(probe),
                            "command": command,
                            "status": "DRY_RUN",
                        }
                    )
                    continue
                if row_path.is_file() and args.resume:
                    payload = _read_json(row_path)
                else:
                    row_path.parent.mkdir(
                        parents=True,
                        exist_ok=True,
                    )
                    completed = subprocess.run(
                        command,
                        cwd=ROOT,
                        env=environment,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    (
                        row_path.with_suffix(".stdout.txt")
                    ).write_text(completed.stdout, encoding="utf-8")
                    (
                        row_path.with_suffix(".stderr.txt")
                    ).write_text(completed.stderr, encoding="utf-8")
                    if completed.returncode != 0 or not row_path.is_file():
                        rows.append(
                            {
                                "config_id": config_id,
                                "scale": scale,
                                "instance_id": instance_id,
                                "probe_json": str(probe),
                                "command": command,
                                "status": "RUNNER_FAILED",
                                "returncode": completed.returncode,
                            }
                        )
                        _write_json(output / "rows.json", rows)
                        continue
                    payload = _read_json(row_path)
                rows.append(
                    _row(
                        payload,
                        config_id=config_id,
                        bucket=bucket,
                        checks=checks,
                    )
                )
                _write_json(output / "rows.json", rows)
                print(
                    f"[DONE] {config_id} scale={scale} "
                    f"instance={instance_id} "
                    f"status={rows[-1]['status']}",
                    flush=True,
                )

    summary = _summarize(
        rows,
        expected=len(probes),
        expected_configurations=len(bucket_grid) * len(check_grid),
    )
    _write_json(output / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["status"] in {"COMPLETE", "DRY_RUN"} else 1


def _row(
    payload: dict,
    *,
    config_id: str,
    bucket: int,
    checks: int,
) -> dict:
    p0 = dict(payload["p0"])
    dssr = dict(payload["dssr"])
    p0_wall = float(p0.get("elapsed_wall_sec") or 0.0)
    dssr_wall = float(dssr.get("elapsed_wall_sec") or 0.0)
    p0_success = bool(
        p0.get("can_enter_certificate_audit")
        or (
            int(p0.get("column_count") or 0) > 0
            and p0.get("partial_columns_valid")
        )
    )
    dssr_success = bool(
        dssr.get("can_enter_certificate_audit")
        or (
            int(dssr.get("column_count") or 0) > 0
            and dssr.get("partial_columns_valid")
        )
    )
    telemetry = dict(dssr.get("telemetry") or {})
    rss_values = [
        value
        for value in (telemetry.get("host_peak_rss_bytes"),)
        if isinstance(value, (int, float))
    ]
    return {
        "config_id": config_id,
        "bucket_limit": bucket,
        "candidate_check_limit": checks,
        "scale": int(payload["scale"]),
        "instance_id": str(payload["instance_id"]),
        "instance_content_hash": str(
            payload["instance_content_hash"]
        ),
        "status": "PASS" if dssr_success else "INCOMPLETE",
        "p0_success": p0_success,
        "dssr_success": dssr_success,
        "extra_incomplete": p0_success and not dssr_success,
        "safety_pass": bool(
            payload.get("audit", {}).get("both_bindings_match")
            and payload.get("audit", {}).get(
                "both_labels_dropped_zero"
            )
            and payload.get("audit", {}).get(
                "dssr_returns_audited_negative_or_exact_certificate"
            )
        ),
        "p0_wall_sec": p0_wall,
        "dssr_wall_sec": dssr_wall,
        "wall_ratio": (
            dssr_wall / p0_wall if p0_wall > 0.0 else math.inf
        ),
        "peak_rss_bytes": max(rss_values, default=None),
        "dssr_pressure_refinement_count": int(
            telemetry.get("dssr_pressure_refinement_count") or 0
        ),
        "dssr_max_bucket_size": int(
            telemetry.get("dssr_max_bucket_size") or 0
        ),
        "dssr_dominance_candidate_checks": int(
            telemetry.get("dssr_dominance_candidate_checks") or 0
        ),
    }


def _summarize(
    rows: list[dict],
    *,
    expected: int,
    expected_configurations: int,
) -> dict:
    if rows and all(row.get("status") == "DRY_RUN" for row in rows):
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "DRY_RUN",
            "rows": rows,
        }
    by_config: dict[str, list[dict]] = {}
    for row in rows:
        by_config.setdefault(str(row["config_id"]), []).append(row)
    configurations = []
    for config_id, config_rows in sorted(by_config.items()):
        ratios_by_scale = {
            scale: [
                float(row["wall_ratio"])
                for row in config_rows
                if int(row.get("scale") or 0) == scale
                and math.isfinite(float(row.get("wall_ratio", math.inf)))
            ]
            for scale in (20, 30)
        }
        scale_geomeans = {
            scale: _geomean(values)
            for scale, values in ratios_by_scale.items()
            if values
        }
        complete = len(config_rows) == expected
        safety = complete and all(
            bool(row.get("safety_pass")) for row in config_rows
        )
        extra_incomplete = sum(
            bool(row.get("extra_incomplete")) for row in config_rows
        )
        configurations.append(
            {
                "config_id": config_id,
                "bucket_limit": config_rows[0].get("bucket_limit"),
                "candidate_check_limit": config_rows[0].get(
                    "candidate_check_limit"
                ),
                "row_count": len(config_rows),
                "safety_pass": safety,
                "extra_incomplete_count": extra_incomplete,
                "worst_scale_geometric_mean": max(
                    scale_geomeans.values(),
                    default=math.inf,
                ),
                "scale_geometric_means": scale_geomeans,
                "mean_wall_sec": (
                    sum(float(row.get("dssr_wall_sec") or 0.0) for row in config_rows)
                    / len(config_rows)
                    if config_rows
                    else math.inf
                ),
                "max_wall_sec": max(
                    (
                        float(row.get("dssr_wall_sec") or 0.0)
                        for row in config_rows
                    ),
                    default=math.inf,
                ),
                "max_peak_rss_bytes": max(
                    (
                        int(row["peak_rss_bytes"])
                        for row in config_rows
                        if row.get("peak_rss_bytes") is not None
                    ),
                    default=None,
                ),
                "scale20_011_regression_pass": _scale20_011_gate(
                    config_rows
                ),
                "scale30_sentinel_exact_close_pass": _scale30_gate(
                    config_rows
                ),
            }
        )
    ranked = sorted(
        configurations,
        key=lambda row: (
            not bool(row["safety_pass"]),
            int(row["extra_incomplete_count"]),
            float(row["worst_scale_geometric_mean"]),
            float(row["mean_wall_sec"]),
            float(row["max_wall_sec"]),
            (
                int(row["max_peak_rss_bytes"])
                if row["max_peak_rss_bytes"] is not None
                else math.inf
            ),
            str(row["config_id"]),
        ),
    )
    complete = bool(
        len(configurations) == expected_configurations
        and all(row["row_count"] == expected for row in configurations)
    )
    selected = ranked[0] if complete and ranked else None
    regression_gate_pass = bool(
        selected
        and selected["safety_pass"]
        and not selected["extra_incomplete_count"]
        and selected["scale20_011_regression_pass"]
        and selected["scale30_sentinel_exact_close_pass"]
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "COMPLETE" if complete else "INCOMPLETE",
        "selection_order": [
            "safety",
            "zero_extra_incomplete",
            "worst_scale_geometric_mean",
            "mean_wall",
            "max_wall",
            "rss",
        ],
        "selected_configuration": selected,
        "regression_gate_pass": regression_gate_pass,
        "freeze_allowed": regression_gate_pass,
        "configurations": configurations,
        "rows": rows,
    }


def _geomean(values: list[float]) -> float:
    if not values or any(value <= 0.0 for value in values):
        return math.inf
    return math.exp(sum(math.log(value) for value in values) / len(values))


def _scale20_011_gate(rows: list[dict]) -> bool:
    selected = [
        row
        for row in rows
        if int(row.get("scale") or 0) == 20
        and "_011_" in f"_{row.get('instance_id', '')}_"
    ]
    return bool(
        len(selected) == 1
        and selected[0].get("dssr_success")
        and not selected[0].get("extra_incomplete")
        and selected[0].get("safety_pass")
        and float(selected[0].get("wall_ratio", math.inf)) <= 1.10
        and int(
            selected[0].get("dssr_max_bucket_size") or 0
        )
        < 79_000
        and int(
            selected[0].get("dssr_dominance_candidate_checks") or 0
        )
        < 10_000_000_000
    )


def _scale30_gate(rows: list[dict]) -> bool:
    selected = [
        row for row in rows if int(row.get("scale") or 0) == 30
    ]
    return bool(
        len(selected) == 5
        and all(
            row.get("dssr_success")
            and not row.get("extra_incomplete")
            and row.get("safety_pass")
            for row in selected
        )
    )


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _probe_identity(payload: dict) -> tuple[int, str]:
    instance_path = Path(str(payload["instance_path"]))
    if not instance_path.is_absolute():
        instance_path = (ROOT / instance_path).resolve()
    instance = _read_json(instance_path)
    return int(instance["scale"]), str(instance["instance_id"])


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


if __name__ == "__main__":
    raise SystemExit(main())
