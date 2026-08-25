#!/usr/bin/env python3
"""Export a hard-zeroed QGR1 residual potential from the frozen V2 ranker."""

from __future__ import annotations

import argparse
import hashlib
import json
from math import isfinite
from pathlib import Path
import sys

import torch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
import scripts.predict_p0v5_qgr1_potential as legacy  # noqa: E402
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import (  # noqa: E402
    verify_portfolio_freezes,
)
from lunar_ice_bpc.guidance.proof_queue_label_state_gat import (  # noqa: E402
    QG2_LABEL_STATE_SCHEMA_V1,
    normalize_qg2_potential_groups,
)
from lunar_ice_bpc.guidance.proof_queue_label_state_gat_v3 import (  # noqa: E402
    load_qg2_v3_checkpoint,
)
from lunar_ice_bpc.guidance.qgr1_residual_supervision_v2 import (  # noqa: E402
    QGR1_RESIDUAL_SUPERVISION_SCHEMA_V2,
)
from lunar_ice_bpc.guidance.qgr1_supervision import (  # noqa: E402
    QGR1_ACTION_SURFACE_V1,
    QGR1_SUPERVISION_SCHEMA_V1,
)


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_interaction_gat_queue_selector_v2_20260807"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    try:
        verify_portfolio_freezes(run_root, ROOT)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    if bool(_load(run_root / "state.json").get("terminal")):
        raise SystemExit("terminal chain forbids QGR1 potential artifacts")
    instance_path = args.instance.resolve()
    snapshot_path = args.snapshot.resolve()
    checkpoint_path = args.checkpoint.resolve()
    data = load_lunar_ice_data(_load(instance_path))
    snapshot = _load(snapshot_path)
    legacy._validate_binding(data, snapshot)
    model, metadata, _normalization = load_qg2_v3_checkpoint(str(checkpoint_path))
    hard_zero = dict(metadata.get("hard_zero_thresholds") or {})
    if (
        str(getattr(model, "model_kind", "")) != "gat"
        or bool(metadata.get("activation_authority"))
        or metadata.get("supervision_schema_version") != QGR1_SUPERVISION_SCHEMA_V1
        or metadata.get("residual_supervision_schema_version")
        != QGR1_RESIDUAL_SUPERVISION_SCHEMA_V2
        or metadata.get("queue_action_surface") != QGR1_ACTION_SURFACE_V1
        or metadata.get("residual_training_contract")
        != "supervised75_neutral25_pressure_weighted.v2"
        or hard_zero.get("quantile") != 0.75
        or not bool(hard_zero.get("frozen_before_wall_outcomes"))
        or any(
            key not in hard_zero or not isfinite(float(hard_zero[key]))
            or float(hard_zero[key]) < 0.0
            for key in ("node", "arc", "state")
        )
    ):
        raise SystemExit("QGR1 V2 checkpoint residual/hard-zero contract mismatch")
    features = legacy._features(data, snapshot)
    torch.set_num_threads(1)
    model.eval()
    with torch.inference_mode():
        output = model(**features.to_tensors())
    raw = (
        output["node_scores"][1:].reshape(-1),
        output["arc_scores"].reshape(-1),
        output["label_state_coefficients"].reshape(-1),
    )
    sparse = tuple(
        torch.where(value.abs() >= float(hard_zero[key]), value, torch.zeros_like(value))
        for key, value in zip(("node", "arc", "state"), raw, strict=True)
    )
    node, arc, state = normalize_qg2_potential_groups(*sparse)
    values = (*node.tolist(), *arc.tolist(), *state.tolist())
    if (
        state.numel() != 15 or not values
        or any(not isfinite(float(value)) for value in values)
        or max(abs(float(value)) for value in values) <= 1.0e-12
    ):
        raise SystemExit("QGR1 V2 potential is zero/nonfinite after hard-zero")
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_qgr1_depth_residual_potential.v1",
        "source_kind": "trained_qgr1_conservative_residual_label_gat_v2",
        "supervision_schema_version": QGR1_SUPERVISION_SCHEMA_V1,
        "residual_supervision_schema_version": QGR1_RESIDUAL_SUPERVISION_SCHEMA_V2,
        "queue_action_surface": QGR1_ACTION_SURFACE_V1,
        "label_state_schema_version": QG2_LABEL_STATE_SCHEMA_V1,
        "activation_authority": False,
        "development_only": True,
        "deployment_authorized": False,
        "instance_content_hash": data.instance_content_hash,
        "source_state_hash": str(snapshot["state_hash"]),
        "source_engine_hash": str(snapshot["engine_hash"]),
        "source_config_hash": str(snapshot["config_hash"]),
        "source_exact_action_policy_hash": str(snapshot["exact_action_policy_hash"]),
        "checkpoint_path": str(checkpoint_path),
        "checkpoint_sha256": _sha256(checkpoint_path),
        "hard_zero_thresholds": hard_zero,
        "task_potentials": dict(zip(features.task_ids, node.tolist(), strict=True)),
        "arc_potentials": dict(zip(features.arc_candidate_ids, arc.tolist(), strict=True)),
        "label_state_coefficients": state.tolist(),
        "guidance_bucket_width": 1.0e-4,
    }
    payload["potential_id"] = hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":")
    ).encode()).hexdigest()
    _write_once(args.output.resolve(), payload)
    return 0


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_once(path, payload):
    path = Path(path)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != text:
        raise SystemExit(f"immutable QGR1 V2 potential drift:{path}")
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
