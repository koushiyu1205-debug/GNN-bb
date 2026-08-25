#!/usr/bin/env python3
"""Train, grouped-CV audit, calibrate, and export Temporal-GAT v2."""

from __future__ import annotations

import argparse
from collections import defaultdict
from itertools import product
import hashlib
import json
from math import isfinite, log
from pathlib import Path
import sys
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.p0v5_temporal_gat_common import (  # noqa: E402
    load_frozen_config,
    mark_terminal_negative,
    write_once,
)

from lunar_ice_bpc.guidance.temporal_frontier_gat_v1 import (  # noqa: E402
    HEADS, HIDDEN, SEEDS, build_temporal_gat_model, export_temporal_bundle,
    temporal_graph_tensors,
)


def _torch():
    import torch

    torch.set_num_threads(1)
    return torch


def _validate_frozen_training_contract(config, *, epochs: int) -> None:
    model = dict(config["model"])
    training = dict(config["training"])
    expected = {
        "kind": "shared_temporal_multires_gat_scale_specific_heads",
        "hidden_size": HIDDEN,
        "attention_heads": HEADS,
        "layers": 2,
        "shared_trunk": [128, 64],
        "dropout": 0.1,
        "ensemble_seeds": list(SEEDS),
        "label_sample_cap": 256,
        "cell_node_count": 64,
    }
    if model != expected:
        raise SystemExit("frozen Temporal-GAT architecture contract drift")
    if (
        int(epochs) != int(training["epochs"])
        or float(training["learning_rate"]) != 1.0e-3
        or float(training["weight_decay"]) != 1.0e-5
        or int(training["instance_grouped_folds"]) != 5
        or str(training["normalization_scope"]) != "fold_train_only"
    ):
        raise SystemExit("frozen Temporal-GAT optimizer/CV contract drift")


def _values(rows, graph_key, value_key):
    for row in rows:
        graph = row["temporal_graph"]
        if graph_key in {"cell_t0", "cell_tk", "graph_t0", "graph_tk"}:
            source = graph[graph_key]
            if value_key == "edge_features":
                for edge in source["edges"]:
                    yield edge["features"]
            else:
                yield from source[value_key]
        else:
            yield graph[graph_key]


def fit_normalization(
    rows: list[dict[str, Any]], *, standard_deviation_radius: float,
) -> dict[str, dict[str, list[float]]]:
    sources = {
        "cell_node": [
            *list(_values(rows, "cell_t0", "node_features")),
            *list(_values(rows, "cell_tk", "node_features")),
        ],
        "cell_edge": [
            *list(_values(rows, "cell_t0", "edge_features")),
            *list(_values(rows, "cell_tk", "edge_features")),
        ],
        "node": [
            *list(_values(rows, "graph_t0", "node_features")),
            *list(_values(rows, "graph_tk", "node_features")),
        ],
        "edge": [
            *list(_values(rows, "graph_t0", "edge_features")),
            *list(_values(rows, "graph_tk", "edge_features")),
        ],
        "counter": list(_values(rows, "counter_features", "")),
        "context": list(_values(rows, "context_features", "")),
    }
    output = {}
    for name, values in sources.items():
        if not values:
            raise ValueError(f"normalization group is empty:{name}")
        width = len(values[0])
        if any(len(row) != width for row in values):
            raise ValueError(f"normalization width drift:{name}")
        mean = [sum(float(row[i]) for row in values) / len(values)
                for i in range(width)]
        variance = [sum((float(row[i]) - mean[i]) ** 2 for row in values) /
                    len(values) for i in range(width)]
        scale = [max(1.0e-12, value ** 0.5) for value in variance]
        output[name] = {
            "mean": mean,
            "scale": scale,
            "minimum": [
                mean[i] - float(standard_deviation_radius) * scale[i]
                for i in range(width)
            ],
            "maximum": [
                mean[i] + float(standard_deviation_radius) * scale[i]
                for i in range(width)
            ],
        }
    return output


def _shuffled_graph(graph: Mapping[str, Any], state_hash: str, suffix: str):
    copied = {key: value for key, value in graph.items()}
    edges = [dict(row) for row in graph["edges"]]
    node_count = len(graph["node_features"])
    offset = 1 + int(hashlib.sha256(
        f"{state_hash}:{suffix}".encode()
    ).hexdigest()[:8], 16) % max(1, node_count - 1)
    for row in edges:
        row["target"] = (int(row["target"]) + offset) % node_count
    copied["edges"] = edges
    return copied


