#!/usr/bin/env python3
"""Precommit a fresh iid scale20/30 development expansion by content hash."""

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
    "lunar_ice_bpc.no_task_wait_v3_branch_candidate_pool_expanded.v1"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_sha256(payload: object) -> str:
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-content-manifest", required=True)
    parser.add_argument("--expansion-source-manifest", required=True)
    parser.add_argument("--output-manifest", required=True)
    parser.add_argument(
        "--unbiased-expansion-census-per-scale",
        type=int,
        default=12,
    )
    args = parser.parse_args()

    base_path = (ROOT / args.base_content_manifest).resolve()
    source_path = (ROOT / args.expansion_source_manifest).resolve()
    output_path = (ROOT / args.output_manifest).resolve()
    base = _load(base_path)
    source = _load(source_path)
    if (
        not bool((base.get("audit") or {}).get("passed"))
        or base.get("calibration_read_authorized") is not False
        or str(source.get("status") or "") != "complete"
        or str(source.get("service_timing_policy_id") or "")
        != SERVICE_TIMING_POLICY_ID
    ):
        raise SystemExit("base or expansion source is not admissible")

    base_rows = [
        *list(base.get("development") or ()),
        *list(base.get("calibration") or ()),
        *list(base.get("protected_final_test") or ()),
    ]
    seen_hashes = {
        str(row["instance_content_hash"]) for row in base_rows
    }
    seen_ids = {str(row["instance_id"]) for row in base_rows}
    expansion_by_scale: dict[int, list[dict]] = {}
    collisions = []
    for source_row in source.get("instances") or ():
        path = (ROOT / str(source_row["path"])).resolve()
        data = load_lunar_ice_data(_load(path))
        content_hash = data.instance_content_hash
        if content_hash in seen_hashes:
            collisions.append(
                {
                    "kind": "content_hash_overlap",
                    "value": content_hash,
                }
            )
        if data.instance_id in seen_ids:
            collisions.append(
                {
                    "kind": "instance_id_overlap",
                    "value": data.instance_id,
                }
            )
        seen_hashes.add(content_hash)
        seen_ids.add(data.instance_id)
        expansion_by_scale.setdefault(int(data.scale), []).append(
            {
                "scale": int(data.scale),
                "instance_id": data.instance_id,
                "instance_path": str(path),
                "instance_content_hash": content_hash,
                "raw_file_sha256": _file_sha256(path),
                "seed": int(source_row["seed"]),
                "generator_attempt_index": int(
                    source_row["attempt_index"]
                ),
                "service_timing_policy_id": (
                    data.service_timing_policy_id
                ),
                "generator_schema_accepted": True,
                "v3_solver_reaccepted": False,
                "v3_exact_actionability_status": "NOT_RUN",
            }
        )
    if set(expansion_by_scale) != {20, 30} or any(
        len(rows) != 60 for rows in expansion_by_scale.values()
    ):
        raise SystemExit("expansion must contain 60 scale20/30 rows each")

    census = max(
        0, int(args.unbiased_expansion_census_per_scale)
    )
    expansion = []
    for scale, rows in sorted(expansion_by_scale.items()):
        rows.sort(key=lambda row: row["instance_content_hash"])
        for index, row in enumerate(rows):
            expansion.append(
                {
                    **row,
                    "pool_role": (
                        "UNBIASED_EXPANSION_CENSUS"
                        if index < census
                        else "BOUNDED_ACTIONABILITY_DISCOVERY_EXPANSION"
                    ),
                    "scale_hash_order_index": (
                        int(base["development_per_scale"]) + index
                    ),
                    "expansion_precommitted_before_screening": True,
                }
            )

    development = [
        *list(base.get("development") or ()),
        *expansion,
    ]
    calibration = list(base.get("calibration") or ())
    scale_counts = {
        str(scale): sum(
            int(row["scale"]) == scale for row in development
        )
        for scale in (20, 30)
    }
    calibration_counts = {
        str(scale): sum(
            int(row["scale"]) == scale for row in calibration
        )
        for scale in (20, 30)
    }
    audit = {
        "passed": bool(
            not collisions
            and scale_counts == {"20": 108, "30": 108}
            and calibration_counts == {"20": 12, "30": 12}
            and len(seen_hashes) == len(base_rows) + len(expansion)
        ),
        "collision_count": len(collisions),
        "collisions": collisions,
        "development_scale_counts": scale_counts,
        "calibration_scale_counts": calibration_counts,
        "expansion_precommitted_before_priority_or_exact_screen": True,
        "calibration_content_read": False,
        "protected_test_content_read": False,
    }
    payload = {
        "schema_version": SCHEMA_VERSION,
        "service_timing_policy_id": SERVICE_TIMING_POLICY_ID,
        "base_content_manifest_path": str(base_path),
        "base_content_manifest_sha256": _file_sha256(base_path),
        "base_content_manifest_hash": str(base["manifest_hash"]),
        "expansion_source_manifest_path": str(source_path),
        "expansion_source_manifest_sha256": _file_sha256(source_path),
        "assignment_key": (
            "base_partition_preserved_then_content_hash_expansion"
        ),
        "development_per_scale": 108,
        "calibration_per_scale": 12,
        "initial_random_census_per_scale": int(
            base.get("initial_random_census_per_scale") or 0
        ),
        "unbiased_expansion_census_per_scale": census,
        "development": development,
        "calibration": calibration,
        "protected_final_test": list(
            base.get("protected_final_test") or ()
        ),
        "opportunity_collection_authorized": True,
        "causal_oracle_collection_authorized": True,
        "training_authorized": False,
        "calibration_read_authorized": False,
        "promotion_authorized": False,
        "expansion_reason": (
            "preexisting fixed development pool cannot reach the frozen "
            "minimum independent actionable-instance gate"
        ),
        "audit": audit,
    }
    payload["manifest_hash"] = _json_sha256(payload)
    _write(output_path, payload)
    print(
        json.dumps(
            {
                "output_manifest": str(output_path),
                "manifest_hash": payload["manifest_hash"],
                "audit": audit,
            },
            sort_keys=True,
        )
    )
    return 0 if audit["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
