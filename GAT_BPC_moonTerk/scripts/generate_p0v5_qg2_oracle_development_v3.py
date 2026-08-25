#!/usr/bin/env python3
"""Freeze 400 candidate instances for at most 300 eligible QG2 contexts."""

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


OUTPUT = ROOT / "data/p0v5_qg2_oracle_development_v3"
V2_ROOT = ROOT / "data/p0v5_qg2_oracle_development_v2"
V2_MANIFEST = V2_ROOT / "manifest.json"
CANDIDATES_PER_SCALE = 200
PRESERVED_PREFIX = 150
SCALE30_NEW_SEED_BASE = 632_300_000
SCALE50_SEED_BASE = 631_500_000


def main() -> int:
    official = _hashes_under(ROOT / "data/instances", scales={30, 50})
    protected_roots = (
        ROOT / "data/p0v4_fixed_k_gat_development_v1",
        ROOT / "data/dssr_v2_validation",
    )
    protected = set(official)
    for root in protected_roots:
        protected.update(_hashes_under(root, scales={30, 50}))

    rows = []
    selected = set()
    for scale in (30, 50):
        target_root = OUTPUT / f"scale_{scale:03d}"
        target_root.mkdir(parents=True, exist_ok=True)
        for index in range(1, CANDIDATES_PER_SCALE + 1):
            if index <= PRESERVED_PREFIX:
                source = (
                    V2_ROOT
                    / f"scale_{scale:03d}"
                    / f"instance_{index:03d}_logical_graph.json"
                )
                payload = _load(source)
                seed = payload.get("seed")
                role = "preserved_qg2_v2_prefix"
            else:
                seed = (
                    SCALE30_NEW_SEED_BASE + index
                    if scale == 30
                    else SCALE50_SEED_BASE + index
                )
                payload = generate_instance(scale, seed=seed, index=index)
                role = "new_qg2_v3_eligibility_slack"
            issues = validate_instance(payload)
            if issues or not bool(
                dict(payload.get("validation") or {}).get("accepted")
            ):
                raise SystemExit(
                    f"invalid QG2 v3 scale{scale} instance {index}: {issues}"
                )
            target = target_root / f"instance_{index:03d}_logical_graph.json"
            if target.exists():
                if _stable_hash(_load(target)) != _stable_hash(payload):
                    raise SystemExit(f"frozen QG2 v3 instance drift: {target}")
            else:
                write_json(target, payload)
            content_hash = str(load_lunar_ice_data(payload).instance_content_hash)
            if content_hash in selected:
                raise SystemExit("QG2 v3 corpus contains duplicate content")
            selected.add(content_hash)
            rows.append({
                "scale": scale,
                "index": index,
                "seed": seed,
                "path": str(target.relative_to(ROOT)),
                "file_sha256": _sha256(target),
                "instance_content_hash": content_hash,
                "source_role": role,
                "official_overlap": content_hash in official,
                "protected_overlap": content_hash in protected,
                "validation_accepted": True,
            })
    official_overlap = sum(bool(row["official_overlap"]) for row in rows)
    protected_overlap = sum(bool(row["protected_overlap"]) for row in rows)
    if official_overlap or protected_overlap:
        raise SystemExit("QG2 v3 corpus overlaps official/protected content")
    manifest = {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_oracle_development_corpus.v3",
        "status": "FROZEN_BEFORE_ANY_QO2_OUTCOME",
        "development_only": True,
        "deployable": False,
        "purpose": "eligibility_slack_for_at_most_300_bounded_qo2_contexts",
        "candidate_instance_count_per_scale": CANDIDATES_PER_SCALE,
        "candidate_instance_count_total": 2 * CANDIDATES_PER_SCALE,
        "maximum_oracle_contexts": 300,
        "maximum_oracle_contexts_per_scale": 150,
        "preserved_v2_prefix_per_scale": PRESERVED_PREFIX,
        "v2_manifest": str(V2_MANIFEST.relative_to(ROOT)),
        "v2_manifest_sha256": _sha256(V2_MANIFEST),
        "seed_policies": {
            "scale30": {"base": SCALE30_NEW_SEED_BASE},
            "scale50": {"base": SCALE50_SEED_BASE},
            "formula": "base_plus_one_based_index",
        },
        "official_evaluation_corpus_overlap_count": official_overlap,
        "protected_content_overlap_count": protected_overlap,
        "protected_roots": [str(path.relative_to(ROOT)) for path in protected_roots],
        "unique_content_hash_count": len(selected),
        "row_count": len(rows),
        "collection_order": "scale_then_one_based_index",
        "capacity_rationale": {
            "context_cap": 300,
            "candidate_instances": 400,
            "observed_early_scale30_eligibility_fraction": 0.8333333333333334,
            "candidate_pool_is_not_a_requirement_to_run_all": True,
            "staged_collection_stops_when_predeclared_gate_is_evaluable": True,
        },
        "rows": rows,
    }
    _write_json(OUTPUT / "manifest.json", manifest)
    print(json.dumps({
        "output": str(OUTPUT / "manifest.json"),
        "row_count": len(rows),
        "unique_content_hash_count": len(selected),
        "official_overlap": official_overlap,
        "protected_overlap": protected_overlap,
    }, sort_keys=True))
    return 0


def _hashes_under(root: Path, *, scales: set[int]) -> set[str]:
    values = set()
    if root.exists():
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
