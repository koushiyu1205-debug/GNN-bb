#!/usr/bin/env python3
"""Generate an isolated, promotion-gated P0 V2 GAT development pool."""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
from math import dist
from pathlib import Path
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.domain.scheduling import generate_instance
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.guidance.resources import (
    recommended_parallelism,
    resource_snapshot,
)
from lunar_ice_bpc.io.instance_io import validate_instance, write_json


SCHEMA_VERSION = "lunar_ice_bpc.p0v2_gat_development_pool.v1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", default="")
    parser.add_argument(
        "--manifest",
        default="",
    )
    parser.add_argument(
        "--records-jsonl",
        default="",
    )
    parser.add_argument("--scales", default="5,10,20,30")
    parser.add_argument("--per-scale", type=int, default=60)
    parser.add_argument("--seed-base", type=int, default=80723000)
    parser.add_argument("--max-attempts-per-instance", type=int, default=80)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--min-free-gb", type=float, default=50.0)
    parser.add_argument(
        "--stage-b-report",
        default="",
        help=(
            "Required for scales 50/100. The report must show HA passed "
            "independently; protected large-scale instances are never used."
        ),
    )
    args = parser.parse_args()

    scales = tuple(
        int(value) for value in args.scales.split(",") if value.strip()
    )
    small_stage = bool(scales) and set(scales).issubset({5, 10, 20, 30})
    large_stage = bool(scales) and set(scales).issubset({50, 100})
    if not small_stage and not large_stage:
        raise SystemExit(
            "generation must be either scales 5/10/20/30 or scales 50/100"
        )
    if large_stage:
        if int(args.per_scale) != 20:
            raise SystemExit(
                "large-scale stage requires exactly 20 accepted instances per scale"
            )
        if not args.stage_b_report:
            raise SystemExit(
                "scale50/100 generation is locked until --stage-b-report"
            )
        stage_b = json.loads(
            (ROOT / args.stage_b_report).read_text(encoding="utf-8")
        )
        if not bool(stage_b.get("ha_independently_passed")) or not bool(
            ((stage_b.get("variants") or {}).get("HA") or {})
            .get("gate", {})
            .get("passed")
        ):
            raise SystemExit(
                "scale50/100 generation requires independently passed HA"
            )
    default_stem = (
        "large_development" if large_stage else "development"
    )
    output_root = (
        ROOT
        / (
            args.output_root
            or f"data/gat_p0v2/{default_stem}_instances"
        )
    ).resolve()
    manifest_argument = (
        args.manifest
        or f"data/gat_p0v2/{default_stem}_instances_manifest.json"
    )
    records_argument = (
        args.records_jsonl
        or f"data/gat_p0v2/{default_stem}_instance_records.jsonl"
    )
    output_root.mkdir(parents=True, exist_ok=True)
    resources = resource_snapshot(output_root)
    if resources.disk_available_bytes < float(args.min_free_gb) * 1024**3:
        raise SystemExit("insufficient free disk for development generation")
    workers = recommended_parallelism(
        resources,
        requested=max(1, int(args.workers)),
        min_memory_per_worker_bytes=2 * 1024**3,
        min_disk_free_bytes=int(float(args.min_free_gb) * 1024**3),
    )

    jobs = [
        (
            scale,
            index,
            int(args.seed_base),
            int(args.max_attempts_per_instance),
            str(output_root),
        )
        for scale in scales
        for index in range(1, int(args.per_scale) + 1)
    ]
    started = perf_counter()
    rows = []
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(_generate_one, *job): (job[0], job[1])
            for job in jobs
        }
        for completed, future in enumerate(as_completed(futures), start=1):
            scale, index = futures[future]
            row = future.result()
            rows.append(row)
            print(
                f"[{completed:03d}/{len(jobs):03d}] "
                f"scale={scale} index={index:03d} "
                f"attempt={row['attempt']} hash={row['instance_content_hash']}",
                flush=True,
            )

    rows.sort(key=lambda row: (int(row["scale"]), int(row["index"])))
    content_hashes = [str(row["instance_content_hash"]) for row in rows]
    if len(content_hashes) != len(set(content_hashes)):
        raise SystemExit("generated development pool contains duplicate content")
    protected_hashes = _protected_hashes()
    protected_overlap = sorted(set(content_hashes).intersection(protected_hashes))
    if protected_overlap:
        raise SystemExit(
            "development pool overlaps protected benchmark content: "
            + ",".join(protected_overlap)
        )

    by_scale = {
        str(scale): sum(int(row["scale"]) == scale for row in rows)
        for scale in scales
    }
    complete = all(
        count == int(args.per_scale) for count in by_scale.values()
    )
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": "complete" if complete else "incomplete",
        "source_role": "new_development",
        "generation_stage": (
            "post_ha_large_bounded" if large_stage else "initial_small_medium"
        ),
        "stage_b_report": (
            ""
            if not large_stage
            else str((ROOT / args.stage_b_report).resolve())
        ),
        "seed_base": int(args.seed_base),
        "scales": list(scales),
        "per_scale_target": int(args.per_scale),
        "accepted_total_count": len(rows),
        "count_by_scale": by_scale,
        "workers": workers,
        "generation_wall_sec": perf_counter() - started,
        "resource_snapshot_before": resources.__dict__,
        "protected_source_roles": [
            "full80_exact_test",
            "existing_large_shadow_test",
        ],
        "protected_hash_count_audited": len(protected_hashes),
        "protected_content_overlap_count": 0,
        "p0_difficulty_status": "pending_binding_v2_b0_measurement",
        "split_status": "not_assigned_until_p0_difficulty_is_available",
        "instances": rows,
    }
    manifest_path = (ROOT / manifest_argument).resolve()
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(manifest_path, manifest)
    records_path = (ROOT / records_argument).resolve()
    records_path.parent.mkdir(parents=True, exist_ok=True)
    records_path.write_text(
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
                    "p0_difficulty_bin": "pending_p0_measurement",
                },
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "accepted_total_count": len(rows),
                "workers": workers,
                "manifest": str(manifest_path),
                "records_jsonl": str(records_path),
                "generation_wall_sec": manifest["generation_wall_sec"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if complete else 2


def _generate_one(
    scale: int,
    index: int,
    seed_base: int,
    max_attempts: int,
    output_root: str,
) -> dict:
    target = (
        Path(output_root)
        / f"scale_{int(scale):03d}"
        / f"instance_{int(index):03d}_logical_graph.json"
    )
    if target.exists():
        instance = json.loads(target.read_text(encoding="utf-8"))
        issues = validate_instance(instance)
        if not issues and bool((instance.get("validation") or {}).get("accepted")):
            return _record(instance, target, scale=scale, index=index, attempt=0)
        raise RuntimeError(f"existing development instance is invalid: {target}")
    for attempt in range(1, max(1, int(max_attempts)) + 1):
        seed = (
            int(seed_base)
            + int(scale) * 1_000_000
            + int(index) * 1_000
            + attempt
        )
        instance = generate_instance(scale, seed=seed, index=index)
        if not bool((instance.get("validation") or {}).get("accepted")):
            continue
        if validate_instance(instance):
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        write_json(target, instance)
        return _record(
            instance,
            target,
            scale=scale,
            index=index,
            attempt=attempt,
            seed=seed,
        )
    raise RuntimeError(
        f"could not generate accepted scale={scale} index={index} "
        f"within {max_attempts} attempts"
    )


def _record(
    instance: dict,
    path: Path,
    *,
    scale: int,
    index: int,
    attempt: int,
    seed: int | None = None,
) -> dict:
    data = load_lunar_ice_data(instance)
    tasks = tuple(instance["tasks"].values())
    horizon = max(1.0, float(instance["scheduling"]["horizon_min"]))
    mean_width = sum(
        float(task["D"]) - float(task["r"]) for task in tasks
    ) / max(1, len(tasks))
    width_ratio = mean_width / horizon
    time_window_mode = (
        "tight" if width_ratio < 0.12 else "medium" if width_ratio < 0.25 else "wide"
    )
    mode_counts = {
        mode: sum(str(task["operation_mode"]) == mode for task in tasks)
        for mode in ("detect", "sample", "drill")
    }
    task_mode = (
        f"d{mode_counts['detect']}_s{mode_counts['sample']}_r{mode_counts['drill']}"
    )
    coordinates = [tuple(float(value) for value in task["xy_km"]) for task in tasks]
    mean_nearest = sum(
        min(
            dist(point, other)
            for other_index, other in enumerate(coordinates)
            if other_index != point_index
        )
        for point_index, point in enumerate(coordinates)
    ) / max(1, len(coordinates))
    hotspot_structure = (
        "concentrated"
        if mean_nearest < 2.0
        else "mixed"
        if mean_nearest < 4.0
        else "dispersed"
    )
    fleet_ratio = float(data.fleet_size) / max(1.0, float(data.scale))
    fleet_ratio_bin = (
        "low" if fleet_ratio < 0.10 else "medium" if fleet_ratio < 0.16 else "high"
    )
    return {
        "scale": int(scale),
        "index": int(index),
        "instance_id": data.instance_id,
        "instance_content_hash": data.instance_content_hash,
        "path": str(path.relative_to(ROOT)),
        "seed": seed,
        "attempt": int(attempt),
        "accepted": True,
        "time_window_mode": time_window_mode,
        "task_mode": task_mode,
        "hotspot_structure": hotspot_structure,
        "fleet_ratio_bin": fleet_ratio_bin,
        "p0_difficulty_bin": "pending_p0_measurement",
    }


def _protected_hashes() -> set[str]:
    values = set()
    for scale in (5, 10, 20, 30, 50, 100):
        directory = ROOT / "data" / "instances" / f"lunar_ice_sp50_{scale:03d}"
        for path in sorted(directory.glob("instance_*_logical_graph.json")):
            raw = json.loads(path.read_text(encoding="utf-8"))
            values.add(load_lunar_ice_data(raw).instance_content_hash)
    return values


if __name__ == "__main__":
    raise SystemExit(main())
