#!/usr/bin/env python3
"""Assign within-scale P0 difficulty bins and freeze the split input rows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from lunar_ice_bpc.guidance.identity import (
    P0V2_BINDING_V2_B0_CONTROL_ID,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--development-manifest", required=True)
    parser.add_argument("--b0-results-jsonl", required=True)
    parser.add_argument("--output-records-jsonl", required=True)
    args = parser.parse_args()
    manifest = json.loads(
        Path(args.development_manifest).read_text(encoding="utf-8")
    )
    results = {}
    for line in Path(args.b0_results_jsonl).read_text(
        encoding="utf-8"
    ).splitlines():
        if line.strip():
            row = json.loads(line)
            results[str(row["instance_content_hash"])] = row
    source_rows = list(manifest.get("instances", ()))
    missing = [
        row["instance_content_hash"]
        for row in source_rows
        if row["instance_content_hash"] not in results
    ]
    if missing:
        raise SystemExit(
            f"B0 results incomplete: {len(missing)} development instances missing"
        )
    redline_failures = [
        content_hash
        for content_hash, row in results.items()
        if not bool(row.get("redlines_zero"))
    ]
    if redline_failures:
        raise SystemExit(
            "B0 redline failures cannot enter split stratification: "
            + ",".join(redline_failures[:10])
        )
    wrong_baselines = [
        content_hash
        for content_hash, row in results.items()
        if str(row.get("source_baseline_id") or "")
        != P0V2_BINDING_V2_B0_CONTROL_ID
    ]
    if wrong_baselines:
        raise SystemExit(
            "B0 ledger contains wrong/missing source baseline IDs: "
            + ",".join(wrong_baselines[:10])
        )
    config_hashes_by_scale = {}
    for scale in (5, 10, 20, 30):
        scale_hashes = {
            str(
                results[row["instance_content_hash"]].get(
                    "config_hash"
                )
                or ""
            )
            for row in source_rows
            if int(row["scale"]) == scale
        }
        if len(scale_hashes) != 1 or not next(iter(scale_hashes)):
            raise SystemExit(
                "B0 ledger must contain one non-empty config hash within "
                f"scale {scale}"
            )
        config_hashes_by_scale[str(scale)] = next(iter(scale_hashes))
    bins = {}
    thresholds = {}
    for scale in (5, 10, 20, 30):
        scale_rows = [
            results[row["instance_content_hash"]]
            for row in source_rows
            if int(row["scale"]) == scale
        ]
        exact_times = sorted(
            float(row["cold_start_total_sec"])
            for row in scale_rows
            if row.get("algorithm_status") == "BPC_OPTIMAL"
        )
        thresholds[str(scale)] = {
            "p50_exact_sec": _quantile(exact_times, 0.50),
            "p80_exact_sec": _quantile(exact_times, 0.80),
            "p95_exact_sec": _quantile(exact_times, 0.95),
            "exact_count": len(exact_times),
            "censored_count": len(scale_rows) - len(exact_times),
        }
        for row in scale_rows:
            content_hash = str(row["instance_content_hash"])
            if row.get("algorithm_status") != "BPC_OPTIMAL":
                bins[content_hash] = "tail_censored"
                continue
            value = float(row["cold_start_total_sec"])
            if value <= thresholds[str(scale)]["p50_exact_sec"]:
                bins[content_hash] = "easy"
            elif value <= thresholds[str(scale)]["p80_exact_sec"]:
                bins[content_hash] = "medium"
            elif value <= thresholds[str(scale)]["p95_exact_sec"]:
                bins[content_hash] = "hard"
            else:
                bins[content_hash] = "tail"
    output = Path(args.output_records_jsonl)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "".join(
            json.dumps(
                {
                    "instance_content_hash": row["instance_content_hash"],
                    "instance_id": row["instance_id"],
                    "scale": row["scale"],
                    "source_role": "new_development",
                    "time_window_mode": row["time_window_mode"],
                    "task_mode": row["task_mode"],
                    "hotspot_structure": row["hotspot_structure"],
                    "fleet_ratio_bin": row["fleet_ratio_bin"],
                    "p0_difficulty_bin": bins[
                        row["instance_content_hash"]
                    ],
                },
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n"
            for row in sorted(
                source_rows,
                key=lambda row: (int(row["scale"]), int(row["index"])),
            )
        ),
        encoding="utf-8",
    )
    report = {
        "schema_version": "lunar_ice_bpc.p0v2_difficulty_bins.v1",
        "source_role": "new_development",
        "record_count": len(source_rows),
        "thresholds_by_scale": thresholds,
        "censored_policy": "tail_censored_no_fixed_penalty",
        "protected_performance_used": False,
        "source_baseline_id": P0V2_BINDING_V2_B0_CONTROL_ID,
        "config_hash_by_scale": config_hashes_by_scale,
        "output_records_jsonl": str(output.resolve()),
    }
    report_path = output.with_suffix(output.suffix + ".report.json")
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    print(str(report_path.resolve()))
    return 0


def _quantile(values: list[float], probability: float) -> float:
    if not values:
        return float("inf")
    index = round((len(values) - 1) * float(probability))
    return float(values[max(0, min(len(values) - 1, index))])


if __name__ == "__main__":
    raise SystemExit(main())
