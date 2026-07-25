"""Leakage-resistant cross-scale split manifests."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


SPLIT_MANIFEST_SCHEMA_V1 = "lunar_ice_bpc.gat_split_manifest.v1"
TRAINABLE_SOURCE_ROLES = frozenset({"new_development"})
PROTECTED_SOURCE_ROLES = frozenset(
    {"full80_exact_test", "existing_large_shadow_test"}
)


@dataclass(frozen=True)
class InstanceSplitRecord:
    instance_content_hash: str
    instance_id: str
    scale: int
    source_role: str
    time_window_mode: str
    task_mode: str
    hotspot_structure: str
    fleet_ratio_bin: str
    p0_difficulty_bin: str

    @property
    def stratum(self) -> tuple[str, ...]:
        return (
            str(self.scale),
            self.time_window_mode,
            self.task_mode,
            self.hotspot_structure,
            self.fleet_ratio_bin,
            self.p0_difficulty_bin,
        )


def build_split_manifest(
    records: Iterable[InstanceSplitRecord],
    *,
    calibration_per_scale: dict[int, int] | None = None,
    fold_count: int = 5,
) -> dict[str, Any]:
    """Assign trainable records to grouped CV/calibration by content hash.

    Protected rows are recorded only in the audit section and can never enter
    a fold, normalization fit, calibration, or model-selection partition.
    """

    rows = tuple(records)
    if fold_count < 2:
        raise ValueError("fold_count must be at least 2")
    hashes = [row.instance_content_hash for row in rows]
    if len(hashes) != len(set(hashes)):
        raise ValueError("duplicate content hash in split input")
    calibration_targets = calibration_per_scale or {
        5: 12,
        10: 12,
        20: 12,
        30: 12,
        50: 8,
        100: 8,
    }
    development: list[InstanceSplitRecord] = []
    calibration: list[InstanceSplitRecord] = []
    protected: list[InstanceSplitRecord] = []
    by_scale: dict[int, list[InstanceSplitRecord]] = defaultdict(list)
    for row in rows:
        if row.source_role in PROTECTED_SOURCE_ROLES:
            protected.append(row)
        elif row.source_role in TRAINABLE_SOURCE_ROLES:
            by_scale[int(row.scale)].append(row)
        else:
            raise ValueError(f"unsupported source_role {row.source_role!r}")

    for scale, scale_rows in sorted(by_scale.items()):
        ordered = sorted(
            scale_rows,
            key=lambda row: (
                row.stratum,
                _bucket_value(row.instance_content_hash, "calibration"),
                row.instance_content_hash,
            ),
        )
        target = min(len(ordered), max(0, int(calibration_targets.get(scale, 0))))
        # Round-robin across strata keeps calibration from becoming a single
        # easy/hard structural pocket.
        grouped: dict[tuple[str, ...], list[InstanceSplitRecord]] = defaultdict(list)
        for row in ordered:
            grouped[row.stratum].append(row)
        chosen: list[InstanceSplitRecord] = []
        positions = {key: 0 for key in grouped}
        group_keys = sorted(
            grouped,
            key=lambda key: (
                _bucket_value("|".join(key), "calibration_stratum"),
                key,
            ),
        )
        while len(chosen) < target:
            progressed = False
            for key in group_keys:
                index = positions[key]
                if index < len(grouped[key]) and len(chosen) < target:
                    chosen.append(grouped[key][index])
                    positions[key] += 1
                    progressed = True
            if not progressed:
                break
        chosen_hashes = {row.instance_content_hash for row in chosen}
        calibration.extend(chosen)
        development.extend(
            row
            for row in ordered
            if row.instance_content_hash not in chosen_hashes
        )

    fold_rows = []
    fold_sizes = [0] * fold_count
    development_by_stratum: dict[
        tuple[str, ...], list[InstanceSplitRecord]
    ] = defaultdict(list)
    for row in development:
        development_by_stratum[row.stratum].append(row)
    stratum_fold_counts: dict[tuple[str, ...], list[int]] = {
        key: [0] * fold_count for key in development_by_stratum
    }
    # Allocate the largest strata first. Within each stratum, content-hash
    # ordering is immutable; the greedy key keeps both per-stratum and global
    # fold counts within one whenever the cardinalities permit it.
    ordered_strata = sorted(
        development_by_stratum,
        key=lambda key: (
            -len(development_by_stratum[key]),
            _bucket_value("|".join(key), "grouped_cv_stratum"),
            key,
        ),
    )
    for stratum in ordered_strata:
        rows_in_stratum = sorted(
            development_by_stratum[stratum],
            key=lambda row: (
                _bucket_value(row.instance_content_hash, "grouped_cv"),
                row.instance_content_hash,
            ),
        )
        tie_rotation = (
            _bucket_value("|".join(stratum), "grouped_cv_tie") % fold_count
        )
        for row in rows_in_stratum:
            fold = min(
                range(fold_count),
                key=lambda candidate: (
                    stratum_fold_counts[stratum][candidate],
                    fold_sizes[candidate],
                    (candidate - tie_rotation) % fold_count,
                ),
            )
            stratum_fold_counts[stratum][fold] += 1
            fold_sizes[fold] += 1
            fold_rows.append(
                _row_payload(row, partition="development", fold=fold)
            )
    calibration_rows = [
        _row_payload(row, partition="calibration", fold=None)
        for row in calibration
    ]
    protected_rows = [
        _row_payload(row, partition="protected_final_test", fold=None)
        for row in protected
    ]
    manifest = {
        "schema_version": SPLIT_MANIFEST_SCHEMA_V1,
        "fold_count": fold_count,
        "assignment_key": "instance_content_hash",
        "stratification_fields": [
            "scale",
            "time_window_mode",
            "task_mode",
            "hotspot_structure",
            "fleet_ratio_bin",
            "p0_difficulty_bin",
        ],
        "normalization_fit_scope": "training_rows_of_each_fold_only",
        "fold_assignment": (
            "content_hash_grouped_stratum_balanced_greedy_v1"
        ),
        "development": sorted(
            fold_rows, key=lambda row: row["instance_content_hash"]
        ),
        "calibration": sorted(
            calibration_rows, key=lambda row: row["instance_content_hash"]
        ),
        "protected_final_test": sorted(
            protected_rows, key=lambda row: row["instance_content_hash"]
        ),
    }
    manifest["audit"] = audit_split_manifest(manifest)
    canonical = json.dumps(
        manifest,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    manifest["manifest_hash"] = hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()
    return manifest


def extend_split_manifest(
    base_manifest: dict[str, Any],
    new_records: Iterable[InstanceSplitRecord],
    *,
    calibration_per_scale: dict[int, int] | None = None,
) -> dict[str, Any]:
    """Append new scales without changing any frozen base assignment."""

    if not bool((base_manifest.get("audit") or {}).get("passed")):
        raise ValueError("base split manifest audit did not pass")
    fold_count = int(base_manifest.get("fold_count") or 0)
    if fold_count < 2:
        raise ValueError("base split manifest has invalid fold count")
    rows = tuple(new_records)
    if not rows:
        raise ValueError("split extension requires new records")
    if any(row.source_role != "new_development" for row in rows):
        raise ValueError("split extension accepts new_development rows only")
    base_hashes = {
        str(row["instance_content_hash"])
        for partition in (
            "development",
            "calibration",
            "protected_final_test",
        )
        for row in base_manifest.get(partition, ())
    }
    overlap = sorted(
        base_hashes.intersection(
            row.instance_content_hash for row in rows
        )
    )
    if overlap:
        raise ValueError(
            "split extension overlaps frozen base content: "
            + ",".join(overlap[:10])
        )
    addition = build_split_manifest(
        rows,
        calibration_per_scale=calibration_per_scale,
        fold_count=fold_count,
    )
    manifest = {
        key: value
        for key, value in base_manifest.items()
        if key
        not in {
            "development",
            "calibration",
            "protected_final_test",
            "audit",
            "manifest_hash",
        }
    }
    manifest.update(
        {
            "schema_version": SPLIT_MANIFEST_SCHEMA_V1,
            "base_manifest_hash": str(
                base_manifest.get("manifest_hash") or ""
            ),
            "extension_policy": (
                "append_new_scales_preserve_all_base_assignments_v1"
            ),
            "extension_scales": sorted({int(row.scale) for row in rows}),
            "development": sorted(
                [
                    *base_manifest.get("development", ()),
                    *addition.get("development", ()),
                ],
                key=lambda row: row["instance_content_hash"],
            ),
            "calibration": sorted(
                [
                    *base_manifest.get("calibration", ()),
                    *addition.get("calibration", ()),
                ],
                key=lambda row: row["instance_content_hash"],
            ),
            "protected_final_test": sorted(
                base_manifest.get("protected_final_test", ()),
                key=lambda row: row["instance_content_hash"],
            ),
        }
    )
    manifest["audit"] = audit_split_manifest(manifest)
    if not manifest["audit"]["passed"]:
        raise ValueError("extended split manifest audit failed")
    canonical = json.dumps(
        manifest,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    manifest["manifest_hash"] = hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()
    return manifest


def audit_split_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    partitions = (
        "development",
        "calibration",
        "protected_final_test",
    )
    hashes_by_partition = {
        name: {
            str(row["instance_content_hash"])
            for row in manifest.get(name, ())
        }
        for name in partitions
    }
    intersections = {}
    for left_index, left in enumerate(partitions):
        for right in partitions[left_index + 1 :]:
            overlap = sorted(
                hashes_by_partition[left].intersection(
                    hashes_by_partition[right]
                )
            )
            intersections[f"{left}__{right}"] = overlap
    protected_leaks = [
        row["instance_content_hash"]
        for name in ("development", "calibration")
        for row in manifest.get(name, ())
        if row.get("source_role") in PROTECTED_SOURCE_ROLES
    ]
    counts = Counter(
        (str(row["partition"]), int(row["scale"]))
        for name in partitions
        for row in manifest.get(name, ())
    )
    passed = not any(intersections.values()) and not protected_leaks
    fold_counts = Counter(
        int(row["fold"])
        for row in manifest.get("development", ())
        if row.get("fold") is not None
    )
    stratum_folds: dict[tuple[str, ...], Counter[int]] = defaultdict(Counter)
    for row in manifest.get("development", ()):
        stratum = tuple(
            str(row[field])
            for field in (
                "scale",
                "time_window_mode",
                "task_mode",
                "hotspot_structure",
                "fleet_ratio_bin",
                "p0_difficulty_bin",
            )
        )
        stratum_folds[stratum][int(row["fold"])] += 1
    stratum_max_imbalance = max(
        (
            max(
                counts_by_fold.get(fold, 0)
                for fold in range(int(manifest.get("fold_count") or 0))
            )
            - min(
                counts_by_fold.get(fold, 0)
                for fold in range(int(manifest.get("fold_count") or 0))
            )
            for counts_by_fold in stratum_folds.values()
        ),
        default=0,
    )
    return {
        "passed": passed,
        "zero_content_hash_overlap": not any(intersections.values()),
        "partition_intersections": intersections,
        "protected_full120_training_or_calibration_count": len(protected_leaks),
        "protected_full120_not_used": not protected_leaks,
        "development_fold_counts": {
            str(fold): fold_counts.get(fold, 0)
            for fold in range(int(manifest.get("fold_count") or 0))
        },
        "development_stratum_max_fold_imbalance": stratum_max_imbalance,
        "counts": {
            f"{partition}:scale{scale}": count
            for (partition, scale), count in sorted(counts.items())
        },
    }


def save_split_manifest(manifest: dict[str, Any], path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _bucket_value(content_hash: str, salt: str) -> int:
    digest = hashlib.sha256(
        f"{salt}:{content_hash}".encode("utf-8")
    ).hexdigest()
    return int(digest[:16], 16)


def _row_payload(
    row: InstanceSplitRecord, *, partition: str, fold: int | None
) -> dict[str, Any]:
    return {
        "instance_content_hash": row.instance_content_hash,
        "instance_id": row.instance_id,
        "scale": int(row.scale),
        "source_role": row.source_role,
        "partition": partition,
        "fold": fold,
        "time_window_mode": row.time_window_mode,
        "task_mode": row.task_mode,
        "hotspot_structure": row.hotspot_structure,
        "fleet_ratio_bin": row.fleet_ratio_bin,
        "p0_difficulty_bin": row.p0_difficulty_bin,
    }
