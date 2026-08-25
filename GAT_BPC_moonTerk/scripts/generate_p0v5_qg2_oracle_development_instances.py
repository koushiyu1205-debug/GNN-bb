#!/usr/bin/env python3
"""Freeze the bounded P0V5 QG2 oracle expansion corpus.

The scale30 rows reuse the already-frozen P0V2 development pool.  Scale50
rows are generated from a disjoint seed range.  The manifest is written
before any QG2 outcome is observed and records overlap audits against the
official evaluation corpus and existing protected development/validation
corpora.
"""

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
from lunar_ice_bpc.io.instance_io import validate_instance, write_json  # noqa: E402


OUTPUT = ROOT / "data/p0v5_qg2_oracle_development_v1"
SOURCE_SCALE30 = ROOT / "data/gat_p0v2/development_instances/scale_030"
SOURCE_SCALE30_MANIFEST = ROOT / "data/gat_p0v2/development_instances_manifest.json"
SCALE30_COUNT = 40
# Twenty files leave no slack: one scale50 instance without an eligible
# fallback would make the predeclared 20-context oracle gate unreachable.
# Freeze a disjoint 40-instance prefix before any QO2 outcome is observed.
SCALE50_COUNT = 40
SCALE50_SEED_BASE = 631_500_000


def main() -> int:
    official_hashes = _hashes_under(
        ROOT / "data/instances",
        scales={30, 50},
    )
    protected_roots = (
        ROOT / "data/p0v4_fixed_k_gat_development_v1",
        ROOT / "data/dssr_v2_validation",
    )
    protected_hashes = set(official_hashes)
    for root in protected_roots:
        protected_hashes.update(_hashes_under(root, scales={30, 50}))

    rows: list[dict] = []
    selected_hashes: set[str] = set()
    for index in range(1, SCALE30_COUNT + 1):
        path = SOURCE_SCALE30 / f"instance_{index:03d}_logical_graph.json"
        if not path.is_file():
            raise SystemExit(f"missing frozen scale30 development instance: {path}")
        payload = _load(path)
        data = load_lunar_ice_data(payload)
        _accept_row(
            rows=rows,
            selected_hashes=selected_hashes,
            protected_hashes=protected_hashes,
            official_hashes=official_hashes,
            scale=30,
            index=index,
            seed=payload.get("seed"),
            path=path,
            content_hash=data.instance_content_hash,
            source_role="reused_frozen_p0v2_development",
        )

    scale50_dir = OUTPUT / "scale_050"
    scale50_dir.mkdir(parents=True, exist_ok=True)
    for index in range(1, SCALE50_COUNT + 1):
        seed = SCALE50_SEED_BASE + index
        payload = generate_instance(50, seed=seed, index=index)
        issues = validate_instance(payload)
        if issues or not bool(dict(payload.get("validation") or {}).get("accepted")):
            raise SystemExit(
                f"invalid generated scale50 instance index={index}: {issues}"
            )
        target = scale50_dir / f"instance_{index:03d}_logical_graph.json"
        if target.exists():
            existing = _load(target)
            if _stable_hash(existing) != _stable_hash(payload):
                raise SystemExit(f"refusing to overwrite mismatched frozen instance: {target}")
        else:
            write_json(target, payload)
        data = load_lunar_ice_data(payload)
        _accept_row(
            rows=rows,
            selected_hashes=selected_hashes,
            protected_hashes=protected_hashes,
            official_hashes=official_hashes,
            scale=50,
            index=index,
            seed=seed,
            path=target,
            content_hash=data.instance_content_hash,
            source_role="new_qg2_oracle_development",
        )

    overlap_official = sum(
        str(row["instance_content_hash"]) in official_hashes for row in rows
    )
    overlap_protected = sum(
        str(row["instance_content_hash"]) in protected_hashes for row in rows
    )
    manifest = {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_oracle_development_corpus.v1",
        "status": "FROZEN_BEFORE_QG2_ORACLE_OUTCOMES",
        "development_only": True,
        "deployable": False,
        "purpose": "bounded_qo2_oracle_snapshot_expansion_only",
        "maximum_oracle_contexts": 300,
        "maximum_oracle_contexts_per_scale": 150,
        "scale30_source_manifest": str(SOURCE_SCALE30_MANIFEST.relative_to(ROOT)),
        "scale30_source_manifest_sha256": _sha256(SOURCE_SCALE30_MANIFEST),
        "scale30_fixed_prefix_count": SCALE30_COUNT,
        "scale50_generated_count": SCALE50_COUNT,
        "scale50_seed_policy": {
            "base": SCALE50_SEED_BASE,
            "formula": "base_plus_one_based_index",
        },
        "official_evaluation_corpus_overlap_count": overlap_official,
        "protected_content_overlap_count": overlap_protected,
        "protected_roots": [str(path.relative_to(ROOT)) for path in protected_roots],
        "unique_content_hash_count": len(selected_hashes),
        "row_count": len(rows),
        "collection_order": "scale_then_one_based_index",
        "rows": rows,
    }
    if overlap_official or overlap_protected:
        raise SystemExit("QG2 oracle expansion overlaps a protected corpus")
    if len(selected_hashes) != len(rows):
        raise SystemExit("QG2 oracle expansion contains duplicate content")
    _write_json(OUTPUT / "manifest.json", manifest)
    print(json.dumps({
        "output": str(OUTPUT / "manifest.json"),
        "row_count": len(rows),
        "scale30_count": SCALE30_COUNT,
        "scale50_count": SCALE50_COUNT,
        "official_overlap": overlap_official,
        "protected_overlap": overlap_protected,
    }, sort_keys=True))
    return 0


def _accept_row(
    *,
    rows: list[dict],
    selected_hashes: set[str],
    protected_hashes: set[str],
    official_hashes: set[str],
    scale: int,
    index: int,
    seed,
    path: Path,
    content_hash: str,
    source_role: str,
) -> None:
    content_hash = str(content_hash)
    rows.append({
        "scale": int(scale),
        "index": int(index),
        "seed": seed,
        "path": str(path.relative_to(ROOT)),
        "file_sha256": _sha256(path),
        "instance_content_hash": content_hash,
        "source_role": str(source_role),
        "official_overlap": content_hash in official_hashes,
        "protected_overlap": content_hash in protected_hashes,
        "validation_accepted": True,
    })
    selected_hashes.add(content_hash)


def _hashes_under(root: Path, *, scales: set[int]) -> set[str]:
    values: set[str] = set()
    if not root.exists():
        return values
    for path in sorted(root.rglob("instance_*_logical_graph.json")):
        payload = _load(path)
        if int(payload.get("scale") or 0) not in scales:
            continue
        values.add(load_lunar_ice_data(payload).instance_content_hash)
    return values


def _stable_hash(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


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
