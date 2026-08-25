#!/usr/bin/env python3
"""Merge staged rows while keeping the primary matched Q0 comparator."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import (  # noqa: E402
    verify_portfolio_freezes,
)


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_context_queue_portfolio_v1_20260807_r1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--primary", type=Path, required=True)
    parser.add_argument("--additional", type=Path, nargs="*", default=[])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args()
    try:
        verify_portfolio_freezes(args.run_root.resolve(), ROOT)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    sources = [args.primary.resolve(), *(path.resolve() for path in args.additional)]
    merged, keys = [], set()
    for source_index, source in enumerate(sources):
        payload = _load(source)
        for raw in payload.get("rows") or ():
            row = dict(raw)
            key = (str(row["context_id"]), str(row["arm"]), int(row["repeat"]))
            if key in keys:
                if source_index > 0 and str(row["arm"]) == "Q0":
                    continue
                raise SystemExit(f"duplicate non-comparator outcome:{key}")
            keys.add(key)
            merged.append(row)
    output = {
        "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_complete_rows.v1",
        "q0_comparator_source": str(sources[0]),
        "q0_comparator_source_sha256": _sha256(sources[0]),
        "sources": [{"path": str(path), "sha256": _sha256(path)} for path in sources],
        "rows": sorted(merged, key=lambda row: (
            int(row["scale"]), str(row["context_id"]),
            str(row["arm"]), int(row["repeat"]),
        )),
    }
    _write_once(args.output.resolve(), output)
    return 0


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _write_once(path, payload):
    path = Path(path)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != text:
        raise SystemExit(f"immutable merged outcome drift:{path}")
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
