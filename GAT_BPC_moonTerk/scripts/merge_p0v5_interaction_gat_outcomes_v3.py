#!/usr/bin/env python3
"""Merge fresh V3 arm matrices without synthesizing or overwriting rows."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import (  # noqa: E402
    verify_portfolio_freezes,
)
from lunar_ice_bpc.guidance.context_queue_portfolio_gates import (  # noqa: E402
    MatchedContextOutcome,
    collapse_matched_matrix,
)

DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_interaction_gat_queue_selector_v3_20260814"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    verify_portfolio_freezes(run_root, ROOT)
    state = json.loads((run_root / "state.json").read_text(encoding="utf-8"))
    if bool(state.get("terminal")):
        raise SystemExit("terminal V3 chain forbids outcome merge writer")
    config = json.loads((run_root / "config.freeze.json").read_text(encoding="utf-8"))
    merged = {}
    sources = []
    for value in args.inputs:
        path = value.resolve()
        payload = json.loads(path.read_text(encoding="utf-8"))
        sources.append({"path": str(path), "sha256": _sha256(path)})
        if payload.get("schema_version") == (
            "lunar_ice_bpc.p0v5_interaction_gat_collapsed_outcome_bundle.v3"
        ):
            outcomes = []
            for raw in payload.get("rows") or ():
                row = dict(raw)
                row["correctness_redlines"] = tuple(row.get("correctness_redlines") or ())
                outcomes.append(MatchedContextOutcome(**row))
        else:
            outcomes = collapse_matched_matrix(
                payload.get("rows") or (),
                caps_by_scale=config["execution"]["replay_caps_sec"],
                required_repeats=3,
            )
        for outcome in outcomes:
            key = (outcome.context_id, outcome.arm)
            row = asdict(outcome)
            if key in merged and merged[key] != row:
                raise SystemExit(f"V3 duplicate collapsed outcome drift:{key}")
            merged[key] = row
    result = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_collapsed_outcome_bundle.v3",
        "fresh_repeats_collapsed_inside_source_matrix": True,
        "fresh_rows_only": True, "synthetic_rows": 0,
        "sources": sources,
        "rows": [merged[key] for key in sorted(merged)],
    }
    _write_once(args.output.resolve(), result)
    print(json.dumps({"row_count": len(merged), "output": str(args.output.resolve())}, indent=2))
    return 0


def _write_once(path, payload):
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != encoded:
        raise SystemExit(f"immutable V3 merged outcome differs:{path}")
    if not path.exists(): path.write_text(encoded, encoding="utf-8")


def _sha256(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__": raise SystemExit(main())
