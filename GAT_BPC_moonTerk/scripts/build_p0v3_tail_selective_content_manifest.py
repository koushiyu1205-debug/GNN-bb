#!/usr/bin/env python3
"""Freeze a fresh label-blind real-map pool for tail-selective validation."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.domain.scenario import SERVICE_TIMING_POLICY_ID  # noqa: E402
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402


SCHEMA_VERSION = (
    "lunar_ice_bpc.tail_selective_content_manifest.v1"
)
REAL_MAP_GENERATOR = "real_lunar_south_pole_sp50_benchmark_v1"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _payload_hash(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def _all_partition_hashes(manifest: dict) -> set[str]:
    return {
        str(row["instance_content_hash"])
        for partition in (
            "development",
            "calibration",
            "protected_final_test",
        )
        for row in manifest.get(partition) or ()
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generation-manifest", required=True)
    parser.add_argument("--prior-content-manifest", required=True)
    parser.add_argument("--protected-manifest", required=True)
    parser.add_argument("--output-manifest", required=True)
    parser.add_argument("--scales", default="20,30")
    parser.add_argument("--development-per-scale", type=int, default=3)
    parser.add_argument("--calibration-per-scale", type=int, default=1)
    parser.add_argument(
        "--tail-trigger-policy-id",
        default="first_exact_legal_top3_elapsed_per_task_ge_1s.v1",
    )
    parser.add_argument(
        "--exclude-prior-overlaps",
        action="store_true",
        help=(
            "Exclude, rather than fail on, generation rows already present "
            "in a prior, calibration, or protected partition. Exclusions are "
            "recorded by content hash before any tail labels are read."
        ),
    )
    args = parser.parse_args()
    scales = tuple(
        int(piece.strip())
        for piece in str(args.scales).split(",")
        if piece.strip()
    )
    if not scales or len(set(scales)) != len(scales):
        raise SystemExit("tail pilot scales must be unique and non-empty")
    if any(scale not in (5, 10, 20, 30, 50, 100) for scale in scales):
        raise SystemExit("tail pilot contains an unsupported scale")

    generation_path = Path(args.generation_manifest).resolve()
    prior_path = Path(args.prior_content_manifest).resolve()
    protected_path = Path(args.protected_manifest).resolve()
    generation = _load(generation_path)
    prior = _load(prior_path)
    protected = _load(protected_path)
    if str(generation.get("generator") or "") != REAL_MAP_GENERATOR:
        raise SystemExit("tail pilot generator ID mismatch")
    forbidden_hashes = (
        _all_partition_hashes(prior) | _all_partition_hashes(protected)
    )
    rows_by_scale: dict[int, list[dict]] = {}
    collisions = []
    for source in generation.get("instances") or ():
        if str(source.get("status") or "") != "accepted":
            continue
        instance_path = (ROOT / str(source["path"])).resolve()
        data = load_lunar_ice_data(_load(instance_path))
        if data.service_timing_policy_id != SERVICE_TIMING_POLICY_ID:
            raise SystemExit("tail pilot service timing policy mismatch")
        row = {
            "scale": int(data.scale),
            "instance_id": data.instance_id,
            "instance_path": str(instance_path),
            "instance_content_hash": data.instance_content_hash,
            "raw_file_sha256": _file_sha256(instance_path),
            "seed": int(source["seed"]),
            "generator_attempt_index": int(source["attempt_index"]),
            "service_timing_policy_id": data.service_timing_policy_id,
            "instance_generator_domain": REAL_MAP_GENERATOR,
            "partition_frozen_before_tail_labels": True,
            "tail_trigger_policy_frozen_before_partition": True,
        }
        if data.instance_content_hash in forbidden_hashes:
            collisions.append(data.instance_content_hash)
            if args.exclude_prior_overlaps:
                continue
        rows_by_scale.setdefault(int(data.scale), []).append(row)
    development = []
    calibration = []
    for scale in scales:
        rows = sorted(
            rows_by_scale.get(scale) or (),
            key=lambda row: str(row["instance_content_hash"]),
        )
        development_count = int(args.development_per_scale)
        calibration_count = int(args.calibration_per_scale)
        if len(rows) != development_count + calibration_count:
            raise SystemExit(
                f"tail pilot scale{scale} accepted {len(rows)} rows; "
                f"expected {development_count + calibration_count}"
            )
        development.extend(
            {
                **row,
                "pool_role": "TAIL_SELECTIVE_FRESH_VALIDATION_DEVELOPMENT",
                "scale_hash_order_index": index,
            }
            for index, row in enumerate(rows[:development_count])
        )
        calibration.extend(
            {
                **row,
                "pool_role": "LOCKED_TAIL_SELECTIVE_CALIBRATION",
                "scale_hash_order_index": index,
            }
            for index, row in enumerate(rows[development_count:])
        )
    development_hashes = {
        str(row["instance_content_hash"]) for row in development
    }
    calibration_hashes = {
        str(row["instance_content_hash"]) for row in calibration
    }
    unresolved_collisions = (
        [] if args.exclude_prior_overlaps else collisions
    )
    passed = bool(
        not unresolved_collisions
        and not (development_hashes & calibration_hashes)
        and len(development_hashes) == len(development)
        and len(calibration_hashes) == len(calibration)
    )
    payload = {
        "schema_version": SCHEMA_VERSION,
        "service_timing_policy_id": SERVICE_TIMING_POLICY_ID,
        "tail_trigger_policy_id": (
            str(args.tail_trigger_policy_id)
        ),
        "assignment_key": "instance_content_hash",
        "assignment_policy": (
            "fresh_real_map_content_hash_ascending_label_blind.v2"
        ),
        "generation_manifest_path": str(generation_path),
        "generation_manifest_sha256": _file_sha256(generation_path),
        "prior_content_manifest_path": str(prior_path),
        "prior_content_manifest_sha256": _file_sha256(prior_path),
        "protected_manifest_path": str(protected_path),
        "protected_manifest_sha256": _file_sha256(protected_path),
        "development": development,
        "calibration": calibration,
        "protected_final_test": list(
            protected.get("protected_final_test") or ()
        ),
        "opportunity_collection_authorized": True,
        "causal_oracle_collection_authorized": True,
        "training_authorized": False,
        "calibration_read_authorized": False,
        "promotion_authorized": False,
        "audit": {
            "passed": passed,
            "collisions": sorted(unresolved_collisions),
            "excluded_prior_or_protected_content_hashes": (
                sorted(collisions)
                if args.exclude_prior_overlaps
                else []
            ),
            "prior_overlap_policy": (
                "exclude_before_partition"
                if args.exclude_prior_overlaps
                else "fail_closed"
            ),
            "prior_or_protected_content_hash_count": len(
                forbidden_hashes
            ),
            "calibration_content_read": False,
            "protected_test_content_read": False,
            "tail_labels_used_for_assignment": [],
            "development_scale_counts": {
                str(scale): sum(
                    int(row["scale"]) == scale for row in development
                )
                for scale in scales
            },
            "calibration_scale_counts": {
                str(scale): sum(
                    int(row["scale"]) == scale for row in calibration
                )
                for scale in scales
            },
        },
    }
    payload["manifest_hash"] = _payload_hash(payload)
    output = Path(args.output_manifest)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(output)
    print(
        json.dumps(
            {
                "output_manifest": str(output),
                "manifest_hash": payload["manifest_hash"],
                "audit": payload["audit"],
            },
            sort_keys=True,
        )
    )
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
