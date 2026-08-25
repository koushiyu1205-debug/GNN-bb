#!/usr/bin/env python3
"""Diagnostic-only grouped OOF test of V7 frontier feature sufficiency.

This script never writes a checkpoint, calibrates an action threshold, exports a
bundle, or creates a candidate manifest.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from math import sqrt
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.guidance.frontier_gat_qd1_v7 import FrontierGraph  # noqa: E402
from scripts import train_p0v5_native_frontier_gat_selector_v7 as trainer  # noqa: E402
from scripts.p0v5_frontier_observability_v7r_common import (  # noqa: E402
    DEFAULT_RUN_ROOT, assert_active, geometric_mean, load, write_once,
    write_terminal,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    assert_active(run_root, "FEATURE_SUFFICIENCY")
    config = load(run_root / "config.freeze.json")
    outcomes = load(run_root / "switch_matrix.collapsed.json")["rows"]
    rows = _dataset(outcomes, int(config["feature_sufficiency"]["fold_count"]))
    training_config = {
        "selector_training": {
            "maximum_epochs": int(config["feature_sufficiency"]["maximum_epochs"]),
            "patience": int(config["feature_sufficiency"]["patience"]),
            "ood_relative_margin": 0.05,
        }
    }
    normalization = trainer._normalization(rows, training_config)
    models = {}
    for kind in config["feature_sufficiency"]["model_kinds"]:
        seed_oof = []
        seed_curves = []
        for seed in config["feature_sufficiency"]["seeds"]:
            predictions, curves = _grouped_oof(
                kind, int(seed), rows, normalization, training_config
            )
            seed_oof.append({row["context_id"]: row for row in predictions})
            seed_curves.append({"seed": int(seed), "folds": curves})
        ensemble = [trainer._aggregate(
            [seed[row["context_id"]] for seed in seed_oof], row
        ) for row in rows]
        instance_rows = _instance_predictions(ensemble)
        models[kind] = {
            "context_count": len(ensemble),
            "instance_count": len(instance_rows),
            "metrics_by_scale": {
                str(scale): _metrics([row for row in instance_rows if row["scale"] == scale])
                for scale in (30, 50)
            },
            "oof_predictions": ensemble,
            "instance_predictions": instance_rows,
            "training_curves": seed_curves,
            "checkpoint_written": False,
        }
    conflicts = _similar_graph_conflicts(
        rows, float(config["feature_sufficiency"]["similar_pair_distance_quantile"])
    )
    gate = _gate(config, models, conflicts)
    report = {
        "schema_version": "lunar_ice_bpc.p0v5_frontier_feature_sufficiency.v1",
        "decision": gate["decision"],
        "reason": gate["reason"],
        "gate": gate,
        "models": models,
        "similar_graph_opposite_wall_labels": conflicts,
        "normalization_fit": "all diagnostic graphs; unsupervised; no action outcomes",
        "folding": "five-fold instance-grouped; all contexts of an instance stay together",
        "candidate_trained": False,
        "checkpoint_count": 0,
        "threshold_search_performed": False,
        "manifest_generated": False,
    }
    write_once(run_root / "feature_sufficiency.report.json", report)
    write_terminal(
        run_root,
        gate["reason"],
        "FEATURE_SUFFICIENCY",
        {
            "gate": gate,
            "feature_sufficiency_report": "feature_sufficiency.report.json",
            "coverage_report": "coverage_hit_rate.report.json",
            "oracle_decision": "switch_oracle.decision.json",
        },
        decision=gate["decision"],
    )
    print(json.dumps({"decision": gate["decision"], "reason": gate["reason"],
                      "gate": gate, "checkpoint_count": 0}, ensure_ascii=False, indent=2))
    return 0


def _dataset(outcomes, fold_count):
    determined = [row for row in outcomes if row["determined"]]
    context_counts = defaultdict(int)
    instances_by_scale = defaultdict(set)
    for row in determined:
        context_counts[row["instance_hash"]] += 1
        instances_by_scale[int(row["scale"])].add(row["instance_hash"])
    folds = {}
    for scale in (30, 50):
        ordered = sorted(instances_by_scale[scale], key=lambda value: hashlib.sha256(
            f"v7r-feature-fold:{scale}:{value}".encode()
        ).hexdigest())
        for index, instance_hash in enumerate(ordered):
            folds[instance_hash] = index % fold_count
    rows = []
    for row in determined:
        if not row.get("qpf0_graph"):
            raise SystemExit("V7R determined outcome lacks frontier graph")
        FrontierGraph.from_native_telemetry(row["qpf0_graph"])
        ratio = float(row["ratio"])
        rows.append({
            "context_id": row["context_id"],
            "instance_hash": row["instance_hash"],
            "state_hash": row["state_hash"],
            "scale": int(row["scale"]),
            "fold": folds[row["instance_hash"]],
            "context_weight": 1.0 / context_counts[row["instance_hash"]],
            "graph": row["qpf0_graph"],
            "target": {
                "ratio": ratio,
                "benefit": int(ratio <= 0.98),
                "positive_gain": max(0.0, 1.0 - ratio),
                "adverse": int(bool(row["adverse"]) or ratio >= 1.05),
            },
        })
    return rows


def _grouped_oof(kind, seed, rows, normalization, config):
    import torch

    predictions = []
    curves = []
    fold_count = len({int(row["fold"]) for row in rows})
    for fold in range(fold_count):
        training = [row for row in rows if int(row["fold"]) != fold]
        validation = [row for row in rows if int(row["fold"]) == fold]
        if not validation:
            raise SystemExit(f"V7R empty fold:{fold}")
        torch.manual_seed(seed + fold)
        model = trainer._build_model(kind).double()
        best_epoch, curve = trainer._fit(
            model, training, validation, normalization, kind, seed + fold,
            int(config["selector_training"]["maximum_epochs"]),
            int(config["selector_training"]["patience"]),
        )
        predictions.extend(trainer._predict(model, validation, normalization, kind))
        curves.append({"fold": fold, "best_epoch": best_epoch, "curve": curve})
    if len(predictions) != len(rows):
        raise SystemExit("V7R OOF coverage mismatch")
    return predictions, curves


def _instance_predictions(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[(int(row["scale"]), row["instance_hash"])].append(row)
    output = []
    for (scale, instance_hash), values in sorted(grouped.items()):
        ratio = geometric_mean(float(row["target"]["ratio"]) for row in values)
        output.append({
            "scale": scale,
            "instance_hash": instance_hash,
            "ratio": ratio,
            "benefit": int(ratio <= 0.98),
            "adverse": int(ratio >= 1.05),
            "p_benefit": sum(float(row["p_benefit"]) for row in values) / len(values),
            "positive_gain": sum(float(row["positive_gain"]) for row in values) / len(values),
            "p_adverse": max(float(row["p_adverse"]) for row in values),
        })
    return output


def _binary_metrics(labels, scores):
    predicted = [int(value >= 0.5) for value in scores]
    tp = sum(y == 1 and p == 1 for y, p in zip(labels, predicted))
    tn = sum(y == 0 and p == 0 for y, p in zip(labels, predicted))
    fp = sum(y == 0 and p == 1 for y, p in zip(labels, predicted))
    fn = sum(y == 1 and p == 0 for y, p in zip(labels, predicted))
    recall = tp / (tp + fn) if tp + fn else None
    specificity = tn / (tn + fp) if tn + fp else None
    balanced = ((recall + specificity) / 2.0
                if recall is not None and specificity is not None else None)
    auc_pairs = [(a, b) for a, ya in zip(scores, labels)
                 for b, yb in zip(scores, labels) if ya == 1 and yb == 0]
    auc = (sum(1.0 if a > b else 0.5 if a == b else 0.0 for a, b in auc_pairs)
           / len(auc_pairs) if auc_pairs else None)
    return {
        "positive": sum(labels), "negative": len(labels) - sum(labels),
        "recall": recall, "specificity": specificity,
        "balanced_accuracy": balanced, "auc": auc,
        "brier": sum((score - label) ** 2 for score, label in zip(scores, labels)) / len(labels),
    }


def _rank_accuracy(rows):
    pairs = []
    for index, left in enumerate(rows):
        left_score = left["p_benefit"] * left["positive_gain"] - left["p_adverse"]
        for right in rows[index + 1:]:
            if abs(left["ratio"] - right["ratio"]) <= 1.0e-12:
                continue
            right_score = right["p_benefit"] * right["positive_gain"] - right["p_adverse"]
            actual = left["ratio"] < right["ratio"]
            predicted = left_score > right_score
            pairs.append(1.0 if actual == predicted else 0.5 if left_score == right_score else 0.0)
    return sum(pairs) / len(pairs) if pairs else None


def _metrics(rows):
    benefit = _binary_metrics(
        [row["benefit"] for row in rows], [row["p_benefit"] for row in rows]
    )
    adverse = _binary_metrics(
        [row["adverse"] for row in rows], [row["p_adverse"] for row in rows]
    )
    return {"benefit": benefit, "adverse": adverse,
            "rank_accuracy": _rank_accuracy(rows)}


def _flat_graph(row):
    graph = row["graph"]
    node = [float(value) for values in graph["node_features"] for value in values]
    context = [float(value) for value in graph["context_features"]]
    edge_values = [edge["features"] for edge in graph["edges"]]
    edge_mean = [sum(float(values[index]) for values in edge_values) / len(edge_values)
                 for index in range(10)]
    edge_max = [max(float(values[index]) for values in edge_values) for index in range(10)]
    adjacency = [0.0] * (64 * 64)
    for edge in graph["edges"]:
        adjacency[int(edge["source"]) * 64 + int(edge["target"])] = 1.0
    return node + context + edge_mean + edge_max + adjacency


def _similar_graph_conflicts(rows, quantile):
    selected = [row for row in rows if int(row["scale"]) == 50]
    vectors = [_flat_graph(row) for row in selected]
    width = len(vectors[0])
    means = [sum(vector[index] for vector in vectors) / len(vectors) for index in range(width)]
    scales = [sqrt(sum((vector[index] - means[index]) ** 2 for vector in vectors) / len(vectors))
              or 1.0 for index in range(width)]
    pairs = []
    for left in range(len(selected)):
        for right in range(left + 1, len(selected)):
            if selected[left]["instance_hash"] == selected[right]["instance_hash"]:
                continue
            distance = sqrt(sum(
                ((vectors[left][index] - vectors[right][index]) / scales[index]) ** 2
                for index in range(width)
            ) / width)
            opposite = int(selected[left]["target"]["benefit"] != selected[right]["target"]["benefit"])
            pairs.append({"left": selected[left]["context_id"],
                          "right": selected[right]["context_id"],
                          "distance": distance, "opposite_benefit_label": opposite})
    ordered = sorted(row["distance"] for row in pairs)
    threshold = ordered[min(len(ordered) - 1, max(0, int(quantile * len(ordered))))]
    similar = [row for row in pairs if row["distance"] <= threshold]
    nearest = []
    for index, row in enumerate(selected):
        candidates = [pair for pair in pairs if pair["left"] == row["context_id"]
                      or pair["right"] == row["context_id"]]
        nearest.append(min(candidates, key=lambda value: value["distance"]))
    return {
        "scale": 50,
        "distance_definition": "zscaled canonical 64x16 nodes + context + edge mean/max + 64x64 adjacency",
        "pair_count": len(pairs),
        "similar_distance_quantile": quantile,
        "similar_distance_threshold": threshold,
        "similar_pair_count": len(similar),
        "similar_opposite_label_fraction": sum(row["opposite_benefit_label"] for row in similar) / len(similar),
        "nearest_neighbor_opposite_label_fraction": sum(row["opposite_benefit_label"] for row in nearest) / len(nearest),
        "closest_opposite_pairs": sorted(
            (row for row in pairs if row["opposite_benefit_label"]),
            key=lambda value: value["distance"],
        )[:10],
    }


def _gate(config, models, conflicts):
    gate = config["feature_sufficiency"]
    minimum_balanced = float(gate["minimum_scale50_balanced_accuracy"])
    minimum_rank = float(gate["minimum_scale50_rank_accuracy"])
    passing = []
    for kind, report in models.items():
        metrics = report["metrics_by_scale"]["50"]
        balanced = metrics["benefit"]["balanced_accuracy"]
        rank = metrics["rank_accuracy"]
        if balanced is not None and rank is not None and balanced >= minimum_balanced and rank >= minimum_rank:
            passing.append(kind)
    gat_metrics = models["gat"]["metrics_by_scale"]["50"]
    gat_balanced = gat_metrics["benefit"]["balanced_accuracy"]
    gat_rank = gat_metrics["rank_accuracy"]
    control_balanced = max(
        models[kind]["metrics_by_scale"]["50"]["benefit"]["balanced_accuracy"] or 0.0
        for kind in ("mlp", "linear", "no_message", "shuffled_topology")
    )
    conflict_ok = conflicts["similar_opposite_label_fraction"] <= float(
        gate["maximum_similar_opposite_label_fraction"]
    )
    gat_ok = (
        gat_balanced is not None and gat_rank is not None
        and gat_balanced >= minimum_balanced and gat_rank >= minimum_rank
        and gat_balanced + float(gate["maximum_gat_gap_to_best_control"]) >= control_balanced
    )
    if not passing:
        decision, reason = "FAIL", "SCALE50_BENEFIT_HARM_NOT_SEPARABLE"
    elif not conflict_ok:
        decision, reason = "FAIL", "FRONTIER_FEATURES_NOT_IDENTIFIABLE"
    elif not gat_ok:
        decision, reason = "FAIL", "FRONTIER_PREDICTABLE_BUT_NOT_BY_GAT"
    else:
        decision, reason = "PASS", "FRONTIER_STATE_PREDICTABLE"
    return {
        "decision": decision,
        "reason": reason,
        "passing_model_kinds": passing,
        "gat_scale50_benefit_balanced_accuracy": gat_balanced,
        "gat_scale50_rank_accuracy": gat_rank,
        "best_control_scale50_benefit_balanced_accuracy": control_balanced,
        "similar_opposite_label_fraction": conflicts["similar_opposite_label_fraction"],
        "candidate_training_authorized_next": decision == "PASS",
        "candidate_trained_in_this_chain": False,
    }


if __name__ == "__main__":
    raise SystemExit(main())
