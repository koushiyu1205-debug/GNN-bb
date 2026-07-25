#!/usr/bin/env python3
"""Freeze a no-outcome-leakage proof-tail context configuration.

Selection uses only the development split, canonical binding metadata, and
stable hashes.  It never reads snapshot result summaries, candidate rows, or
QC0/QD1 outcomes.  Scale 30 targets observed exact-proof invocations.  Every
selected snapshot is treated only as a mathematical context and receives new
fresh QC0/QD1 controls; an old run is never trusted as a complete control.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from lunar_ice_bpc.exact.bpc.guidance.replay import (
    load_pricing_snapshot,
)
from lunar_ice_bpc.exact.core.cuts import stable_payload_hash
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_SCHEMA_V1 = "lunar_ice_bpc.proof_tail_context_config.v1"
SPLIT_SCHEMA_V1 = "lunar_ice_bpc.gat_split_manifest.v1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--split-manifest",
        default="data/gat_p0v2/p0v2_gat_split_manifest.json",
    )
    parser.add_argument(
        "--snapshot-root",
        default="runs/p0v2_gat_binding_v2_training_collection/snapshots",
    )
    parser.add_argument(
        "--instance-root",
        default="data/gat_p0v2/development_instances",
    )
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--contexts-per-scale",
        type=int,
        default=20,
    )
    parser.add_argument(
        "--selection-salt",
        default="p0v2-proof-tail-development-quota-v1-20260724",
    )
    args = parser.parse_args()
    if args.contexts_per_scale <= 0:
        raise SystemExit("--contexts-per-scale must be positive")

    split_path = _resolve(args.split_manifest)
    snapshot_root = _resolve(args.snapshot_root)
    instance_root = _resolve(args.instance_root)
    split = json.loads(split_path.read_text(encoding="utf-8"))
    if str(split.get("schema_version") or "") != SPLIT_SCHEMA_V1:
        raise SystemExit("proof-tail split manifest schema mismatch")
    expected_hash = str(split.get("manifest_hash") or "")
    actual_hash = stable_payload_hash(
        {key: value for key, value in split.items() if key != "manifest_hash"}
    )
    if expected_hash != actual_hash:
        raise SystemExit("proof-tail split manifest hash mismatch")

    instance_paths = _index_instance_paths(instance_root)
    development = {
        int(scale): [
            dict(row)
            for row in split.get("development", ())
            if int(row.get("scale") or 0) == int(scale)
        ]
        for scale in (20, 30)
    }
    contexts: list[dict[str, Any]] = []
    selection_summary: dict[str, Any] = {}
    for scale in (20, 30):
        eligible = _eligible_instance_contexts(
            scale=scale,
            rows=development[scale],
            snapshot_root=snapshot_root,
            instance_paths=instance_paths,
            selection_salt=str(args.selection_salt),
        )
        selected = sorted(
            eligible,
            key=lambda row: stable_payload_hash(
                {
                    "selection_salt": str(args.selection_salt),
                    "scale": scale,
                    "instance_content_hash": row[
                        "instance_content_hash"
                    ],
                }
            ),
        )[: int(args.contexts_per_scale)]
        if len(selected) < int(args.contexts_per_scale):
            raise SystemExit(
                f"scale {scale} has only {len(selected)} eligible contexts"
            )
        contexts.extend(row["config_row"] for row in selected)
        selection_summary[str(scale)] = {
            "eligible_instance_count": len(eligible),
            "selected_context_count": len(selected),
            "source_pricing_modes": _counts(
                row["source_pricing_mode"] for row in selected
            ),
            "folds": _counts(str(row["fold"]) for row in selected),
            "p0_difficulty_bins": _counts(
                str(row["p0_difficulty_bin"]) for row in selected
            ),
        }

    payload = {
        "schema_version": CONFIG_SCHEMA_V1,
        "selection_stream": "development_quota_pre_outcome_v1",
        "selection_salt": str(args.selection_salt),
        "selection_uses_qc0_qd1_outcomes": False,
        "selection_fields": [
            "development_partition",
            "scale",
            "instance_content_hash",
            "canonical_binding",
            "source_pricing_mode",
            "stable_selection_salt",
        ],
        "split_manifest": _relative(split_path),
        "split_manifest_hash": expected_hash,
        "allowed_partitions": ["development"],
        "selection_summary": selection_summary,
        "contexts": contexts,
    }
    payload["config_hash"] = stable_payload_hash(payload)
    output = Path(args.output)
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    print(output.resolve())
    return 0


def _eligible_instance_contexts(
    *,
    scale: int,
    rows: list[dict[str, Any]],
    snapshot_root: Path,
    instance_paths: dict[str, Path],
    selection_salt: str,
) -> list[dict[str, Any]]:
    eligible = []
    for split_row in rows:
        instance_hash = str(split_row["instance_content_hash"])
        candidates = []
        for path in sorted((snapshot_root / instance_hash).glob("*.json")):
            snapshot = load_pricing_snapshot(path)
            if snapshot.objective_mode != "official":
                continue
            if scale == 30 and snapshot.pricing_mode != "exact_proof":
                continue
            candidates.append((path, snapshot))
        if not candidates:
            continue
        path, snapshot = min(
            candidates,
            key=lambda item: stable_payload_hash(
                {
                    "selection_salt": selection_salt,
                    "scale": scale,
                    "instance_content_hash": instance_hash,
                    "binding_hash": item[1].binding.binding_hash,
                    "snapshot_hash": item[1].snapshot_hash,
                }
            ),
        )
        instance_path = instance_paths.get(instance_hash)
        if instance_path is None:
            raise SystemExit(
                f"development instance file is missing: {instance_hash}"
            )
        iteration = str(snapshot.binding.rmp_iteration_id or "context")
        subset = "on" if scale == 30 else "off"
        eligible.append(
            {
                "instance_content_hash": instance_hash,
                "source_pricing_mode": snapshot.pricing_mode,
                "fold": split_row.get("fold"),
                "p0_difficulty_bin": split_row.get(
                    "p0_difficulty_bin", "unknown"
                ),
                "config_row": {
                    "context_id": (
                        f"scale{scale}_hash{instance_hash[:5]}_"
                        f"{stable_payload_hash(iteration)[:6]}"
                    ),
                    "scale": scale,
                    "instance": _relative(instance_path),
                    "snapshot": _relative(path),
                    "source_role": "mathematical_context",
                    "completion_bound": "off",
                    "subset_dominance": subset,
                    "wall_time_limit_sec": (
                        120.0 if scale == 30 else 30.0
                    ),
                    "selection_reason": (
                        "pre_outcome_stable_hash_from_development_split"
                    ),
                    "source_pricing_mode": snapshot.pricing_mode,
                },
            }
        )
    return eligible


def _index_instance_paths(root: Path) -> dict[str, Path]:
    result = {}
    for path in sorted(root.glob("scale_*/*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        data = load_lunar_ice_data(payload)
        instance_hash = str(data.instance_content_hash)
        if instance_hash in result:
            raise SystemExit(
                f"duplicate development instance content hash: {instance_hash}"
            )
        result[instance_hash] = path.resolve()
    return result


def _counts(values) -> dict[str, int]:
    result: dict[str, int] = {}
    for value in values:
        key = str(value)
        result[key] = result.get(key, 0) + 1
    return dict(sorted(result.items()))


def _resolve(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    path = path.resolve()
    if not path.exists():
        raise SystemExit(f"proof-tail source path does not exist: {path}")
    return path


def _relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
