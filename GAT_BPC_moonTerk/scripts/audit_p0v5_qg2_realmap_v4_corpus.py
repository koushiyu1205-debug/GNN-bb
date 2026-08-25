#!/usr/bin/env python3
"""Audit the independent real-map corpus before any QG2 matched outcome."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

SCHEMA = "lunar_ice_bpc.p0v5_qg2_realmap_v4_corpus_audit.v1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--corpus-root",
        default="data/p0v5_qg2_realmap_development_v4",
    )
    parser.add_argument("--formal-root", default="data/instances")
    parser.add_argument(
        "--output",
        default=(
            "runs/p0v5_qg2_v4_realmap_gat_first_20260806/"
            "realmap_v4_corpus_audit.json"
        ),
    )
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()

    corpus_root = _resolve(args.corpus_root)
    formal_root = _resolve(args.formal_root)
    development = _paths(corpus_root)
    formal = _paths(formal_root)
    expected = {30: 20, 50: 20}
    counts = {
        scale: len(development[scale]) for scale in (30, 50)
    }
    complete = counts == expected
    if not complete and not args.allow_partial:
        raise SystemExit(f"real-map V4 corpus is incomplete: {counts}")

    development_rows = [
        _identity(path) for scale in (30, 50)
        for path in development[scale]
    ]
    formal_rows = [
        _identity(path) for scale in (30, 50)
        for path in formal[scale]
    ]
    overlap = sorted(
        {row["instance_content_hash"] for row in development_rows}
        & {row["instance_content_hash"] for row in formal_rows}
    )
    wrong_generator = [
        row for row in development_rows
        if row["benchmark_id"] != "lunar_ice_sp50_real_map_v1"
        or row["candidate_pool_policy"]
        != "water_ice_hotspot_directional_sampling_v1"
    ]
    duplicate_hashes = _duplicates(
        row["instance_content_hash"] for row in development_rows
    )
    duplicate_seeds = _duplicates(row["seed"] for row in development_rows)
    distribution = (
        _distribution_audit(development, formal) if complete else None
    )
    corpus_ready = bool(
        complete
        and not overlap
        and not wrong_generator
        and not duplicate_hashes
        and not duplicate_seeds
        and distribution
        and distribution["schema_safe"]
    )
    payload = {
        "schema_version": SCHEMA,
        "development_only": True,
        "corpus_root": str(corpus_root),
        "formal_root": str(formal_root),
        "counts_by_scale": {str(key): value for key, value in counts.items()},
        "expected_counts_by_scale": {str(key): value for key, value in expected.items()},
        "complete": complete,
        "formal_content_hash_overlap_count": len(overlap),
        "formal_content_hash_overlap": overlap,
        "wrong_generator_count": len(wrong_generator),
        "duplicate_content_hashes": duplicate_hashes,
        "duplicate_seeds": duplicate_seeds,
        "development_rows": development_rows,
        "formal_rows_sha256": _stable_hash(formal_rows),
        "distribution_audit": distribution,
        "corpus_ready_for_preoutcome_split": corpus_ready,
    }
    output = _resolve(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "output": str(output),
        "counts_by_scale": payload["counts_by_scale"],
        "overlap_count": len(overlap),
        "corpus_ready": corpus_ready,
    }, sort_keys=True))
    return 0 if corpus_ready or (args.allow_partial and not complete) else 2


def _paths(root: Path) -> dict[int, tuple[Path, ...]]:
    return {
        scale: tuple(sorted(
            (root / f"lunar_ice_sp50_{scale:03d}").glob(
                "instance_*_logical_graph.json"
            )
        ))
        for scale in (30, 50)
    }


def _identity(path: Path) -> dict:
    from lunar_ice_bpc.exact.core.data import load_lunar_ice_data

    payload = json.loads(path.read_text(encoding="utf-8"))
    data = load_lunar_ice_data(payload)
    resource = dict(payload.get("resource_map") or {})
    scheduling = dict(payload.get("scheduling") or {})
    return {
        "scale": int(data.scale),
        "instance_id": str(payload.get("instance_id") or ""),
        "instance_content_hash": data.instance_content_hash,
        "seed": int(payload.get("seed") or 0),
        "path": str(path.resolve()),
        "benchmark_id": str(resource.get("benchmark_id") or ""),
        "candidate_pool_policy": str(resource.get("candidate_pool_policy") or ""),
        "time_window_mode": str(scheduling.get("time_window_mode") or ""),
    }


def _distribution_audit(development, formal) -> dict:
    from lunar_ice_bpc.guidance.tensorization import (
        EDGE_STATIC_FEATURES,
        NODE_STATIC_FEATURES,
    )

    dev_node, dev_edge = _feature_values(development)
    formal_node, formal_edge = _feature_values(formal)
    return {
        "input_feature_schema": (
            "lunar_ice_bpc.p0v5_qg2_features.objective_normalized_risk.v3_1"
        ),
        "schema_safe": all(dev_node) and all(dev_edge),
        "node": _range_rows(
            NODE_STATIC_FEATURES, dev_node, formal_node
        ),
        "edge": _range_rows(
            tuple(
                "risk_over_objective_reference" if value == "risk" else value
                for value in EDGE_STATIC_FEATURES
            ),
            dev_edge,
            formal_edge,
        ),
        "note": (
            "Formal ranges are diagnostic-only and never enter normalization, "
            "threshold fitting, or the train envelope."
        ),
    }


def _feature_values(paths_by_scale):
    from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
    from lunar_ice_bpc.guidance.proof_queue_label_state_gat import (
        build_qg2_features,
    )
    from lunar_ice_bpc.guidance.proof_queue_label_state_gat_v3 import (
        normalize_qg2_v3_features,
    )
    from lunar_ice_bpc.guidance.tensorization import (
        EDGE_STATIC_FEATURES,
        NODE_STATIC_FEATURES,
    )

    node = [[] for _ in NODE_STATIC_FEATURES]
    edge = [[] for _ in EDGE_STATIC_FEATURES]
    for scale in (30, 50):
        for path in paths_by_scale[scale]:
            data = load_lunar_ice_data(json.loads(path.read_text(encoding="utf-8")))
            features = normalize_qg2_v3_features(
                data,
                build_qg2_features(
                    data,
                    cover_duals={task_id: 0.0 for task_id in data.task_ids},
                    fleet_dual=0.0,
                    active_column_count=None,
                    active_task_sets=None,
                    round_index=None,
                    previous_proof_wall_sec=None,
                    previous_processed_labels=None,
                    dual_l1_delta_from_previous=None,
                    branch_decisions=(),
                    cut_duals={},
                    v5_midpoint_wall_sec=None,
                    root_lifecycle_scope=True,
                ),
            )
            for row in features.node_features:
                for index, value in enumerate(row[:len(node)]):
                    node[index].append(float(value))
            for row in features.edge_features:
                for index, value in enumerate(row):
                    edge[index].append(float(value))
    return node, edge


def _range_rows(names, development, formal):
    rows = []
    for name, dev, heldout in zip(names, development, formal, strict=True):
        rows.append({
            "feature": str(name),
            "development_min": min(dev),
            "development_max": max(dev),
            "formal_min_diagnostic_only": min(heldout),
            "formal_max_diagnostic_only": max(heldout),
        })
    return rows


def _duplicates(values) -> list:
    materialized = list(values)
    return sorted({value for value in materialized if materialized.count(value) > 1})


def _stable_hash(payload) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _resolve(value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


if __name__ == "__main__":
    raise SystemExit(main())