def _inputs(row, normalization, *, shuffled=False):
    torch = _torch()
    payload = row["temporal_graph"]
    state_hash = str(row.get("state_hash") or row["context_id"])
    def graph(name, node_group, edge_group):
        value = payload[name]
        if shuffled:
            value = _shuffled_graph(value, state_hash, name)
        return temporal_graph_tensors(
            value, normalization, node_group=node_group, edge_group=edge_group
        )
    counter = torch.tensor(payload["counter_features"], dtype=torch.float64)
    context = torch.tensor(payload["context_features"], dtype=torch.float64)
    counter = (counter - torch.tensor(
        normalization["counter"]["mean"], dtype=torch.float64
    )) / torch.tensor(normalization["counter"]["scale"], dtype=torch.float64)
    context = (context - torch.tensor(
        normalization["context"]["mean"], dtype=torch.float64
    )) / torch.tensor(normalization["context"]["scale"], dtype=torch.float64)
    return {
        "cell_t0": graph("cell_t0", "cell_node", "cell_edge"),
        "cell_tk": graph("cell_tk", "cell_node", "cell_edge"),
        "label_t0": graph("graph_t0", "node", "edge"),
        "label_tk": graph("graph_tk", "node", "edge"),
        "counter_features": counter, "context_features": context,
        "scale": int(row["scale"]),
    }


def _prepared_inputs(rows, normalization, *, shuffled=False):
    return {
        id(row): _inputs(row, normalization, shuffled=shuffled)
        for row in rows
    }


def _train_gat(rows, normalization, seed, *, no_message=False,
               shuffled=False, epochs=120, prepared=None):
    torch = _torch()
    torch.manual_seed(int(seed))
    model = build_temporal_gat_model(no_message=no_message).double()
    optimizer = torch.optim.AdamW(model.parameters(), lr=1.0e-3, weight_decay=1e-5)
    bce = torch.nn.BCELoss(reduction="none")
    prepared = prepared or _prepared_inputs(
        rows, normalization, shuffled=shuffled
    )
    for epoch in range(int(epochs)):
        model.train()
        ordered = sorted(rows, key=lambda row: hashlib.sha256(
            f"{seed}:{epoch}:{row['context_id']}".encode()
        ).hexdigest())
        optimizer.zero_grad()
        for index, row in enumerate(ordered):
            output = model(**prepared[id(row)])
            weight = float(row["instance_balance_weight"])
            loss = weight * (
                bce(output["p_benefit"], torch.tensor(
                    float(row["benefit"]), dtype=torch.float64
                )) +
                bce(output["p_adverse"], torch.tensor(
                    float(row["adverse"]), dtype=torch.float64
                )) +
                torch.nn.functional.smooth_l1_loss(
                    output["positive_gain"], torch.tensor(
                        float(row["positive_gain"]), dtype=torch.float64
                    )
                )
            ) / max(1, len(ordered))
            loss.backward()
            if index + 1 == len(ordered):
                torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
                optimizer.step()
    return model.eval()


def _simple_features(row, normalization):
    torch = _torch()
    payload = row["temporal_graph"]
    counter = torch.tensor(payload["counter_features"], dtype=torch.float64)
    context = torch.tensor(payload["context_features"], dtype=torch.float64)
    counter = (counter - torch.tensor(
        normalization["counter"]["mean"], dtype=torch.float64
    )) / torch.tensor(normalization["counter"]["scale"], dtype=torch.float64)
    context = (context - torch.tensor(
        normalization["context"]["mean"], dtype=torch.float64
    )) / torch.tensor(normalization["context"]["scale"], dtype=torch.float64)
    scale = torch.tensor([
        float(int(row["scale"]) == 30), float(int(row["scale"]) == 50)
    ], dtype=torch.float64)
    return torch.cat((counter, context, scale))


def _train_simple(
    rows, normalization, seed, *, kind, epochs, prepared=None,
):
    torch = _torch()
    torch.manual_seed(int(seed))
    model = (
        torch.nn.Linear(54, 3) if kind == "linear" else
        torch.nn.Sequential(
            torch.nn.Linear(54, 64), torch.nn.ReLU(),
            torch.nn.Linear(64, 3),
        )
    ).double()
    optimizer = torch.optim.AdamW(model.parameters(), lr=1.0e-3)
    prepared = prepared or {
        id(row): _simple_features(row, normalization) for row in rows
    }
    for epoch in range(int(epochs)):
        model.train()
        optimizer.zero_grad()
        losses = []
        for row in rows:
            values = torch.sigmoid(model(prepared[id(row)]))
            labels = torch.tensor([
                float(row["benefit"]), float(row["positive_gain"]),
                float(row["adverse"]),
            ], dtype=torch.float64)
            loss = (
                torch.nn.functional.binary_cross_entropy(values[0], labels[0]) +
                torch.nn.functional.smooth_l1_loss(values[1], labels[1]) +
                torch.nn.functional.binary_cross_entropy(values[2], labels[2])
            ) * float(row["instance_balance_weight"])
            losses.append(loss)
        (sum(losses) / max(1, len(losses))).backward()
        optimizer.step()
    return model.eval()


