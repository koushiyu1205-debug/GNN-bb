#!/usr/bin/env python3
"""One-shot shared-outcome heldout validation for the frozen V7 models."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from time import perf_counter


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
import scripts.train_p0v5_native_frontier_gat_selector_v7 as training  # noqa: E402
from lunar_ice_bpc.guidance.frontier_gat_qd1_v7 import FrontierGraph, MODEL_SEEDS  # noqa: E402
from scripts.p0v5_native_frontier_gat_qd1_v7_common import (  # noqa: E402
    DEFAULT_RUN_ROOT,
    assert_active,
    collapse_matched_blocks,
    geometric_mean,
    load,
    sha256,
    update_state,
    write_once,
    write_terminal,
)


REPLAY = ROOT / "scripts/replay_p0v5_qg2_label_state_snapshot.py"
KINDS = training.MODEL_KINDS


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    assert_active(run_root, "HELDOUT")
    _verify_preheldout(run_root)
    config = load(run_root / "config.freeze.json")
    contexts = [row for row in load(run_root / "main_corpus.freeze.json")["rows"]
                if row["partition"] == "selector_heldout"]
    if {scale: len({row["instance_content_hash"] for row in contexts
                    if int(row["scale"]) == scale}) for scale in (30, 50)} != {30: 6, 50: 6}:
        raise SystemExit("V7 heldout split is not 6+6")
    raw_dir = run_root / "heldout_raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    base_raw = []
    target = {}
    for context in contexts:
        for block in range(3):
            for arm in ("Q0", "QPF0"):
                raw = _run_replay(config, context, arm, block, raw_dir)
                base_raw.append(_row(context, arm, block, raw))
        q0 = [row for row in base_raw if row["context_id"] == context["context_id"]
              and row["arm"] == "Q0"]
        kinds = {load(row["raw_path"])["milestone_kind"] for row in q0
                 if load(row["raw_path"]).get("milestone_reached")}
        if len(kinds) != 1:
            return _fail(run_root, "HELDOUT_FRESH_FAILED", {"context": context["context_id"],
                                                             "reason": "Q0 milestone censor"})
        target[context["context_id"]] = next(iter(kinds))
    actions = _predict_actions(run_root, contexts, base_raw)
    write_once(run_root / "heldout_actions.freeze.json", {
        "schema_version": "lunar_ice_bpc.p0v5_frontier_gat_heldout_actions.v1",
        "frozen_before_qpd1_outcomes": True, "rows": actions,
    })
    selected_contexts = {row["context_id"] for row in actions
                         if row["selected_action"] == "QPD1"}
    all_raw = list(base_raw)
    for context in contexts:
        if context["context_id"] not in selected_contexts:
            continue
        for block in range(3):
            raw = _run_replay(config, context, "QPD1", block, raw_dir)
            all_raw.append(_row(context, "QPD1", block, raw))
    outcomes = _outcomes(all_raw, target)
    write_once(run_root / "heldout_outcomes.json", {
        "schema_version": "lunar_ice_bpc.p0v5_frontier_gat_heldout_outcomes.v1",
        "rows": outcomes,
    })
    decision = _decision(actions, outcomes, config)
    write_once(run_root / "heldout.decision.json", {"decision": decision})
    write_once(run_root / "selector_heldout.decision.json", decision)
    if not decision["passed"]:
        return _fail(run_root, decision["reason"], decision)
    manifest = load(run_root / "development_candidate.manifest.json")
    write_once(run_root / "research_candidate.manifest.json", manifest)
    write_once(run_root / "research_candidate.freeze.json", {
        "schema_version": "lunar_ice_bpc.p0v5_frontier_gat_research_candidate.v1",
        "manifest_sha256": sha256(run_root / "research_candidate.manifest.json"),
        "bundle_sha256": sha256(run_root / "frontier_gat_native_bundle.json"),
        "heldout_decision_sha256": sha256(run_root / "heldout.decision.json"),
        "development_only": True, "deployment_authorized": False,
        "production_switch_authorized": False,
    })
    update_state(run_root, "DEVELOPMENT_E2E", "READY")
    print(json.dumps(decision, ensure_ascii=False, indent=2))
    return 0


def _verify_preheldout(run_root):
    freeze = load(run_root / "preheldout.freeze.registry.json")
    for name, key in (("frontier_gat_training_dataset.freeze.json", "dataset_sha256"),
                      ("selector_training_report.json", "training_report_sha256"),
                      ("frontier_gat_native_bundle.json", "bundle_sha256"),
                      ("development_candidate.manifest.json", "manifest_sha256")):
        if sha256(run_root / name) != freeze[key]:
            raise SystemExit(f"FREEZE_HASH_DRIFT:{name}")


def _run_replay(config, context, arm, block, directory):
    path = directory / f"{context['context_id']}_b{block}_{arm}.json"
    if not path.is_file():
        command = [
            sys.executable, str(REPLAY), "--instance", str(context["instance_path"]),
            "--snapshot", str(context["snapshot_path"]), "--output", str(path),
            "--policy", arm, "--repeat-index", str(block + 1),
            "--wall-time-limit-sec", str(config["execution"]["replay_caps_sec"][str(context["scale"])]),
            "--memory-limit-gb", str(config["execution"]["memory_limit_gb"]),
        ]
        result = subprocess.run(command, cwd=ROOT, env=_environment(config), check=False)
        if result.returncode:
            raise SystemExit(f"V7 heldout replay failed:{path.name}")
    payload = load(path)
    payload["_v7_raw_path"] = str(path)
    return payload


def _environment(config):
    value = dict(os.environ)
    value["PYTHONPATH"] = os.pathsep.join((
        str((ROOT / config["native_build_dir"]).resolve()), str((ROOT / "src").resolve())
    ))
    value.pop("LUNAR_ICE_P0V5_FRONTIER_GAT_QD1_V7_MANIFEST", None)
    return value


def _row(context, arm, block, raw):
    frontier = dict((raw.get("proof_telemetry") or {}).get(
        "proof_queue_frontier_probe") or {})
    redlines = ["labels_dropped"] if raw.get("labels_dropped") else []
    if arm == "QPD1" and frontier.get("reached"):
        before = int(frontier.get("frontier_before_migration") or 0)
        if not (frontier.get("switched_to_qd1")
                and before == int(frontier.get("drained_count") or -1)
                and before == int(frontier.get("migrated_count") or -1)
                and int(frontier.get("duplicate_count") or 0) == 0
                and int(frontier.get("creation_hash_before") or 0)
                == int(frontier.get("creation_hash_after") or -1)):
            redlines.append("migration_mismatch")
    return {
        "context_id": context["context_id"], "block_id": f"{context['context_id']}:b{block}",
        "arm": arm, "status": "COMPLETE" if raw.get("milestone_reached") else str(raw.get("engine_status")),
        "wall_seconds": float(raw.get("milestone_wall_sec") or raw.get("backend_solve_wall_sec") or 0),
        "cap_seconds": float(raw["requested_wall_time_limit_sec"]),
        "correctness_redlines": redlines,
        "metadata": {"scale": context["scale"], "partition": "selector_heldout",
                     "instance_hash": context["instance_content_hash"],
                     "state_hash": context["state_hash"]},
        "frontier_graph": ({"graph_hash": frontier.get("graph_hash"),
                            "node_features": frontier.get("node_features"),
                            "edges": frontier.get("edges"),
                            "context_features": frontier.get("context_features")}
                           if arm == "QPF0" and frontier.get("graph_built") else None),
        "frontier_telemetry": frontier,
        "milestone_kind": raw.get("milestone_kind"),
        "raw_path": raw["_v7_raw_path"],
    }


def _predict_actions(run_root, contexts, raw_rows):
    import torch

    report = load(run_root / "selector_training_report.json")
    best = report["selection"]["best"]
    by_graph = defaultdict(list)
    for row in raw_rows:
        if row["arm"] == "QPF0" and row["frontier_graph"]:
            by_graph[row["context_id"]].append(row["frontier_graph"])
    actions = []
    for kind in KINDS:
        spec = report["models"][kind]
        models = []
        normalization = None
        cold_load_ms = 0.0
        for seed, path_value, expected in zip(
            MODEL_SEEDS,
            [run_root / "selector_training" / f"{kind}_seed{seed}.pt" for seed in MODEL_SEEDS],
            spec["checkpoint_sha256"],
        ):
            if sha256(path_value) != expected:
                raise SystemExit(f"V7 heldout checkpoint drift:{kind}:{seed}")
            started = perf_counter()
            checkpoint = torch.load(path_value, map_location="cpu", weights_only=False)
            model = training._build_model(kind).double()
            model.load_state_dict(checkpoint["state_dict"], strict=True)
            model.eval()
            cold_load_ms += (perf_counter() - started) * 1000.0
            normalization = checkpoint["normalization"]
            models.append(model)
        calibrator = spec["calibrator"]
        thresholds = (best.get(kind) or {}).get("thresholds_by_scale", {})
        if kind == "gat":
            load_started = perf_counter()
            load(run_root / "frontier_gat_native_bundle.json")
            candidate_bundle_load_ms = (perf_counter() - load_started) * 1000.0
        else:
            candidate_bundle_load_ms = cold_load_ms
        for ordinal, context in enumerate(contexts):
            graphs = by_graph[context["context_id"]]
            if len({graph["graph_hash"] for graph in graphs}) != 1:
                raise SystemExit("V7 heldout frontier graph is not deterministic")
            source = {"context_id": context["context_id"],
                      "instance_hash": context["instance_content_hash"],
                      "state_hash": context["state_hash"], "scale": context["scale"],
                      "context_weight": 1.0, "graph": graphs[0],
                      "target": {"ratio": 1.0, "net_ratio": 1.0,
                                 "benefit": 0, "positive_gain": 0.0, "adverse": 0}}
            started = perf_counter()
            values = []
            with torch.inference_mode():
                for model in models:
                    output = training._forward(model, source, normalization, kind)
                    values.append({"p_benefit": float(output["p_benefit"]),
                                   "positive_gain": float(output["positive_gain"]),
                                   "p_adverse": float(output["p_adverse"])})
            inference_ms = (perf_counter() - started) * 1000.0
            prediction = training._calibrated(training._aggregate(values, source), calibrator)
            threshold = thresholds.get(str(context["scale"]))
            selected = bool(threshold and _select(prediction, threshold))
            frontier_ms = max(1000.0 * (
                float(row["frontier_telemetry"].get("graph_build_wall_seconds") or 0.0)
                + float(row["frontier_telemetry"].get("inference_wall_seconds") or 0.0)
            ) for row in raw_rows if row["context_id"] == context["context_id"]
                and row["arm"] == "QPF0")
            actions.append({
                "model_kind": kind, "context_id": context["context_id"],
                "instance_hash": context["instance_content_hash"], "scale": context["scale"],
                "selected_action": "QPD1" if selected else "QPF0",
                "prediction": {key: prediction[key] for key in
                               ("p_benefit", "positive_gain", "p_adverse", "disagreement")},
                "threshold": threshold, "warm_preparation_ms": frontier_ms + inference_ms,
                "inference_ms": inference_ms,
                "cold_load_ms": candidate_bundle_load_ms if ordinal == 0 else 0.0,
            })
    return actions


def _select(row, threshold):
    expected = row["p_benefit"] * row["positive_gain"]
    return bool(row["p_benefit"] >= threshold["minimum_benefit_probability"]
                and row["p_adverse"] <= threshold["maximum_adverse_probability"]
                and expected >= threshold["minimum_expected_gain"]
                and expected - threshold["adverse_penalty"] * row["p_adverse"] > 0
                and row["disagreement"] <= threshold["maximum_disagreement"])


def _outcomes(rows, targets):
    output = []
    for context_id in sorted({row["context_id"] for row in rows}):
        selected = [dict(row) for row in rows if row["context_id"] == context_id]
        for row in selected:
            if row.get("milestone_kind") != targets[context_id]:
                row["status"] = "MILESTONE_MISMATCH"
        probe = _pair(selected, "Q0", "QPF0")
        switch = _pair(selected, "QPF0", "QPD1") if any(
            row["arm"] == "QPD1" for row in selected) else None
        net = _pair(selected, "Q0", "QPD1") if switch else None
        metadata = selected[0]["metadata"]
        output.append({"context_id": context_id, **metadata,
                       "probe_ratio": probe.get("ratio"),
                       "switch_ratio": switch.get("ratio") if switch else None,
                       "net_ratio": net.get("ratio") if net else None,
                       "q0_median_wall": _median_complete_wall(selected, "Q0"),
                       "qpf0_median_wall": _median_complete_wall(selected, "QPF0"),
                       "qpd1_median_wall": _median_complete_wall(selected, "QPD1"),
                       "determined": bool(probe.get("determined") and
                                          (switch is None or switch.get("determined"))),
                       "adverse": bool(switch and switch.get("adverse")),
                       "correctness_redlines": sorted({value for row in selected
                                                       for value in row["correctness_redlines"]})})
    return output


def _pair(rows, left, right):
    prepared = []
    for row in rows:
        if row["arm"] not in {left, right}:
            continue
        value = dict(row)
        value["arm"] = "QPF0" if row["arm"] == left else "QPD1"
        prepared.append(value)
    result = collapse_matched_blocks(prepared)
    return result[0] if result else {}


def _median_complete_wall(rows, arm):
    from statistics import median
    values = [float(row["wall_seconds"]) for row in rows
              if row["arm"] == arm and row["status"] == "COMPLETE"]
    return median(values) if values else None


def _decision(actions, outcomes, config):
    by_outcome = {row["context_id"]: row for row in outcomes}
    metrics = {}
    for kind in KINDS:
        rows = [row for row in actions if row["model_kind"] == kind]
        by_scale = {}
        for scale in (30, 50):
            selected = [row for row in rows if int(row["scale"]) == scale]
            ratios = defaultdict(list)
            activations = set()
            harmful = censored = 0
            preparation = []
            for row in selected:
                outcome = by_outcome[row["context_id"]]
                active = row["selected_action"] == "QPD1"
                base_wall = outcome["qpd1_median_wall"] if active else outcome["qpf0_median_wall"]
                q0_wall = outcome["q0_median_wall"]
                ratio = None if base_wall is None or q0_wall is None else (
                    float(base_wall)
                    + (float(row["inference_ms"]) + float(row["cold_load_ms"])) / 1000.0
                ) / float(q0_wall)
                if ratio is None:
                    censored += int(active)
                    ratio = 2.0 if active else 1.0
                ratios[row["instance_hash"]].append(float(ratio))
                if active:
                    activations.add(row["instance_hash"])
                    harmful += int(outcome["adverse"] or float(ratio) >= 1.05)
                preparation.append(float(row["warm_preparation_ms"]))
            values = [geometric_mean(value) for value in ratios.values()]
            by_scale[str(scale)] = {"gm": geometric_mean(values),
                                    "activation_instances": len(activations),
                                    "harmful": harmful, "censored": censored,
                                    "warm_p99_ms": sorted(preparation)[-1]}
        metrics[kind] = {"scales": by_scale,
                         "combined_gm": geometric_mean((by_scale["30"]["gm"],
                                                        by_scale["50"]["gm"]))}
    gat = metrics["gat"]
    simple = [metrics["mlp"], metrics["linear"]]
    topology = [metrics["no_message"], metrics["shuffled_topology"]]
    safety = all(gat["scales"][str(scale)]["activation_instances"] >= 3
                 and gat["scales"][str(scale)]["gm"] < 1.0
                 and gat["scales"][str(scale)]["harmful"] == 0
                 and gat["scales"][str(scale)]["censored"] == 0
                 and gat["scales"][str(scale)]["warm_p99_ms"] <= 10.0
                 for scale in (30, 50))
    advantage = bool(gat["scales"]["50"]["gm"] < min(row["scales"]["50"]["gm"] for row in simple)
                     and gat["combined_gm"] < min(row["combined_gm"] for row in simple)
                     and gat["scales"]["30"]["gm"] <= min(row["scales"]["30"]["gm"] for row in simple)
                     and all(gat["scales"][str(scale)]["gm"] <= row["scales"][str(scale)]["gm"]
                             for row in topology for scale in (30, 50)))
    redlines = sorted({value for row in outcomes for value in row["correctness_redlines"]})
    passed = bool(safety and advantage and not redlines)
    return {"schema_version": "lunar_ice_bpc.p0v5_frontier_gat_heldout_decision.v1",
            "passed": passed,
            "reason": None if passed else ("NO_FRONTIER_GAT_ADVANTAGE" if safety and not advantage
                                            else "HELDOUT_FRESH_FAILED"),
            "metrics": metrics, "correctness_redlines": redlines}


def _fail(run_root, reason, detail):
    write_terminal(run_root, reason=reason, stage="HELDOUT", detail=detail)
    print(json.dumps({"decision": "FAIL", "reason": reason}, indent=2))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
