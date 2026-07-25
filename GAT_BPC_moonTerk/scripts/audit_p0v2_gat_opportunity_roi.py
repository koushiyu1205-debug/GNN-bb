#!/usr/bin/env python3
"""Block training when sparse guidance cannot amortize its runtime cost."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from lunar_ice_bpc.exact.core.cuts import stable_payload_hash
from lunar_ice_bpc.guidance.opportunity_gate import audit_opportunity_roi


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--observations-jsonl",
        required=True,
        action="append",
        help=(
            "Repeat for immutable opportunity-observation shards. Only rows "
            "marked sentinel estimate population opportunity density."
        ),
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--required-scales", default="20,30")
    parser.add_argument(
        "--minimum-sentinel-contexts-per-scale",
        type=int,
        default=20,
    )
    parser.add_argument(
        "--minimum-sentinel-instances-per-scale",
        type=int,
        default=20,
    )
    parser.add_argument(
        "--minimum-positive-context-fraction-lcb",
        type=float,
        default=0.02,
    )
    parser.add_argument(
        "--minimum-net-gain-sec-per-context-lcb",
        type=float,
        default=0.0,
    )
    parser.add_argument(
        "--maximum-censored-context-fraction",
        type=float,
        default=0.10,
    )
    parser.add_argument("--bootstrap-samples", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20260724)
    args = parser.parse_args()

    sources = tuple(Path(value) for value in args.observations_jsonl)
    source_payloads = tuple(
        (source, source.read_bytes()) for source in sources
    )
    observations = [
        json.loads(line)
        for _, source_bytes in source_payloads
        for line in source_bytes.decode("utf-8").splitlines()
        if line.strip()
    ]
    required_scales = tuple(
        int(value)
        for value in str(args.required_scales).split(",")
        if value.strip()
    )
    report = audit_opportunity_roi(
        observations,
        required_scales=required_scales,
        minimum_sentinel_contexts_per_scale=max(
            1, int(args.minimum_sentinel_contexts_per_scale)
        ),
        minimum_sentinel_instances_per_scale=max(
            1, int(args.minimum_sentinel_instances_per_scale)
        ),
        minimum_positive_context_fraction_lcb=float(
            args.minimum_positive_context_fraction_lcb
        ),
        minimum_net_gain_sec_per_context_lcb=float(
            args.minimum_net_gain_sec_per_context_lcb
        ),
        maximum_censored_context_fraction=float(
            args.maximum_censored_context_fraction
        ),
        bootstrap_samples=max(100, int(args.bootstrap_samples)),
        seed=int(args.seed),
    )
    report.update(
        {
            "observations_jsonl": (
                str(sources[0].resolve())
                if len(sources) == 1
                else ""
            ),
            "observations_jsonl_paths": [
                str(source.resolve()) for source in sources
            ],
            "observations_jsonl_sha256": (
                hashlib.sha256(source_payloads[0][1]).hexdigest()
                if len(sources) == 1
                else ""
            ),
            "observations_input_bundle_hash": stable_payload_hash(
                [
                    {
                        "path": str(source.resolve()),
                        "sha256": hashlib.sha256(source_bytes).hexdigest(),
                    }
                    for source, source_bytes in source_payloads
                ]
            ),
            "observations_payload_hash": stable_payload_hash(observations),
        }
    )
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(
            report, ensure_ascii=False, indent=2, sort_keys=True
        )
        + "\n",
        encoding="utf-8",
    )
    print(str(target.resolve()))
    return 0 if bool(report["passed"]) else 2


if __name__ == "__main__":
    raise SystemExit(main())
