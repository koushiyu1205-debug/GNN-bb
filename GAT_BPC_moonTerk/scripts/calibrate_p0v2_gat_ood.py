#!/usr/bin/env python3
"""Calibrate OOD thresholds without touching model selection or weights."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from math import ceil
from pathlib import Path

import torch

from lunar_ice_bpc.exact.core.cuts import stable_payload_hash


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--calibration-jsonl", required=True)
    parser.add_argument("--split-manifest", required=True)
    parser.add_argument(
        "--static-cache-dir",
        default="data/gat_p0v2/static_tensor_cache",
    )
    parser.add_argument("--output-checkpoint", required=True)
    parser.add_argument("--checkpoint-id", required=True)
    parser.add_argument("--ood-policy-version", required=True)
    parser.add_argument("--quantile", type=float, default=0.995)
    parser.add_argument("--margin", type=float, default=1.05)
    args = parser.parse_args()
    if not 0.0 < float(args.quantile) <= 1.0:
        raise SystemExit("quantile must be in (0, 1]")
    if float(args.margin) < 1.0:
        raise SystemExit("margin must be at least 1")

    manifest = json.loads(
        Path(args.split_manifest).read_text(encoding="utf-8")
    )
    if not bool((manifest.get("audit") or {}).get("passed")):
        raise SystemExit("split manifest audit did not pass")
    calibration_hashes = {
        str(row["instance_content_hash"])
        for row in manifest.get("calibration", ())
    }
    forbidden_hashes = {
        str(row["instance_content_hash"])
        for partition in ("development", "protected_final_test")
        for row in manifest.get(partition, ())
    }
    rows = []
    for line in Path(args.calibration_jsonl).read_text(
        encoding="utf-8"
    ).splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        content_hash = str(row["instance_content_hash"])
        if content_hash in forbidden_hashes or content_hash not in calibration_hashes:
            raise SystemExit(
                f"non-calibration row supplied to OOD calibration: {content_hash}"
            )
        rows.append(row)
    if not rows:
        raise SystemExit("no calibration rows")

    payload = torch.load(
        args.checkpoint, map_location="cpu", weights_only=False
    )
    metadata = dict(payload.get("metadata") or {})
    node_mean = torch.tensor(metadata["node_feature_mean"], dtype=torch.float32)
    node_std = torch.tensor(
        metadata["node_feature_std"], dtype=torch.float32
    ).clamp_min(1.0e-8)
    edge_mean = torch.tensor(metadata["edge_feature_mean"], dtype=torch.float32)
    edge_std = torch.tensor(
        metadata["edge_feature_std"], dtype=torch.float32
    ).clamp_min(1.0e-8)
    by_scale = defaultdict(list)
    static_cache = {}
    for row in rows:
        node_values, edge_values = _feature_arrays(
            row,
            cache_dir=Path(args.static_cache_dir),
            cache=static_cache,
        )
        node = torch.tensor(node_values, dtype=torch.float32)
        edge = torch.tensor(edge_values, dtype=torch.float32)
        if node.shape[1] != node_mean.numel() or edge.shape[1] != edge_mean.numel():
            raise SystemExit("calibration feature width mismatch")
        max_abs_z = max(
            float(((node - node_mean) / node_std).abs().max()),
            float(((edge - edge_mean) / edge_std).abs().max()),
        )
        by_scale[int(row["scale"])].append(max_abs_z)
    thresholds = {
        str(scale): _quantile(values, float(args.quantile))
        * float(args.margin)
        for scale, values in sorted(by_scale.items())
    }
    calibrated_metadata = {
        **metadata,
        "checkpoint_id": str(args.checkpoint_id),
        "ood_policy_version": str(args.ood_policy_version),
        "ood_max_abs_z": max(thresholds.values()),
        "ood_max_abs_z_by_scale": thresholds,
        "ood_calibrated": True,
        "ood_calibration_split_manifest_hash": manifest.get("manifest_hash"),
        "ood_calibration_quantile": float(args.quantile),
        "ood_calibration_margin": float(args.margin),
        "ood_calibration_row_count_by_scale": {
            str(scale): len(values)
            for scale, values in sorted(by_scale.items())
        },
        "model_selection_reopened": False,
        "calibration_used_for": "ood_threshold_and_deployment_gate_only",
        "online_eligible": False,
    }
    output_payload = dict(payload)
    output_payload["metadata"] = calibrated_metadata
    target = Path(args.output_checkpoint)
    target.parent.mkdir(parents=True, exist_ok=True)
    torch.save(output_payload, target)
    report = {
        "schema_version": "lunar_ice_bpc.gat_ood_calibration.v1",
        "input_checkpoint": str(Path(args.checkpoint).resolve()),
        "output_checkpoint": str(target.resolve()),
        "checkpoint_id": str(args.checkpoint_id),
        "split_manifest_hash": manifest.get("manifest_hash"),
        "threshold_by_scale": thresholds,
        "calibration_row_count": len(rows),
        "development_used": False,
        "protected_final_test_used": False,
        "checkpoint_weights_changed": False,
        "model_selection_reopened": False,
        "static_tensor_cache_entry_count": len(static_cache),
    }
    report_path = target.with_suffix(target.suffix + ".ood_report.json")
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(str(report_path.resolve()))
    return 0


def _feature_arrays(
    row: dict, *, cache_dir: Path, cache: dict[str, dict]
) -> tuple[list, list]:
    if row.get("node_features") is not None:
        return row["node_features"], row["edge_features"]
    key = str(row.get("static_tensor_cache_key") or "")
    if not key or key != str(row.get("instance_content_hash") or ""):
        raise SystemExit("calibration row/static tensor identity mismatch")
    payload = cache.get(key)
    if payload is None:
        path = cache_dir / f"{key}.json"
        if not path.exists():
            raise SystemExit(f"static tensor sidecar missing: {key}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        observed_hash = str(
            payload.get("static_tensor_cache_hash") or ""
        )
        unsigned = dict(payload)
        unsigned.pop("static_tensor_cache_hash", None)
        if (
            str(payload.get("instance_content_hash") or "") != key
            or stable_payload_hash(unsigned) != observed_hash
        ):
            raise SystemExit(f"stale static tensor sidecar rejected: {key}")
        cache[key] = payload
    if str(row.get("static_tensor_cache_hash") or "") != str(
        payload["static_tensor_cache_hash"]
    ):
        raise SystemExit("calibration row/static tensor hash mismatch")
    dynamic = list(row.get("dynamic_node_features") or ())
    static_node = list(payload["node_static_features"])
    if len(dynamic) != len(static_node):
        raise SystemExit("calibration static/dynamic node count mismatch")
    node = [
        [*static_values, *dynamic_values]
        for static_values, dynamic_values in zip(
            static_node, dynamic, strict=True
        )
    ]
    return node, payload["edge_features"]


def _quantile(values, probability: float) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        raise ValueError("quantile requires at least one value")
    index = max(0, min(len(ordered) - 1, ceil(probability * len(ordered)) - 1))
    return ordered[index]


if __name__ == "__main__":
    raise SystemExit(main())
