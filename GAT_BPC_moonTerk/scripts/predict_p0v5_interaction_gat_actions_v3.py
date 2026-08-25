#!/usr/bin/env python3
"""Freeze all five heldout actions before reading any heldout arm outcome."""

from __future__ import annotations

import argparse
import hashlib
import json
from math import exp, log
from pathlib import Path
import subprocess
import sys
from time import perf_counter

import torch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
import scripts.build_p0v5_context_queue_portfolio_training_dataset as v1  # noqa: E402
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import verify_portfolio_freezes  # noqa: E402
from lunar_ice_bpc.guidance.context_queue_portfolio_v1 import PORTFOLIO_ARMS  # noqa: E402
from lunar_ice_bpc.guidance.interaction_gat_queue_v2 import (  # noqa: E402
    build_interaction_graph, interaction_is_ood, interaction_parameter_count,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_v3 import (  # noqa: E402
    INTERACTION_CHECKPOINT_SCHEMA_V2, build_model_v3, features_for_model_kind,
)


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_interaction_gat_queue_selector_v3_20260814"
MODEL_KINDS = ("gat", "mlp", "linear", "no_message", "shuffled_topology")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    _verify_active(run_root)
    selection = _load(run_root / "selector_selection.decision.json")
    controls = _load(run_root / "selector_controls.freeze.json")["controls"]
    manifest = _load(Path(selection["heldout_manifest"]))
    envelope = _load(Path(manifest["ood_envelope_path"]))
    model_specs = {
        "gat": {
            "checkpoint_path": selection["selected_checkpoint"],
            "checkpoint_sha256": selection["selected_checkpoint_sha256"],
            "thresholds": selection["selected_threshold"],
            "allowed_arms_by_scale": {
                str(scale): [arm for arm, scales in manifest["arm_scale_mask"].items()
                             if scale in {int(value) for value in scales}]
                for scale in (30, 50)
            },
        },
        **{kind: dict(controls[kind]) for kind in controls},
    }
    if set(model_specs) != set(MODEL_KINDS):
        raise SystemExit("V3 heldout requires five frozen models")
    if len({row["checkpoint_sha256"] for row in model_specs.values()}) != 5:
        raise SystemExit("V3 topology/simple controls lack independent checkpoints")
    torch_first_import_ms = _fresh_torch_import_ms()
    models = {}
    load_ms = {}
    for kind, spec in model_specs.items():
        started = perf_counter()
        models[kind] = _load_model(kind, spec)
        load_ms[kind] = (perf_counter() - started) * 1000.0
    corpus = _load(run_root / "corpus.freeze.json")
    contexts = [row for row in corpus["rows"] if row["partition"] == "selector_heldout"]
    if {scale: sum(int(row["scale"]) == scale for row in contexts) for scale in (30, 50)} != {30: 6, 50: 10}:
        raise SystemExit("V3 heldout context count drift")
    rows = []
    torch.set_num_threads(1)
    for context in contexts:
        actions = {}
        for kind in MODEL_KINDS:
            graph_started = perf_counter()
            snapshot = _load(Path(context["snapshot_path"]))
            request = v1._request(context, snapshot)
            features = build_interaction_graph(request)
            graph_ms = (perf_counter() - graph_started) * 1000.0
            ood, ood_reason = interaction_is_ood(features, envelope)
            if ood:
                actions[kind] = {
                    "action": "Q0", "reason": ood_reason, "ood": True,
                    "graph_build_ms": graph_ms, "tensorization_ms": 0.0,
                    "inference_ms": 0.0, "checkpoint_load_ms": load_ms[kind],
                    "torch_first_import_ms": torch_first_import_ms,
                    "total_preparation_ms": graph_ms + load_ms[kind] + torch_first_import_ms,
                    "predictions": {},
                }
                continue
            feature = features_for_model_kind(
                features, model_kind=kind, state_hash=context["state_hash"]
            )
            tensor_started = perf_counter()
            tensors = feature.to_tensors()
            tensor_ms = (perf_counter() - tensor_started) * 1000.0
            infer_started = perf_counter()
            with torch.inference_mode():
                output = models[kind][0](**tensors)
            inference_ms = (perf_counter() - infer_started) * 1000.0
            predictions = _calibrated(output, models[kind][1]["probability_calibration"])
            allowed = list(dict(model_specs[kind].get("allowed_arms_by_scale") or {}).get(
                str(context["scale"]), ()
            ))
            action = _choose(predictions, model_specs[kind]["thresholds"], allowed)
            actions[kind] = {
                "action": action, "reason": "frozen_threshold", "ood": False,
                "graph_build_ms": graph_ms, "tensorization_ms": tensor_ms,
                "inference_ms": inference_ms,
                "checkpoint_load_ms": load_ms[kind],
                "torch_first_import_ms": torch_first_import_ms,
                "total_preparation_ms": (
                    graph_ms + tensor_ms + inference_ms + load_ms[kind]
                    + torch_first_import_ms
                ),
                "predictions": predictions,
            }
        union = sorted({"Q0", *(row["action"] for row in actions.values())})
        rows.append({
            "context_id": context["context_id"],
            "instance_hash": context["instance_content_hash"],
            "scale": int(context["scale"]), "state_hash": context["state_hash"],
            "actions": actions, "distinct_action_union": union,
        })
    freeze = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_heldout_action_freeze.v3",
        "status": "FROZEN_BEFORE_ANY_SELECTOR_HELDOUT_ARM_OUTCOME",
        "models": list(MODEL_KINDS),
        "all_models_independently_trained": True,
        "model_specs": model_specs,
        "heldout_outcomes_read": 0, "formal_outcomes_read": 0,
        "rows": rows,
    }
    _write_once(run_root / "selector_heldout_actions.freeze.json", freeze)
    print(json.dumps({
        "contexts": len(rows),
        "distinct_replay_tasks_per_repeat": sum(len(row["distinct_action_union"]) for row in rows),
        "heldout_outcomes_read": 0,
    }, ensure_ascii=False, indent=2))
    return 0


