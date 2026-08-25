#!/usr/bin/env python3
"""Freeze a full 300-context-capable QG2 development corpus before QO2.

The first 40 instances of each scale preserve the already frozen v1 prefix.
The remaining rows use disjoint deterministic seed ranges.  No QO2 outcome is
read or used by this generator.
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


OUTPUT = ROOT / "data/p0v5_qg2_oracle_development_v2"
LEGACY_SCALE30 = ROOT / "data/gat_p0v2/development_instances/scale_030"
LEGACY_SCALE50 = ROOT / "data/p0v5_qg2_oracle_development_v1/scale_050"
LEGACY_MANIFEST = ROOT / "data/p0v5_qg2_oracle_development_v1/manifest.json"
COUNT_PER_SCALE = 150
PRESERVED_PREFIX = 40
SCALE30_NEW_SEED_BASE = 632_300_000
SCALE50_SEED_BASE = 631_500_000


def main() -> int:
    official_hashes = _hashes_under(ROOT / "data/instances", scales={30, 50})
    protected_roots = (
        ROOT / "data/p0v4_fixed_k_gat_development_v1",
        ROOT / "data/dssr_v2_validation",
    )
    protected_hashes = set(official_hashes)
    for root in protected_roots:
        protected_hashes.update(_hashes_under(root, scales={30, 50}))

    rows: list[dict] = []
    selected_hashes: set[str] = set()
    for scale in (30, 50):
        target_root = OUTPUT / f"scale_{scale:03d}"
        target_root.mkdir(parents=True, exist_ok=True)
        for index in range(1, COUNT_PER_SCALE + 1):
            if index <= PRESERVED_PREFIX:
                source = (
                    LEGACY_SCALE30 / f"instance_{index:03d}_logical_graph.json"
                    if scale == 30
                    else LEGACY_SCALE50 / f"instance_{index:03d}_logical_graph.json"
                )
                payload = _load(source)
                seed = payload.get("seed")
                source_role = "preserved_qg2_v1_prefix"
            else:
                seed = (
                    SCALE30_NEW_SEED_BASE + index
                    if scale == 30
                    else SCALE50_SEED_BASE + index
                )
                payload = generate_instance(scale, seed=seed, index=index)
                source_role = "new_qg2_v2_bounded_oracle_expansion"
            issues = validate_instance(payload)
            if issues or not bool(
                dict(payload.get("validation") or {}).get("accepted")
            ):
                raise SystemExit(
                    f"invalid generated scale{scale} instance {index}: {issues}"
                )
            target = target_root / f"instance_{index:03d}_logical_graph.json"
            if target.exists():
                if _stable_hash(_load(target)) != _stable_hash(payload):
                    raise SystemExit(
                        f"refusing to overwrite mismatched frozen instance: {target}"
                    )
            else:
                write_json(target, payload)
            data = load_lunar_ice_data(payload)
            content_hash = str(data.instance_content_hash)
            if content_hash in selected_hashes:
                raise SystemExit("QG2 v2 corpus contains duplicate content")
            selected_hashes.add(content_hash)
            rows.append({
                "scale": scale,
                "index": index,
                "seed": seed,
                "path": str(target.relative_to(ROOT)),
                "file_sha256": _sha256(target),
                "instance_content_hash": content_hash,
                "source_role": source_role,
                "official_overlap": content_hash in official_hashes,
                "protected_overlap": content_hash in protected_hashes,
                "validation_accepted": True,
            })

    overlap_official = sum(bool(row["official_overlap"]) for row in rows)
    overlap_protected = sum(bool(row["protected_overlap"]) for row in rows)
    if overlap_official or overlap_protected:
        raise SystemExit("QG2 v2 corpus overlaps an official/protected corpus")
    manifest = {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_oracle_development_corpus.v2",
        "status": "FROZEN_BEFORE_ANY_QO2_OUTCOME",
        "development_only": True,
        "deployable": False,
        "purpose": "full_bounded_qo2_oracle_and_calibration_feasibility",
        "maximum_oracle_contexts": 300,
        "maximum_oracle_contexts_per_scale": 150,
        "count_per_scale": COUNT_PER_SCALE,
        "preserved_v1_prefix_per_scale": PRESERVED_PREFIX,
        "legacy_manifest": str(LEGACY_MANIFEST.relative_to(ROOT)),
        "legacy_manifest_sha256": _sha256(LEGACY_MANIFEST),
        "seed_policies": {
            "scale30_new": {
                "base": SCALE30_NEW_SEED_BASE,
                "first_new_index": PRESERVED_PREFIX + 1,
            },
            "scale50": {
                "base": SCALE50_SEED_BASE,
                "formula": "base_plus_one_based_index",
            },
        },
        "official_evaluation_corpus_overlap_count": overlap_official,
        "protected_content_overlap_count": overlap_protected,
        "protected_roots": [str(path.relative_to(ROOT)) for path in protected_roots],
        "unique_content_hash_count": len(selected_hashes),
        "row_count": len(rows),
        "collection_order": "scale_then_one_based_index",
        "statistical_feasibility": {
            "split_ratio": [60, 20, 20],
            "maximum_calibration_contexts": 60,
            "minimum_zero_harm_activations_for_one_sided_95pct_upper_le_5pct": 52,
            "full_300_context_pool_required_for_gate_feasibility": True,
        },
        "rows": rows,
    }
    _write_json(OUTPUT / "manifest.json", manifest)
    print(json.dumps({
        "output": str(OUTPUT / "manifest.json"),
        "row_count": len(rows),
        "unique_content_hash_count": len(selected_hashes),
        "official_overlap": overlap_official,
        "protected_overlap": overlap_protected,
    }, sort_keys=True))
    return 0


def _hashes_under(root: Path, *, scales: set[int]) -> set[str]:
    values: set[str] = set()
    if not root.exists():
        return values
    for path in sorted(root.rglob("instance_*_logical_graph.json")):
        payload = _load(path)
        if int(payload.get("scale") or 0) in scales:
            values.add(load_lunar_ice_data(payload).instance_content_hash)
    return values


def _stable_hash(payload: object) -> str:
    return hashlib.sha256(json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")).hexdigest()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


if __name__ == "__main__":
    raise SystemExit(main())
