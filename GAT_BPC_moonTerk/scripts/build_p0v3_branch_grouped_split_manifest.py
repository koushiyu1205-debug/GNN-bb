#!/usr/bin/env python3
"""Freeze five grouped folds without using branch labels or protected tests."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from math import dist
from pathlib import Path


SCHEMA_VERSION = "lunar_ice_bpc.branch_grouped_split_manifest.v2"
SYNTHETIC_POLAR_GRID_DOMAIN = "synthetic_polar_resource_grid_v1"
REAL_MAP_SP50_DOMAIN = "real_lunar_south_pole_sp50_benchmark_v1"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _bucket(value: str, salt: str) -> int:
    return int.from_bytes(
        hashlib.sha256(f"{salt}:{value}".encode()).digest()[:8],
        "big",
    )


def _manifest_hash(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def _structural_metadata(instance_path: Path) -> dict[str, str]:
    instance = _load(instance_path)
    instance_id = str(instance.get("instance_id") or "")
    if instance_id.startswith("lunar_ice_sp50_"):
        generator_domain = REAL_MAP_SP50_DOMAIN
    elif instance_id.startswith("lunar_ice_"):
        generator_domain = SYNTHETIC_POLAR_GRID_DOMAIN
    else:
        raise ValueError(
            f"unrecognized instance-generator domain: {instance_id!r}"
        )
    tasks = tuple((instance.get("tasks") or {}).values())
    horizon = max(
        1.0,
        float((instance.get("scheduling") or {})["horizon_min"]),
    )
    mean_width = sum(
        float(task["D"]) - float(task["r"]) for task in tasks
    ) / max(1, len(tasks))
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
    ) / max(1, len(coordinates))
    fleet_ratio = float(
        (instance.get("vehicle") or {})["fleet_size"]
    ) / max(1.0, float(instance["scale"]))
    return {
        "instance_generator_domain": generator_domain,
        "time_window_mode": time_window_mode,
        "task_mode": (
            f"d{mode_counts['detect']}_s{mode_counts['sample']}_"
            f"r{mode_counts['drill']}"
        ),
        "hotspot_structure": (
            "concentrated"
            if mean_nearest < 2.0
            else "mixed"
            if mean_nearest < 4.0
            else "dispersed"
        ),
        "fleet_ratio_bin": (
            "low"
            if fleet_ratio < 0.10
            else "medium"
            if fleet_ratio < 0.16
            else "high"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--content-manifest", required=True)
    parser.add_argument("--source-manifest", required=True)
    parser.add_argument("--output-manifest", required=True)
    parser.add_argument("--fold-count", type=int, default=5)
    args = parser.parse_args()
    if int(args.fold_count) < 2:
        raise SystemExit("fold count must be at least two")

    content_path = Path(args.content_manifest)
    source_path = Path(args.source_manifest)
    content = _load(content_path)
    _load(source_path)
    if not str(content.get("service_timing_policy_id") or ""):
        raise SystemExit(
            "content manifest has no service-timing policy binding"
        )
    if (
        content.get("opportunity_collection_authorized") is not True
        or content.get("causal_oracle_collection_authorized") is not True
    ):
        raise SystemExit(
            "content manifest does not authorize development collection"
        )
    development = list(content.get("development") or ())
    calibration = list(content.get("calibration") or ())
    all_rows = development + calibration
    if len(all_rows) != len(
        {str(row["instance_content_hash"]) for row in all_rows}
    ):
        raise SystemExit("content manifest partitions overlap")
    structural_by_hash = {
        str(row["instance_content_hash"]): _structural_metadata(
            Path(str(row["instance_path"]))
        )
        for row in all_rows
    }

    fold_count = int(args.fold_count)
    groups: dict[tuple[str, ...], list[dict]] = defaultdict(list)
    for row in development:
        source_row = structural_by_hash[str(row["instance_content_hash"])]
        stratum = (
            str(source_row["instance_generator_domain"]),
            str(int(row["scale"])),
            str(source_row["time_window_mode"]),
            str(source_row["task_mode"]),
            str(source_row["hotspot_structure"]),
            str(source_row["fleet_ratio_bin"]),
            "unmeasured_v3_not_used_for_assignment",
        )
        groups[stratum].append(row)
    fold_sizes = [0] * fold_count
    stratum_fold_sizes = {
        stratum: [0] * fold_count for stratum in groups
    }
    assigned = []
    for stratum in sorted(groups, key=lambda key: (-len(groups[key]), key)):
        for row in sorted(
            groups[stratum],
            key=lambda value: (
                _bucket(
                    str(value["instance_content_hash"]),
                    "p0v3_branch_fold",
                ),
                str(value["instance_content_hash"]),
            ),
        ):
            fold = min(
                range(fold_count),
                key=lambda candidate: (
                    stratum_fold_sizes[stratum][candidate],
                    fold_sizes[candidate],
                    candidate,
                ),
            )
            stratum_fold_sizes[stratum][fold] += 1
            fold_sizes[fold] += 1
            source_row = structural_by_hash[
                str(row["instance_content_hash"])
            ]
            assigned.append(
                {
                    **row,
                    "partition": "development",
                    "fold": fold,
                    "instance_generator_domain": source_row[
                        "instance_generator_domain"
                    ],
                    "time_window_mode": source_row[
                        "time_window_mode"
                    ],
                    "task_mode": source_row["task_mode"],
                    "hotspot_structure": source_row[
                        "hotspot_structure"
                    ],
                    "fleet_ratio_bin": source_row[
                        "fleet_ratio_bin"
                    ],
                    "p0_difficulty_bin": (
                        "unmeasured_v3_not_used_for_assignment"
                    ),
                }
            )
    calibration_rows = []
    for row in calibration:
        source_row = structural_by_hash[str(row["instance_content_hash"])]
        calibration_rows.append(
            {
                **row,
                "partition": "calibration",
                "fold": None,
                "instance_generator_domain": source_row[
                    "instance_generator_domain"
                ],
                "time_window_mode": source_row["time_window_mode"],
                "task_mode": source_row["task_mode"],
                "hotspot_structure": source_row[
                    "hotspot_structure"
                ],
                "fleet_ratio_bin": source_row["fleet_ratio_bin"],
                "p0_difficulty_bin": (
                    "unmeasured_v3_not_used_for_assignment"
                ),
            }
        )
    scale_partition_counts = {}
    for partition, rows in (
        ("development", assigned),
        ("calibration", calibration_rows),
    ):
        for scale in sorted({int(row["scale"]) for row in rows}):
            scale_partition_counts[
                f"{partition}:scale{scale}"
            ] = sum(int(row["scale"]) == scale for row in rows)
    expected_partition_counts = {}
    for partition, rows in (
        ("development", development),
        ("calibration", calibration),
    ):
        for scale in sorted({int(row["scale"]) for row in rows}):
            expected_partition_counts[
                f"{partition}:scale{scale}"
            ] = sum(int(row["scale"]) == scale for row in rows)
    fold_balance_ok = bool(
        fold_sizes
        and max(fold_sizes) - min(fold_sizes) <= 1
    )
    generator_domain_partition_counts = {}
    for partition, rows in (
        ("development", assigned),
        ("calibration", calibration_rows),
    ):
        for domain in sorted(
            {
                str(row["instance_generator_domain"])
                for row in rows
            }
        ):
            generator_domain_partition_counts[
                f"{partition}:{domain}"
            ] = sum(
                str(row["instance_generator_domain"]) == domain
                for row in rows
            )
    audit = {
        "passed": bool(
            len(assigned) == len(development)
            and len(calibration_rows) == len(calibration)
            and fold_balance_ok
            and scale_partition_counts == expected_partition_counts
        ),
        "development_count": len(assigned),
        "calibration_count": len(calibration_rows),
        "fold_sizes": fold_sizes,
        "fold_balance_max_minus_min": (
            max(fold_sizes) - min(fold_sizes)
            if fold_sizes
            else None
        ),
        "scale_partition_counts": scale_partition_counts,
        "expected_scale_partition_counts": expected_partition_counts,
        "generator_domain_partition_counts": (
            generator_domain_partition_counts
        ),
        "label_fields_used_for_assignment": [],
        "protected_test_content_read": False,
    }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "service_timing_policy_id": content.get(
            "service_timing_policy_id"
        ),
        "fold_count": fold_count,
        "assignment_key": "instance_content_hash",
        "assignment_policy": (
            "content_hash_structural_strata_balanced_no_branch_labels.v1"
        ),
        "stratification_fields": [
            "instance_generator_domain",
            "scale",
            "time_window_mode",
            "task_mode",
            "hotspot_structure",
            "fleet_ratio_bin",
            "p0_difficulty_bin",
        ],
        "p0_difficulty_status": (
            "unmeasured_under_v3_and_constant_so_not_used_for_assignment"
        ),
        "source_content_manifest_hash": content.get("manifest_hash"),
        "authorized_collection_manifest_hashes": sorted(
            {
                str(value)
                for value in (
                    *(content.get(
                        "authorized_collection_manifest_hashes"
                    ) or ()),
                    content.get("manifest_hash"),
                    content.get("base_content_manifest_hash"),
                )
                if value
            }
        ),
        "authorized_collection_split_manifest_hashes": sorted(
            {
                str(value)
                for value in content.get(
                    "authorized_collection_split_manifest_hashes"
                )
                or ()
                if value
            }
        ),
        "source_content_manifest_sha256": hashlib.sha256(
            content_path.read_bytes()
        ).hexdigest(),
        "source_structural_manifest_sha256": hashlib.sha256(
            source_path.read_bytes()
        ).hexdigest(),
        "development": sorted(
            assigned,
            key=lambda row: str(row["instance_content_hash"]),
        ),
        "calibration": sorted(
            calibration_rows,
            key=lambda row: str(row["instance_content_hash"]),
        ),
        "protected_final_test": list(
            content.get("protected_final_test") or ()
        ),
        "audit": audit,
        "training_authorized": False,
        "opportunity_collection_authorized": True,
        "causal_oracle_collection_authorized": True,
        "calibration_read_authorized": False,
        "promotion_authorized": False,
    }
    manifest["manifest_hash"] = _manifest_hash(manifest)
    if not audit["passed"]:
        raise SystemExit(f"split audit failed: {audit}")
    destination = Path(args.output_manifest)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(destination)
    print(
        json.dumps(
            {
                "output_manifest": str(destination),
                "manifest_hash": manifest["manifest_hash"],
                "audit": audit,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
