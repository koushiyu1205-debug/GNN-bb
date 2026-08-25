#!/usr/bin/env python3
"""Predict one frozen heldout action in a fresh process for one V2 model."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from time import perf_counter


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import (  # noqa: E402
    verify_portfolio_freezes,
)
from lunar_ice_bpc.guidance.context_queue_portfolio_snapshot import (  # noqa: E402
    literal_q0_request_from_snapshot,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_runtime_v2 import (  # noqa: E402
    INTERACTION_GAT_EVALUATION_ENV,
    INTERACTION_GAT_MANIFEST_ENV,
    prepare_root_interaction_gat_request_from_environment,
)
from lunar_ice_bpc.guidance.qgr1_supervision import (  # noqa: E402
    QGR1_ACTION_SURFACE_V1,
    QGR1_SUPERVISION_SCHEMA_V1,
)


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_interaction_gat_queue_selector_v2_20260807"
VARIANTS = ("gat", "mlp", "linear", "no_message", "shuffled_topology")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--variant", choices=VARIANTS, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--potential-output", type=Path)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    try:
        verify_portfolio_freezes(run_root, ROOT)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    if bool(_load(run_root / "state.json").get("terminal")):
        raise SystemExit("terminal chain forbids heldout prediction artifacts")
    selection = _load(run_root / "selector_selection.decision.json")
    if selection.get("selected_model_kind") != "gat":
        raise SystemExit("heldout V2 prediction requires the frozen GAT candidate")
    controls = _load(run_root / "selector_controls.freeze.json")
    if not bool(controls.get("frozen_before_heldout")):
        raise SystemExit("heldout controls were not frozen before outcomes")
    instance_path = args.instance.resolve()
    snapshot_path = args.snapshot.resolve()
    manifest_path = args.manifest.resolve()
    data = load_lunar_ice_data(_load(instance_path))
    snapshot = _load(snapshot_path)
    request = literal_q0_request_from_snapshot(data, snapshot)
    started = perf_counter()
    if args.variant == "gat":
        os.environ[INTERACTION_GAT_MANIFEST_ENV] = str(manifest_path)
        os.environ[INTERACTION_GAT_EVALUATION_ENV] = "1"
        selected, telemetry = prepare_root_interaction_gat_request_from_environment(request)
        action = str(telemetry.get("proof_tail_interaction_gat_action") or "Q0")
        prediction = dict(telemetry.get("proof_tail_interaction_gat_predictions") or {})
        ood = bool(telemetry.get("proof_tail_interaction_gat_ood"))
        first_import_ms = float(
            telemetry.get("proof_tail_interaction_gat_torch_first_import_wall_ms") or 0.0
        )
        preparation_sec = float(
            telemetry.get("proof_tail_interaction_gat_total_prepare_wall_ms") or 0.0
        ) / 1000.0
        warm_graph_tensor_inference_ms = sum(float(telemetry.get(key) or 0.0) for key in (
            "proof_tail_interaction_gat_graph_build_wall_ms",
            "proof_tail_interaction_gat_tensorization_wall_ms",
            "proof_tail_interaction_gat_inference_wall_ms",
        ))
    else:
        selected, action, prediction, ood, first_import_ms = _control_action(
            request, args.variant, manifest_path, controls, started
        )
        preparation_sec = perf_counter() - started
        warm_graph_tensor_inference_ms = preparation_sec * 1000.0
    if action not in {"Q0", "QD1", "QB1", "QGR1"}:
        raise SystemExit("heldout V2 model emitted an action outside the frozen universe")
    potential_path = None
    if action == "QGR1":
        if args.potential_output is None:
            raise SystemExit("QGR1 heldout action requires --potential-output")
        if selected.guidance_hints is None:
            selected = _install_manual_qgr1(
                request, manifest_path, started=started
            )
            preparation_sec = perf_counter() - started
        potential_path = args.potential_output.resolve()
        _write_potential(potential_path, data, snapshot, selected.guidance_hints)
    result = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_heldout_action.v2",
        "variant": args.variant,
        "model_kind": (
            args.variant if args.variant in {"gat", "mlp", "linear"} else "gat"
        ),
        "message_passing_variant": args.variant,
        "instance_content_hash": data.instance_content_hash,
        "state_hash": str(snapshot["state_hash"]),
        "selected_action": action,
        "literal_q0_request_identity_preserved": bool(action == "Q0" and selected is request),
        "predictions": prediction,
        "ood": ood,
        "preparation_wall_sec": preparation_sec,
        "torch_first_import_wall_ms": first_import_ms,
        "warm_graph_tensorization_inference_wall_ms": warm_graph_tensor_inference_ms,
        "first_import_load_included": True,
        "potential_path": str(potential_path) if potential_path else None,
        "potential_sha256": _sha256(potential_path) if potential_path else None,
        "manifest_sha256": _sha256(manifest_path),
    }
    _write_once(args.output.resolve(), result)
    return 0


def _control_action(request, variant, manifest_path, controls, started):
    manifest = _load(manifest_path)
    import_started = perf_counter()
    import torch
    import scripts.train_p0v5_context_queue_portfolio_selector as trainer
    from lunar_ice_bpc.exact.core.cuts import stable_payload_hash
    from lunar_ice_bpc.guidance.interaction_gat_queue_v2 import (
        InteractionGATSelector,
        InteractionLinearControl,
        InteractionMLPControl,
        build_interaction_graph,
        interaction_is_ood,
    )
    first_import_ms = (perf_counter() - import_started) * 1000.0
    features = build_interaction_graph(request)
    ood, _reason = interaction_is_ood(features, dict(manifest["feature_envelope"]))
    if ood:
        return request, "Q0", {}, True, first_import_ms
    if variant in {"mlp", "linear"}:
        row = dict(dict(controls["controls"])[variant])
        checkpoint_path = Path(row["checkpoint_path"]).resolve()
        if _sha256(checkpoint_path) != str(row["checkpoint_sha256"]):
            raise SystemExit(f"heldout {variant} checkpoint drift")
        thresholds = dict(row["threshold"])
    else:
        checkpoint_path = Path(manifest["selector_checkpoint_path"]).resolve()
        if _sha256(checkpoint_path) != str(manifest["selector_checkpoint_sha256"]):
            raise SystemExit("heldout GAT topology-control checkpoint drift")
        thresholds = dict(manifest["thresholds"])
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    kind = str(checkpoint["model_kind"])
    classes = {
        "gat": InteractionGATSelector,
        "mlp": InteractionMLPControl,
        "linear": InteractionLinearControl,
    }
    if kind not in classes or (variant in {"no_message", "shuffled_topology"} and kind != "gat"):
        raise SystemExit("heldout control checkpoint kind mismatch")
    model = classes[kind](dict(checkpoint["normalization"]))
    model.load_state_dict(checkpoint["state_dict"], strict=True)
    model.eval()
    torch.set_num_threads(1)
    output = trainer._variant_output(
        model, features,
        None if variant in {"mlp", "linear"} else variant,
    )
    calibrated = trainer._calibrated_output(
        output, dict(checkpoint["probability_calibration"])
    )
    allowed = _allowed_arms(manifest, int(request.data.scale))
    action = trainer._action_from_values(calibrated, thresholds, allowed)
    prediction = {
        arm: {
            "benefit_probability": values["benefit"],
            "conditional_positive_gain": values["gain"],
            "adverse_probability": values["adverse"],
        }
        for arm, values in calibrated.items()
    }
    # Keep a content hash in the execution trace even though controls cannot
    # become candidates.
    prediction["feature_hash"] = stable_payload_hash(features.audit_payload())
    selected = request
    if action in {"QD1", "QB1"}:
        from dataclasses import replace
        selected = replace(request, proof_queue_policy_id=action)
    return selected, action, prediction, False, first_import_ms


def _install_manual_qgr1(request, manifest_path, *, started):
    from lunar_ice_bpc.exact.core.cuts import stable_payload_hash
    from lunar_ice_bpc.guidance.interaction_gat_queue_runtime_v2 import (
        _exact_action_policy_hash,
        _install_qgr1,
    )
    from lunar_ice_bpc.guidance.interaction_gat_queue_v2 import build_interaction_graph

    manifest = _load(manifest_path)
    features = build_interaction_graph(request)
    selector_hash = str(manifest["selector_checkpoint_sha256"])
    selected, _telemetry = _install_qgr1(
        request, manifest_path, manifest,
        stable_payload_hash(features.audit_payload()),
        _exact_action_policy_hash(request), selector_hash,
        {
            "proof_tail_interaction_gat_runtime_enabled": True,
            "proof_tail_interaction_gat_action": "QGR1",
            "proof_tail_interaction_gat_ranker_calls": 0,
        },
        started=started,
    )
    if selected.guidance_hints is None:
        raise SystemExit("frozen heldout QGR1 ranker failed closed")
    return selected


def _allowed_arms(manifest, scale):
    veto = set(manifest.get("forced_veto_arms") or ())
    veto.update(dict(manifest.get("forced_veto_arms_by_scale") or {}).get(str(scale), ()))
    return [
        arm for arm in ("QGR1", "QD1", "QB1")
        if arm not in veto and scale in {
            int(value) for value in dict(manifest["arm_scale_mask"]).get(arm, ())
        }
    ]


def _write_potential(path, data, snapshot, hints):
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_qgr1_depth_residual_potential.v1",
        "source_kind": "frozen_interaction_gat_heldout_qgr1",
        "supervision_schema_version": QGR1_SUPERVISION_SCHEMA_V1,
        "queue_action_surface": QGR1_ACTION_SURFACE_V1,
        "activation_authority": False,
        "development_only": True,
        "deployment_authorized": False,
        "instance_content_hash": data.instance_content_hash,
        "source_state_hash": str(snapshot["state_hash"]),
        "source_engine_hash": str(snapshot["engine_hash"]),
        "source_config_hash": str(snapshot["config_hash"]),
        "source_exact_action_policy_hash": str(snapshot["exact_action_policy_hash"]),
        "task_potentials": dict(hints.task_priorities),
        "arc_potentials": dict(hints.arc_priorities),
        "label_state_coefficients": list(hints.label_state_coefficients),
        "guidance_bucket_width": 1.0e-4,
    }
    payload["potential_id"] = hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":")
    ).encode()).hexdigest()
    _write_once(path, payload)


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_once(path, payload):
    path = Path(path)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != text:
        raise SystemExit(f"immutable V2 heldout prediction drift:{path}")
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
