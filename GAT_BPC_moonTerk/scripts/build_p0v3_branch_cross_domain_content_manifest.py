#!/usr/bin/env python3
"""Freeze a tiny fresh real-map pilot beside the synthetic branch pool."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.domain.scenario import (  # noqa: E402
    SERVICE_TIMING_POLICY_ID,
)
from lunar_ice_bpc.exact.core.data import (  # noqa: E402
    load_lunar_ice_data,
)


SCHEMA_VERSION = (
    "lunar_ice_bpc.branch_cross_domain_content_manifest.v1"
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


def _payload_sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _protected_hashes(manifest: dict) -> set[str]:
    return {
        str(row["instance_content_hash"])
        for partition in (
            "development",
            "calibration",
            "protected_final_test",
        )
        for row in manifest.get(partition) or ()
    }


def _real_rows(generation: dict) -> dict[int, list[dict]]:
    if str(generation.get("generator") or "") != REAL_MAP_GENERATOR:
        raise SystemExit("real-map generation manifest ID mismatch")
    rows_by_scale: dict[int, list[dict]] = {}
    for source in generation.get("instances") or ():
        if str(source.get("status") or "") != "accepted":
            continue
        path = (ROOT / str(source["path"])).resolve()
        data = load_lunar_ice_data(_load(path))
        if data.service_timing_policy_id != SERVICE_TIMING_POLICY_ID:
            raise SystemExit(f"real-map timing policy mismatch: {path}")
        rows_by_scale.setdefault(int(data.scale), []).append(
            {
                "scale": int(data.scale),
                "instance_id": data.instance_id,
                "instance_path": str(path),
                "instance_content_hash": data.instance_content_hash,
                "raw_file_sha256": _file_sha256(path),
                "seed": int(source["seed"]),
                "generator_attempt_index": int(
                    source["attempt_index"]
                ),
                "service_timing_policy_id": (
                    data.service_timing_policy_id
                ),
                "generator_schema_accepted": True,
                "v3_solver_reaccepted": False,
                "v3_exact_actionability_status": "NOT_RUN",
                "instance_generator_domain": REAL_MAP_GENERATOR,
            }
        )
    return rows_by_scale


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--synthetic-content-manifest", required=True)
    parser.add_argument("--real-generation-manifest", required=True)
    parser.add_argument("--protected-manifest", required=True)
    parser.add_argument("--output-manifest", required=True)
    parser.add_argument("--prior-cross-domain-content-manifest")
    parser.add_argument("--prior-grouped-split-manifest")
    parser.add_argument(
        "--real-development-per-scale",
        type=int,
        default=3,
    )
    parser.add_argument(
        "--real-calibration-per-scale",
        type=int,
        default=1,
    )
    args = parser.parse_args()

    synthetic_path = Path(args.synthetic_content_manifest).resolve()
    real_path = Path(args.real_generation_manifest).resolve()
    protected_path = Path(args.protected_manifest).resolve()
    synthetic = _load(synthetic_path)
    real_generation = _load(real_path)
    protected = _load(protected_path)
    prior_content_path = (
        None
        if not args.prior_cross_domain_content_manifest
        else Path(args.prior_cross_domain_content_manifest).resolve()
    )
    prior_content = (
        None if prior_content_path is None else _load(prior_content_path)
    )
    prior_split_path = (
        None
        if not args.prior_grouped_split_manifest
        else Path(args.prior_grouped_split_manifest).resolve()
    )
    prior_split = (
        None if prior_split_path is None else _load(prior_split_path)
    )
    if (prior_content is None) != (prior_split is None):
        raise SystemExit(
            "prior content and grouped split must be supplied together"
        )
    if prior_content is not None and (
        str(prior_content.get("schema_version") or "")
        != SCHEMA_VERSION
        or str(prior_split.get("source_content_manifest_hash") or "")
        != str(prior_content.get("manifest_hash") or "")
        or prior_content.get("calibration_read_authorized") is not False
        or prior_split.get("calibration_read_authorized") is not False
    ):
        raise SystemExit("prior frozen real-map partition binding mismatch")
    protected_hashes = _protected_hashes(protected)
    real_by_scale = _real_rows(real_generation)
    required_scales = (20, 30)
    real_development: list[dict] = []
    real_calibration: list[dict] = []
    collisions = []
    seen = {
        str(row["instance_content_hash"])
        for partition in ("development", "calibration")
        for row in synthetic.get(partition) or ()
    }
    for scale in required_scales:
        rows = sorted(
            real_by_scale.get(scale) or (),
            key=lambda row: str(row["instance_content_hash"]),
        )
        development_count = int(args.real_development_per_scale)
        calibration_count = int(args.real_calibration_per_scale)
        expected = development_count + calibration_count
        if len(rows) != expected:
            raise SystemExit(
                f"real-map scale{scale} has {len(rows)} accepted rows; "
                f"expected {expected}"
            )
        prior_development = (
            []
            if prior_content is None
            else [
                row
                for row in prior_content.get("development") or ()
                if (
                    str(row.get("instance_generator_domain") or "")
                    == REAL_MAP_GENERATOR
                    and int(row["scale"]) == scale
                )
            ]
        )
        prior_calibration = (
            []
            if prior_content is None
            else [
                row
                for row in prior_content.get("calibration") or ()
                if (
                    str(row.get("instance_generator_domain") or "")
                    == REAL_MAP_GENERATOR
                    and int(row["scale"]) == scale
                )
            ]
        )
        if (
            len(prior_development) > development_count
            or len(prior_calibration) > calibration_count
        ):
            raise SystemExit(
                f"requested final partition shrinks frozen scale{scale}"
            )
        prior_hashes = {
            str(row["instance_content_hash"])
            for row in prior_development + prior_calibration
        }
        generated_hashes = {
            str(row["instance_content_hash"]) for row in rows
        }
        if not prior_hashes.issubset(generated_hashes):
            raise SystemExit(
                f"generation manifest lost frozen scale{scale} instances"
            )
        for row in rows:
            content_hash = str(row["instance_content_hash"])
            if content_hash in seen:
                collisions.append(
                    {
                        "kind": "cross_domain_content_overlap",
                        "value": content_hash,
                    }
                )
            if content_hash in protected_hashes:
                collisions.append(
                    {
                        "kind": "protected_content_overlap",
                        "value": content_hash,
                    }
                )
            seen.add(content_hash)
        unassigned = [
            row
            for row in rows
            if str(row["instance_content_hash"]) not in prior_hashes
        ]
        additional_development_count = (
            development_count - len(prior_development)
        )
        additional_calibration_count = (
            calibration_count - len(prior_calibration)
        )
        if len(unassigned) != (
            additional_development_count
            + additional_calibration_count
        ):
            raise SystemExit(
                f"scale{scale} unassigned real-map count mismatch"
            )
        real_development.extend(prior_development)
        real_calibration.extend(prior_calibration)
        for index, row in enumerate(
            unassigned[:additional_development_count],
            start=len(prior_development),
        ):
            real_development.append(
                {
                    **row,
                    "pool_role": (
                        "REAL_MAP_HEADROOM_BOUNDED_EXPANSION_DEVELOPMENT"
                        if prior_content is not None
                        else "REAL_MAP_HEADROOM_PILOT_DEVELOPMENT"
                    ),
                    "scale_hash_order_index": index,
                    "partition_frozen_before_branch_labels": True,
                }
            )
        for index, row in enumerate(
            unassigned[additional_development_count:],
            start=len(prior_calibration),
        ):
            real_calibration.append(
                {
                    **row,
                    "pool_role": (
                        "LOCKED_REAL_MAP_BOUNDED_EXPANSION_CALIBRATION"
                        if prior_content is not None
                        else "LOCKED_REAL_MAP_CALIBRATION"
                    ),
                    "scale_hash_order_index": index,
                    "partition_frozen_before_branch_labels": True,
                }
            )

    development = [
        *list(synthetic.get("development") or ()),
        *real_development,
    ]
    calibration = [
        *list(synthetic.get("calibration") or ()),
        *real_calibration,
    ]
    partition_hashes = {
        "development": {
            str(row["instance_content_hash"]) for row in development
        },
        "calibration": {
            str(row["instance_content_hash"]) for row in calibration
        },
        "protected_final_test": {
            str(row["instance_content_hash"])
            for row in protected.get("protected_final_test") or ()
        },
    }
    intersections = {
        "development__calibration": sorted(
            partition_hashes["development"]
            & partition_hashes["calibration"]
        ),
        "development__protected_final_test": sorted(
            partition_hashes["development"]
            & partition_hashes["protected_final_test"]
        ),
        "calibration__protected_final_test": sorted(
            partition_hashes["calibration"]
            & partition_hashes["protected_final_test"]
        ),
    }
    passed = bool(
        not collisions
        and not any(intersections.values())
        and len(partition_hashes["development"]) == len(development)
        and len(partition_hashes["calibration"]) == len(calibration)
    )
    payload = {
        "schema_version": SCHEMA_VERSION,
        "service_timing_policy_id": SERVICE_TIMING_POLICY_ID,
        "assignment_key": (
            "source_partitions_preserved_real_map_content_hash_order"
        ),
        "synthetic_content_manifest_path": str(synthetic_path),
        "synthetic_content_manifest_sha256": _file_sha256(
            synthetic_path
        ),
        "real_generation_manifest_path": str(real_path),
        "real_generation_manifest_sha256": _file_sha256(real_path),
        "protected_manifest_path": str(protected_path),
        "protected_manifest_sha256": _file_sha256(protected_path),
        "base_content_manifest_hash": synthetic.get("manifest_hash"),
        "authorized_collection_manifest_hashes": sorted(
            {
                str(value)
                for value in (
                    synthetic.get("manifest_hash"),
                    synthetic.get("base_content_manifest_hash"),
                    (
                        None
                        if prior_content is None
                        else prior_content.get("manifest_hash")
                    ),
                )
                if value
            }
        ),
        "authorized_collection_split_manifest_hashes": sorted(
            {
                str(value)
                for value in (
                    *(
                        ()
                        if prior_split is None
                        else prior_split.get(
                            "authorized_collection_split_manifest_hashes"
                        )
                        or ()
                    ),
                    (
                        None
                        if prior_split is None
                        else prior_split.get("manifest_hash")
                    ),
                )
                if value
            }
        ),
        "prior_cross_domain_content_manifest_path": (
            None if prior_content_path is None else str(prior_content_path)
        ),
        "prior_cross_domain_content_manifest_sha256": (
            None
            if prior_content_path is None
            else _file_sha256(prior_content_path)
        ),
        "prior_grouped_split_manifest_path": (
            None if prior_split_path is None else str(prior_split_path)
        ),
        "prior_grouped_split_manifest_sha256": (
            None
            if prior_split_path is None
            else _file_sha256(prior_split_path)
        ),
        "real_map_partition_policy": (
            "frozen_prior_partitions_then_new_content_hash_order"
        ),
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
            "collisions": collisions,
            "partition_intersections": intersections,
            "protected_hash_count": len(protected_hashes),
            "protected_content_read": False,
            "real_map_partition_frozen_before_branch_labels": True,
            "real_map_development_scale_counts": {
                str(scale): sum(
                    int(row["scale"]) == scale
                    for row in real_development
                )
                for scale in required_scales
            },
            "real_map_calibration_scale_counts": {
                str(scale): sum(
                    int(row["scale"]) == scale
                    for row in real_calibration
                )
                for scale in required_scales
            },
        },
    }
    payload["manifest_hash"] = _payload_sha256(payload)
    output = Path(args.output_manifest)
    _write(output, payload)
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
