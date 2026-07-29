#!/usr/bin/env python3
"""Materialize dense bounded-harvest outcomes from development trajectories."""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "lunar_ice_bpc.p0v3_harvest_dynamics_rows.v1"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _hash(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
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
    parser.add_argument("--root-source-glob", action="append", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root_paths = sorted(
        {
            path.resolve()
            for pattern in args.root_source_glob
            for path in (
                Path(item)
                for item in glob.glob(
                    str((ROOT / pattern).resolve())
                )
            )
        }
    )
    if not root_paths:
        raise SystemExit("no root sources matched")
    rows = []
    source_roots = []
    for root_path in root_paths:
        source = _load(root_path)
        if not bool(source.get("development_only")):
            raise SystemExit("harvest dynamics source must be development-only")
        result = dict(source.get("result") or {})
        history = {
            int(row.get("round") or 0): dict(row)
            for row in result.get("history") or ()
        }
        snapshot_dir = root_path.parent / "round_snapshots"
        manifest_path = snapshot_dir / "manifest.json"
        manifest = _load(manifest_path)
        if str(manifest.get("instance_content_hash") or "") != str(
            source.get("instance_content_hash") or ""
        ):
            raise SystemExit("snapshot/root content hash mismatch")
        source_roots.append(
            {
                "root_source_path": str(root_path),
                "instance_id": source["instance_id"],
                "instance_content_hash": source[
                    "instance_content_hash"
                ],
                "scale": len(
                    (result.get("dual_context") or {}).get(
                        "task_duals"
                    )
                    or {}
                ),
                "root_exact_safe": bool(source.get("root_exact_safe")),
            }
        )
        for snapshot_row in manifest.get("snapshots") or ():
            snapshot_path = Path(snapshot_row["snapshot_path"])
            snapshot = _load(snapshot_path)
            round_index = int(snapshot["round"])
            outcome = history.get(round_index)
            if outcome is None:
                raise SystemExit(
                    "snapshot round is missing from root history"
                )
            if str(snapshot.get("source_pass_strategy") or "") != (
                "harvest_then_proof"
            ):
                continue
            if bool(
                outcome.get(
                    "labeling_final_judge_proof_pass_attempted"
                )
            ):
                continue
            processed_labels = int(
                outcome.get(
                    "labeling_final_judge_harvest_pass_processed_labels"
                )
                or 0
            )
            if processed_labels <= 0:
                continue
            target = max(
                1,
                int(snapshot.get("effective_harvest_target") or 1),
            )
            harvest_count = int(
                outcome.get(
                    "labeling_final_judge_harvest_pass_column_count"
                )
                or 0
            )
            added_count = int(
                outcome.get("added_column_count") or 0
            )
            rows.append(
                {
                    "instance_id": source["instance_id"],
                    "instance_content_hash": source[
                        "instance_content_hash"
                    ],
                    "instance_path": source["instance_path"],
                    "scale": len(
                        (snapshot.get("true_duals") or {}).get(
                            "task_duals"
                        )
                        or {}
                    ),
                    "state_hash": snapshot["state_hash"],
                    "round": round_index,
                    "snapshot_path": str(snapshot_path),
                    "root_source_path": str(root_path),
                    "column_catalog_path": str(
                        snapshot_dir / "column_catalog.json"
                    ),
                    "root_exact_safe": bool(
                        source.get("root_exact_safe")
                    ),
                    "effective_harvest_target": target,
                    "harvest_column_count": harvest_count,
                    "harvest_yield_fraction": min(
                        1.0,
                        harvest_count / float(target),
                    ),
                    "added_column_count": added_count,
                    "added_fraction": min(
                        1.0,
                        added_count / float(target),
                    ),
                    "harvest_processed_labels": processed_labels,
                    "harvest_best_true_rc": float(
                        outcome.get("harvest_best_true_rc") or 0.0
                    ),
                    "harvest_pass_wall_sec": float(
                        outcome.get(
                            "labeling_final_judge_harvest_pass_wall_time"
                        )
                        or 0.0
                    ),
                    "sparse_harvest": bool(harvest_count < target),
                    "observed_outcome_only": True,
                    "certificate_role": "NONE",
                }
            )
    payload = {
        "schema_version": SCHEMA,
        "development_only": True,
        "deployable": False,
        "can_certify": False,
        "target_observation": (
            "next bounded-harvest outcome from the same pre-call state"
        ),
        "source_root_count": len(source_roots),
        "source_roots": source_roots,
        "row_count": len(rows),
        "instance_count": len(
            {row["instance_content_hash"] for row in rows}
        ),
        "scale_counts": {
            str(scale): sum(row["scale"] == scale for row in rows)
            for scale in sorted({row["scale"] for row in rows})
        },
        "sparse_row_count": sum(row["sparse_harvest"] for row in rows),
        "rows": rows,
    }
    payload["artifact_hash"] = _hash(payload)
    output_path = (ROOT / args.output).resolve()
    _write(output_path, payload)
    print(
        json.dumps(
            {
                "source_root_count": payload["source_root_count"],
                "row_count": payload["row_count"],
                "instance_count": payload["instance_count"],
                "scale_counts": payload["scale_counts"],
                "sparse_row_count": payload["sparse_row_count"],
                "output": str(output_path),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
