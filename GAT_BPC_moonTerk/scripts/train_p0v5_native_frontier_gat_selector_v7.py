#!/usr/bin/env python3
"""Grouped-CV training, calibration and Native bundle freeze for V7."""

from __future__ import annotations

import argparse
from collections import defaultdict
from copy import deepcopy
import itertools
import json
from math import exp, log
from pathlib import Path
from statistics import median
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.guidance.frontier_gat_qd1_v7 import (  # noqa: E402
    FRONTIER_CHECKPOINT_SCHEMA_V1,
    FRONTIER_RUNTIME_POLICY_V7,
    MODEL_SEEDS,
    FrontierGraph,
    build_frontier_gat_model,
    build_frontier_linear_model,
    build_frontier_mlp_model,
    export_portable_bundle,
    parameter_count,
    shuffled_topology,
)
from lunar_ice_bpc.guidance.frontier_gat_qd1_runtime_v7 import (  # noqa: E402
    MANIFEST_SCHEMA_V1,
)
from scripts.p0v5_native_frontier_gat_qd1_v7_common import (  # noqa: E402
    DEFAULT_RUN_ROOT,
    assert_active,
    geometric_mean,
    load,
    sha256,
    update_state,
    write_once,
    write_terminal,
)


MODEL_KINDS = ("gat", "mlp", "linear", "no_message", "shuffled_topology")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    assert_active(run_root, "TRAINING")
    config = load(run_root / "config.freeze.json")
    dataset_path = run_root / "frontier_gat_training_dataset.freeze.json"
    training_input = load(run_root / "training_input.freeze.json")
    if sha256(dataset_path) != training_input["dataset_sha256"]:
        raise SystemExit("FREEZE_HASH_DRIFT:V7 training dataset")
    rows = list(load(dataset_path)["rows"])
    train_rows = [row for row in rows if row["partition"] == "train"]
    calibration_rows = [row for row in rows if row["partition"] == "calibration"]
    normalization = _normalization(train_rows, config)
    output_root = run_root / "selector_training"
    output_root.mkdir(parents=True, exist_ok=True)
    trained: dict[str, dict[str, Any]] = {}
    for kind in MODEL_KINDS:
        seed_runs = []
        for seed in MODEL_SEEDS:
            run = _cross_validate_and_refit(
                kind, seed, train_rows, normalization, config
            )
            checkpoint_path = output_root / f"{kind}_seed{seed}.pt"
            _save_checkpoint(checkpoint_path, run["model"], kind, seed,
                             run["refit_epoch"], normalization)
            run["checkpoint_path"] = str(checkpoint_path)
            run["checkpoint_sha256"] = sha256(checkpoint_path)
            seed_runs.append(run)
        oof = _ensemble_oof(seed_runs, train_rows)
        calibrator = _fit_calibrator(oof)
        calibration_predictions = _ensemble_predictions(
            seed_runs, calibration_rows, normalization, kind, calibrator
        )
        thresholds = {
            str(scale): _threshold_candidates(
                [row for row in calibration_predictions if int(row["scale"]) == scale],
                config["threshold_grid"], scale,
            )
            for scale in (30, 50)
        }
        trained[kind] = {
            "seed_runs": seed_runs, "oof": oof, "calibrator": calibrator,
            "calibration_predictions": calibration_predictions,
            "threshold_candidates": thresholds,
            "rank_accuracy": _rank_accuracy(oof),
        }
    selected = _select_candidate(trained, config)
    report = _report(trained, selected)
    write_once(run_root / "selector_training_report.json", report)
    if selected.get("decision") != "PASS":
        write_terminal(run_root, reason=selected["reason"], stage="CALIBRATION",
                       detail=selected)
        print(json.dumps(selected, ensure_ascii=False, indent=2))
        return 0
    gat = trained["gat"]
    thresholds = selected["thresholds_by_scale"]
    corpus = load(run_root / "main_corpus.freeze.json")
    bindings = {
        "engine_hashes": sorted({row["source_engine_hash"] for row in corpus["rows"]}),
        "selected_exact_config_sha256": load(run_root / "source.freeze.json")[
            "selected_exact_config_sha256"
        ],
        "action_policy_hashes": sorted({
            row["source_exact_action_policy_hash"] for row in corpus["rows"]
        }),
    }
    bundle_path = run_root / "frontier_gat_native_bundle.json"
    bundle = export_portable_bundle(
        models=[(seed, run["model"]) for seed, run in zip(MODEL_SEEDS, gat["seed_runs"])],
        normalization=normalization,
        calibration_by_scale=gat["calibrator"]["by_scale"],
        thresholds_by_scale=thresholds,
        bindings=bindings, output_path=bundle_path,
    )
    manifest = _manifest(run_root, config, corpus, bundle_path, bundle, thresholds)
    write_once(run_root / "development_candidate.manifest.json", manifest)
    write_once(run_root / "preheldout.freeze.registry.json", {
        "schema_version": "lunar_ice_bpc.p0v5_frontier_gat_preheldout_freeze.v1",
        "heldout_outcomes_seen": 0, "e2e_outcomes_seen": 0, "formal_outcomes_seen": 0,
        "dataset_sha256": sha256(dataset_path),
        "training_report_sha256": sha256(run_root / "selector_training_report.json"),
        "bundle_sha256": sha256(bundle_path),
        "manifest_sha256": sha256(run_root / "development_candidate.manifest.json"),
        "control_checkpoint_sha256": {
            kind: [row["checkpoint_sha256"] for row in trained[kind]["seed_runs"]]
            for kind in MODEL_KINDS if kind != "gat"
        },
    })
    update_state(run_root, "HELDOUT", "READY")
    print(json.dumps({"decision": "PASS", "status": "READY_FOR_ONE_SHOT_HELDOUT",
                      "thresholds_by_scale": thresholds,
                      "bundle_sha256": sha256(bundle_path)}, ensure_ascii=False, indent=2))
    return 0


