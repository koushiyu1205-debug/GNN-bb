#!/usr/bin/env python3
"""Generate and content-hash lock the DSSR V2 development/test pool."""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from math import dist
from pathlib import Path
import shutil
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.domain.scheduling import generate_instance
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.io.instance_io import validate_instance, write_json


SCHEMA_VERSION = "lunar_ice_bpc.dssr_v2_validation_pool.v1"
DEFAULT_COUNTS = {
    5: (12, 8),
    10: (12, 8),
    20: (12, 8),
    30: (12, 8),
    50: (3, 2),
    100: (3, 2),
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ROOT / "data" / "dssr_v2_validation",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=(
            ROOT
            / "data"
            / "manifests"
            / "dssr_v2_validation_split_manifest.json"
        ),
    )
    parser.add_argument("--seed-base", type=int, default=90729000)
    parser.add_argument("--max-attempts", type=int, default=80)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--min-free-gb", type=float, default=20.0)
    args = parser.parse_args()

    output_root = args.output_root.resolve()
    manifest_path = args.manifest.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    free_bytes = shutil.disk_usage(output_root).free
    if free_bytes < float(args.min_free_gb) * 1024**3:
        raise SystemExit("insufficient free disk for DSSR V2 generation")

    protected = _protected_hashes()
    jobs = []
    for scale, (development_count, locked_count) in DEFAULT_COUNTS.items():
        for index in range(1, development_count + locked_count + 1):
            jobs.append(
                (
                    scale,
                    index,
                    int(args.seed_base),
                    int(args.max_attempts),
                    str(output_root),
                )
            )

    started = perf_counter()
    rows: list[dict] = []
    with ProcessPoolExecutor(
        max_workers=max(1, int(args.workers))
    ) as executor:
        pending = {
            executor.submit(_generate_one, *job): job[:2]
            for job in jobs
        }
        for completed, future in enumerate(
            as_completed(pending),
            start=1,
        ):
            scale, index = pending[future]
            row = future.result()
            rows.append(row)
            print(
                f"[{completed:03d}/{len(jobs):03d}] "
                f"scale={scale} index={index:03d} "
                f"hash={row['instance_content_hash']}",
                flush=True,
            )

    rows.sort(
        key=lambda row: (
            int(row["scale"]),
            str(row["instance_content_hash"]),
        )
    )
    hashes = [str(row["instance_content_hash"]) for row in rows]
    if len(hashes) != len(set(hashes)):
        raise SystemExit("DSSR V2 pool contains duplicate content")
    overlap = sorted(set(hashes) & protected)
    if overlap:
        raise SystemExit(
            "DSSR V2 pool overlaps protected instances: "
            + ",".join(overlap)
        )

    development: list[dict] = []
    locked_test: list[dict] = []
    for scale, (development_count, locked_count) in DEFAULT_COUNTS.items():
        scale_rows = [
            row for row in rows if int(row["scale"]) == scale
        ]
        selected_development = _stratified_development_hashes(
            scale_rows,
            development_count=development_count,
        )
        for row in scale_rows:
            target = (
                development
                if row["instance_content_hash"] in selected_development
                else locked_test
            )
            target.append(
                {
                    **row,
                    "partition": (
                        "development"
                        if target is development
                        else "locked_test"
                    ),
                }
            )
        if (
            sum(int(row["scale"]) == scale for row in development)
            != development_count
            or sum(int(row["scale"]) == scale for row in locked_test)
            != locked_count
        ):
            raise RuntimeError("stratified split count mismatch")

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": "LOCKED",
        "assignment_unit": "instance_content_hash",
        "assignment_policy": (
            "stratified_content_hash_largest_remainder_v1"
        ),
        "stratification_fields": [
            "time_window_mode",
            "task_mode",
            "hotspot_structure",
            "fleet_ratio_bin",
        ],
        "seed_base": int(args.seed_base),
        "generation_wall_sec": perf_counter() - started,
        "protected_hash_count": len(protected),
        "protected_overlap_count": 0,
        "development": sorted(
            development,
            key=lambda row: (
                int(row["scale"]),
                str(row["instance_content_hash"]),
            ),
        ),
        "locked_test": sorted(
            locked_test,
            key=lambda row: (
                int(row["scale"]),
                str(row["instance_content_hash"]),
            ),
        ),
        "counts": {
            str(scale): {
                "development": development_count,
                "locked_test": locked_count,
            }
            for scale, (
                development_count,
                locked_count,
            ) in DEFAULT_COUNTS.items()
        },
        "audit": {
            "unique_content_hashes": len(hashes) == len(set(hashes)),
            "development_locked_overlap_count": len(
                {
                    row["instance_content_hash"]
                    for row in development
                }
                & {
                    row["instance_content_hash"]
                    for row in locked_test
                }
            ),
            "formal_or_prior_protected_overlap_count": 0,
            "locked_test_policy": (
                "run_once_only_after_policy_thresholds_and_code_freeze"
            ),
            "locked_test_used_for_selection": False,
        },
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(manifest_path, manifest)
    print(
        json.dumps(
            {
                "status": "LOCKED",
                "manifest": str(manifest_path),
                "development_count": len(development),
                "locked_test_count": len(locked_test),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


def _generate_one(
    scale: int,
    index: int,
    seed_base: int,
    max_attempts: int,
    output_root: str,
) -> dict:
    path = (
        Path(output_root)
        / f"scale_{scale:03d}"
        / f"instance_{index:03d}_logical_graph.json"
    )
    if path.is_file():
        payload = json.loads(path.read_text(encoding="utf-8"))
        if (
            not validate_instance(payload)
            and bool((payload.get("validation") or {}).get("accepted"))
        ):
            return _record(payload, path, scale, index, None)
        raise RuntimeError(f"invalid existing instance: {path}")
    for attempt in range(1, max(1, max_attempts) + 1):
        seed = (
            seed_base
            + scale * 1_000_000
            + index * 1_000
            + attempt
        )
        payload = generate_instance(scale, seed=seed, index=index)
        if (
            not bool((payload.get("validation") or {}).get("accepted"))
            or validate_instance(payload)
        ):
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        write_json(path, payload)
        return _record(payload, path, scale, index, seed)
    raise RuntimeError(
        f"could not generate scale={scale} index={index}"
    )


def _record(
    payload: dict,
    path: Path,
    scale: int,
    index: int,
    seed: int | None,
) -> dict:
    data = load_lunar_ice_data(payload)
    tasks = tuple(payload["tasks"].values())
    horizon = max(
        1.0,
        float(payload["scheduling"]["horizon_min"]),
    )
    mean_width = sum(
        float(task["D"]) - float(task["r"]) for task in tasks
    ) / len(tasks)
    width_ratio = mean_width / horizon
    time_window_mode = (
        "tight"
        if width_ratio < 0.12
        else "medium"
        if width_ratio < 0.25
        else "wide"
    )
    mode_counts = {
        mode: sum(
            str(task["operation_mode"]) == mode for task in tasks
        )
        for mode in ("detect", "sample", "drill")
    }
    task_mode = (
        f"d{mode_counts['detect']}_"
        f"s{mode_counts['sample']}_"
        f"r{mode_counts['drill']}"
    )
    coordinates = [
        tuple(float(value) for value in task["xy_km"])
        for task in tasks
    ]
    mean_nearest = sum(
        min(
            dist(point, other)
            for other_index, other in enumerate(coordinates)
            if other_index != point_index
        )
        for point_index, point in enumerate(coordinates)
    ) / len(coordinates)
    hotspot_structure = (
        "concentrated"
        if mean_nearest < 2.0
        else "mixed"
        if mean_nearest < 4.0
        else "dispersed"
    )
    fleet_ratio = float(data.fleet_size) / float(data.scale)
    fleet_ratio_bin = (
        "low"
        if fleet_ratio < 0.10
        else "medium"
        if fleet_ratio < 0.16
        else "high"
    )
    return {
        "scale": scale,
        "index": index,
        "instance_id": data.instance_id,
        "instance_content_hash": data.instance_content_hash,
        "path": str(path.relative_to(ROOT)),
        "seed": seed,
        "time_window_mode": time_window_mode,
        "task_mode": task_mode,
        "hotspot_structure": hotspot_structure,
        "fleet_ratio_bin": fleet_ratio_bin,
    }


def _stratified_development_hashes(
    rows: list[dict],
    *,
    development_count: int,
) -> set[str]:
    groups: dict[tuple[str, ...], list[dict]] = {}
    fields = (
        "time_window_mode",
        "task_mode",
        "hotspot_structure",
        "fleet_ratio_bin",
    )
    for row in rows:
        groups.setdefault(
            tuple(str(row[field]) for field in fields),
            [],
        ).append(row)
    ratio = development_count / len(rows)
    quotas = {
        key: int(len(values) * ratio)
        for key, values in groups.items()
    }
    remaining = development_count - sum(quotas.values())
    remainder_order = sorted(
        groups,
        key=lambda key: (
            -(len(groups[key]) * ratio - quotas[key]),
            _hash_text(repr(key)),
        ),
    )
    for key in remainder_order[:remaining]:
        quotas[key] += 1
    selected: set[str] = set()
    for key, values in groups.items():
        ordered = sorted(
            values,
            key=lambda row: _hash_text(
                "dssr-v2-split:"
                + str(row["instance_content_hash"])
            ),
        )
        selected.update(
            str(row["instance_content_hash"])
            for row in ordered[: quotas[key]]
        )
    if len(selected) != development_count:
        raise RuntimeError("development quota construction failed")
    return selected


def _protected_hashes() -> set[str]:
    hashes: set[str] = set()
    for scale in DEFAULT_COUNTS:
        directory = (
            ROOT
            / "data"
            / "instances"
            / f"lunar_ice_sp50_{scale:03d}"
        )
        for path in directory.glob(
            "instance_*_logical_graph.json"
        ):
            payload = json.loads(path.read_text(encoding="utf-8"))
            hashes.add(
                load_lunar_ice_data(payload).instance_content_hash
            )
    return hashes


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