def _load_model(kind, spec):
    path = Path(str(spec["checkpoint_path"])).resolve()
    if not path.is_file() or _sha256(path) != str(spec["checkpoint_sha256"]):
        raise SystemExit(f"V3 {kind} checkpoint drift")
    checkpoint = torch.load(path, map_location="cpu", weights_only=False)
    if (
        checkpoint.get("schema_version") != INTERACTION_CHECKPOINT_SCHEMA_V2
        or checkpoint.get("model_kind") != kind
        or not bool(checkpoint.get("independently_trained"))
    ):
        raise SystemExit(f"V3 {kind} checkpoint contract mismatch")
    model = build_model_v3(kind, checkpoint["normalization"])
    model.load_state_dict(checkpoint["state_dict"], strict=True)
    if int(checkpoint["parameter_count"]) != interaction_parameter_count(model):
        raise SystemExit(f"V3 {kind} parameter binding drift")
    model.eval()
    return model, checkpoint


def _fresh_torch_import_ms():
    completed = subprocess.run([
        sys.executable, "-c",
        "from time import perf_counter as p;s=p();import torch;print((p()-s)*1000.0)",
    ], cwd=ROOT, check=True, text=True, stdout=subprocess.PIPE)
    value = float(completed.stdout.strip())
    if value < 0.0:
        raise SystemExit("fresh Torch import timing is invalid")
    return value


def _calibrated(output, calibration):
    result = {}
    for index, arm in enumerate(PORTFOLIO_ARMS):
        benefit = _platt(float(output["benefit_probability"][0, index]), calibration["benefit"][arm])
        adverse = _platt(float(output["adverse_probability"][0, index]), calibration["adverse"][arm])
        gain = float(output["conditional_positive_gain"][0, index]) * float(
            calibration["positive_gain_scale"][arm]
        )
        result[arm] = {"benefit": benefit, "adverse": adverse, "gain": gain}
    return result


def _choose(predictions, thresholds, allowed):
    options = []
    for arm in allowed:
        row = predictions[arm]
        expected = row["benefit"] * row["gain"]
        score = expected - float(thresholds["risk_penalty"]) * row["adverse"]
        if (
            row["benefit"] >= float(thresholds["minimum_benefit_probability"])
            and row["adverse"] <= float(thresholds["maximum_adverse_probability"])
            and expected >= float(thresholds["minimum_expected_gain"]) and score > 0.0
        ):
            options.append((score, arm))
    return max(options, default=(0.0, "Q0"))[1]


def _platt(value, row):
    value = min(1.0 - 1.0e-7, max(1.0e-7, value))
    score = float(row["slope"]) * log(value / (1.0 - value)) + float(row["intercept"])
    return 1.0 / (1.0 + exp(-max(-40.0, min(40.0, score))))


def _verify_active(run_root):
    verify_portfolio_freezes(run_root, ROOT)
    if bool(_load(run_root / "state.json").get("terminal")):
        raise SystemExit("terminal V3 chain forbids heldout action freeze")


def _write_once(path, payload):
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != encoded:
        raise SystemExit(f"immutable V3 heldout action drift:{path}")
    if not path.exists():
        path.write_text(encoded, encoding="utf-8")


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