def _build_model(kind):
    if kind == "gat" or kind == "shuffled_topology":
        return build_frontier_gat_model()
    if kind == "no_message":
        return build_frontier_gat_model(no_message=True)
    if kind == "mlp":
        return build_frontier_mlp_model()
    if kind == "linear":
        return build_frontier_linear_model()
    raise ValueError(kind)


def _normalization(rows, config):
    import torch

    groups = {"node": [], "edge": [], "context": []}
    for row in rows:
        graph = FrontierGraph.from_native_telemetry(row["graph"])
        groups["node"].extend(graph.node_features)
        groups["edge"].extend(graph.edge_features)
        groups["context"].append(graph.context_features)
    margin = float(config["selector_training"]["ood_relative_margin"])
    result = {}
    for name, values in groups.items():
        tensor = torch.tensor(values, dtype=torch.float64)
        mean = tensor.mean(0)
        scale = tensor.std(0, unbiased=False).clamp_min(1.0e-9)
        minimum = tensor.min(0).values
        maximum = tensor.max(0).values
        span = (maximum - minimum).abs().clamp_min(1.0e-6)
        result[name] = {
            "mean": mean.tolist(), "scale": scale.tolist(),
            "minimum": (minimum - margin * span).tolist(),
            "maximum": (maximum + margin * span).tolist(),
        }
    return result


def _cross_validate_and_refit(kind, seed, rows, normalization, config):
    import torch

    torch.manual_seed(seed)
    fold_results = []
    oof = []
    maximum = int(config["selector_training"]["maximum_epochs"])
    patience = int(config["selector_training"]["patience"])
    for fold in range(5):
        training = [row for row in rows if int(row["fold"]) != fold]
        validation = [row for row in rows if int(row["fold"]) == fold]
        model = _build_model(kind).double()
        if kind == "gat" and parameter_count(model) >= 15_000:
            raise SystemExit("V7 per-seed GAT parameter limit exceeded")
        best_epoch, curve = _fit(
            model, training, validation, normalization, kind, seed + fold,
            maximum, patience,
        )
        fold_results.append({"fold": fold, "best_epoch": best_epoch,
                             "curve": curve})
        oof.extend(_predict(model, validation, normalization, kind))
    refit_epoch = max(1, int(median(row["best_epoch"] for row in fold_results)))
    torch.manual_seed(seed)
    model = _build_model(kind).double()
    _fit(model, rows, (), normalization, kind, seed, refit_epoch, refit_epoch + 1)
    return {"seed": seed, "kind": kind, "model": model,
            "parameter_count": parameter_count(model), "folds": fold_results,
            "oof_predictions": oof, "refit_epoch": refit_epoch}


