#!/usr/bin/env python3
"""Instance-grouped OOF gate for the single-timepoint multi-resolution GAT."""

from __future__ import annotations

import argparse
from collections import defaultdict
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
    BaseFrontierExample,
    graph_from_payload,
)
from lunar_ice_bpc.guidance.counterfactual_prefix_gat_qd1_v8 import (  # noqa: E402
    CONTEXT_FEATURE_NAMES,
    EDGE_FEATURE_NAMES as LABEL_EDGE_FEATURE_NAMES,
    NODE_FEATURE_NAMES as LABEL_NODE_FEATURE_NAMES,
)
from lunar_ice_bpc.guidance.frontier_gat_qd1_v7 import (  # noqa: E402
    EDGE_FEATURE_NAMES as CELL_EDGE_FEATURE_NAMES,
    NODE_FEATURE_NAMES as CELL_NODE_FEATURE_NAMES,
)
from lunar_ice_bpc.guidance.multires_frontier_gat_qd1_v9 import (  # noqa: E402
    MODEL_KINDS,
    MODEL_SEEDS,
    MultiResolutionExample,
    build_multires_model,
    cell_graph_from_payload,
    multires_tensors,
    parameter_count,
    pooled_numeric_signature,
    shuffled_multires_tensors,
)
from scripts.p0v5_multires_frontier_v9r1_common import (  # noqa: E402
    DEFAULT_RUN_ROOT,
    assert_active,
    load,
    stable_hash,
    update_state,
    write_once,
    write_terminal,
)


def _example(row: Mapping[str, Any]) -> MultiResolutionExample:
    target = dict(row["target"])
    label = BaseFrontierExample(
        graph=graph_from_payload(row["label_graph"]),
        context_id=str(row["context_id"]),
        instance_hash=str(row["instance_hash"]),
        state_hash=str(row["state_hash"]),
        scale=int(row["scale"]),
        ratio=float(target["ratio"]),
        benefit=int(target["benefit"]),
        positive_gain=float(target["positive_gain"]),
        adverse=int(target["adverse"]),
        qpf0_wall_seconds=float(row["qpf0_reference_wall_seconds"]),
        graph_build_wall_seconds=float(row["label_graph_build_wall_seconds"]),
    )
    value = MultiResolutionExample(
        label=label,
        cell=cell_graph_from_payload(row["cell_graph"]),
        cell_graph_build_wall_seconds=float(row["cell_graph_build_wall_seconds"]),
    )
    value.validate()
    return value


