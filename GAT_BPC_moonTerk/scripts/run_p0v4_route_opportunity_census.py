#!/usr/bin/env python3
"""Audit post-E_K route opportunities without manufacturing candidates."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.guidance.route_admission import (  # noqa: E402
    audit_route_opportunity_census,
    build_one_deviation_actions,
    fixed_exact_admission_batch_size,
    route_opportunity_ineligibility_reason,
    validate_route_admission_snapshot,
    validate_route_opportunity_census_binding,
)
from lunar_ice_bpc.exact.core.cuts import stable_payload_hash  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--snapshot-root",
        action="append",
        required=True,
        help="May be repeated; every root is recursively audited.",
    )
    parser.add_argument("--fixed-k-selection", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    snapshot_roots = tuple(
        _resolve(value) for value in args.snapshot_root
    )
    fixed_k_path = _resolve(args.fixed_k_selection)
    output = _resolve(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    fixed_k = _load_json(fixed_k_path)
    if str(fixed_k.get("status")) != "FIXED_K_SELECTED":
        raise SystemExit("route census requires a frozen fixed E_K")
    rows_by_hash: dict[str, tuple[dict, Path]] = {}
    rejected = []
    duplicate_snapshot_paths = []
    snapshot_paths = sorted(
        {
            path.resolve()
            for root in snapshot_roots
            for path in root.rglob("route_admission_snapshot.json")
        }
    )
    for path in snapshot_paths:
        try:
            snapshot = validate_route_admission_snapshot(_load_json(path))
            expected_batch_size = fixed_exact_admission_batch_size(
                fixed_k, scale=int(snapshot["scale"])
            )
            if int(snapshot["selection_limit"]) != expected_batch_size:
                raise ValueError("snapshot selection limit differs from E_K")
            snapshot_hash = str(snapshot["snapshot_hash"])
            previous = rows_by_hash.get(snapshot_hash)
            if previous is not None:
                duplicate_snapshot_paths.append(
                    {
                        "snapshot_hash": snapshot_hash,
                        "canonical_path": str(previous[1]),
                        "duplicate_path": str(path.resolve()),
                    }
                )
                continue
            rows_by_hash[snapshot_hash] = (snapshot, path.resolve())
        except Exception as exc:
            rejected.append(
                {"path": str(path.resolve()), "reason": repr(exc)}
            )
    rows = [
        snapshot
        for snapshot, _path in rows_by_hash.values()
    ]
    audit = audit_route_opportunity_census(rows)
    split_by_hash = _instance_split(rows)
    eligible_snapshots = []
    for snapshot_hash, (snapshot, path) in sorted(
        rows_by_hash.items()
    ):
        reason = route_opportunity_ineligibility_reason(snapshot)
        if reason:
            continue
        eligible_snapshots.append(
            {
                "snapshot_hash": snapshot_hash,
                "source_snapshot": str(path),
                "source_snapshot_sha256": _sha256(path),
                "scale": int(snapshot["scale"]),
                "instance_content_hash": str(
                    snapshot["instance_content_hash"]
                ),
                "instance_split": str(
                    split_by_hash[
                        str(snapshot["instance_content_hash"])
                    ]
                ),
            }
        )
    census_binding_payload = {
        "schema_version": (
            "lunar_ice_bpc.p0v4_route_opportunity_census_binding.v1"
        ),
        "fixed_k_selection_sha256": _sha256(fixed_k_path),
        "eligibility_policy": (
            "root_true_rc_audited_post_generation_budget_min8_v2"
        ),
        "eligible_snapshots": [
            {
                key: value
                for key, value in row.items()
                if key != "source_snapshot"
            }
            for row in eligible_snapshots
        ],
        "instance_split_by_hash": split_by_hash,
        "instance_split_policy": (
            "pre_outcome_scale_stratified_sorted_every_fifth_calibration_v1"
        ),
    }
    census_content_binding_hash = stable_payload_hash(
        census_binding_payload
    )
    for record in eligible_snapshots:
        snapshot_hash = str(record["snapshot_hash"])
        snapshot, path = rows_by_hash[snapshot_hash]
        actions = build_one_deviation_actions(snapshot)
        _write_json(
            output / "action_manifests" / f"{snapshot_hash}.json",
            {
                **actions,
                "source_snapshot": str(path),
                "source_snapshot_sha256": str(
                    record["source_snapshot_sha256"]
                ),
                "fixed_k_selection": str(fixed_k_path),
                "fixed_k_selection_sha256": _sha256(fixed_k_path),
                "census_content_binding_hash": (
                    census_content_binding_hash
                ),
                "instance_content_hash": str(
                    record["instance_content_hash"]
                ),
                "instance_split": str(record["instance_split"]),
            },
        )
    manifest = {
        "schema_version": "lunar_ice_bpc.p0v4_route_opportunity_census.v1",
        "fixed_k_selection": str(fixed_k_path),
        "fixed_k_selection_sha256": _sha256(fixed_k_path),
        "scale50_selected_batch_size": int(
            fixed_k["selected_batch_size"]
        ),
        "admission_batch_size_by_scale": {
            str(scale): fixed_exact_admission_batch_size(
                fixed_k, scale=scale
            )
            for scale in (20, 30, 50)
        },
        "snapshot_roots": [
            str(path.resolve()) for path in snapshot_roots
        ],
        "discovered_snapshot_count": len(snapshot_paths),
        "valid_snapshot_path_count": (
            len(rows) + len(duplicate_snapshot_paths)
        ),
        "valid_snapshot_count": len(rows),
        "duplicate_snapshot_count": len(duplicate_snapshot_paths),
        "duplicate_snapshot_paths": duplicate_snapshot_paths,
        "rejected_snapshots": rejected,
        "eligible_snapshot_count": len(eligible_snapshots),
        "eligible_snapshots": eligible_snapshots,
        "action_manifest_count": len(eligible_snapshots),
        "census_content_binding_hash": census_content_binding_hash,
        "census_binding_payload": census_binding_payload,
        "audit": audit,
        "instance_split_by_hash": split_by_hash,
        "instance_split_policy": (
            "pre_outcome_scale_stratified_sorted_every_fifth_calibration_v1"
        ),
        "train_calibration_instance_disjoint": True,
        "expensive_oracle_authorized": bool(
            audit["gat_oracle_authorized"]
        ),
        "candidate_manufacturing_used": False,
        "failure_policy": (
            "stop_route_gat_and_report_insufficient_action_opportunity"
        ),
    }
    validate_route_opportunity_census_binding(
        manifest,
        fixed_k_selection_sha256=_sha256(fixed_k_path),
    )
    _write_json(output / "opportunity_census.json", manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0 if manifest["expensive_oracle_authorized"] else 3


def _instance_split(rows: list[dict]) -> dict[str, str]:
    by_scale: dict[int, set[str]] = {}
    for row in rows:
        by_scale.setdefault(int(row["scale"]), set()).add(
            str(row["instance_content_hash"])
        )
    split = {}
    for scale, values in sorted(by_scale.items()):
        ordered = sorted(values)
        for index, instance_hash in enumerate(ordered):
            assignment = (
                "calibration"
                if index % 5 == 0
                else "train"
            )
            previous = split.setdefault(instance_hash, assignment)
            if previous != assignment:
                raise ValueError(
                    "one instance appeared in multiple split strata"
                )
    return split


def _resolve(value: object) -> Path:
    path = Path(str(value))
    return path if path.is_absolute() else ROOT / path


def _load_json(path: Path) -> dict:
    return dict(json.loads(path.read_text(encoding="utf-8")))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


if __name__ == "__main__":
    raise SystemExit(main())