def _fit(model, training, validation, normalization, kind, seed, maximum, patience):
    import torch

    torch.manual_seed(seed)
    optimizer = torch.optim.Adam(model.parameters(), lr=1.0e-3, weight_decay=1.0e-5)
    best_state = deepcopy(model.state_dict())
    best_loss = float("inf")
    best_epoch = 1
    stale = 0
    curve = []
    for epoch in range(1, maximum + 1):
        model.train()
        optimizer.zero_grad()
        terms = [_loss(model, row, normalization, kind) * float(row["context_weight"])
                 for row in training]
        loss = sum(terms) / max(1.0, sum(float(row["context_weight"]) for row in training))
        loss.backward()
        optimizer.step()
        validation_loss = _evaluation_loss(
            model, validation if validation else training, normalization, kind
        )
        curve.append({"epoch": epoch, "train_loss": float(loss.detach()),
                      "validation_loss": validation_loss})
        if validation_loss < best_loss - 1.0e-9:
            best_loss, best_epoch = validation_loss, epoch
            best_state = deepcopy(model.state_dict())
            stale = 0
        else:
            stale += 1
        if validation and stale >= patience:
            break
    if validation:
        model.load_state_dict(best_state)
        return best_epoch, curve
    return maximum, curve


def _forward(model, row, normalization, kind):
    graph = FrontierGraph.from_native_telemetry(row["graph"])
    tensors = graph.tensors(normalization)
    if kind == "shuffled_topology":
        tensors["edge_index"] = shuffled_topology(
            tensors["edge_index"], state_hash=row["state_hash"]
        )
    return model(**tensors)


def _loss(model, row, normalization, kind):
    import torch
    import torch.nn.functional as functional

    output = _forward(model, row, normalization, kind)
    target = row["target"]
    benefit = torch.tensor(float(target["benefit"]), dtype=torch.float64)
    adverse = torch.tensor(float(target["adverse"]), dtype=torch.float64)
    pb = output["p_benefit"].clamp(1.0e-7, 1.0 - 1.0e-7)
    pa = output["p_adverse"].clamp(1.0e-7, 1.0 - 1.0e-7)
    value = functional.binary_cross_entropy(pb, benefit)
    value = value + functional.binary_cross_entropy(pa, adverse)
    if target["benefit"]:
        value = value + 0.5 * functional.smooth_l1_loss(
            output["positive_gain"],
            torch.tensor(float(target["positive_gain"]), dtype=torch.float64),
        )
    utility = pb * output["positive_gain"] - pa
    sign = 1.0 if float(target["ratio"]) < 1.0 else -1.0
    return value + 0.25 * functional.softplus(-sign * utility)


def _evaluation_loss(model, rows, normalization, kind):
    import torch

    model.eval()
    with torch.no_grad():
        values = [float(_loss(model, row, normalization, kind)) * float(row["context_weight"])
                  for row in rows]
    return sum(values) / max(1.0, sum(float(row["context_weight"]) for row in rows))


def _predict(model, rows, normalization, kind):
    import torch

    model.eval()
    output = []
    with torch.no_grad():
        for row in rows:
            value = _forward(model, row, normalization, kind)
            output.append({
                "context_id": row["context_id"], "instance_hash": row["instance_hash"],
                "state_hash": row["state_hash"], "scale": int(row["scale"]),
                "context_weight": float(row["context_weight"]), "target": row["target"],
                "p_benefit": float(value["p_benefit"]),
                "positive_gain": float(value["positive_gain"]),
                "p_adverse": float(value["p_adverse"]),
            })
    return output


def _ensemble_oof(seed_runs, rows):
    by_seed = [{row["context_id"]: row for row in run["oof_predictions"]}
               for run in seed_runs]
    output = []
    for source in rows:
        values = [seed[source["context_id"]] for seed in by_seed]
        output.append(_aggregate(values, source))
    return output


