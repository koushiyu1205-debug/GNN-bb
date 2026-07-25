#!/usr/bin/env python3
"""Fail closed when ordering actions have no measurable oracle headroom."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from lunar_ice_bpc.exact.core.cuts import stable_payload_hash
from lunar_ice_bpc.guidance.trajectory_targets import (
    audit_oracle_headroom,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--records-jsonl",
        required=True,
        action="append",
        help=(
            "Repeat to audit several development-only record shards. "
            "Formal training binding still requires a single materialized "
            "JSONL."
        ),
    )
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--required-scales",
        default="20,30",
        help="Comma-separated scales that must show positive oracle headroom.",
    )
    parser.add_argument(
        "--minimum-contexts-per-scale", type=int, default=20
    )
    parser.add_argument(
        "--minimum-mean-oracle-gain-lcb", type=float, default=0.005
    )
    parser.add_argument(
        "--minimum-positive-context-fraction-lcb",
        type=float,
        default=0.10,
    )
    parser.add_argument("--bootstrap-samples", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20260724)
    parser.add_argument(
        "--allow-non-native-event-time",
        action="store_true",
        help=(
            "Diagnostic only. Reports produced with this option cannot "
            "authorize formal training."
        ),
    )
    args = parser.parse_args()

    sources = tuple(Path(value) for value in args.records_jsonl)
    source_payloads = tuple(
        (source, source.read_bytes()) for source in sources
    )
    records = [
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
    report = audit_oracle_headroom(
        records,
        required_scales=required_scales,
        minimum_contexts_per_scale=max(
            1, int(args.minimum_contexts_per_scale)
        ),
        minimum_mean_oracle_gain_lcb=float(
            args.minimum_mean_oracle_gain_lcb
        ),
        minimum_positive_context_fraction_lcb=float(
            args.minimum_positive_context_fraction_lcb
        ),
        bootstrap_samples=max(100, int(args.bootstrap_samples)),
        seed=int(args.seed),
        require_native_event_trace=not bool(
            args.allow_non_native_event_time
        ),
    )
    report.update(
        {
            "records_jsonl": (
                str(sources[0].resolve())
                if len(sources) == 1
                else ""
            ),
            "records_jsonl_paths": [
                str(source.resolve()) for source in sources
            ],
            "records_jsonl_sha256": (
                hashlib.sha256(source_payloads[0][1]).hexdigest()
                if len(source_payloads) == 1
                else ""
            ),
            "records_input_bundle_hash": stable_payload_hash(
                [
                    {
                        "path": str(source.resolve()),
                        "sha256": hashlib.sha256(source_bytes).hexdigest(),
                    }
                    for source, source_bytes in source_payloads
                ]
            ),
            "records_payload_hash": stable_payload_hash(records),
            "diagnostic_non_native_event_time_allowed": bool(
                args.allow_non_native_event_time
            ),
        }
    )
    if args.allow_non_native_event_time:
        report["passed"] = False
        report["training_authorized"] = False
        report["failure_action"] = (
            "diagnostic_only_non_native_event_time_cannot_authorize_training"
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
