#!/usr/bin/env python3
"""Grouped-OOF representation-development gate for the three V8 budgets.

V7R3 labels are deliberately diagnostic-only.  This program may select the
smallest identifiable prefix budget, but it may not create a runtime candidate
or authorize performance.  A negative result writes the frozen V8 terminal.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from math import sqrt
from pathlib import Path
import statistics
import sys
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.guidance.counterfactual_prefix_gat_qd1_v8 import (  # noqa: E402
    CONTEXT_FEATURE_NAMES,
    COUNTER_DELTA_NAMES,
    EDGE_FEATURE_NAMES,
    MODEL_SEEDS,
    NODE_FEATURE_NAMES,
    CounterfactualGraph,
    CounterfactualTriplet,
    build_counterfactual_model,
    parameter_count,
    shuffled_triplet_tensors,
    triplet_tensors,
)
from scripts.p0v5_counterfactual_prefix_gat_qd1_v8_common import (  # noqa: E402
    CONFIG,
    DEFAULT_RUN_ROOT,
    assert_active,
    geometric_mean,
    load,
    stable_hash,
    update_state,
    write_once,
    write_terminal,
)


MODEL_KINDS = ("gat", "mlp", "linear", "no_message", "shuffled_topology")


def _graph(row: dict[str, Any]) -> CounterfactualGraph:
    graph = CounterfactualGraph(
        node_features=tuple(tuple(map(float, values)) for values in row["node_features"]),
        edge_index=tuple(tuple(map(int, values)) for values in row["edge_index"]),
        edge_features=tuple(tuple(map(float, values)) for values in row["edge_features"]),
        context_features=tuple(map(float, row["context_features"])),
        graph_hash=str(row["graph_hash"]),
        label_count=int(row["label_count"]),
        task_count=int(row["task_count"]),
    )
    graph.validate()
    return graph


def _triplet(row: dict[str, Any]) -> CounterfactualTriplet:
    value = CounterfactualTriplet(
        base=_graph(row["base"]), q0=_graph(row["q0"]), qd1=_graph(row["qd1"]),
        counter_deltas=tuple(map(float, row["counter_deltas"])),
        rollout_budget=int(row["rollout_budget"]),
        state_hash=str(row["state_hash"]),
    )
    value.validate()
    return value


def _fold(instance_hash: str, scale: int) -> int:
    digest = hashlib.sha256(f"v8-representation-fold:{scale}:{instance_hash}".encode()).digest()
    return int.from_bytes(digest[:4], "big") % 5


def _normalization(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, list[float]]]:
    groups: dict[str, list[list[float]]] = {
        "node": [], "edge": [], "context": [], "counter": [],
    }
    for row in rows:
        for view in ("base", "q0", "qd1"):
            groups["node"].extend(row[view]["node_features"])
            groups["edge"].extend(row[view]["edge_features"])
            groups["context"].append(row[view]["context_features"])
        groups["counter"].append(row["counter_deltas"])
    widths = {
        "node": len(NODE_FEATURE_NAMES), "edge": len(EDGE_FEATURE_NAMES),
        "context": len(CONTEXT_FEATURE_NAMES), "counter": len(COUNTER_DELTA_NAMES),
    }
    output: dict[str, dict[str, list[float]]] = {}
    for group, width in widths.items():
        columns = list(zip(*groups[group])) if groups[group] else [()] * width
        mean, scale, minimum, maximum = [], [], [], []
        for values in columns:
            numbers = [float(value) for value in values]
            center = statistics.fmean(numbers) if numbers else 0.0
            variance = statistics.fmean((value - center) ** 2 for value in numbers) if numbers else 0.0
            mean.append(center)
            scale.append(max(sqrt(variance), 1.0e-9))
            minimum.append(min(numbers) if numbers else 0.0)
            maximum.append(max(numbers) if numbers else 0.0)
        if len(mean) != width:
            raise SystemExit(f"V8 normalization width drift:{group}")
        output[group] = {"mean": mean, "scale": scale, "minimum": minimum, "maximum": maximum}
    return output


def _loss(model, tensors: dict[str, Any], target: dict[str, Any]):
    import torch
    import torch.nn.functional as functional

    output = model(**tensors)
    benefit = torch.tensor(float(target["benefit"]), dtype=torch.float64)
    adverse = torch.tensor(float(target["adverse"]), dtype=torch.float64)
    ratio = float(target["ratio"])
    loss = functional.binary_cross_entropy(output["p_benefit"], benefit)
    loss = loss + functional.binary_cross_entropy(output["p_adverse"], adverse)
    if bool(target["benefit"]):
        gain = torch.tensor(float(target["positive_gain"]), dtype=torch.float64)
        loss = loss + 0.5 * functional.huber_loss(output["positive_gain"], gain)
    utility = output["p_benefit"] * output["positive_gain"] - output["p_adverse"]
    direction = torch.tensor(1.0 if ratio < 1.0 else -1.0, dtype=torch.float64)
    loss = loss + 0.25 * functional.softplus(-5.0 * direction * utility)
    return loss, output


def _fit_predict(
    train_rows: list[dict[str, Any]], validation_rows: list[dict[str, Any]],
    *, kind: str, seed: int, maximum_epochs: int, patience: int,
) -> list[dict[str, float]]:
    import torch

    torch.set_num_threads(1)
    torch.manual_seed(seed)
    normalization = _normalization(train_rows)
    model = build_counterfactual_model(kind=kind).double()
    if kind == "gat" and parameter_count(model) >= 30_000:
        raise SystemExit("V8 GAT parameter cap exceeded")
    optimizer = torch.optim.Adam(model.parameters(), lr=2.0e-3, weight_decay=1.0e-5)
    context_counts: dict[str, int] = defaultdict(int)
    for row in train_rows:
        context_counts[str(row["instance_hash"])] += 1
    cached_train = []
    for row in train_rows:
        tensors = triplet_tensors(_triplet(row), normalization)
        if kind == "shuffled_topology":
            tensors = shuffled_triplet_tensors(tensors, state_hash=str(row["state_hash"]))
        cached_train.append((row, tensors, 1.0 / context_counts[str(row["instance_hash"])]))
    cached_validation = []
    for row in validation_rows:
        tensors = triplet_tensors(_triplet(row), normalization)
        if kind == "shuffled_topology":
            tensors = shuffled_triplet_tensors(tensors, state_hash=str(row["state_hash"]))
        cached_validation.append((row, tensors))
    best_state, best_loss, stale = None, float("inf"), 0
    for epoch in range(maximum_epochs):
        model.train()
        order = sorted(
            range(len(cached_train)),
            key=lambda index: stable_hash({"seed": seed, "epoch": epoch, "row": cached_train[index][0]["context_id"]}),
        )
        optimizer.zero_grad()
        total = sum(weight for _, _, weight in cached_train)
        combined = None
        for index in order:
            row, tensors, weight = cached_train[index]
            value, _ = _loss(model, tensors, row["target"])
            value = value * (weight / max(total, 1.0e-12))
            combined = value if combined is None else combined + value
        assert combined is not None
        combined.backward()
        optimizer.step()
        model.eval()
        with torch.no_grad():
            values = [float(_loss(model, tensors, row["target"])[0]) for row, tensors in cached_validation]
        validation_loss = statistics.fmean(values) if values else float(combined.detach())
        if validation_loss < best_loss - 1.0e-8:
            best_loss, stale = validation_loss, 0
            best_state = {name: value.detach().clone() for name, value in model.state_dict().items()}
        else:
            stale += 1
            if stale >= patience:
                break
    if best_state is not None:
        model.load_state_dict(best_state)
    model.eval()
    predictions = []
    with torch.no_grad():
        for row, tensors in cached_validation:
            output = model(**tensors)
            predictions.append({
                "context_id": str(row["context_id"]),
                "instance_hash": str(row["instance_hash"]),
                "scale": int(row["scale"]),
                "benefit": float(output["p_benefit"]),
                "gain": float(output["positive_gain"]),
                "adverse": float(output["p_adverse"]),
            })
    return predictions


def _balanced_accuracy(rows: list[dict[str, Any]], truth: dict[str, dict[str, Any]]) -> float:
    collapsed: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for row in rows:
        actual = int(truth[row["context_id"]]["target"]["benefit"])
        predicted = int(float(row["benefit"]) >= 0.5)
        collapsed[row["instance_hash"]].append((actual, predicted))
    pairs = []
    for values in collapsed.values():
        actual = int(statistics.fmean(value[0] for value in values) >= 0.5)
        predicted = int(statistics.fmean(value[1] for value in values) >= 0.5)
        pairs.append((actual, predicted))
    positive = [predicted for actual, predicted in pairs if actual]
    negative = [predicted for actual, predicted in pairs if not actual]
    if not positive or not negative:
        return 0.5
    return 0.5 * (statistics.fmean(positive) + statistics.fmean(1 - value for value in negative))


def _rank_accuracy(rows: list[dict[str, Any]], truth: dict[str, dict[str, Any]]) -> float:
    values: dict[str, list[float]] = defaultdict(list)
    correct: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        predicted = float(row["benefit"]) * float(row["gain"]) - float(row["adverse"])
        actual = float(truth[row["context_id"]]["target"]["ratio"])
        values[row["instance_hash"]].append(predicted)
        correct[row["instance_hash"]].append(1.0 if (predicted > 0.0) == (actual < 1.0) else 0.0)
    return statistics.fmean(statistics.fmean(rows) for rows in correct.values())


def _similar_opposite_fraction(rows: list[dict[str, Any]]) -> float:
    # A deterministic numeric graph signature.  Distances use only pre-action
    # triplet values; labels are inspected only after the closest pairs freeze.
    signatures = []
    for row in rows:
        vector = []
        for view in ("base", "q0", "qd1"):
            for group in ("node_features", "edge_features"):
                values = row[view][group]
                width = len(values[0])
                vector.extend(statistics.fmean(float(value[index]) for value in values) for index in range(width))
            vector.extend(map(float, row[view]["context_features"]))
        vector.extend(map(float, row["counter_deltas"]))
        signatures.append((row, vector))
    pairs = []
    for left in range(len(signatures)):
        for right in range(left + 1, len(signatures)):
            a, b = signatures[left], signatures[right]
            distance = sqrt(sum((x - y) ** 2 for x, y in zip(a[1], b[1])))
            tie = stable_hash((a[0]["context_id"], b[0]["context_id"]))
            pairs.append((distance, tie, a[0], b[0]))
    count = max(1, int(len(pairs) * 0.10))
    closest = sorted(pairs, key=lambda item: (item[0], item[1]))[:count]
    return statistics.fmean(
        int(left["target"]["benefit"]) != int(right["target"]["benefit"])
        for _, _, left, right in closest
    )


def _taxed_oracle(rows: list[dict[str, Any]], scale: int) -> float:
    ratios: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        if int(row["scale"]) != scale:
            continue
        reference = float(row["qpf0_reference_wall_seconds"])
        if reference <= 0.0:
            raise SystemExit("V8 QPF0 reference wall missing")
        tax = float(row["paired_prefix_native_warm_wall_seconds"])
        ratios[row["instance_hash"]].append(min(1.0, float(row["target"]["ratio"])) + tax / reference)
    return geometric_mean(
        geometric_mean(values) for values in ratios.values()
    )


def _cost_gate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    walls = sorted(
        1000.0 * float(row["paired_prefix_native_warm_wall_seconds"])
        for row in rows
    )
    p99_index = max(0, min(len(walls) - 1, int(0.99 * len(walls) + 0.999999) - 1))
    fractions = [
        float(row["paired_prefix_native_warm_wall_seconds"])
        / float(row["qpf0_reference_wall_seconds"])
        for row in rows
    ]
    taxed = {str(scale): _taxed_oracle(rows, scale) for scale in (30, 50)}
    gate = {
        "paired_prefix_warm_p99": walls[p99_index] <= 250.0,
        "paired_prefix_fraction": max(fractions) <= 0.02,
        "taxed_oracle": all(value <= 0.97 for value in taxed.values()),
    }
    return {
        "paired_prefix_p99_ms": walls[p99_index],
        "paired_prefix_median_ms": statistics.median(walls),
        "maximum_paired_prefix_fraction_of_qpf0": max(fractions),
        "contexts_above_250ms": sum(value > 250.0 for value in walls),
        "contexts_above_two_percent": sum(value > 0.02 for value in fractions),
        "taxed_oracle_gm": taxed,
        "cost_gate": gate,
        "cost_gate_passed": all(gate.values()),
    }


def run(run_root: Path) -> None:
    assert_active(run_root, "REPRESENTATION_TRAIN")
    dataset = load(run_root / "representation_triplets.json")
    config = load(run_root / "config.freeze.json")
    all_rows = list(dataset["rows"])
    results = []
    rows_by_budget = {
        budget: [
            row for row in all_rows if int(row["rollout_budget"]) == budget
        ] for budget in (128, 512, 2048)
    }
    cost_by_budget = {
        budget: _cost_gate(rows) for budget, rows in rows_by_budget.items()
    }
    viable_budgets = {
        budget for budget, result in cost_by_budget.items()
        if bool(result["cost_gate_passed"])
    }
    if not viable_budgets:
        for budget in (128, 512, 2048):
            cost = cost_by_budget[budget]
            results.append({
                "rollout_budget": budget,
                **{key: value for key, value in cost.items() if key != "cost_gate"},
                "gate": {**cost["cost_gate"], "representation_metrics": False},
                "metrics_status": "NOT_EVALUATED_EARLY_COST_GATE_FAILED",
                "passed": False,
            })
        report = {
            "schema_version": "lunar_ice_bpc.p0v5_counterfactual_representation_report.v1",
            "diagnostic_only": True,
            "performance_authority": False,
            "smallest_passing_budget": None,
            "budget_results": results,
            "decision": "FAIL",
            "reason": "PREFIX_COST_GATE_FAILED_BEFORE_OOF",
            "ooF_training_started": False,
            "ooF_training_completed": False,
            "ooF_artifacts_emitted": False,
            "timing_contract": dataset.get("timing_contract"),
        }
        write_once(run_root / "representation_development.report.json", report)
        decision = {
            "schema_version": "lunar_ice_bpc.p0v5_counterfactual_prefix_budget_decision.v1",
            "decision": "FAIL", "selected_rollout_budget": None,
            "reason": "COUNTERFACTUAL_PREFIX_NOT_IDENTIFIABLE",
            "immediate_cause": "PREFIX_COST_GATE_FAILED_BEFORE_OOF",
            "performance_authority": False,
        }
        write_once(run_root / "representation_budget.decision.json", decision)
        write_terminal(
            run_root, reason="COUNTERFACTUAL_PREFIX_NOT_IDENTIFIABLE",
            stage="REPRESENTATION_TRAIN",
            detail={
                "immediate_cause": "PREFIX_COST_GATE_FAILED_BEFORE_OOF",
                "report": "representation_development.report.json",
            },
        )
        print(json.dumps(decision, sort_keys=True))
        return
    for budget in (128, 512, 2048):
        rows = rows_by_budget[budget]
        if budget not in viable_budgets:
            cost = cost_by_budget[budget]
            results.append({
                "rollout_budget": budget,
                **{key: value for key, value in cost.items() if key != "cost_gate"},
                "gate": {**cost["cost_gate"], "representation_metrics": False},
                "metrics_status": "NOT_EVALUATED_COST_GATE_FAILED",
                "passed": False,
            })
            continue
        truth = {row["context_id"]: row for row in rows}
        by_kind: dict[str, list[dict[str, float]]] = {}
        for kind in MODEL_KINDS:
            seed_predictions: dict[str, list[dict[str, float]]] = defaultdict(list)
            for seed in MODEL_SEEDS:
                for fold in range(5):
                    validation = [row for row in rows if _fold(row["instance_hash"], int(row["scale"])) == fold]
                    training = [row for row in rows if row not in validation]
                    for prediction in _fit_predict(
                        training, validation, kind=kind, seed=seed,
                        maximum_epochs=int(config["selector_training"]["maximum_epochs"]),
                        patience=int(config["selector_training"]["patience"]),
                    ):
                        seed_predictions[prediction["context_id"]].append(prediction)
            aggregate = []
            for context_id, predictions in sorted(seed_predictions.items()):
                if len(predictions) != len(MODEL_SEEDS):
                    raise SystemExit("V8 OOF seed coverage drift")
                aggregate.append({
                    "context_id": context_id,
                    "instance_hash": predictions[0]["instance_hash"],
                    "scale": predictions[0]["scale"],
                    "benefit": statistics.fmean(row["benefit"] for row in predictions),
                    "gain": min(row["gain"] for row in predictions),
                    "adverse": max(row["adverse"] for row in predictions),
                })
            by_kind[kind] = aggregate
        metrics = {}
        for kind, predictions in by_kind.items():
            metrics[kind] = {
                str(scale): {
                    "benefit_balanced_accuracy": _balanced_accuracy(
                        [row for row in predictions if int(row["scale"]) == scale], truth
                    ),
                    "rank_accuracy": _rank_accuracy(
                        [row for row in predictions if int(row["scale"]) == scale], truth
                    ),
                } for scale in (30, 50)
            }
            metrics[kind]["combined_rank_accuracy"] = _rank_accuracy(predictions, truth)
        cost = cost_by_budget[budget]
        similar_opposite = _similar_opposite_fraction(
            [row for row in rows if int(row["scale"]) == 50]
        )
        gat50 = metrics["gat"]["50"]
        best_simple_ba = max(metrics[kind]["50"]["benefit_balanced_accuracy"] for kind in ("mlp", "linear"))
        topology_drop = max(
            metrics["gat"]["combined_rank_accuracy"] - metrics[kind]["combined_rank_accuracy"]
            for kind in ("no_message", "shuffled_topology")
        )
        gate = {
            "scale50_benefit_ba": gat50["benefit_balanced_accuracy"] >= 0.70,
            "scale50_rank_accuracy": gat50["rank_accuracy"] >= 0.65,
            "similar_opposite_fraction": similar_opposite <= 0.35,
            "simple_control_gap": gat50["benefit_balanced_accuracy"] >= best_simple_ba - 0.02,
            "topology_not_better_than_gat": all(
                gat50["rank_accuracy"] >= metrics[kind]["50"]["rank_accuracy"]
                for kind in ("no_message", "shuffled_topology")
            ),
            "topology_contribution": topology_drop >= 0.02,
            **cost["cost_gate"],
        }
        results.append({
            "rollout_budget": budget, "metrics": metrics,
            "similar_opposite_label_fraction": similar_opposite,
            **{key: value for key, value in cost.items() if key not in {"cost_gate", "cost_gate_passed"}},
            "topology_rank_drop": topology_drop,
            "gate": gate, "passed": all(gate.values()),
        })
    results.sort(key=lambda row: int(row["rollout_budget"]))
    selected = next((row["rollout_budget"] for row in results if row["passed"]), None)
    report = {
        "schema_version": "lunar_ice_bpc.p0v5_counterfactual_representation_report.v1",
        "diagnostic_only": True, "performance_authority": False,
        "smallest_passing_budget": selected, "budget_results": results,
    }
    write_once(run_root / "representation_development.report.json", report)
    decision = {
        "schema_version": "lunar_ice_bpc.p0v5_counterfactual_prefix_budget_decision.v1",
        "decision": "PASS" if selected is not None else "FAIL",
        "selected_rollout_budget": selected,
        "reason": "COUNTERFACTUAL_PREFIX_IDENTIFIABLE" if selected is not None else "COUNTERFACTUAL_PREFIX_NOT_IDENTIFIABLE",
        "performance_authority": False,
    }
    write_once(run_root / "representation_budget.decision.json", decision)
    if selected is None:
        write_terminal(
            run_root, reason="COUNTERFACTUAL_PREFIX_NOT_IDENTIFIABLE",
            stage="REPRESENTATION_TRAIN", detail={"report": "representation_development.report.json"},
        )
    else:
        update_state(run_root, "PILOT_CENSUS", "READY", selected_rollout_budget=selected)
    print(json.dumps(decision, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args()
    run(args.run_root.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