def _ensemble_predictions(seed_runs, rows, normalization, kind, calibrator):
    by_seed = [
        {row["context_id"]: row for row in _predict(run["model"], rows, normalization, kind)}
        for run in seed_runs
    ]
    return [_calibrated(_aggregate(
        [seed[source["context_id"]] for seed in by_seed], source
    ), calibrator) for source in rows]


def _aggregate(values, source):
    benefits = [row["p_benefit"] for row in values]
    return {
        "context_id": source["context_id"], "instance_hash": source["instance_hash"],
        "state_hash": source["state_hash"], "scale": int(source["scale"]),
        "context_weight": float(source["context_weight"]), "target": source["target"],
        "p_benefit": sum(benefits) / len(benefits),
        "positive_gain": min(row["positive_gain"] for row in values),
        "p_adverse": max(row["p_adverse"] for row in values),
        "disagreement": max(benefits) - min(benefits),
    }


def _fit_calibrator(rows):
    return {
        "fit_partition": "train_oof_by_scale_only",
        "by_scale": {str(scale): {
            "benefit": _fit_platt([row for row in rows if int(row["scale"]) == scale], "benefit"),
            "adverse": _fit_platt([row for row in rows if int(row["scale"]) == scale], "adverse"),
            "gain_scale": _gain_scale([row for row in rows if int(row["scale"]) == scale]),
        } for scale in (30, 50)},
    }


def _fit_platt(rows, field):
    import torch
    import torch.nn.functional as functional

    probabilities = torch.tensor([
        _logit(float(row[f"p_{field}"])) for row in rows
    ], dtype=torch.float64)
    labels = torch.tensor([float(row["target"][field]) for row in rows], dtype=torch.float64)
    if len(set(labels.tolist())) < 2:
        probability = (float(labels.sum()) + 1.0) / (len(labels) + 2.0)
        return {"kind": "constant", "probability": probability, "single_class": True}
    a = torch.tensor(1.0, dtype=torch.float64, requires_grad=True)
    b = torch.tensor(0.0, dtype=torch.float64, requires_grad=True)
    optimizer = torch.optim.LBFGS((a, b), max_iter=100, line_search_fn="strong_wolfe")
    def closure():
        optimizer.zero_grad()
        loss = functional.binary_cross_entropy_with_logits(a * probabilities + b, labels)
        loss.backward()
        return loss
    optimizer.step(closure)
    return {"kind": "platt", "a": float(a.detach()), "b": float(b.detach()),
            "single_class": False}


def _gain_scale(rows):
    beneficial = [row for row in rows if row["target"]["benefit"]]
    if not beneficial:
        return 0.0
    ratios = [float(row["target"]["positive_gain"]) /
              max(1.0e-9, float(row["positive_gain"])) for row in beneficial]
    return max(0.0, min(10.0, median(ratios)))


def _calibrated(row, calibrator):
    output = dict(row)
    scale = calibrator["by_scale"][str(row["scale"])]
    output["p_benefit"] = _apply_platt(row["p_benefit"], scale["benefit"])
    output["p_adverse"] = _apply_platt(row["p_adverse"], scale["adverse"])
    output["positive_gain"] = max(0.0, min(1.0,
        float(row["positive_gain"]) * float(scale["gain_scale"])))
    return output


def _apply_platt(probability, payload):
    if payload["kind"] == "constant":
        return float(payload["probability"])
    return 1.0 / (1.0 + exp(-(
        float(payload["a"]) * _logit(float(probability)) + float(payload["b"])
    )))


def _logit(value):
    value = max(1.0e-7, min(1.0 - 1.0e-7, value))
    return log(value / (1.0 - value))


def _threshold_candidates(rows, grid, scale):
    candidates = []
    keys = ("minimum_benefit_probability", "maximum_adverse_probability",
            "minimum_expected_gain", "adverse_penalty", "maximum_disagreement")
    for values in itertools.product(*(grid[key] for key in keys)):
        threshold = dict(zip(keys, map(float, values)))
        evaluation = _evaluate_threshold(rows, threshold)
        minimum = 4 if scale == 30 else 3
        if evaluation["harmful_activations"] == 0 and evaluation["censored_activations"] == 0 \
                and evaluation["activation_instances"] >= minimum \
                and evaluation["instance_weighted_net_gm"] < 1.0:
            candidates.append({"threshold": threshold, **evaluation})
    return sorted(candidates, key=lambda row: (
        row["instance_weighted_net_gm"], row["harmful_activations"],
        -row["activation_instances"], tuple(row["threshold"].values())
    ))


