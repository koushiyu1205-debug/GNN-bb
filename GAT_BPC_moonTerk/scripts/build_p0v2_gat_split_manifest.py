#!/usr/bin/env python3
"""Build and audit the immutable P0 V2 GAT split manifest from JSONL."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.guidance.splits import (
    InstanceSplitRecord,
    build_split_manifest,
    extend_split_manifest,
    save_split_manifest,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records-jsonl", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--fold-count", type=int, default=5)
    parser.add_argument(
        "--base-manifest",
        default="",
        help=(
            "Append post-HA scale50/100 rows while preserving every frozen "
            "partition/fold assignment in this base manifest."
        ),
    )
    parser.add_argument(
        "--protected-root",
        default="data/instances",
        help=(
            "Schema-check and register the frozen full80 plus existing "
            "scale50/100 shadow set. Use an empty value only for unit fixtures."
        ),
    )
    args = parser.parse_args()
    records = []
    for line in Path(args.records_jsonl).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = InstanceSplitRecord(**json.loads(line))
        if (
            record.source_role == "new_development"
            and record.p0_difficulty_bin == "pending_p0_measurement"
        ):
            raise SystemExit(
                "P0 difficulty is pending; run binding-V2 B0 and finalize "
                "development split records first"
            )
        records.append(record)
    protected_count = 0
    if args.base_manifest:
        if args.protected_root != "data/instances":
            raise SystemExit(
                "--protected-root is not used with --base-manifest"
            )
        base = json.loads(
            Path(args.base_manifest).read_text(encoding="utf-8")
        )
        manifest = extend_split_manifest(
            base,
            records,
            calibration_per_scale={50: 8, 100: 8},
        )
        protected_count = len(
            manifest.get("protected_final_test", ())
        )
    elif args.protected_root:
        protected_root = Path(args.protected_root)
        records.extend(_protected_records(protected_root))
        protected_count = 120
        manifest = build_split_manifest(
            records, fold_count=args.fold_count
        )
    else:
        manifest = build_split_manifest(
            records, fold_count=args.fold_count
        )
    if not manifest["audit"]["passed"]:
        raise SystemExit("split audit failed")
    save_split_manifest(manifest, args.output)
    print(
        json.dumps(
            {
                "output": str(Path(args.output).resolve()),
                "manifest_hash": manifest["manifest_hash"],
                "audit": manifest["audit"],
                "protected_record_count": protected_count,
            },
            ensure_ascii=False,
        )
    )
    return 0


def _protected_records(root: Path) -> list[InstanceSplitRecord]:
    records = []
    counts = {}
    for scale in (5, 10, 20, 30, 50, 100):
        paths = sorted(
            (root / f"lunar_ice_sp50_{scale:03d}").glob(
                "instance_*_logical_graph.json"
            )
        )
        counts[scale] = len(paths)
        if len(paths) != 20:
            raise SystemExit(
                f"expected 20 protected scale{scale} instances, got {len(paths)}"
            )
        for path in paths:
            data = load_lunar_ice_data(
                json.loads(path.read_text(encoding="utf-8"))
            )
            records.append(
                InstanceSplitRecord(
                    instance_content_hash=data.instance_content_hash,
                    instance_id=data.instance_id,
                    scale=scale,
                    source_role=(
                        "full80_exact_test"
                        if scale <= 30
                        else "existing_large_shadow_test"
                    ),
                    time_window_mode="protected_not_inspected",
                    task_mode="protected_not_inspected",
                    hotspot_structure="protected_not_inspected",
                    fleet_ratio_bin="protected_not_inspected",
                    p0_difficulty_bin="protected_not_measured",
                )
            )
    if len(records) != 120:
        raise SystemExit(f"expected protected full120, got {len(records)}")
    return records


if __name__ == "__main__":
    raise SystemExit(main())