def _normalization(
    examples: Iterable[MultiResolutionExample],
) -> dict[str, dict[str, list[float]]]:
    groups: dict[str, list[Sequence[float]]] = {
        "label_node": [], "label_edge": [], "cell_node": [],
        "cell_edge": [], "context": [],
    }
    for example in examples:
        groups["label_node"].extend(example.label.graph.node_features)
        groups["label_edge"].extend(example.label.graph.edge_features)
        groups["cell_node"].extend(example.cell.node_features)
        groups["cell_edge"].extend(example.cell.edge_features)
        groups["context"].append(example.label.graph.context_features)
    widths = {
        "label_node": len(LABEL_NODE_FEATURE_NAMES),
        "label_edge": len(LABEL_EDGE_FEATURE_NAMES),
        "cell_node": len(CELL_NODE_FEATURE_NAMES),
        "cell_edge": len(CELL_EDGE_FEATURE_NAMES),
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


def _class_weights(
    examples: Iterable[MultiResolutionExample],
) -> dict[str, dict[int, float]]:
    rows = tuple(examples)
    multiplicity: dict[str, int] = defaultdict(int)
    for row in rows:
        multiplicity[row.label.instance_hash] += 1
    output = {}
    for name in ("benefit", "adverse"):
        weighted = [
            (int(getattr(row.label, name)), 1.0 / multiplicity[row.label.instance_hash])
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

    truth = example.label
    output = model(graph=tensors)
    benefit = torch.tensor(float(truth.benefit), dtype=torch.float64)
    adverse = torch.tensor(float(truth.adverse), dtype=torch.float64)
    loss = class_weights["benefit"][truth.benefit] * functional.binary_cross_entropy(
        output["p_benefit"], benefit
    )
    loss = loss + class_weights["adverse"][truth.adverse] * functional.binary_cross_entropy(
        output["p_adverse"], adverse
    )
    if truth.benefit:
        loss = loss + 0.5 * functional.huber_loss(
            output["positive_gain"],
            torch.tensor(truth.positive_gain, dtype=torch.float64),
        )
    utility = output["p_benefit"] * output["positive_gain"] - output["p_adverse"]
    direction = torch.tensor(
        1.0 if truth.ratio < 1.0 else -1.0, dtype=torch.float64
    )
    return loss + 0.25 * functional.softplus(-5.0 * direction * utility)


def _fit_predict(
    train: list[MultiResolutionExample], validation: list[MultiResolutionExample],
    *, kind: str, seed: int, maximum_epochs: int, patience: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    import torch

    torch.set_num_threads(1)
    torch.manual_seed(seed)
    normalization = _normalization(train)
    class_weights = _class_weights(train)
    model = build_multires_model(kind=kind).double()
    count = parameter_count(model)
    if count >= 30_000:
        raise SystemExit("multi-resolution parameter cap exceeded")
    optimizer = torch.optim.Adam(model.parameters(), lr=2.0e-3, weight_decay=1.0e-5)
    train_count: dict[str, int] = defaultdict(int)
    validation_count: dict[str, int] = defaultdict(int)
    for example in train:
        train_count[example.label.instance_hash] += 1
    for example in validation:
        validation_count[example.label.instance_hash] += 1

    def tensors_for(example):
        values = multires_tensors(example, normalization)
        if kind == "shuffled_topology":
            values = shuffled_multires_tensors(
                values, state_hash=example.label.state_hash
            )
        return values

    train_cache = [
        (row, tensors_for(row), 1.0 / train_count[row.label.instance_hash])
        for row in train
    ]
    validation_cache = [
        (row, tensors_for(row), 1.0 / validation_count[row.label.instance_hash])
        for row in validation
    ]
    best_state = None
    best_loss = float("inf")
    stale = 0
    curve = []
    for epoch in range(maximum_epochs):
        model.train()
        order = sorted(range(len(train_cache)), key=lambda index: stable_hash({
            "seed": seed, "epoch": epoch,
            "context": train_cache[index][0].label.context_id,
        }))
        optimizer.zero_grad()
        total_weight = sum(row[2] for row in train_cache)
        combined = None
        for index in order:
            example, tensors, weight = train_cache[index]
            value = _loss(model, tensors, example, class_weights) * weight / total_weight
            combined = value if combined is None else combined + value
        assert combined is not None
        combined.backward()
        optimizer.step()
        model.eval()
        with torch.no_grad():
            values = [
                (float(_loss(model, tensors, row, class_weights)), weight)
                for row, tensors, weight in validation_cache
            ]
        validation_loss = (
            sum(value * weight for value, weight in values) / sum(weight for _, weight in values)
            if values else float(combined.detach())
        )
        curve.append({
            "epoch": epoch + 1, "train_loss": float(combined.detach()),
            "validation_loss": validation_loss,
        })
        if validation_loss < best_loss - 1.0e-8:
            best_loss = validation_loss
            stale = 0
            best_state = {
                name: value.detach().clone() for name, value in model.state_dict().items()
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
            truth = example.label
            output = model(graph=tensors)
            predictions.append({
                "context_id": truth.context_id,
                "instance_hash": truth.instance_hash,
                "scale": truth.scale, "ratio": truth.ratio,
                "benefit": truth.benefit, "adverse": truth.adverse,
                "p_benefit": float(output["p_benefit"]),
                "positive_gain": float(output["positive_gain"]),
                "p_adverse": float(output["p_adverse"]),
            })
    return predictions, {
        "epochs_run": len(curve), "best_validation_loss": best_loss,
        "parameter_count": count, "curve": curve,
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
    recall = statistics.fmean(float(row[probability]) >= 0.5 for row in positive) if positive else None
    specificity = statistics.fmean(float(row[probability]) < 0.5 for row in negative) if negative else None
    return {
        "balanced_accuracy": (
            0.5 * (recall + specificity)
            if recall is not None and specificity is not None else None
        ),
        "recall": recall, "specificity": specificity,
        "positive_count": len(positive), "negative_count": len(negative),
        "brier": statistics.fmean(
            (float(row[probability]) - int(row[target])) ** 2 for row in rows
        ),
    }


def _rank_accuracy(rows: list[dict[str, Any]]) -> float:
    return statistics.fmean(
        (
            float(row["p_benefit"]) * float(row["positive_gain"])
            - float(row["p_adverse"]) > 0.0
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
                "rank_accuracy": _rank_accuracy(context), "count": len(context),
            },
            "instance": {
                "benefit": _classification(instance, "benefit"),
                "adverse": _classification(instance, "adverse"),
                "rank_accuracy": _rank_accuracy(instance), "count": len(instance),
            },
        }
    result["combined_instance_rank_accuracy"] = _rank_accuracy(instances)
    return result


def _similar_opposite_fraction(examples: list[MultiResolutionExample]) -> float:
    rows = [row for row in examples if row.label.scale == 50]
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
                stable_hash((rows[left].label.context_id, rows[right].label.context_id)),
                rows[left].label.benefit != rows[right].label.benefit,
            ))
    count = max(1, int(len(pairs) * 0.10))
    return statistics.fmean(row[2] for row in sorted(pairs)[:count])


def _warm_cost(examples, normalization):
    import torch

    torch.set_num_threads(1)
    models = []
    for seed in MODEL_SEEDS:
        torch.manual_seed(seed)
        models.append(build_multires_model(kind="gat").double().eval())
    rows = []
    with torch.no_grad():
        for example in examples:
            for _ in range(3):
                tensors = multires_tensors(example, normalization)
                for model in models:
                    model(graph=tensors)
            samples = []
            for _ in range(20):
                started = perf_counter()
                tensors = multires_tensors(example, normalization)
                for model in models:
                    model(graph=tensors)
                samples.append(perf_counter() - started)
            inference = statistics.median(samples)
            graph_build = (
                example.label.graph_build_wall_seconds
                + example.cell_graph_build_wall_seconds
            )
            total = graph_build + inference
            rows.append({
                "context_id": example.label.context_id,
                "scale": example.label.scale,
                "label_graph_build_wall_seconds": example.label.graph_build_wall_seconds,
                "cell_graph_build_wall_seconds": example.cell_graph_build_wall_seconds,
                "conservative_separate_graph_build_wall_seconds": graph_build,
                "tensorization_plus_ensemble_inference_wall_seconds": inference,
                "combined_wall_seconds": total,
                "fraction_of_qpf0": total / example.label.qpf0_wall_seconds,
            })

    def p99(name):
        values = sorted(float(row[name]) for row in rows)
        return values[max(0, int(0.99 * len(values) + 0.999999) - 1)]

    return {
        "rows": rows,
        "inference_p99_ms": 1000.0 * p99(
            "tensorization_plus_ensemble_inference_wall_seconds"
        ),
        "conservative_total_p99_ms": 1000.0 * p99("combined_wall_seconds"),
        "maximum_fraction_of_qpf0": max(float(row["fraction_of_qpf0"]) for row in rows),
        "separate_graph_build_sum_is_conservative": True,
    }


def run(run_root: Path) -> None:
    assert_active(run_root, "OOF_DIAGNOSTIC")
    config = load(run_root / "config.freeze.json")
    examples = [
        _example(row) for row in load(run_root / "corpus.freeze.json")["rows"]
    ]
    by_context = {row.label.context_id: row for row in examples}
    fold_by_instance = {
        str(row["instance_hash"]): int(row["fold"])
        for row in load(run_root / "folds.freeze.json")["rows"]
    }
    predictions_by_model = {}
    training_audit = {}
    for kind in MODEL_KINDS:
        seed_predictions: dict[str, list[dict[str, Any]]] = defaultdict(list)
        training_audit[kind] = {}
        for seed in MODEL_SEEDS:
            training_audit[kind][str(seed)] = []
            for fold in range(5):
                validation = [
                    row for row in examples
                    if fold_by_instance[row.label.instance_hash] == fold
                ]
                train = [
                    row for row in examples
                    if fold_by_instance[row.label.instance_hash] != fold
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
            truth = by_context[context_id].label
            aggregate.append({
                "context_id": context_id, "instance_hash": truth.instance_hash,
                "scale": truth.scale, "ratio": truth.ratio,
                "benefit": truth.benefit, "adverse": truth.adverse,
                "p_benefit": statistics.fmean(float(row["p_benefit"]) for row in rows),
                "positive_gain": min(float(row["positive_gain"]) for row in rows),
                "p_adverse": max(float(row["p_adverse"]) for row in rows),
            })
        predictions_by_model[kind] = aggregate

    metrics = {kind: _metrics(rows) for kind, rows in predictions_by_model.items()}
    conflict = _similar_opposite_fraction(examples)
    cost = _warm_cost(examples, _normalization(examples))
    gat50 = metrics["gat"]["50"]["instance"]
    simple_ba = max(
        metrics[kind]["50"]["instance"]["benefit"]["balanced_accuracy"]
        for kind in ("mlp", "linear")
    )
    topology_ba = {
        kind: metrics[kind]["50"]["instance"]["benefit"]["balanced_accuracy"]
        for kind in ("no_message", "shuffled_topology")
    }
    topology_rank = {
        kind: metrics[kind]["50"]["instance"]["rank_accuracy"]
        for kind in ("no_message", "shuffled_topology")
    }
    ba_drop = max(
        gat50["benefit"]["balanced_accuracy"] - value
        for value in topology_ba.values()
    )
    rank_drop = max(
        gat50["rank_accuracy"] - value for value in topology_rank.values()
    )
    topology_contribution = max(ba_drop, rank_drop)
    thresholds = config["gate"]
    gate = {
        "scale50_benefit_balanced_accuracy": (
            gat50["benefit"]["balanced_accuracy"]
            >= float(thresholds["scale50_minimum_benefit_balanced_accuracy"])
        ),
        "scale50_adverse_balanced_accuracy": (
            gat50["adverse"]["balanced_accuracy"]
            >= float(thresholds["scale50_minimum_adverse_balanced_accuracy"])
        ),
        "scale50_rank_accuracy": (
            gat50["rank_accuracy"]
            >= float(thresholds["scale50_minimum_rank_accuracy"])
        ),
        "simple_control_gap": (
            gat50["benefit"]["balanced_accuracy"]
            >= simple_ba - float(thresholds["maximum_gap_below_best_simple_ba"])
        ),
        "topology_benefit_not_worse": all(
            gat50["benefit"]["balanced_accuracy"]
            >= value - float(thresholds["maximum_gap_below_best_topology_ba"])
            for value in topology_ba.values()
        ),
        "topology_rank_not_worse": all(
            gat50["rank_accuracy"] >= value for value in topology_rank.values()
        ),
        "topology_contribution": (
            topology_contribution >= float(thresholds["minimum_topology_rank_drop"])
        ),
        "warm_inference_p99": (
            cost["inference_p99_ms"]
            <= float(thresholds["warm_tensorization_plus_ensemble_inference_p99_ms"])
        ),
        "conservative_total_p99": (
            cost["conservative_total_p99_ms"]
            <= float(thresholds["conservative_separate_graph_build_plus_inference_p99_ms"])
        ),
        "per_context_cost_fraction": (
            cost["maximum_fraction_of_qpf0"]
            <= float(thresholds["maximum_per_context_fraction_of_qpf0"])
        ),
    }
    passed = all(gate.values())
    write_once(run_root / "oof_predictions.json", {
        "schema_version": "lunar_ice_bpc.p0v5_multires_frontier_oof.v1",
        "rows_by_model": predictions_by_model,
    })
    write_once(run_root / "training_audit.json", {
        "schema_version": "lunar_ice_bpc.p0v5_multires_frontier_training_audit.v1",
        "models": training_audit,
    })
    write_once(run_root / "runtime_cost_diagnostic.json", {
        "schema_version": "lunar_ice_bpc.p0v5_multires_frontier_cost.v1",
        **cost,
    })
    report = {
        "schema_version": "lunar_ice_bpc.p0v5_multires_frontier_observability_report.v1",
        "decision": "PASS" if passed else "FAIL",
        "reason": (
            "MULTIRES_FRONTIER_IDENTIFIABLE"
            if passed else "MULTIRES_FRONTIER_NOT_IDENTIFIABLE"
        ),
        "metrics": metrics,
        "scale50_similar_opposite_label_fraction_diagnostic": conflict,
        "best_simple_scale50_benefit_balanced_accuracy": simple_ba,
        "topology_scale50_benefit_balanced_accuracy": topology_ba,
        "topology_scale50_rank_accuracy": topology_rank,
        "topology_benefit_drop": ba_drop,
        "topology_rank_drop": rank_drop,
        "topology_contribution": topology_contribution,
        "cost": {key: value for key, value in cost.items() if key != "rows"},
        "gate": gate, "passed": passed,
        "baseline_v9r0": {
            "gat_scale50_benefit_balanced_accuracy": 0.6636363636363636,
            "gat_scale50_rank_accuracy": 0.6875,
            "similar_opposite_label_fraction": 0.4117647058823529,
        },
        "diagnostic_only": True, "performance_authority": False,
    }
    write_once(run_root / "observability.report.json", report)
    if passed:
        update_state(
            run_root, "SINGLE_REQUEST_NATIVE_FRESH_PILOT", "READY",
            observability_report="observability.report.json",
        )
    else:
        write_terminal(
            run_root, reason="MULTIRES_FRONTIER_NOT_IDENTIFIABLE",
            detail={"report": "observability.report.json", "gate": gate},
        )
    print({"decision": report["decision"], "reason": report["reason"], "gate": gate})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args()
    run(args.run_root.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