def _evaluate_threshold(rows, threshold):
    by_instance = defaultdict(list)
    harmful = censored = 0
    activated = set()
    for row in rows:
        expected = row["p_benefit"] * row["positive_gain"]
        selected = bool(
            row["p_benefit"] >= threshold["minimum_benefit_probability"]
            and row["p_adverse"] <= threshold["maximum_adverse_probability"]
            and expected >= threshold["minimum_expected_gain"]
            and expected - threshold["adverse_penalty"] * row["p_adverse"] > 0.0
            and row["disagreement"] <= threshold["maximum_disagreement"]
        )
        target = row["target"]
        ratio = float(target["net_ratio"]) if selected else 1.0
        by_instance[row["instance_hash"]].append(ratio)
        if selected:
            activated.add(row["instance_hash"])
            harmful += int(bool(target["adverse"]) or float(target["ratio"]) >= 1.05)
    instance = [geometric_mean(values) for values in by_instance.values()]
    return {"activation_instances": len(activated), "harmful_activations": harmful,
            "censored_activations": censored,
            "instance_weighted_net_gm": geometric_mean(instance)}


def _select_candidate(trained, config):
    best = {kind: _best_pair(payload["threshold_candidates"])
            for kind, payload in trained.items()}
    if best["gat"] is None:
        return {"decision": "FAIL", "reason": "NO_SAFE_FRONTIER_GAT_THRESHOLD"}
    gat = best["gat"]
    simple = [best["mlp"], best["linear"]]
    topology = [best["no_message"], best["shuffled_topology"]]
    if any(row is None for row in (*simple, *topology)):
        # Honest Q0 no-op controls have GM 1 and remain valid comparisons.
        simple = [row or _noop_pair() for row in simple]
        topology = [row or _noop_pair() for row in topology]
    rank = {kind: trained[kind]["rank_accuracy"] for kind in MODEL_KINDS}
    topology_drop = max(
        rank["gat"]["combined"] - rank[kind]["combined"]
        for kind in ("no_message", "shuffled_topology")
    )
    advantage = bool(
        gat["scale_gm"]["50"] < min(row["scale_gm"]["50"] for row in simple)
        and gat["combined_gm"] < min(row["combined_gm"] for row in simple)
        and gat["scale_gm"]["30"] <= min(row["scale_gm"]["30"] for row in simple)
        and all(gat["scale_gm"][str(scale)] <= row["scale_gm"][str(scale)]
                for row in topology for scale in (30, 50))
        and rank["gat"]["combined"] >= max(rank[kind]["combined"]
                                            for kind in ("no_message", "shuffled_topology"))
        and (topology_drop >= float(config["gates"]["calibration"]["minimum_topology_rank_drop"])
             or rank["gat"]["50"] - min(rank[kind]["50"]
                                          for kind in ("no_message", "shuffled_topology")) >= .02)
    )
    if not advantage:
        return {"decision": "FAIL", "reason": "NO_FRONTIER_GAT_ADVANTAGE",
                "best": best, "rank_accuracy": rank, "topology_drop": topology_drop}
    return {"decision": "PASS", "reason": None, "best": best,
            "rank_accuracy": rank, "topology_drop": topology_drop,
            "thresholds_by_scale": gat["thresholds_by_scale"]}


def _best_pair(by_scale):
    if not by_scale["30"] or not by_scale["50"]:
        return None
    choices = []
    for row30, row50 in itertools.product(by_scale["30"], by_scale["50"]):
        gm30, gm50 = row30["instance_weighted_net_gm"], row50["instance_weighted_net_gm"]
        choices.append({
            "scale_gm": {"30": gm30, "50": gm50},
            "combined_gm": geometric_mean((gm30, gm50)),
            "worst_scale_gm": max(gm30, gm50),
            "thresholds_by_scale": {"30": row30["threshold"], "50": row50["threshold"]},
            "activation_instances": {"30": row30["activation_instances"],
                                     "50": row50["activation_instances"]},
        })
    return min(choices, key=lambda row: (row["worst_scale_gm"], row["combined_gm"],
                                         tuple(row["thresholds_by_scale"]["30"].values()),
                                         tuple(row["thresholds_by_scale"]["50"].values())))


