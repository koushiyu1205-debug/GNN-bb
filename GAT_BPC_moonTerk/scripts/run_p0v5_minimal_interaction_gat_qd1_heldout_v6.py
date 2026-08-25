#!/usr/bin/env python3
"""One-shot shared-action heldout validation for all frozen V6 models."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter

import torch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
import scripts.build_p0v5_context_queue_portfolio_training_dataset as dataset_v1  # noqa: E402
import scripts.run_p0v5_context_queue_portfolio_matrix as matrix_v1  # noqa: E402
from scripts.p0v5_minimal_interaction_gat_qd1_v6_common import (  # noqa: E402
    DEFAULT_RUN_ROOT, assert_active, geometric_mean, load, sha256, terminal,
    update_state, verify_freezes, write_once,
)
from lunar_ice_bpc.guidance.context_queue_portfolio_gates import (  # noqa: E402
    rotate_blocked_arm_order,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_gates_v4 import (  # noqa: E402
    collapse_censor_aware_matrix,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_runtime_v6 import (  # noqa: E402
    _choose_action_v6, _predictions_v6,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_v2 import (  # noqa: E402
    build_interaction_graph, interaction_is_ood,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_v6 import (  # noqa: E402
    build_model_v6, features_for_model_kind_v6,
)


REPLAY = ROOT / "scripts/replay_p0v5_qg2_label_state_snapshot.py"
MODELS = ("gat", "mlp", "linear", "no_message", "shuffled_topology")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("predict", "milestone", "freeze", "run", "analyze"))
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    assert_active(run_root)
    verify_freezes(run_root)
    if load(run_root / "state.json").get("current_stage") != "SELECTOR_HELDOUT_FRESH":
        raise SystemExit("V6 heldout writer is not authorized in current stage")
    return {
        "predict": _predict, "milestone": _milestone, "freeze": _freeze,
        "run": _run, "analyze": _analyze,
    }[args.mode](run_root)


def _predict(run_root):
    manifest = load(run_root / "selector_heldout_candidate.manifest.json")
    controls = load(run_root / "selector_controls.freeze.json")["controls"]
    specs = {
        "gat": {
            "checkpoint_path": manifest["selector_checkpoint_path"],
            "checkpoint_sha256": manifest["selector_checkpoint_sha256"],
            "thresholds_by_scale": manifest["thresholds_by_scale"],
        },
        **controls,
    }
    envelope = manifest["feature_envelope"]
    corpus = [
        row for row in load(run_root / "corpus.freeze.json")["rows"]
        if row["partition"] == "selector_heldout"
    ]
    import_started = perf_counter()
    imported = subprocess.run(
        [sys.executable, "-c", "import torch"], cwd=ROOT, check=False,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    if imported.returncode:
        raise SystemExit("fresh heldout Torch import measurement failed")
    cold_import_ms = (perf_counter() - import_started) * 1000.0
    actions = []
    for kind in MODELS:
        spec = specs[kind]
        checkpoint_path = Path(str(spec["checkpoint_path"])).resolve()
        if sha256(checkpoint_path) != str(spec["checkpoint_sha256"]):
            raise SystemExit(f"V6 heldout checkpoint drift:{kind}")
        load_started = perf_counter()
        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        model = build_model_v6(kind, checkpoint["normalization"])
        model.load_state_dict(checkpoint["state_dict"], strict=True)
        model.eval()
        load_ms = (perf_counter() - load_started) * 1000.0
        thresholds_by_scale = dict(spec.get("thresholds_by_scale") or {})
        calibration = checkpoint["probability_calibration"]
        for ordinal, context in enumerate(corpus):
            snapshot = load(context["snapshot_path"])
            graph_started = perf_counter()
            features = build_interaction_graph(dataset_v1._request(context, snapshot))
            graph_ms = (perf_counter() - graph_started) * 1000.0
            ood, reason = interaction_is_ood(features, envelope)
            inference_ms = 0.0
            scale_key = str(int(context["scale"]))
            if ood or not thresholds_by_scale.get(scale_key):
                action, predictions = "Q0", {}
                decision_reason = reason if ood else "control_noop_scale"
            else:
                selected_features = features_for_model_kind_v6(
                    features, model_kind=kind, state_hash=context["state_hash"]
                )
                started = perf_counter()
                with torch.inference_mode():
                    output = model(**selected_features.to_tensors())
                inference_ms = (perf_counter() - started) * 1000.0
                predictions = _predictions_v6(output, calibration)
                local_manifest = {
                    "thresholds_by_scale": thresholds_by_scale,
                    "arm_scale_mask": {"QD1": [30, 50]},
                    "forced_veto_arms": [], "forced_veto_arms_by_scale": {},
                }
                action, decision_reason = _choose_action_v6(
                    predictions, local_manifest, int(context["scale"])
                )
            actions.append({
                "model_kind": kind, "context_id": context["context_id"],
                "instance_hash": context["instance_content_hash"],
                "scale": int(context["scale"]), "state_hash": context["state_hash"],
                "selected_action": action, "decision_reason": decision_reason,
                "predictions": predictions, "ood": ood,
                "graph_build_ms": graph_ms, "inference_ms": inference_ms,
                "torch_first_import_ms": cold_import_ms if ordinal == 0 else 0.0,
                "checkpoint_load_ms": load_ms if ordinal == 0 else 0.0,
                "total_preparation_ms": graph_ms + inference_ms + (
                    load_ms + cold_import_ms if ordinal == 0 else 0.0
                ),
            })
    write_once(run_root / "selector_heldout_actions.freeze.json", {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_qd1_heldout_actions.v1",
        "frozen_before_heldout_arm_outcomes": True,
        "all_controls_independently_trained": True, "rows": actions,
    })
    return 0


def _milestone(run_root):
    config = load(run_root / "config.freeze.json")
    corpus = [
        row for row in load(run_root / "corpus.freeze.json")["rows"]
        if row["partition"] == "selector_heldout"
    ]
    raw_dir = run_root / "selector_heldout_milestone_raw"
    raw_dir.mkdir(exist_ok=True)
    rows = {}
    for context in corpus:
        output = raw_dir / f"{context['context_id']}_Q0.json"
        if not output.is_file():
            _replay(config, run_root, context, "Q0", output, repeat=0)
        raw = load(output)
        reached = bool(raw.get("milestone_reached"))
        status = str(raw.get("engine_status") or "")
        eligible = (
            reached and status not in {"TIMEOUT", "MEMORY_LIMIT"}
            and not bool(raw.get("labels_dropped"))
        )
        rows[context["context_id"]] = {
            "context_id": context["context_id"],
            "instance_hash": context["instance_content_hash"],
            "scale": context["scale"], "replay_eligible": eligible,
            "q0_status": status,
            "target_milestone_kind": raw.get("milestone_kind") if reached else None,
            "raw_path": str(output), "raw_sha256": sha256(output),
        }
    write_once(run_root / "selector_heldout_milestone.freeze.json", {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_qd1_heldout_milestone.v1",
        "frozen_before_heldout_arm_outcomes": True, "by_context": rows,
    })
    return 0


def _freeze(run_root):
    actions = load(run_root / "selector_heldout_actions.freeze.json")["rows"]
    milestone = load(run_root / "selector_heldout_milestone.freeze.json")["by_context"]
    if any(not row["replay_eligible"] for row in milestone.values()):
        return terminal(run_root, "HELDOUT_FRESH_FAILED", "heldout Q0 milestone censor")
    config = load(run_root / "config.freeze.json")
    corpus = {
        row["context_id"]: row for row in load(run_root / "corpus.freeze.json")["rows"]
    }
    selected_by_context = defaultdict(set)
    for row in actions:
        selected_by_context[row["context_id"]].add(row["selected_action"])
    tasks = []
    for context_id, selected in sorted(selected_by_context.items()):
        context = corpus[context_id]
        arms = ("Q0", "QD1") if "QD1" in selected else ("Q0",)
        for block, order in enumerate(rotate_blocked_arm_order(
            context["state_hash"], arms=arms, repeats=3
        )):
            for ordinal, arm in enumerate(order):
                tasks.append({
                    "context_id": context_id,
                    "instance_hash": context["instance_content_hash"],
                    "scale": context["scale"], "partition": "selector_heldout",
                    "state_hash": context["state_hash"], "arm": arm,
                    "block": block, "ordinal_in_block": ordinal,
                    "cap_sec": config["execution"]["replay_caps_sec"][str(context["scale"])],
                    "memory_limit_gb": config["execution"]["memory_limit_gb"],
                })
    write_once(run_root / "selector_heldout_execution.freeze.json", {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_qd1_heldout_execution.v1",
        "frozen_after_actions_before_arm_outcomes": True,
        "action_freeze_sha256": sha256(run_root / "selector_heldout_actions.freeze.json"),
        "milestone_freeze_sha256": sha256(run_root / "selector_heldout_milestone.freeze.json"),
        "single_native_process": True, "tasks": tasks,
    })
    return 0


def _run(run_root):
    config = load(run_root / "config.freeze.json")
    schedule = load(run_root / "selector_heldout_execution.freeze.json")
    corpus = {
        row["context_id"]: row for row in load(run_root / "corpus.freeze.json")["rows"]
    }
    milestone = load(run_root / "selector_heldout_milestone.freeze.json")["by_context"]
    directory = run_root / "selector_heldout_raw"
    directory.mkdir(exist_ok=True)
    rows = []
    for task in schedule["tasks"]:
        context = corpus[task["context_id"]]
        output = directory / f"{task['context_id']}_b{task['block']}_{task['arm']}.json"
        if not output.is_file():
            _replay(
                config, run_root, context, task["arm"], output,
                repeat=int(task["block"]) + 1,
            )
        raw = load(output)
        task_for_base = {**task, "execution_policy": task["arm"]}
        matrix_v1._validate_raw_binding(raw, task_for_base, context)
        rows.append(matrix_v1._matrix_row(
            task_for_base, context, raw, output, milestone[task["context_id"]]
        ))
    matrix_v1._add_cross_arm_redlines(rows)
    write_once(run_root / "selector_heldout_rows.json", {
        "schema_version": "lunar_ice_bpc.p0v5_censor_aware_matched_rows.v1",
        "rows": rows,
    })
    return _analyze(run_root)


def _analyze(run_root):
    config = load(run_root / "config.freeze.json")
    raw_rows = load(run_root / "selector_heldout_rows.json")["rows"]
    outcomes = collapse_censor_aware_matrix(
        raw_rows, caps_by_scale=config["execution"]["replay_caps_sec"],
        required_repeats=3, minimum_comparable_blocks=2,
    )
    by_context_arm = {(row.context_id, row.arm): row for row in outcomes}
    q0_walls = defaultdict(list)
    for row in raw_rows:
        if row["arm"] == "Q0" and row["milestone_reached"]:
            q0_walls[row["context_id"]].append(float(row["solver_wall_sec"]))
    actions = load(run_root / "selector_heldout_actions.freeze.json")["rows"]
    summaries = {}
    for kind in MODELS:
        selected = [row for row in actions if row["model_kind"] == kind]
        by_instance, activated = defaultdict(list), set()
        harmful = adverse = censor = 0
        for action_row in selected:
            action = action_row["selected_action"]
            outcome = by_context_arm.get((action_row["context_id"], action)) if action == "QD1" else None
            determined = action == "Q0" or bool(outcome and outcome.determined)
            ratio = 1.0 if action == "Q0" or not determined else float(outcome.ratio)
            baseline = _median(q0_walls[action_row["context_id"]])
            if baseline > 0:
                ratio += float(action_row["total_preparation_ms"]) / 1000.0 / baseline
            if action == "QD1":
                activated.add(action_row["instance_hash"])
                harmful += int(bool(outcome and outcome.harmful))
                adverse += int(bool(outcome and outcome.adverse))
                censor += int(
                    not determined or bool(outcome and outcome.resource_censor_positive)
                )
            by_instance[action_row["instance_hash"]].append(ratio)
        instance_ratios = {
            key: geometric_mean(values) for key, values in by_instance.items()
        }
        scales = {}
        for scale in (30, 50):
            instances = {
                row["instance_hash"] for row in selected if row["scale"] == scale
            }
            scales[str(scale)] = {
                "activation_instances": len(activated & instances),
                "instance_weighted_gm": geometric_mean(
                    instance_ratios[value] for value in instances
                ),
            }
        summaries[kind] = {
            "scales": scales,
            "combined_gm": geometric_mean(instance_ratios.values()),
            "harmful": harmful, "adverse": adverse, "resource_censor": censor,
            "warm_preparation_p99_ms": _p99([
                row["total_preparation_ms"] for row in selected
                if row["checkpoint_load_ms"] == 0.0
            ]),
        }
    gat = summaries["gat"]
    passed = bool(
        all(
            gat["scales"][str(scale)]["activation_instances"] >= 2
            and gat["scales"][str(scale)]["instance_weighted_gm"] < 1.0
            for scale in (30, 50)
        )
        and gat["harmful"] == gat["adverse"] == gat["resource_censor"] == 0
        and gat["warm_preparation_p99_ms"] <= 10.0
        and all(
            gat["scales"]["50"]["instance_weighted_gm"]
            < summaries[kind]["scales"]["50"]["instance_weighted_gm"]
            for kind in ("mlp", "linear")
        )
        and all(
            gat["scales"]["30"]["instance_weighted_gm"]
            <= summaries[kind]["scales"]["30"]["instance_weighted_gm"]
            for kind in ("mlp", "linear")
        )
        and all(gat["combined_gm"] < summaries[kind]["combined_gm"]
                for kind in ("mlp", "linear"))
        and all(gat["combined_gm"] <= summaries[kind]["combined_gm"]
                for kind in ("no_message", "shuffled_topology"))
        and not any(row.correctness_redlines for row in outcomes)
    )
    decision = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_qd1_heldout_decision.v1",
        "passed": passed, "reason": None if passed else "HELDOUT_FRESH_FAILED",
        "models": summaries, "one_shot_no_reselection": True,
    }
    write_once(run_root / "selector_heldout.decision.json", decision)
    if not passed:
        return terminal(run_root, "HELDOUT_FRESH_FAILED", decision)
    manifest = load(run_root / "selector_heldout_candidate.manifest.json")
    write_once(run_root / "research_candidate.manifest.json", manifest)
    write_once(run_root / "research_candidate.freeze.json", {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_qd1_candidate.v1",
        "manifest_sha256": sha256(run_root / "research_candidate.manifest.json"),
        "development_only": True, "deployment_authorized": False,
        "production_switch_authorized": False,
    })
    update_state(run_root, "DEVELOPMENT_E2E", "READY")
    return 0


def _replay(config, run_root, context, arm, output, *, repeat):
    command = [
        sys.executable, str(REPLAY), "--instance", context["instance_path"],
        "--snapshot", context["snapshot_path"], "--output", str(output),
        "--policy", arm, "--repeat-index", str(repeat),
        "--wall-time-limit-sec",
        str(config["execution"]["replay_caps_sec"][str(context["scale"])]),
        "--memory-limit-gb", str(config["execution"]["memory_limit_gb"]),
    ]
    env = dict(os.environ)
    for key in tuple(env):
        if key.startswith("LUNAR_ICE_P0V5_") or key.startswith("LUNAR_ICE_GAT_"):
            env.pop(key, None)
    build = Path(load(run_root / "source.freeze.json")["native_binary"]).parent
    env["PYTHONPATH"] = os.pathsep.join((str(build), str((ROOT / "src").resolve())))
    completed = subprocess.run(command, cwd=ROOT, env=env, check=False)
    if completed.returncode:
        raise SystemExit(f"heldout replay failed:{completed.returncode}")


def _median(values):
    values = sorted(float(value) for value in values)
    if not values:
        return 0.0
    middle = len(values) // 2
    return values[middle] if len(values) % 2 else (values[middle - 1] + values[middle]) / 2


def _p99(values):
    values = sorted(float(value) for value in values)
    return 0.0 if not values else values[min(len(values) - 1, int(0.99 * len(values)))]


if __name__ == "__main__":
    raise SystemExit(main())
