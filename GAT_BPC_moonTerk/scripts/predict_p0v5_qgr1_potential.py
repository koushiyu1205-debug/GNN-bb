#!/usr/bin/env python3
"""Export one state-bound QGR1 potential from the frozen label GAT."""

from __future__ import annotations

import argparse
import hashlib
import json
from math import isfinite
from pathlib import Path
import sys

import torch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.exact.bpc.pricing.backends.base import (  # noqa: E402
    PRICING_LIFECYCLE_SCOPE_ROOT_CG,
)
from lunar_ice_bpc.exact.core.branching import branch_context_from_payload  # noqa: E402
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.guidance.proof_queue_label_state_gat import (  # noqa: E402
    build_qg2_features, normalize_qg2_potential_groups,
)
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import (  # noqa: E402
    verify_portfolio_freezes,
)
from lunar_ice_bpc.guidance.proof_queue_label_state_gat_v3 import (  # noqa: E402
    load_qg2_v3_checkpoint, normalize_qg2_v3_features,
)
from lunar_ice_bpc.guidance.qgr1_supervision import (  # noqa: E402
    QGR1_ACTION_SURFACE_V1, QGR1_SUPERVISION_SCHEMA_V1,
)
from lunar_ice_bpc.guidance.proof_queue_label_state_gat import (  # noqa: E402
    QG2_LABEL_STATE_SCHEMA_V1,
)


SCHEMA = "lunar_ice_bpc.p0v5_qgr1_depth_residual_potential.v1"
DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_context_queue_portfolio_v1_20260807_r1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args()
    try:
        verify_portfolio_freezes(args.run_root.resolve(), ROOT)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    instance_path = args.instance.resolve()
    snapshot_path = args.snapshot.resolve()
    checkpoint_path = args.checkpoint.resolve()
    data = load_lunar_ice_data(_load(instance_path))
    snapshot = _load(snapshot_path)
    _validate_binding(data, snapshot)
    model, metadata, _normalization = load_qg2_v3_checkpoint(
        str(checkpoint_path)
    )
    if (
        str(getattr(model, "model_kind", "")) != "gat"
        or bool(metadata.get("activation_authority"))
        or metadata.get("supervision_schema_version")
        != QGR1_SUPERVISION_SCHEMA_V1
        or metadata.get("queue_action_surface") != QGR1_ACTION_SURFACE_V1
    ):
        raise SystemExit("QGR1 checkpoint ordering-only contract mismatch")
    features = _features(data, snapshot)
    torch.set_num_threads(1)
    model.eval()
    with torch.inference_mode():
        output = model(**features.to_tensors())
    coefficients = output["label_state_coefficients"].reshape(-1)
    if coefficients.numel() != 15:
        raise SystemExit("QGR1 checkpoint state dimension mismatch")
    node, arc, coefficients = normalize_qg2_potential_groups(
        output["node_scores"][1:].reshape(-1),
        output["arc_scores"].reshape(-1),
        coefficients,
    )
    values = (*node.tolist(), *arc.tolist(), *coefficients.tolist())
    if (
        not values
        or any(not isfinite(float(value)) for value in values)
        or max(abs(float(value)) for value in values) <= 1.0e-12
    ):
        raise SystemExit("QGR1 potential is zero or nonfinite")
    payload = {
        "schema_version": SCHEMA,
        "source_kind": "trained_qgr1_depth_residual_label_gat",
        "supervision_schema_version": QGR1_SUPERVISION_SCHEMA_V1,
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
        "task_potentials": dict(zip(features.task_ids, node.tolist(), strict=True)),
        "arc_potentials": dict(zip(features.arc_candidate_ids, arc.tolist(), strict=True)),
        "label_state_coefficients": coefficients.tolist(),
        "guidance_bucket_width": 1.0e-4,
    }
    payload["potential_id"] = _stable_hash(payload)
    _write_once(args.output.resolve(), payload)
    return 0


def _features(data, snapshot):
    duals = dict(snapshot.get("true_duals") or {})
    trajectory = dict(snapshot.get("trajectory_features") or {})
    return normalize_qg2_v3_features(data, build_qg2_features(
        data,
        cover_duals=dict(duals.get("task_duals") or duals.get("cover") or {}),
        fleet_dual=float(duals.get("fleet_dual") if duals.get("fleet_dual") is not None else duals.get("fleet_limit") or 0.0),
        active_column_count=_optional_int(snapshot.get("active_column_count")),
        active_task_sets=(None if snapshot.get("active_task_sets") is None else tuple(tuple(str(v) for v in row) for row in snapshot["active_task_sets"])),
        round_index=_optional_int(snapshot.get("round")),
        previous_proof_wall_sec=(
            _optional_float(trajectory.get("previous_proof_pass_wall_time"))
            if str(trajectory.get("previous_queue_policy_id") or "") == "Q0"
            else None
        ),
        previous_processed_labels=(
            _optional_int(trajectory.get("previous_proof_processed_labels"))
            if str(trajectory.get("previous_queue_policy_id") or "") == "Q0"
            else None
        ),
        dual_l1_delta_from_previous=_optional_float(trajectory.get("dual_l1_delta_from_previous")),
        branch_decisions=tuple(branch_context_from_payload(snapshot.get("branch_context") or {}).pair_decisions),
        cut_duals=dict(duals.get("cut_duals") or duals.get("cuts") or {}),
        v5_midpoint_wall_sec=_optional_float(snapshot.get("bidirectional_midpoint_prepass_wall_sec")),
        root_lifecycle_scope=str(snapshot.get("pricing_lifecycle_scope") or PRICING_LIFECYCLE_SCOPE_ROOT_CG) == PRICING_LIFECYCLE_SCOPE_ROOT_CG,
    ))


def _validate_binding(data, snapshot):
    if data.instance_content_hash != str(snapshot.get("instance_content_hash") or ""):
        raise SystemExit("QGR1 snapshot instance mismatch")
    for field in ("state_hash", "engine_hash", "config_hash", "exact_action_policy_hash"):
        if not str(snapshot.get(field) or ""):
            raise SystemExit(f"QGR1 snapshot missing {field}")


def _optional_int(value):
    return None if value is None else int(value)


def _optional_float(value):
    return None if value is None else float(value)


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_once(path, payload):
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != text:
        raise SystemExit(f"immutable potential drift:{path}")
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _stable_hash(payload):
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