def _is_ood(row, normalization) -> bool:
    """Mirror the Native frozen fold-train mean +/- 8 sigma veto exactly."""
    payload = row["temporal_graph"]

    def outside(values, group_name):
        group = normalization[group_name]
        minimum = group["minimum"]
        maximum = group["maximum"]
        return any(
            len(values_row) != len(minimum) or any(
                not isfinite(float(value))
                or float(value) < float(minimum[index])
                or float(value) > float(maximum[index])
                for index, value in enumerate(values_row)
            )
            for values_row in values
        )

    for graph_name, node_group, edge_group in (
        ("cell_t0", "cell_node", "cell_edge"),
        ("cell_tk", "cell_node", "cell_edge"),
        ("graph_t0", "node", "edge"),
        ("graph_tk", "node", "edge"),
    ):
        graph = payload[graph_name]
        if outside(graph["node_features"], node_group) or outside(
            (edge["features"] for edge in graph["edges"]), edge_group
        ):
            return True
    return outside((payload["counter_features"],), "counter") or outside(
        (payload["context_features"],), "context"
    )


def _predict_simple(models, rows, normalization, *, prepared=None):
    torch = _torch()
    output = []
    prepared = prepared or {
        id(row): _simple_features(row, normalization) for row in rows
    }
    with torch.inference_mode():
        for row in rows:
            values = [
                torch.sigmoid(model(prepared[id(row)]))
                for model in models
            ]
            output.append({
                **{key: row[key] for key in (
                    "context_id", "instance_hash", "scale", "benefit",
                    "adverse", "positive_gain", "continue_vs_revert_ratio",
                    "instance_balance_weight",
                )},
                "p_benefit": sum(float(value[0]) for value in values) / len(values),
                "positive_gain_prediction": min(float(value[1]) for value in values),
                "p_adverse": max(float(value[2]) for value in values),
                "disagreement": max(
                    max(float(value[index]) for value in values) -
                    min(float(value[index]) for value in values)
                    for index in range(3)
                ),
                "ood": _is_ood(row, normalization),
            })
    return output


def _predict(
    models, rows, normalization, *, shuffled=False, prepared=None,
):
    torch = _torch()
    output = []
    prepared = prepared or _prepared_inputs(
        rows, normalization, shuffled=shuffled
    )
    with torch.inference_mode():
        for row in rows:
            values = [
                model(**prepared[id(row)])
                for model in models
            ]
            output.append({
                **{key: row[key] for key in (
                    "context_id", "instance_hash", "scale", "benefit",
                    "adverse", "positive_gain", "continue_vs_revert_ratio",
                    "instance_balance_weight",
                )},
                "p_benefit": sum(float(value["p_benefit"]) for value in values) /
                    len(values),
                "positive_gain_prediction": min(
                    float(value["positive_gain"]) for value in values
                ),
                "p_adverse": max(float(value["p_adverse"]) for value in values),
                "disagreement": max(
                    max(float(value[name]) for value in values) -
                    min(float(value[name]) for value in values)
                    for name in ("p_benefit", "positive_gain", "p_adverse")
                ),
                "ood": _is_ood(row, normalization),
            })
    return output


def _balanced_accuracy(rows, score, label, threshold=0.5):
    positives = [row for row in rows if int(row[label]) == 1]
    negatives = [row for row in rows if int(row[label]) == 0]
    if not positives or not negatives:
        return None
    positive_weight = sum(float(row["instance_balance_weight"]) for row in positives)
    negative_weight = sum(float(row["instance_balance_weight"]) for row in negatives)
    sensitivity = sum(
        float(row["instance_balance_weight"])
        for row in positives if float(row[score]) >= threshold
    ) / positive_weight
    specificity = sum(
        float(row["instance_balance_weight"])
        for row in negatives if float(row[score]) < threshold
    ) / negative_weight
    return 0.5 * (sensitivity + specificity)


def _policy_utility(rows):
    weighted_logs = []
    for row in rows:
        ratio = row.get("continue_vs_revert_ratio")
        if ratio is None or float(ratio) <= 0.0:
            continue
        selected = (
            not bool(row.get("ood")) and
            float(row["p_benefit"]) >= 0.5 and
            float(row["p_adverse"]) <= 0.5 and
            float(row["positive_gain_prediction"]) > 0.0
        )
        weight = float(row["instance_balance_weight"])
        weighted_logs.append((weight, log(float(ratio) if selected else 1.0)))
    total_weight = sum(row[0] for row in weighted_logs)
    return None if not weighted_logs or total_weight <= 0.0 else pow(
        2.718281828459045,
        sum(weight * value for weight, value in weighted_logs) / total_weight,
    )


