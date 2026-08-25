#!/usr/bin/env python3
"""Run force-on after restoring frozen snapshot identity on context rows.

The trace-only compatibility view intentionally carried engine/config/action
identity on ``initial_rows`` but not ``context_rows``.  The frozen force-on
runner constructs its local contexts from the latter.  This wrapper restores
the three immutable values from the already-bound fallback snapshot before
the original hash checks run; it does not relax or replace any check.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
FROZEN_WRAPPER = (
    ROOT / "scripts/calibrate_p0v5_qg2_v4_instance_balanced_gat_force_on.py"
)


def main() -> int:
    wrapper = _load_wrapper()
    original = wrapper._instance_balanced_context_order

    def context_order(rows, *, maximum_per_scale: int):
        enriched = [_enrich(dict(row)) for row in rows]
        return original(enriched, maximum_per_scale=maximum_per_scale)

    wrapper._instance_balanced_context_order = context_order
    returncode = int(wrapper.main())
    output = wrapper._argument_path("--output")
    if output is not None and output.is_file():
        payload = json.loads(output.read_text(encoding="utf-8"))
        payload.update({
            "trace_view_identity_repair": (
                "restored_from_hash_bound_fallback_snapshot.v1"
            ),
            "identity_checks_relaxed": False,
            "engine_config_action_policy_hash_checks_retained": True,
        })
        wrapper._write(output, payload)
    return returncode


def _enrich(row: dict) -> dict:
    snapshot_path = Path(str(row.get("snapshot_path") or ""))
    if not snapshot_path.is_absolute():
        snapshot_path = (ROOT / snapshot_path).resolve()
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    if (
        str(snapshot.get("state_hash") or "")
        != str(row.get("state_hash") or "")
        or not str(snapshot.get("engine_hash") or "")
        or not str(snapshot.get("config_hash") or "")
        or not str(snapshot.get("exact_action_policy_hash") or "")
    ):
        raise SystemExit("trace-view force-on snapshot identity mismatch")
    row.update({
        "source_engine_hash": str(snapshot["engine_hash"]),
        "source_config_hash": str(snapshot["config_hash"]),
        "source_exact_action_policy_hash": str(
            snapshot["exact_action_policy_hash"]
        ),
    })
    return row


def _load_wrapper():
    spec = importlib.util.spec_from_file_location(
        "p0v5_qg2_v5_frozen_instance_force", FROZEN_WRAPPER
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen instance-balanced force wrapper")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    raise SystemExit(main())
