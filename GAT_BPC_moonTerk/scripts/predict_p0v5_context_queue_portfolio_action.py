#!/usr/bin/env python3
"""Select one heldout action in a fresh process without executing Native."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import (  # noqa: E402
    verify_portfolio_freezes,
)
from lunar_ice_bpc.guidance.context_queue_portfolio_runtime import (  # noqa: E402
    PORTFOLIO_EVALUATION_ENV, PORTFOLIO_MANIFEST_ENV,
    prepare_context_queue_portfolio_request_from_environment,
)
from lunar_ice_bpc.guidance.context_queue_portfolio_snapshot import (  # noqa: E402
    literal_q0_request_from_snapshot,
)
from lunar_ice_bpc.guidance.qgr1_supervision import (  # noqa: E402
    QGR1_ACTION_SURFACE_V1, QGR1_SUPERVISION_SCHEMA_V1,
)


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_context_queue_portfolio_v1_20260807_r1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--potential-output", type=Path)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    try:
        verify_portfolio_freezes(run_root, ROOT)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    instance_path = args.instance.resolve()
    snapshot_path = args.snapshot.resolve()
    manifest_path = args.manifest.resolve()
    data = load_lunar_ice_data(_load(instance_path))
    snapshot = _load(snapshot_path)
    request = literal_q0_request_from_snapshot(data, snapshot)
    os.environ[PORTFOLIO_MANIFEST_ENV] = str(manifest_path)
    os.environ[PORTFOLIO_EVALUATION_ENV] = "1"
    selected, telemetry = prepare_context_queue_portfolio_request_from_environment(
        request
    )
    action = str(telemetry.get("proof_tail_portfolio_action") or "Q0")
    if action not in {"Q0", "QD1", "QB1", "QGR1"}:
        raise SystemExit("selector emitted action outside frozen universe")
    potential_path = None
    if action == "QGR1":
        if args.potential_output is None or selected.guidance_hints is None:
            raise SystemExit("selected QGR1 requires potential output")
        potential_path = args.potential_output.resolve()
        hints = selected.guidance_hints
        potential = {
            "schema_version": "lunar_ice_bpc.p0v5_qgr1_depth_residual_potential.v1",
            "source_kind": "frozen_context_selector_qgr1",
            "supervision_schema_version": QGR1_SUPERVISION_SCHEMA_V1,
            "queue_action_surface": QGR1_ACTION_SURFACE_V1,
            "activation_authority": False,
            "development_only": True,
            "deployment_authorized": False,
            "instance_content_hash": data.instance_content_hash,
            "source_state_hash": str(snapshot["state_hash"]),
            "source_engine_hash": str(snapshot["engine_hash"]),
            "source_config_hash": str(snapshot["config_hash"]),
            "source_exact_action_policy_hash": str(
                snapshot["exact_action_policy_hash"]
            ),
            "task_potentials": dict(hints.task_priorities),
            "arc_potentials": dict(hints.arc_priorities),
            "label_state_coefficients": list(hints.label_state_coefficients),
            "guidance_bucket_width": 1.0e-4,
        }
        potential["potential_id"] = _stable_hash(potential)
        _write_once(potential_path, potential)
    result = {
        "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_action_prediction.v1",
        "instance_content_hash": data.instance_content_hash,
        "state_hash": str(snapshot["state_hash"]),
        "selected_action": action,
        "literal_q0_request_identity_preserved": selected is request,
        "selector_telemetry": telemetry,
        "preparation_wall_sec": float(
            telemetry.get("proof_tail_portfolio_total_prepare_wall_ms") or 0.0
        ) / 1000.0,
        "potential_path": str(potential_path) if potential_path else None,
        "potential_sha256": _sha256(potential_path) if potential_path else None,
        "manifest_sha256": _sha256(manifest_path),
    }
    _write_once(args.output.resolve(), result)
    return 0


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_once(path, payload):
    path = Path(path)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != text:
        raise SystemExit(f"immutable selector prediction drift:{path}")
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _stable_hash(payload):
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":")
    ).encode()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