def _deterministic_control(rows, action):
    ratios = [
        (float(row["continue_vs_revert_ratio"]),
         float(row["instance_balance_weight"]))
        for row in rows
        if row.get("continue_vs_revert_ratio") is not None
        and float(row["continue_vs_revert_ratio"]) > 0.0
    ]
    if not ratios:
        return None
    total_weight = sum(weight for _, weight in ratios)
    return pow(2.718281828459045, sum(
        weight * log(value if action == "CONTINUE_QD1" else 1.0)
        for value, weight in ratios
    ) / total_weight)


def _gain_scale(rows):
    numerator = sum(
        float(row["positive_gain_prediction"]) * float(row["positive_gain"])
        for row in rows
    )
    denominator = sum(
        float(row["positive_gain_prediction"]) ** 2 for row in rows
    )
    value = 1.0 if denominator <= 1.0e-15 else numerator / denominator
    value = max(0.0, min(10.0, float(value)))
    if not isfinite(value):
        raise ValueError("CALIBRATION_NONFINITE_GAIN_SCALE")
    return value


def _platt(rows, score, label):
    torch = _torch()
    if len({int(row[label]) for row in rows}) < 2:
        probability = sum(int(row[label]) for row in rows) / max(1, len(rows))
        return {"kind": "constant", "probability": probability}
    logits = torch.tensor([
        log(max(1e-7, min(1 - 1e-7, float(row[score]))) /
            (1 - max(1e-7, min(1 - 1e-7, float(row[score])))))
        for row in rows
    ], dtype=torch.float64)
    labels = torch.tensor([float(row[label]) for row in rows], dtype=torch.float64)
    a = torch.nn.Parameter(torch.tensor(1.0, dtype=torch.float64))
    b = torch.nn.Parameter(torch.tensor(0.0, dtype=torch.float64))
    optimizer = torch.optim.LBFGS([a, b], max_iter=80, line_search_fn="strong_wolfe")
    def closure():
        optimizer.zero_grad()
        loss = torch.nn.functional.binary_cross_entropy_with_logits(a * logits + b, labels)
        loss.backward()
        return loss
    optimizer.step(closure)
    fitted_a = float(a.detach())
    fitted_b = float(b.detach())
    if not isfinite(fitted_a) or not isfinite(fitted_b):
        raise ValueError("CALIBRATION_NONFINITE_PLATT")
    return {"kind": "platt", "a": fitted_a, "b": fitted_b}


def _calibrated(value, row):
    if row["kind"] == "constant":
        return float(row["probability"])
    bounded = max(1e-7, min(1 - 1e-7, float(value)))
    logit = log(bounded / (1 - bounded))
    return 1.0 / (1.0 + pow(2.718281828459045,
                           -(float(row["a"]) * logit + float(row["b"]))))


