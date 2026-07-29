#!/usr/bin/env python3
"""Rebind the frozen GAT split membership to no-task-wait V3 hashes.

The old manifest remains immutable historical evidence.  This script preserves
its instance-ID partition/fold membership, recomputes every content hash under
the current service-timing semantics, and marks the old P0 difficulty strata as
stale.  The result is suitable for V3 causal-oracle collection, but not for
training until V3 B0 difficulty measurements are attached.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from lunar_ice_bpc.domain.scenario import SERVICE_TIMING_POLICY_ID
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.guidance.splits import audit_split_manifest


ROOT = Path(__file__).resolve().parents[1]


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _instance_index(
    *,
    development_root: Path,
    protected_root: Path,
) -> dict[str, dict]:
    paths = [
        *sorted(development_root.glob("scale_*/instance_*_logical_graph.json")),
        *[
            path
            for scale in (5, 10, 20, 30, 50, 100)
            for path in sorted(
                (
                    protected_root
                    / f"lunar_ice_sp50_{scale:03d}"
                ).glob("instance_*_logical_graph.json")
            )
        ],
    ]
    rows: dict[str, dict] = {}
    for path in paths:
        data = load_lunar_ice_data(_load_json(path))
        if data.instance_id in rows:
            raise SystemExit(f"duplicate instance ID: {data.instance_id}")
        rows[data.instance_id] = {
            "instance_content_hash": data.instance_content_hash,
            "instance_path": str(path.resolve()),
            "scale": int(data.scale),
            "service_timing_policy_id": data.service_timing_policy_id,
        }
    return rows


def _canonical_hash(payload: dict) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-manifest",
        default="data/gat_p0v2/p0v2_gat_split_manifest.json",
    )
    parser.add_argument(
        "--development-root",
        default="data/gat_p0v2/development_instances",
    )
    parser.add_argument("--protected-root", default="data/instances")
    parser.add_argument(
        "--output",
        default=(
            "data/gat_p0v2/"
            "p0_no_task_wait_v3_gat_split_rebind_manifest.json"
        ),
    )
    args = parser.parse_args()

    source_path = (ROOT / args.source_manifest).resolve()
    development_root = (ROOT / args.development_root).resolve()
    protected_root = (ROOT / args.protected_root).resolve()
    output_path = (ROOT / args.output).resolve()
    source = _load_json(source_path)
    if not bool((source.get("audit") or {}).get("passed")):
        raise SystemExit("source split manifest audit did not pass")

    index = _instance_index(
        development_root=development_root,
        protected_root=protected_root,
    )
    rebound: dict[str, list[dict]] = {}
    missing: list[str] = []
    stale_hash_reused: list[str] = []
    policy_mismatches: list[str] = []
    for partition in (
        "development",
        "calibration",
        "protected_final_test",
    ):
        rebound_rows = []
        for old_row in source.get(partition, ()):
            instance_id = str(old_row["instance_id"])
            current = index.get(instance_id)
            if current is None:
                missing.append(instance_id)
                continue
            if int(current["scale"]) != int(old_row["scale"]):
                raise SystemExit(f"scale mismatch for {instance_id}")
            if (
                current["service_timing_policy_id"]
                != SERVICE_TIMING_POLICY_ID
            ):
                policy_mismatches.append(instance_id)
            if (
                current["instance_content_hash"]
                == str(old_row["instance_content_hash"])
            ):
                stale_hash_reused.append(instance_id)
            row = dict(old_row)
            row["source_instance_content_hash"] = str(
                old_row["instance_content_hash"]
            )
            row["instance_content_hash"] = str(
                current["instance_content_hash"]
            )
            row["instance_path"] = str(current["instance_path"])
            row["service_timing_policy_id"] = str(
                current["service_timing_policy_id"]
            )
            row["p0_difficulty_bin_source"] = "stale_task_waiting_v2"
            row["p0_difficulty_remeasurement_required"] = (
                partition in {"development", "calibration"}
            )
            rebound_rows.append(row)
        rebound[partition] = sorted(
            rebound_rows,
            key=lambda row: row["instance_content_hash"],
        )

    if missing:
        raise SystemExit(
            f"{len(missing)} source instances were not found: "
            + ",".join(missing[:10])
        )
    if stale_hash_reused:
        raise SystemExit(
            "V3 rebind unexpectedly reused old content hashes: "
            + ",".join(stale_hash_reused[:10])
        )
    if policy_mismatches:
        raise SystemExit(
            "service timing policy mismatch: "
            + ",".join(policy_mismatches[:10])
        )

    manifest = {
        "schema_version": (
            "lunar_ice_bpc.gat_split_manifest.no_task_wait_v3_rebind.v1"
        ),
        "source_manifest_path": str(source_path),
        "source_manifest_hash": str(source.get("manifest_hash") or ""),
        "service_timing_policy_id": SERVICE_TIMING_POLICY_ID,
        "assignment_key": (
            "frozen_v2_instance_id_membership_rebound_to_v3_content_hash"
        ),
        "membership_preserved_by_instance_id": True,
        "fold_count": int(source["fold_count"]),
        "fold_assignment": "preserved_from_source_manifest",
        "normalization_fit_scope": "not_authorized_before_v3_b0_remeasurement",
        "difficulty_strata_status": "stale_remeasurement_required",
        "causal_oracle_collection_authorized": True,
        "training_authorized": False,
        "development": rebound["development"],
        "calibration": rebound["calibration"],
        "protected_final_test": rebound["protected_final_test"],
    }
    manifest["audit"] = audit_split_manifest(manifest)
    manifest["audit"].update(
        {
            "source_instance_count": sum(
                len(source.get(partition, ()))
                for partition in (
                    "development",
                    "calibration",
                    "protected_final_test",
                )
            ),
            "rebound_instance_count": sum(
                len(manifest[partition])
                for partition in (
                    "development",
                    "calibration",
                    "protected_final_test",
                )
            ),
            "old_content_hash_reuse_count": 0,
            "service_timing_policy_mismatch_count": 0,
            "instance_id_membership_preserved": True,
            "difficulty_remeasurement_required": True,
        }
    )
    if not bool(manifest["audit"]["passed"]):
        raise SystemExit("rebound split audit failed")
    manifest["manifest_hash"] = _canonical_hash(manifest)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(output_path)
    print(
        json.dumps(
            {
                "output": str(output_path),
                "manifest_hash": manifest["manifest_hash"],
                "audit": manifest["audit"],
                "training_authorized": manifest["training_authorized"],
                "causal_oracle_collection_authorized": manifest[
                    "causal_oracle_collection_authorized"
                ],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
