#!/usr/bin/env python3
"""Audit the no-model scale rule on a frozen proof-tail gate dataset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from lunar_ice_bpc.guidance.proof_tail_gate import (
    audit_static_proof_tail_scale_rule,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--minimum-contexts-per-scale",
        type=int,
        default=20,
    )
    args = parser.parse_args()

    dataset = json.loads(
        Path(args.dataset).read_text(encoding="utf-8")
    )
    audit = audit_static_proof_tail_scale_rule(
        dataset,
        minimum_contexts_per_scale=int(
            args.minimum_contexts_per_scale
        ),
    )
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    print(str(target.resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