def _select_thresholds(rows, grid, calibration):
    candidates = []
    for benefit, adverse, gain, disagreement in product(
        grid["minimum_benefit_probability"],
        grid["maximum_adverse_probability"],
        grid["minimum_expected_gain"], grid["maximum_disagreement"],
    ):
        activated = []
        for row in rows:
            if bool(row.get("ood")):
                continue
            p_benefit = _calibrated(row["p_benefit"], calibration["benefit"])
            p_adverse = _calibrated(row["p_adverse"], calibration["adverse"])
            expected = p_benefit * min(
                1.0, row["positive_gain_prediction"] * calibration["gain_scale"]
            )
            if (p_benefit >= benefit and p_adverse <= adverse and
                expected >= gain and expected - p_adverse > 0 and
                row["disagreement"] <= disagreement):
                activated.append(row)
        instances = {row["instance_hash"] for row in activated}
        harms = sum(int(row["adverse"]) for row in activated)
        # Exact one-sided upper bound when no observed activation harm.
        harm_upper = 1.0 if harms or not activated else 1.0 - pow(0.05, 1 / len(activated))
        if len(instances) >= 4 and harms == 0 and harm_upper <= 0.10:
            candidates.append((
                len(activated), len(instances), float(benefit),
                -float(adverse), float(gain), -float(disagreement),
                {"minimum_benefit_probability": float(benefit),
                 "maximum_adverse_probability": float(adverse),
                 "minimum_expected_gain": float(gain),
                 "adverse_penalty": 1.0,
                 "maximum_disagreement": float(disagreement)},
                harm_upper,
            ))
    if not candidates:
        raise ValueError("CALIBRATION_NO_SAFE_THRESHOLD")
    # Coverage is primary. Ties choose the more conservative frozen point:
    # higher benefit/gain, lower adverse/disagreement.
    selected = max(candidates, key=lambda row: row[:6])
    return selected[6], {"activated_rows": selected[0],
                         "activated_instances": selected[1],
                         "harm_upper_95": selected[7]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--k-selection", type=Path, required=True)
    parser.add_argument("--source-freeze", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=120)
    args = parser.parse_args()
    try:
        config, config_freeze_path = load_frozen_config(
            args.config, run_root=args.source_freeze.resolve().parent
        )
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    _validate_frozen_training_contract(config, epochs=args.epochs)
    if dict(config.get("ood_policy") or {}) != {
        "kind": "per_feature_fold_train_mean_std_envelope_v1",
        "standard_deviation_radius": 8.0,
        "zero_variance_epsilon": 1.0e-12,
    }:
        raise SystemExit("frozen Temporal-GAT OOD contract drift")
    ood_radius = float(config["ood_policy"]["standard_deviation_radius"])
    dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
    k_selection = json.loads(args.k_selection.read_text(encoding="utf-8"))
    selected_k = k_selection["selected_k_by_scale"]
    source = json.loads(args.source_freeze.read_text(encoding="utf-8"))
    source_freeze_sha256 = hashlib.sha256(
        args.source_freeze.read_bytes()
    ).hexdigest()
    config_freeze_sha256 = hashlib.sha256(
        config_freeze_path.read_bytes()
    ).hexdigest()
    if (
        dataset.get("source_config_freeze_sha256") != config_freeze_sha256
        or dataset.get("source_freeze_sha256") != source_freeze_sha256
        or k_selection.get("source_config_freeze_sha256")
            != config_freeze_sha256
        or k_selection.get("status")
            != "FIXED_BEFORE_CALIBRATION_AND_HELDOUT"
    ):
        raise SystemExit("dataset/K/source immutable binding drift")
    corpus_path = Path(source["corpus_manifest"]).resolve()
    if not corpus_path.is_file() or hashlib.sha256(
        corpus_path.read_bytes()
    ).hexdigest() != source["corpus_manifest_sha256"]:
        raise SystemExit("frozen corpus/source binding drift")
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    corpus_partition = {
        str(row["instance_content_hash"]): str(row["partition"])
        for row in corpus["rows"]
    }
    for row in dataset["rows"]:
        instance_hash = str(row.get("instance_hash") or "")
        partition = str(row.get("partition") or "")
        if (
            instance_hash not in corpus_partition
            or corpus_partition[instance_hash] != partition
            or partition not in {"train", "calibration"}
        ):
            raise SystemExit("dataset partition/corpus leakage boundary drift")
    rows = [dict(row) for row in dataset["rows"] if row.get("supervised") and
            int(row["k"]) == int(selected_k[str(row["scale"])])]
    train = [row for row in rows if row["partition"] == "train"]
    calibration_rows = [row for row in rows if row["partition"] == "calibration"]
    if not train or not calibration_rows:
        mark_terminal_negative(
            args.source_freeze.resolve().parent,
            stage="TRAINING_INPUT_GATE",
            reason="TRAIN_OR_CALIBRATION_SUPERVISION_EMPTY",
            detail={
                "train_supervised_rows": len(train),
                "calibration_supervised_rows": len(calibration_rows),
            },
        )
        raise SystemExit("train/calibration Temporal-GAT rows are incomplete")
    if any(not str(row.get("engine_hash") or "") or not str(
        row.get("config_hash") or ""
    ) for row in rows):
        raise SystemExit("Temporal-GAT rows have an unbound engine/config")
    if {str(row["engine_hash"]) for row in rows} != {
        str(source["exact_engine_hash"])
    }:
        raise SystemExit("Temporal-GAT row/source engine hash drift")
    for scale in (30, 50):
        calibration_instances = {
            str(row["instance_hash"]) for row in calibration_rows
            if int(row["scale"]) == scale
        }
        frozen_calibration_instances = {
            instance_hash for instance_hash, partition in corpus_partition.items()
            if partition == "calibration" and any(
                int(value["scale"]) == scale and
                str(value["instance_content_hash"]) == instance_hash
                for value in corpus["rows"]
            )
        }
        if not calibration_instances.issubset(frozen_calibration_instances):
            raise SystemExit(f"scale{scale} calibration leakage boundary drift")
    folds = {
        instance: int(hashlib.sha256(f"temporal-fold:{instance}".encode()).hexdigest(), 16) % 5
        for instance in {row["instance_hash"] for row in train}
    }
    oof = []
    no_message_oof = []
    linear_oof = []
    mlp_oof = []
    shuffled_oof = []
    for fold in range(5):
        fold_train = [row for row in train if folds[row["instance_hash"]] != fold]
        fold_test = [row for row in train if folds[row["instance_hash"]] == fold]
        if not fold_train or not fold_test:
            mark_terminal_negative(
                args.source_freeze.resolve().parent, stage="GROUPED_CV",
                reason="EMPTY_HASH_GROUPED_CV_FOLD",
                detail={"fold": fold, "train_rows": len(fold_train),
                        "test_rows": len(fold_test)},
            )
            raise SystemExit("EMPTY_HASH_GROUPED_CV_FOLD")
        normalization = fit_normalization(
            fold_train, standard_deviation_radius=ood_radius
        )
        gat_train_inputs = _prepared_inputs(fold_train, normalization)
        gat_test_inputs = _prepared_inputs(fold_test, normalization)
        shuffled_test_inputs = _prepared_inputs(
            fold_test, normalization, shuffled=True
        )
        shuffled_train_inputs = _prepared_inputs(
            fold_train, normalization, shuffled=True
        )
        simple_train_inputs = {
            id(row): _simple_features(row, normalization)
            for row in fold_train
        }
        simple_test_inputs = {
            id(row): _simple_features(row, normalization)
            for row in fold_test
        }
        models = [_train_gat(
            fold_train, normalization, seed, epochs=args.epochs,
            prepared=gat_train_inputs,
        ) for seed in SEEDS]
        oof.extend(_predict(
            models, fold_test, normalization, prepared=gat_test_inputs
        ))
        no_message_models = [_train_gat(
            fold_train, normalization, seed, no_message=True,
            epochs=args.epochs, prepared=gat_train_inputs,
        ) for seed in SEEDS]
        no_message_oof.extend(_predict(
            no_message_models, fold_test, normalization,
            prepared=gat_test_inputs,
        ))
        linear_oof.extend(_predict_simple([
            _train_simple(
                fold_train, normalization, seed, kind="linear",
                epochs=args.epochs, prepared=simple_train_inputs,
            ) for seed in SEEDS
        ], fold_test, normalization, prepared=simple_test_inputs))
        mlp_oof.extend(_predict_simple([
            _train_simple(
                fold_train, normalization, seed, kind="mlp",
                epochs=args.epochs, prepared=simple_train_inputs,
            ) for seed in SEEDS
        ], fold_test, normalization, prepared=simple_test_inputs))
        shuffled_models = [_train_gat(
            fold_train, normalization, seed, shuffled=True,
            epochs=args.epochs, prepared=shuffled_train_inputs,
        ) for seed in SEEDS]
        shuffled_oof.extend(_predict(
            shuffled_models, fold_test, normalization, shuffled=True,
            prepared=shuffled_test_inputs,
        ))
    normalization = fit_normalization(
        train, standard_deviation_radius=ood_radius
    )
    final_gat_train_inputs = _prepared_inputs(train, normalization)
    final_simple_train_inputs = {
        id(row): _simple_features(row, normalization) for row in train
    }
    models = [(seed, _train_gat(
        train, normalization, seed, epochs=args.epochs,
        prepared=final_gat_train_inputs,
    )) for seed in SEEDS]
    final_controls = {
        "no_message": [(seed, _train_gat(
            train, normalization, seed, no_message=True, epochs=args.epochs,
            prepared=final_gat_train_inputs,
        )) for seed in SEEDS],
        "linear": [(seed, _train_simple(
            train, normalization, seed, kind="linear", epochs=args.epochs,
            prepared=final_simple_train_inputs,
        )) for seed in SEEDS],
        "mlp": [(seed, _train_simple(
            train, normalization, seed, kind="mlp", epochs=args.epochs,
            prepared=final_simple_train_inputs,
        )) for seed in SEEDS],
    }
    def scale50(rows):
        return [row for row in rows if int(row["scale"]) == 50]
    scale50_oof = scale50(oof)
    gat_ba = _balanced_accuracy(scale50_oof, "p_benefit", "benefit")
    control_rows = {
        "no_message": scale50(no_message_oof),
        "linear": scale50(linear_oof), "mlp": scale50(mlp_oof),
    }
    control_ba = {
        name: _balanced_accuracy(value, "p_benefit", "benefit")
        for name, value in control_rows.items()
    }
    control_utility = {
        name: _policy_utility(value) for name, value in control_rows.items()
    }
    gat_utility = _policy_utility(scale50_oof)
    shuffled_ba = _balanced_accuracy(
        scale50(shuffled_oof), "p_benefit", "benefit"
    )
    comparable_ba = [value for value in control_ba.values() if value is not None]
    comparable_utility = [
        value for value in control_utility.values() if value is not None
    ]
    representation_gate = bool(
        gat_ba is not None and gat_utility is not None and comparable_ba and
        comparable_utility and gat_ba > max(comparable_ba) and
        gat_utility < min(comparable_utility) and shuffled_ba is not None and
        gat_ba - shuffled_ba >= float(config["representation_gates"][
            "shuffled_topology_ba_degradation_at_least"
        ])
    )
    deterministic_by_scale = {}
    best_e2e_control_by_scale = {}
    for scale in (30, 50):
        selected_rows = [row for row in oof if int(row["scale"]) == scale]
        values = {
            action: _deterministic_control(selected_rows, action)
            for action in ("CONTINUE_QD1", "MIGRATE_BACK_TO_Q0")
        }
        deterministic_by_scale[str(scale)] = values
        simple_predictions = {
            "no_message": no_message_oof,
            "linear": linear_oof,
            "mlp": mlp_oof,
        }
        simple_values = {
            name: _policy_utility([
                row for row in predictions if int(row["scale"]) == scale
            ]) for name, predictions in simple_predictions.items()
        }
        eligible = {
            f"deterministic:{name}": value for name, value in values.items()
            if value is not None
        }
        eligible.update({
            f"simple:{name}": value for name, value in simple_values.items()
            if value is not None
        })
        if not eligible:
            mark_terminal_negative(
                args.source_freeze.resolve().parent,
                stage="CONTROL_GATE",
                reason=f"SCALE{scale}_DETERMINISTIC_CONTROL_UNAVAILABLE",
                detail={"scale": scale, "oof_row_count": len(selected_rows)},
            )
            raise SystemExit(f"scale{scale} deterministic control is unavailable")
        selected_name = min(eligible, key=lambda name: (eligible[name], name))
        family, name = selected_name.split(":", 1)
        best_e2e_control_by_scale[str(scale)] = {
            "family": family,
            "name": name,
            "policy_utility": eligible[selected_name],
            "force_action": name if family == "deterministic" else "",
        }
        deterministic_by_scale[str(scale)]["simple_controls"] = simple_values
    control_audit = {
        "gat_scale50_oof_benefit_ba": gat_ba,
        "gat_scale50_oof_policy_utility": gat_utility,
        "control_scale50_oof_benefit_ba": control_ba,
        "control_scale50_oof_policy_utility": control_utility,
        "shuffled_topology_scale50_oof_benefit_ba": shuffled_ba,
        "representation_gate_pass": representation_gate,
        "deterministic_control_policy_utility_by_scale": (
            deterministic_by_scale
        ),
        "best_e2e_control_by_scale": best_e2e_control_by_scale,
        "always_continue_and_revert_retained": True,
    }
    if not representation_gate:
        terminal = args.output_dir.resolve() / "terminal_negative.json"
        terminal.parent.mkdir(parents=True, exist_ok=True)
        terminal.write_text(json.dumps({
            "status": "TERMINATED_NEGATIVE",
            "reason": "TEMPORAL_GAT_DID_NOT_BEAT_SIMPLE_OR_TOPOLOGY_CONTROL",
            "control_audit": control_audit,
            "deployment_authorized": False,
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        mark_terminal_negative(
            args.source_freeze.resolve().parent,
            stage="REPRESENTATION_GATE",
            reason="TEMPORAL_GAT_DID_NOT_BEAT_SIMPLE_OR_TOPOLOGY_CONTROL",
            detail=control_audit,
        )
        raise SystemExit("Temporal-GAT representation gate failed")
    calibration_inputs = _prepared_inputs(calibration_rows, normalization)
    calibration_predictions = _predict(
        [row[1] for row in models], calibration_rows, normalization,
        prepared=calibration_inputs,
    )
    calibration_by_scale = {}
    thresholds_by_scale = {}
    threshold_audit = {}
    try:
        for scale in (30, 50):
            selected = [
                row for row in calibration_predictions if row["scale"] == scale
            ]
            calibratable = [row for row in selected if not bool(row.get("ood"))]
            if not calibratable:
                raise ValueError(f"CALIBRATION_ALL_OOD_SCALE{scale}")
            value = {
                "benefit": _platt(calibratable, "p_benefit", "benefit"),
                "adverse": _platt(calibratable, "p_adverse", "adverse"),
                "gain_scale": _gain_scale(calibratable),
            }
            calibration_by_scale[str(scale)] = value
            thresholds_by_scale[str(scale)], threshold_audit[str(scale)] = (
                _select_thresholds(selected, config["threshold_grid"], value)
            )
            threshold_audit[str(scale)]["calibration_ood_rows"] = (
                len(selected) - len(calibratable)
            )
    except ValueError as exc:
        mark_terminal_negative(
            args.source_freeze.resolve().parent, stage="CALIBRATION_GATE",
            reason=str(exc), detail={
                "calibration_prediction_count": len(calibration_predictions),
                "threshold_grid": config["threshold_grid"],
            },
        )
        raise SystemExit(str(exc)) from exc
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    bundle = export_temporal_bundle(
        models=models, normalization=normalization,
        calibration_by_scale=calibration_by_scale,
        thresholds_by_scale=thresholds_by_scale,
        trial_pop_budget_by_scale=selected_k,
        boundary_by_scale=config["boundary_by_scale"],
        bindings={
            "engine_hashes": sorted({str(row["engine_hash"]) for row in rows}),
            # Live request config hashes include per-RMP/request state.  Keep
            # them for traceability, never as a production allowlist.
            "source_request_config_hashes_observed_diagnostic_only": sorted({
                str(row["config_hash"]) for row in rows
            }),
            "selected_exact_config_sha256": source[
                "selected_exact_config_sha256"
            ],
            "dataset_sha256": hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
            "k_selection_sha256": hashlib.sha256(
                args.k_selection.read_bytes()
            ).hexdigest(),
            "source_freeze_sha256": hashlib.sha256(
                args.source_freeze.read_bytes()
            ).hexdigest(),
            "experiment_config_sha256": hashlib.sha256(
                config_freeze_path.read_bytes()
            ).hexdigest(),
            "native_binary_sha256": source["native_binary_sha256"],
        },
        evaluation_controls=final_controls,
        output_path=output / "temporal_frontier_gat_bundle.v2.json",
    )
    bundle_path = output / "temporal_frontier_gat_bundle.v2.json"
    report = {
        "schema_version": "lunar_ice_bpc.p0v5_temporal_gat_training_report.v1",
        "status": "TRAINED_DEVELOPMENT_ONLY_NOT_PROMOTED",
        "grouped_cv_fold_count": 5, "instance_grouped": True,
        "normalization_fit_on_fold_train_only": True,
        "ensemble_seeds": list(SEEDS), "control_audit": control_audit,
        "threshold_audit": threshold_audit,
        "bundle_sha256": bundle["bundle_sha256"],
        "bundle_file_sha256": hashlib.sha256(
            bundle_path.read_bytes()
        ).hexdigest(),
        "dataset_sha256": hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
        "k_selection_sha256": hashlib.sha256(
            args.k_selection.read_bytes()
        ).hexdigest(),
        "source_freeze_sha256": hashlib.sha256(
            args.source_freeze.read_bytes()
        ).hexdigest(),
        "experiment_config_sha256": hashlib.sha256(
            config_freeze_path.read_bytes()
        ).hexdigest(),
        "deployment_authorized": False, "production_switch_authorized": False,
    }
    training_report_path = output / "training_report.json"
    write_once(training_report_path, report)
    runtime_manifest = {
        "schema_version": "lunar_ice_bpc.p0v5_temporal_frontier_runtime_manifest.v1",
        "runtime_policy": "P0V4_V5_ROOT_TEMPORAL_GAT_QD1_REVERSIBLE_V1",
        "action_universe": ["CONTINUE_QD1", "MIGRATE_BACK_TO_Q0"],
        "allowed_scales": [30, 50],
        "pricing_lifecycle_authority": "root_cg_only",
        "boundary_by_scale": config["boundary_by_scale"],
        "trial_pop_budget_by_scale": selected_k,
        "portable_bundle_path": bundle_path.name,
        "portable_bundle_file_sha256": hashlib.sha256(
            bundle_path.read_bytes()
        ).hexdigest(),
        "allowed_exact_engine_hashes": sorted({
            str(row["engine_hash"]) for row in rows
        }),
        "selected_exact_config_sha256": source[
            "selected_exact_config_sha256"
        ],
        "native_binary_sha256": source["native_binary_sha256"],
        "source_freeze_sha256": source_freeze_sha256,
        "experiment_config_sha256": config_freeze_sha256,
        "training_report_path": training_report_path.name,
        "training_report_sha256": hashlib.sha256(
            training_report_path.read_bytes()
        ).hexdigest(),
        "development_e2e_authorized": True,
        "deployment_authorized": False,
        "production_switch_authorized": False,
    }
    write_once(output / "runtime_manifest.development.json", runtime_manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