def _noop_pair():
    return {"scale_gm": {"30": 1.0, "50": 1.0}, "combined_gm": 1.0,
            "worst_scale_gm": 1.0, "thresholds_by_scale": {},
            "activation_instances": {"30": 0, "50": 0}}


def _rank_accuracy(rows):
    by_scale_instance = defaultdict(lambda: defaultdict(list))
    for row in rows:
        utility = row["p_benefit"] * row["positive_gain"] - row["p_adverse"]
        correct = (utility > 0.0) == (float(row["target"]["ratio"]) < 1.0)
        by_scale_instance[int(row["scale"])][row["instance_hash"]].append(float(correct))
    output = {}
    combined = []
    for scale in (30, 50):
        values = [sum(rows) / len(rows) for rows in by_scale_instance[scale].values()]
        output[str(scale)] = sum(values) / len(values)
        combined.extend(values)
    output["combined"] = sum(combined) / len(combined)
    return output


def _report(trained, selected):
    return {
        "schema_version": "lunar_ice_bpc.p0v5_frontier_gat_training_report.v1",
        "candidate_model": "gat", "ensemble_seeds": list(MODEL_SEEDS),
        "all_controls_independently_trained": True,
        "calibration_not_used_for_representation_training": True,
        "selection": selected,
        "models": {kind: {
            "parameter_count_per_seed": [row["parameter_count"] for row in value["seed_runs"]],
            "refit_epochs": [row["refit_epoch"] for row in value["seed_runs"]],
            "checkpoint_sha256": [row["checkpoint_sha256"] for row in value["seed_runs"]],
            "rank_accuracy": value["rank_accuracy"],
            "safe_threshold_count": {scale: len(rows)
                                     for scale, rows in value["threshold_candidates"].items()},
            "calibrator": value["calibrator"],
        } for kind, value in trained.items()},
    }


def _save_checkpoint(path, model, kind, seed, epoch, normalization):
    import torch

    if path.exists():
        raise SystemExit(f"immutable V7 checkpoint already exists:{path}")
    torch.save({
        "schema_version": FRONTIER_CHECKPOINT_SCHEMA_V1, "model_kind": kind,
        "seed": seed, "refit_epoch": epoch, "normalization": normalization,
        "state_dict": model.state_dict(), "independently_trained": True,
    }, path)


def _manifest(run_root, config, corpus, bundle_path, bundle, thresholds):
    return {
        "schema_version": MANIFEST_SCHEMA_V1,
        "runtime_policy": FRONTIER_RUNTIME_POLICY_V7,
        "action_universe": ["CONTINUE_Q0", "SWITCH_QD1"],
        "forced_veto_actions": ["QB1", "QGR1"], "probe_boundary": 4096,
        "allowed_scales": [30, 50], "model_kind": "frontier_interaction_gat",
        "message_passing_required": True, "pricing_lifecycle_authority": "root_cg_only",
        "portable_bundle_path": str(bundle_path),
        "portable_bundle_file_sha256": sha256(bundle_path),
        "portable_bundle_internal_sha256": bundle["bundle_sha256"],
        "allowed_exact_engine_hashes": sorted({row["source_engine_hash"] for row in corpus["rows"]}),
        "selected_exact_config_sha256": load(run_root / "source.freeze.json")[
            "selected_exact_config_sha256"
        ],
        "allowed_exact_action_policy_hashes": sorted({
            row["source_exact_action_policy_hash"] for row in corpus["rows"]
        }),
        "thresholds_by_scale": thresholds,
        "development_only": True, "development_e2e_authorized": True,
        "deployment_authorized": False, "production_switch_authorized": False,
        "controls_authorized": False, "ranker_path": None,
        "training_report_sha256": sha256(run_root / "selector_training_report.json"),
        "native_binary_sha256": load(run_root / "source.freeze.json")["native_binary_sha256"],
    }


if __name__ == "__main__":
    raise SystemExit(main())
