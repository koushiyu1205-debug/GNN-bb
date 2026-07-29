#!/usr/bin/env python3
"""Freeze a fresh V3 branch-development candidate pool by content hash."""

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


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_json(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _protected_hashes(path: Path) -> set[str]:
    manifest = _load_json(path)
    rows = [
        *manifest.get("development", ()),
        *manifest.get("calibration", ()),
        *manifest.get("protected_final_test", ()),
    ]
    return {
        str(row["instance_content_hash"])
        for row in rows
        if row.get("instance_content_hash")
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-manifest",
        default="data/gat_v3_branch_candidate_pool_20260725_manifest.json",
    )
    parser.add_argument(
        "--protected-manifest",
        default=(
            "data/gat_p0v2/"
            "p0_no_task_wait_v3_gat_split_rebind_manifest.json"
        ),
    )
    parser.add_argument(
        "--output",
        default=(
            "data/gat_v3_branch_candidate_pool_20260725_"
            "content_manifest.json"
        ),
    )
    parser.add_argument("--development-per-scale", type=int, default=48)
    parser.add_argument("--calibration-per-scale", type=int, default=12)
    parser.add_argument(
        "--initial-random-census-per-scale",
        type=int,
        default=12,
    )
    args = parser.parse_args()

    source_path = (ROOT / args.source_manifest).resolve()
    protected_path = (ROOT / args.protected_manifest).resolve()
    output_path = (ROOT / args.output).resolve()
    source = _load_json(source_path)
    if source.get("status") != "complete":
        raise SystemExit("source candidate manifest is incomplete")
    if (
        str(source.get("service_timing_policy_id") or "")
        != SERVICE_TIMING_POLICY_ID
    ):
        raise SystemExit("source candidate manifest timing-policy mismatch")

    protected = _protected_hashes(protected_path)
    rows_by_scale: dict[int, list[dict]] = {}
    seen_content_hashes: set[str] = set()
    seen_instance_ids: set[str] = set()
    collisions: list[dict] = []
    for source_row in source.get("instances", ()):
        instance_path = (ROOT / str(source_row["path"])).resolve()
        raw = _load_json(instance_path)
        data = load_lunar_ice_data(raw)
        if data.service_timing_policy_id != SERVICE_TIMING_POLICY_ID:
            raise SystemExit(
                f"instance timing-policy mismatch: {instance_path}"
            )
        content_hash = data.instance_content_hash
        if content_hash in seen_content_hashes:
            collisions.append(
                {
                    "kind": "candidate_content_hash_duplicate",
                    "value": content_hash,
                    "path": str(instance_path),
                }
            )
        if data.instance_id in seen_instance_ids:
            collisions.append(
                {
                    "kind": "candidate_instance_id_duplicate",
                    "value": data.instance_id,
                    "path": str(instance_path),
                }
            )
        if content_hash in protected:
            collisions.append(
                {
                    "kind": "protected_content_hash_overlap",
                    "value": content_hash,
                    "path": str(instance_path),
                }
            )
        seen_content_hashes.add(content_hash)
        seen_instance_ids.add(data.instance_id)
        rows_by_scale.setdefault(int(data.scale), []).append(
            {
                "scale": int(data.scale),
                "instance_id": data.instance_id,
                "instance_path": str(instance_path),
                "instance_content_hash": content_hash,
                "raw_file_sha256": _sha256_file(instance_path),
                "seed": int(source_row["seed"]),
                "generator_attempt_index": int(
                    source_row["attempt_index"]
                ),
                "service_timing_policy_id": data.service_timing_policy_id,
                "generator_schema_accepted": True,
                "v3_solver_reaccepted": False,
                "v3_exact_actionability_status": "NOT_RUN",
            }
        )

    development: list[dict] = []
    calibration: list[dict] = []
    census_count = max(0, int(args.initial_random_census_per_scale))
    for scale, rows in sorted(rows_by_scale.items()):
        rows.sort(key=lambda row: str(row["instance_content_hash"]))
        development_count = int(args.development_per_scale)
        calibration_count = int(args.calibration_per_scale)
        if len(rows) != development_count + calibration_count:
            raise SystemExit(
                f"scale{scale} has {len(rows)} rows; expected "
                f"{development_count + calibration_count}"
            )
        for index, row in enumerate(rows[:development_count]):
            development.append(
                {
                    **row,
                    "pool_role": (
                        "UNBIASED_OPPORTUNITY_CENSUS"
                        if index < census_count
                        else "BOUNDED_ACTIONABILITY_DISCOVERY"
                    ),
                    "scale_hash_order_index": index,
                }
            )
        for index, row in enumerate(rows[development_count:]):
            calibration.append(
                {
                    **row,
                    "pool_role": "LOCKED_CALIBRATION",
                    "scale_hash_order_index": index,
                }
            )

    payload = {
        "schema_version": (
            "lunar_ice_bpc.no_task_wait_v3_branch_candidate_pool.v1"
        ),
        "service_timing_policy_id": SERVICE_TIMING_POLICY_ID,
        "source_manifest_path": str(source_path),
        "source_manifest_sha256": _sha256_file(source_path),
        "protected_manifest_path": str(protected_path),
        "protected_manifest_sha256": _sha256_file(protected_path),
        "assignment_key": "instance_content_hash_ascending_within_scale",
        "development_per_scale": int(args.development_per_scale),
        "calibration_per_scale": int(args.calibration_per_scale),
        "initial_random_census_per_scale": census_count,
        "development": development,
        "calibration": calibration,
        "opportunity_collection_authorized": True,
        "causal_oracle_collection_authorized": True,
        "training_authorized": False,
        "calibration_read_authorized": False,
        "promotion_authorized": False,
        "audit": {
            "candidate_count": len(seen_content_hashes),
            "scale_counts": {
                str(scale): len(rows)
                for scale, rows in sorted(rows_by_scale.items())
            },
            "protected_hash_count": len(protected),
            "collision_count": len(collisions),
            "collisions": collisions,
            "passed": not collisions,
        },
    }
    without_hash = dict(payload)
    payload["manifest_hash"] = _sha256_json(without_hash)
    _write_json(output_path, payload)
    print(
        json.dumps(
            {
                "output": str(output_path),
                "manifest_hash": payload["manifest_hash"],
                "development_count": len(development),
                "calibration_count": len(calibration),
                "audit": payload["audit"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if payload["audit"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
