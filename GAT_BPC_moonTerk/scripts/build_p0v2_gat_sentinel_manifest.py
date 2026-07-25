#!/usr/bin/env python3
"""Precommit a target-independent sentinel stream for opportunity auditing."""

from __future__ import annotations

import argparse
import json
from math import isfinite
from pathlib import Path

from lunar_ice_bpc.exact.core.cuts import stable_payload_hash


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance-manifest", required=True)
    parser.add_argument("--split-manifest", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--probability",
        action="append",
        required=True,
        metavar="SCALE=P",
        help="Bernoulli instance-selection probability for each scale.",
    )
    parser.add_argument("--seed", type=int, default=20260724)
    args = parser.parse_args()

    instance_manifest = json.loads(
        Path(args.instance_manifest).read_text(encoding="utf-8")
    )
    split_manifest = json.loads(
        Path(args.split_manifest).read_text(encoding="utf-8")
    )
    if not bool((split_manifest.get("audit") or {}).get("passed")):
        raise SystemExit("split manifest audit did not pass")
    probabilities = _parse_probabilities(args.probability)
    development = {
        str(row["instance_content_hash"]): row
        for row in split_manifest.get("development", ())
    }
    forbidden = {
        str(row["instance_content_hash"])
        for partition in ("calibration", "protected_final_test")
        for row in split_manifest.get(partition, ())
    }
    candidates = []
    for row in instance_manifest.get("instances", ()):
        content_hash = str(row.get("instance_content_hash") or "")
        scale = int(row.get("scale") or 0)
        if not bool(row.get("accepted")) or content_hash not in development:
            continue
        if content_hash in forbidden:
            raise SystemExit("protected/calibration instance leaked into sentinel")
        if scale not in probabilities:
            continue
        selection_hash = stable_payload_hash(
            {
                "schema_version": (
                    "lunar_ice_bpc.gat_sentinel_bernoulli_key.v1"
                ),
                "seed": int(args.seed),
                "scale": scale,
                "instance_content_hash": content_hash,
            }
        )
        uniform = int(selection_hash[:16], 16) / float(2**64)
        candidates.append(
            {
                "instance_content_hash": content_hash,
                "instance_id": str(row.get("instance_id") or ""),
                "scale": scale,
                "path": str(row.get("path") or ""),
                "selection_probability": probabilities[scale],
                "selection_uniform": uniform,
                "selected": uniform < probabilities[scale],
                "selection_key_hash": selection_hash,
            }
        )
    missing_scales = sorted(
        set(probabilities).difference(
            int(row["scale"]) for row in candidates
        )
    )
    if missing_scales:
        raise SystemExit(
            "no development candidates for scales "
            + ",".join(str(scale) for scale in missing_scales)
        )
    payload = {
        "schema_version": "lunar_ice_bpc.gat_sentinel_manifest.v1",
        "sampling_design": (
            "pre_action_bernoulli_instance_cluster_all_contexts_v1"
        ),
        "selection_uses_target_or_outcome": False,
        "selection_seed": int(args.seed),
        "probability_by_scale": {
            str(scale): probability
            for scale, probability in sorted(probabilities.items())
        },
        "candidate_instance_count": len(candidates),
        "selected_instance_count": sum(
            bool(row["selected"]) for row in candidates
        ),
        "selected_count_by_scale": {
            str(scale): sum(
                bool(row["selected"]) and int(row["scale"]) == scale
                for row in candidates
            )
            for scale in sorted(probabilities)
        },
        "instances": candidates,
        "split_manifest_hash": str(
            split_manifest.get("manifest_hash") or ""
        ),
        "calibration_used": False,
        "protected_final_test_used": False,
    }
    payload["manifest_hash"] = stable_payload_hash(payload)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(
            payload, ensure_ascii=False, indent=2, sort_keys=True
        )
        + "\n",
        encoding="utf-8",
    )
    print(str(target.resolve()))
    return 0


def _parse_probabilities(rows: list[str]) -> dict[int, float]:
    parsed: dict[int, float] = {}
    for row in rows:
        scale_raw, separator, probability_raw = str(row).partition("=")
        if not separator:
            raise SystemExit(f"invalid probability row {row!r}")
        scale = int(scale_raw)
        probability = float(probability_raw)
        if (
            scale not in {5, 10, 20, 30, 50, 100}
            or not isfinite(probability)
            or probability <= 0.0
            or probability > 1.0
            or scale in parsed
        ):
            raise SystemExit(f"invalid probability row {row!r}")
        parsed[scale] = probability
    return parsed


if __name__ == "__main__":
    raise SystemExit(main())
