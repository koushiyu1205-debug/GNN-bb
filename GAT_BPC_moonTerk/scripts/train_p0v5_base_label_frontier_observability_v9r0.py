#!/usr/bin/env python3
"""Instance-grouped OOF observability gate for the 256-label base graph."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from math import exp, log, sqrt
from pathlib import Path
import statistics
import sys
from time import perf_counter
from typing import Any, Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.guidance.base_frontier_gat_qd1_v9 import (  # noqa: E402
    MODEL_KINDS,
    MODEL_SEEDS,
    BaseFrontierExample,
    build_base_frontier_model,
    graph_from_payload,
    graph_tensors,
    parameter_count,
    pooled_numeric_signature,
    shuffled_graph_tensors,
)
from lunar_ice_bpc.guidance.counterfactual_prefix_gat_qd1_v8 import (  # noqa: E402
    CONTEXT_FEATURE_NAMES,
    EDGE_FEATURE_NAMES,
    NODE_FEATURE_NAMES,
)
from scripts.p0v5_base_label_frontier_v9r0_common import (  # noqa: E402
    DEFAULT_RUN_ROOT,
    assert_active,
    load,
    stable_hash,
    update_state,
    write_once,
    write_terminal,
)


def _example(row: Mapping[str, Any]) -> BaseFrontierExample:
    target = dict(row["target"])
    value = BaseFrontierExample(
        graph=graph_from_payload(row["graph"]),
        context_id=str(row["context_id"]),
        instance_hash=str(row["instance_hash"]),
        state_hash=str(row["state_hash"]),
        scale=int(row["scale"]), ratio=float(target["ratio"]),
        benefit=int(target["benefit"]),
        positive_gain=float(target["positive_gain"]),
        adverse=int(target["adverse"]),
        qpf0_wall_seconds=float(row["qpf0_reference_wall_seconds"]),
        graph_build_wall_seconds=float(row["base_graph_build_wall_seconds"]),
    )
    value.validate()
    return value


def _normalization(
    examples: Iterable[BaseFrontierExample],
) -> dict[str, dict[str, list[float]]]:
    groups: dict[str, list[Sequence[float]]] = {
        "node": [], "edge": [], "context": [],
    }
    for example in examples:
        groups["node"].extend(example.graph.node_features)
        groups["edge"].extend(example.graph.edge_features)
        groups["context"].append(example.graph.context_features)
    widths = {
        "node": len(NODE_FEATURE_NAMES), "edge": len(EDGE_FEATURE_NAMES),
        "context": len(CONTEXT_FEATURE_NAMES),
    }
    output = {}
    for group, width in widths.items():
        columns = list(zip(*groups[group]))
        if len(columns) != width:
            raise SystemExit(f"normalization width drift:{group}")
        mean, scale, minimum, maximum = [], [], [], []
        for column in columns:
            values = [float(value) for value in column]
            center = statistics.fmean(values)
            variance = statistics.fmean((value - center) ** 2 for value in values)
            mean.append(center)
            scale.append(max(sqrt(variance), 1.0e-9))
            minimum.append(min(values))
            maximum.append(max(values))
        output[group] = {
            "mean": mean, "scale": scale,
            "minimum": minimum, "maximum": maximum,
        }
    return output


def _class_weights(examples: Iterable[BaseFrontierExample]) -> dict[str, dict[int, float]]:
    rows = tuple(examples)
    multiplicity: dict[str, int] = defaultdict(int)
    for row in rows:
        multiplicity[row.instance_hash] += 1
    output = {}
    for name in ("benefit", "adverse"):
        weighted = [
            (int(getattr(row, name)), 1.0 / multiplicity[row.instance_hash])
            for row in rows
        ]
        positive = sum(weight for label, weight in weighted if label == 1)
        negative = sum(weight for label, weight in weighted if label == 0)
        total = positive + negative
        output[name] = {
            0: 1.0 if negative == 0 else total / (2.0 * negative),
            1: 1.0 if positive == 0 else total / (2.0 * positive),
        }
    return output


def _loss(model, tensors, example, class_weights):
    import torch
    import torch.nn.functional as functional

    output = model(graph=tensors)
    benefit = torch.tensor(float(example.benefit), dtype=torch.float64)
    adverse = torch.tensor(float(example.adverse), dtype=torch.float64)
    loss = (
        class_weights["benefit"][example.benefit]
        * functional.binary_cross_entropy(output["p_benefit"], benefit)
    )
    loss = loss + (
        class_weights["adverse"][example.adverse]
        * functional.binary_cross_entropy(output["p_adverse"], adverse)
    )
    if example.benefit:
        target_gain = torch.tensor(example.positive_gain, dtype=torch.float64)
        loss = loss + 0.5 * functional.huber_loss(
            output["positive_gain"], target_gain
        )
    utility = (
        output["p_benefit"] * output["positive_gain"]
        - output["p_adverse"]
    )
    direction = torch.tensor(
        1.0 if example.ratio < 1.0 else -1.0, dtype=torch.float64
    )
    loss = loss + 0.25 * functional.softplus(-5.0 * direction * utility)
    return loss, output


def _fit_predict(
    train: list[BaseFrontierExample], validation: list[BaseFrontierExample],
    *, kind: str, seed: int, maximum_epochs: int, patience: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    import torch

    torch.set_num_threads(1)
    torch.manual_seed(seed)
    normalization = _normalization(train)
    class_weights = _class_weights(train)
    model = build_base_frontier_model(kind=kind).double()
    if parameter_count(model) >= 20_000:
        raise SystemExit("base-frontier model parameter cap exceeded")
    optimizer = torch.optim.Adam(
        model.parameters(), lr=2.0e-3, weight_decay=1.0e-5
    )
    counts: dict[str, int] = defaultdict(int)
    for example in train:
        counts[example.instance_hash] += 1
    train_cache = []
    for example in train:
        tensors = graph_tensors(example.graph, normalization)
        if kind == "shuffled_topology":
            tensors = shuffled_graph_tensors(tensors, state_hash=example.state_hash)
        train_cache.append((example, tensors, 1.0 / counts[example.instance_hash]))
    validation_counts: dict[str, int] = defaultdict(int)
    for example in validation:
        validation_counts[example.instance_hash] += 1
    validation_cache = []
    for example in validation:
        tensors = graph_tensors(example.graph, normalization)
        if kind == "shuffled_topology":
            tensors = shuffled_graph_tensors(tensors, state_hash=example.state_hash)
        validation_cache.append((
            example, tensors, 1.0 / validation_counts[example.instance_hash]
        ))
    best_state = None
    best_loss = float("inf")
    stale = 0
    curve = []
    for epoch in range(maximum_epochs):
        model.train()
        order = sorted(
            range(len(train_cache)),
            key=lambda index: stable_hash({
                "seed": seed, "epoch": epoch,
                "context": train_cache[index][0].context_id,
            }),
        )
        optimizer.zero_grad()
        total_weight = sum(row[2] for row in train_cache)
        combined = None
        for index in order:
            example, tensors, weight = train_cache[index]
            value, _ = _loss(model, tensors, example, class_weights)
            value = value * weight / total_weight
            combined = value if combined is None else combined + value
        assert combined is not None
        combined.backward()
        optimizer.step()
        model.eval()
        with torch.no_grad():
            validation_values = [
                (
                    float(_loss(model, tensors, example, class_weights)[0]),
                    weight,
                )
                for example, tensors, weight in validation_cache
            ]
        validation_loss = (
            sum(value * weight for value, weight in validation_values)
            / sum(weight for _, weight in validation_values)
            if validation_values else float(combined.detach())
        )
        curve.append({
            "epoch": epoch + 1, "train_loss": float(combined.detach()),
            "validation_loss": validation_loss,
        })
        if validation_loss < best_loss - 1.0e-8:
            best_loss = validation_loss
            stale = 0
            best_state = {
                name: value.detach().clone()
                for name, value in model.state_dict().items()
            }
        else:
            stale += 1
            if stale >= patience:
                break
    if best_state is not None:
        model.load_state_dict(best_state)
    model.eval()
    predictions = []
    with torch.no_grad():
        for example, tensors, _ in validation_cache:
            output = model(graph=tensors)
            predictions.append({
                "context_id": example.context_id,
                "instance_hash": example.instance_hash,
                "scale": example.scale,
                "ratio": example.ratio,
                "benefit": example.benefit,
                "adverse": example.adverse,
                "p_benefit": float(output["p_benefit"]),
                "positive_gain": float(output["positive_gain"]),
                "p_adverse": float(output["p_adverse"]),
            })
    return predictions, {
        "epochs_run": len(curve), "best_validation_loss": best_loss,
        "parameter_count": parameter_count(model), "curve": curve,
    }


def _instance_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(int(row["scale"]), str(row["instance_hash"]))].append(row)
    output = []
    for (scale, instance_hash), values in sorted(grouped.items()):
        ratio = exp(statistics.fmean(log(float(row["ratio"])) for row in values))
        output.append({
            "scale": scale, "instance_hash": instance_hash, "ratio": ratio,
            "benefit": int(ratio <= 0.98), "adverse": int(ratio >= 1.05),
            "p_benefit": statistics.fmean(float(row["p_benefit"]) for row in values),
            "positive_gain": statistics.fmean(float(row["positive_gain"]) for row in values),
            "p_adverse": statistics.fmean(float(row["p_adverse"]) for row in values),
        })
    return output


def _classification(rows: list[dict[str, Any]], target: str) -> dict[str, Any]:
    probability = "p_benefit" if target == "benefit" else "p_adverse"
    positive = [row for row in rows if int(row[target]) == 1]
    negative = [row for row in rows if int(row[target]) == 0]
    recall = (
        statistics.fmean(float(row[probability]) >= 0.5 for row in positive)
        if positive else None
    )
    specificity = (
        statistics.fmean(float(row[probability]) < 0.5 for row in negative)
        if negative else None
    )
    balanced = (
        0.5 * (recall + specificity)
        if recall is not None and specificity is not None else None
    )
    return {
        "balanced_accuracy": balanced, "recall": recall,
        "specificity": specificity, "positive_count": len(positive),
        "negative_count": len(negative),
        "brier": statistics.fmean(
            (float(row[probability]) - int(row[target])) ** 2 for row in rows
        ),
    }


def _rank_accuracy(rows: list[dict[str, Any]]) -> float:
    return statistics.fmean(
        (
            float(row["p_benefit"]) * float(row["positive_gain"])
            - float(row["p_adverse"])
            > 0.0
        ) == (float(row["ratio"]) < 1.0)
        for row in rows
    )


def _metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    instances = _instance_rows(rows)
    result = {}
    for scale in (30, 50):
        context = [row for row in rows if int(row["scale"]) == scale]
        instance = [row for row in instances if int(row["scale"]) == scale]
        result[str(scale)] = {
            "context": {
                "benefit": _classification(context, "benefit"),
                "adverse": _classification(context, "adverse"),
                "rank_accuracy": _rank_accuracy(context),
                "count": len(context),
            },
            "instance": {
                "benefit": _classification(instance, "benefit"),
                "adverse": _classification(instance, "adverse"),
                "rank_accuracy": _rank_accuracy(instance),
                "count": len(instance),
            },
        }
    result["combined_instance_rank_accuracy"] = _rank_accuracy(instances)
    return result


def _similar_opposite_fraction(examples: list[BaseFrontierExample]) -> float:
    rows = [row for row in examples if row.scale == 50]
    signatures = [list(pooled_numeric_signature(row)) for row in rows]
    columns = list(zip(*signatures))
    centers = [statistics.fmean(column) for column in columns]
    scales = [
        max(sqrt(statistics.fmean((value - center) ** 2 for value in column)), 1.0e-9)
        for column, center in zip(columns, centers)
    ]
    normalized = [
        [(value - center) / scale for value, center, scale in zip(row, centers, scales)]
        for row in signatures
    ]
    pairs = []
    for left in range(len(rows)):
        for right in range(left + 1, len(rows)):
            distance = sqrt(sum(
                (a - b) ** 2 for a, b in zip(normalized[left], normalized[right])
            ))
            pairs.append((
                distance,
                stable_hash((rows[left].context_id, rows[right].context_id)),
                rows[left].benefit != rows[right].benefit,
            ))
    count = max(1, int(len(pairs) * 0.10))
    return statistics.fmean(row[2] for row in sorted(pairs)[:count])


def _warm_inference_cost(examples, normalization):
    import torch

    torch.set_num_threads(1)
    models = []
    for seed in MODEL_SEEDS:
        torch.manual_seed(seed)
        models.append(build_base_frontier_model(kind="gat").double().eval())
    rows = []
    with torch.no_grad():
        for example in examples:
            for _ in range(3):
                tensors = graph_tensors(example.graph, normalization)
                for model in models:
                    model(graph=tensors)
            samples = []
            for _ in range(20):
                started = perf_counter()
                tensors = graph_tensors(example.graph, normalization)
                for model in models:
                    model(graph=tensors)
                samples.append(perf_counter() - started)
            preparation_and_inference = statistics.median(samples)
            total = preparation_and_inference + example.graph_build_wall_seconds
            rows.append({
                "context_id": example.context_id, "scale": example.scale,
                "graph_build_wall_seconds": example.graph_build_wall_seconds,
                "tensorization_plus_ensemble_inference_wall_seconds": (
                    preparation_and_inference
                ),
                "combined_wall_seconds": total,
                "fraction_of_qpf0": total / example.qpf0_wall_seconds,
            })
    ordered = sorted(float(row["combined_wall_seconds"]) for row in rows)
    p99 = ordered[max(0, int(0.99 * len(ordered) + 0.999999) - 1)]
    return rows, 1000.0 * p99, max(float(row["fraction_of_qpf0"]) for row in rows)


def run(run_root: Path) -> None:
    assert_active(run_root, "OOF_DIAGNOSTIC")
    config = load(run_root / "config.freeze.json")
    corpus = load(run_root / "corpus.freeze.json")
    examples = [_example(row) for row in corpus["rows"]]
    by_context = {row.context_id: row for row in examples}
    fold_by_instance = {
        str(row["instance_hash"]): int(row["fold"])
        for row in load(run_root / "folds.freeze.json")["rows"]
    }
    all_predictions = {}
    training_audit = {}
    for kind in MODEL_KINDS:
        seed_predictions: dict[str, list[dict[str, Any]]] = defaultdict(list)
        training_audit[kind] = {}
        for seed in MODEL_SEEDS:
            training_audit[kind][str(seed)] = []
            for fold in range(5):
                validation = [
                    row for row in examples
                    if fold_by_instance[row.instance_hash] == fold
                ]
                train = [
                    row for row in examples
                    if fold_by_instance[row.instance_hash] != fold
                ]
                predictions, audit = _fit_predict(
                    train, validation, kind=kind, seed=seed,
                    maximum_epochs=int(config["model"]["maximum_epochs"]),
                    patience=int(config["model"]["patience"]),
                )
                for row in predictions:
                    seed_predictions[row["context_id"]].append(row)
                training_audit[kind][str(seed)].append({"fold": fold, **audit})
        aggregate = []
        for context_id in sorted(by_context):
            rows = seed_predictions[context_id]
            if len(rows) != 3:
                raise SystemExit(f"OOF seed coverage drift:{kind}:{context_id}")
            truth = by_context[context_id]
            aggregate.append({
                "context_id": context_id, "instance_hash": truth.instance_hash,
                "scale": truth.scale, "ratio": truth.ratio,
                "benefit": truth.benefit, "adverse": truth.adverse,
                "p_benefit": statistics.fmean(float(row["p_benefit"]) for row in rows),
                "positive_gain": min(float(row["positive_gain"]) for row in rows),
                "p_adverse": max(float(row["p_adverse"]) for row in rows),
            })
        all_predictions[kind] = aggregate
    metrics = {kind: _metrics(rows) for kind, rows in all_predictions.items()}
    conflict = _similar_opposite_fraction(examples)
    normalization = _normalization(examples)
    cost_rows, p99_ms, maximum_fraction = _warm_inference_cost(
        examples, normalization
    )
    gat50 = metrics["gat"]["50"]["instance"]
    simple_ba = max(
        metrics[kind]["50"]["instance"]["benefit"]["balanced_accuracy"]
        for kind in ("mlp", "linear")
    )
    topology_rank = {
        kind: metrics[kind]["50"]["instance"]["rank_accuracy"]
        for kind in ("no_message", "shuffled_topology")
    }
    topology_drop = max(
        gat50["rank_accuracy"] - value for value in topology_rank.values()
    )
    gate_config = config["gate"]
    gate = {
        "scale50_benefit_balanced_accuracy": (
            gat50["benefit"]["balanced_accuracy"]
            >= float(gate_config["scale50_minimum_benefit_balanced_accuracy"])
        ),
        "scale50_rank_accuracy": (
            gat50["rank_accuracy"]
            >= float(gate_config["scale50_minimum_rank_accuracy"])
        ),
        "simple_control_gap": (
            gat50["benefit"]["balanced_accuracy"]
            >= simple_ba - float(gate_config["maximum_gap_below_best_simple_ba"])
        ),
        "topology_not_worse": all(
            gat50["rank_accuracy"] >= value for value in topology_rank.values()
        ),
        "topology_contribution": (
            topology_drop >= float(gate_config["minimum_topology_rank_drop"])
        ),
        "similar_opposite_fraction": (
            conflict <= float(gate_config["maximum_similar_opposite_label_fraction"])
        ),
        "warm_cost_p99": (
            p99_ms <= float(gate_config["warm_graph_plus_ensemble_inference_p99_ms"])
        ),
        "per_context_cost_fraction": (
            maximum_fraction
            <= float(gate_config["maximum_per_context_fraction_of_qpf0"])
        ),
    }
    passed = all(gate.values())
    write_once(run_root / "oof_predictions.json", {
        "schema_version": "lunar_ice_bpc.p0v5_base_label_frontier_oof.v1",
        "rows_by_model": all_predictions,
    })
    write_once(run_root / "training_audit.json", {
        "schema_version": "lunar_ice_bpc.p0v5_base_label_frontier_training_audit.v1",
        "models": training_audit,
    })
    write_once(run_root / "runtime_cost_diagnostic.json", {
        "schema_version": "lunar_ice_bpc.p0v5_base_label_frontier_cost.v1",
        "rows": cost_rows, "warm_p99_ms": p99_ms,
        "maximum_fraction_of_qpf0": maximum_fraction,
        "torch_inference_is_conservative_for_future_native_forward": True,
    })
    report = {
        "schema_version": "lunar_ice_bpc.p0v5_base_label_frontier_observability_report.v1",
        "decision": "PASS" if passed else "FAIL",
        "reason": (
            "BASE_LABEL_FRONTIER_IDENTIFIABLE"
            if passed else "BASE_LABEL_FRONTIER_NOT_IDENTIFIABLE"
        ),
        "metrics": metrics,
        "scale50_similar_opposite_label_fraction": conflict,
        "scale50_topology_rank_drop": topology_drop,
        "best_simple_scale50_benefit_balanced_accuracy": simple_ba,
        "warm_graph_plus_ensemble_inference_p99_ms": p99_ms,
        "maximum_per_context_fraction_of_qpf0": maximum_fraction,
        "gate": gate, "passed": passed,
        "baseline_v7r3": {
            "gat_scale50_benefit_balanced_accuracy": 0.6090909090909091,
            "gat_scale50_rank_accuracy": 0.525,
            "similar_opposite_label_fraction": 0.6470588235294118,
        },
        "diagnostic_only": True, "performance_authority": False,
    }
    write_once(run_root / "observability.report.json", report)
    if passed:
        update_state(
            run_root, "RUNTIME_IMPLEMENTATION", "READY",
            observability_report="observability.report.json",
        )
    else:
        write_terminal(
            run_root, reason="BASE_LABEL_FRONTIER_NOT_IDENTIFIABLE",
            detail={"report": "observability.report.json", "gate": gate},
        )
    print(json.dumps({
        "decision": report["decision"], "reason": report["reason"],
        "gate": gate,
    }, indent=2, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args()
    run(args.run_root.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
