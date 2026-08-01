#!/usr/bin/env python3
"""Freeze an outcome-independent scale30/50 development instance corpus."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.domain.scheduling import generate_instance  # noqa: E402
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.io.instance_io import (  # noqa: E402
    validate_instance,
    write_json,
)


OUTPUT = ROOT / "data/p0v4_fixed_k_gat_development_v1"
SCALES = (30, 50)
INSTANCE_COUNT = 10
SEED_BASE_BY_SCALE = {
    30: 629_300_000,
    50: 629_500_000,
}


def main() -> int:
    official_hashes = _official_content_hashes()
    rows = []
    for scale in SCALES:
        directory = OUTPUT / f"scale_{scale:03d}"
        directory.mkdir(parents=True, exist_ok=True)
        for index in range(1, INSTANCE_COUNT + 1):
            seed = SEED_BASE_BY_SCALE[scale] + index
            instance = generate_instance(
                scale, seed=seed, index=index
            )
            issues = validate_instance(instance)
            if issues or not bool(
                dict(instance.get("validation") or {}).get("accepted")
            ):
                raise SystemExit(
                    f"invalid generated instance scale={scale} index={index}"
                )
            target = (
                directory
                / f"instance_{index:03d}_logical_graph.json"
            )
            write_json(target, instance)
            data = load_lunar_ice_data(instance)
            if data.instance_content_hash in official_hashes:
                raise SystemExit(
                    "development instance overlaps official evaluation corpus"
                )
            rows.append(
                {
                    "scale": scale,
                    "index": index,
                    "seed": seed,
                    "path": str(target.relative_to(ROOT)),
                    "file_sha256": _sha256(target),
                    "instance_content_hash": data.instance_content_hash,
                    "validation_accepted": True,
                }
            )
    content_hashes = [
        str(row["instance_content_hash"]) for row in rows
    ]
    manifest = {
        "schema_version": (
            "lunar_ice_bpc.p0v4_fixed_k_gat_development_corpus.v1"
        ),
        "status": "FROZEN_BEFORE_ALGORITHM_OUTCOMES",
        "purpose": (
            "fixed_E_K_selection_and_one_deviation_train_calibration_only"
        ),
        "scales": list(SCALES),
        "instance_count_per_scale": INSTANCE_COUNT,
        "seed_policy": {
            str(scale): {
                "base": SEED_BASE_BY_SCALE[scale],
                "formula": "base_plus_one_based_index",
            }
            for scale in SCALES
        },
        "official_evaluation_corpus_overlap_count": 0,
        "unique_content_hash_count": len(set(content_hashes)),
        "row_count": len(rows),
        "rows": rows,
    }
    if len(set(content_hashes)) != len(rows):
        raise SystemExit("development corpus contains duplicate content")
    _write_json(OUTPUT / "manifest.json", manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


def _official_content_hashes() -> set[str]:
    values = set()
    for scale in SCALES:
        directory = (
            ROOT
            / "data/instances"
            / f"lunar_ice_sp50_{scale:03d}"
        )
        for path in sorted(
            directory.glob("instance_*_logical_graph.json")
        ):
            payload = json.loads(path.read_text(encoding="utf-8"))
            values.add(
                load_lunar_ice_data(payload).instance_content_hash
            )
    return values


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
