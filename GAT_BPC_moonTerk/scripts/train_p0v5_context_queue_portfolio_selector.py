#!/usr/bin/env python3
"""Train GAT/MLP/Linear selectors and freeze the unique calibration winner.

Input rows are context-level examples.  Three repeats must already be reduced
to one median outcome per arm; the script rejects repeated context identities
and never reads selector-heldout or formal outcomes.
"""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from dataclasses import replace
import hashlib
import itertools
import json
from math import exp, log, sqrt
from pathlib import Path
import random
from statistics import fmean, median, pstdev
import sys
from time import perf_counter

import torch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.guidance.context_queue_portfolio_gates import (  # noqa: E402
    geometric_mean, percentile,
)
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import (  # noqa: E402
    verify_portfolio_freezes,
)
from lunar_ice_bpc.guidance.context_queue_portfolio_runtime import (  # noqa: E402
    PORTFOLIO_MANIFEST_SCHEMA_V1, PORTFOLIO_RUNTIME_POLICY_V1,
    QGR1_BUCKET_WIDTH, context_queue_portfolio_runtime_implementation_hash,
)
from lunar_ice_bpc.guidance.context_queue_portfolio_v1 import (  # noqa: E402
    PORTFOLIO_ACTION_UNIVERSE, PORTFOLIO_ARMS,
    PORTFOLIO_CHECKPOINT_SCHEMA_V1, PORTFOLIO_FEATURE_SCHEMA_V1,
    PORTFOLIO_INPUT_PARITY_CONTRACT_V1, PORTFOLIO_CONTEXT_FEATURES,
    PORTFOLIO_EDGE_FEATURES, PORTFOLIO_NODE_FEATURES, QG2Features,
    PortfolioGATSelector, PortfolioLinearSelector, PortfolioMLPSelector,
    fit_portfolio_feature_envelope, fit_portfolio_normalization,
    portfolio_parameter_count, portfolio_training_loss,
)


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_context_queue_portfolio_v1_20260807_r1"
MODEL_CLASSES = {
    "gat": PortfolioGATSelector,
    "mlp": PortfolioMLPSelector,
    "linear": PortfolioLinearSelector,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--qgr1-ranker", type=Path)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    _verify_freezes(run_root)
    oracle = _load(run_root / "portfolio_oracle.decision.json")["decision"]
    if not bool(oracle.get("selector_training_authorized")):
        raise SystemExit("portfolio oracle did not authorize selector training")
    admission = _load(run_root / "qgr1_force_on.decision.json")["decision"]
    config = _load(run_root / "config.freeze.json")
    dataset_path = args.dataset.resolve()
    dataset = _load(dataset_path)
    rows = _dataset_rows(dataset)
    train_rows = [row for row in rows if row["partition"] == "train"]
    calibration_rows = [row for row in rows if row["partition"] == "calibration"]
    if not train_rows or not calibration_rows:
        raise SystemExit("train/calibration rows are required")
    normalization = fit_portfolio_normalization(
        [row["features"] for row in train_rows]
    )
    envelope = fit_portfolio_feature_envelope(
        [row["features"] for row in train_rows], relative_margin=0.05
    )
    training = config["selector_training"]
    torch.set_num_threads(1)
    candidates = []
    training_dir = run_root / "selector_training"
    training_dir.mkdir(parents=True, exist_ok=True)
    for kind in training["model_order"]:
        for seed in training["seeds"]:
            candidate = _train_one(
                kind=str(kind), seed=int(seed), normalization=normalization,
                train_rows=train_rows, calibration_rows=calibration_rows,
                maximum_epochs=int(training["maximum_epochs"]),
                patience=int(training["patience"]),
            )
            calibration = _fit_probability_calibration(
                candidate["model"], calibration_rows
            )
            candidate["probability_calibration"] = calibration
            candidate["metrics"] = {
                "train": _prediction_metrics(
                    candidate["model"], calibration, train_rows
                ),
                "calibration": _prediction_metrics(
                    candidate["model"], calibration, calibration_rows
                ),
            }
            candidate["threshold_candidates"] = _threshold_results(
                candidate["model"], calibration, calibration_rows,
                config["threshold_grid"],
                allowed_arms_by_scale=_allowed_arms(admission),
            )
            eligible = [row for row in candidate["threshold_candidates"] if row["eligible"]]
            candidate["best_threshold"] = min(
                eligible, key=_threshold_key
            ) if eligible else None
            candidate_path = training_dir / f"{kind}_seed{seed}.pt"
            torch.save(_checkpoint_payload(candidate, normalization), candidate_path)
            candidate["checkpoint_path"] = candidate_path
            candidate["checkpoint_sha256"] = _sha256(candidate_path)
            _write_once(
                training_dir / f"{kind}_seed{seed}.curve.json",
                {
                    "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_training_curve.v1",
                    "model_kind": kind, "seed": seed,
                    "parameter_count": candidate["parameter_count"],
                    "best_epoch": candidate["best_epoch"],
                    "curve": candidate["curve"],
                    "probability_calibration": calibration,
                    "best_threshold": candidate["best_threshold"],
                },
            )
            candidates.append(candidate)

    eligible_candidates = [
        row for row in candidates if row["best_threshold"] is not None
    ]
    summary = {
        "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_model_selection.v1",
        "dataset": str(dataset_path),
        "dataset_sha256": _sha256(dataset_path),
        "heldout_rows_read": 0,
        "formal_rows_read": 0,
        "candidate_count": len(candidates),
        "eligible_candidate_count": len(eligible_candidates),
        "candidates": [_candidate_summary(row) for row in candidates],
        "seed_variance": _seed_variance(candidates),
    }
    if not eligible_candidates:
        summary.update({
            "decision": "NO_OP",
            "reason": "NO_ZERO_HARM_CALIBRATION_THRESHOLD",
            "selector_frozen": False,
        })
        _write_once(run_root / "selector_selection.decision.json", summary)
        _terminal(run_root, "NO_ZERO_HARM_CALIBRATION_THRESHOLD", summary)
        return 2

    selected = min(eligible_candidates, key=_candidate_key)
    selected["attribution"] = _attribution(
        selected, calibration_rows, normalization,
        allowed_arms_by_scale=_allowed_arms(admission),
    )
    disagreement = _candidate_disagreement(
        selected, eligible_candidates, calibration_rows,
        allowed_arms_by_scale=_allowed_arms(admission),
    )
    selected_checkpoint = run_root / "selector_candidate.pt"
    torch.save(_checkpoint_payload(selected, normalization), selected_checkpoint)
    threshold = selected["best_threshold"]
    manifest = _runtime_manifest(
        run_root=run_root,
        config=config,
        admission=admission,
        selected=selected,
        selected_checkpoint=selected_checkpoint,
        envelope=envelope,
        qgr1_ranker=args.qgr1_ranker,
    )
    manifest_path = run_root / "research_candidate.manifest.json"
    _write_once(manifest_path, manifest)
    summary.update({
        "decision": "SELECTED_UNIQUE_MODEL",
        "selector_frozen": True,
        "selected_model_kind": selected["kind"],
        "selected_seed": selected["seed"],
        "selected_parameter_count": selected["parameter_count"],
        "selected_checkpoint": str(selected_checkpoint),
        "selected_checkpoint_sha256": _sha256(selected_checkpoint),
        "selected_threshold": threshold["thresholds"],
        "selected_metrics": selected["metrics"],
        "selected_attribution": selected["attribution"],
        "selected_action_disagreement": disagreement,
        "research_candidate_manifest": str(manifest_path),
        "development_only": True,
        "deployment_authorized": False,
        "production_switch_authorized": False,
        "claim_boundary": (
            "GAT graph advantage may be claimed only if GAT is the measured winner"
            if selected["kind"] == "gat"
            else "queue-policy selector speedup; no GAT graph-structure claim"
        ),
    })
    _write_once(run_root / "selector_selection.decision.json", summary)
    _update_state(run_root, "SELECTOR_HELDOUT_FRESH", "READY")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def _dataset_rows(payload):
    if payload.get("schema_version") != (
        "lunar_ice_bpc.p0v5_context_queue_portfolio_training_dataset.v1"
    ):
        raise SystemExit("training dataset schema mismatch")
    seen = set()
    rows = []
    for raw in payload.get("rows") or ():
        partition = str(raw.get("partition") or "")
        if partition not in {"train", "calibration"}:
            # Heldout outcomes are not even deserialized.
            continue
        context_id = str(raw.get("context_id") or "")
        instance_hash = str(raw.get("instance_hash") or "")
        identity = (partition, context_id)
        if not context_id or not instance_hash or identity in seen:
            raise SystemExit("repeated or incomplete context row")
        seen.add(identity)
        features = _features(raw["features"])
        targets = dict(raw.get("targets") or {})
        if set(targets) != set(PORTFOLIO_ARMS):
            raise SystemExit("dataset must contain the same targets for all arms")
        if any(
            tuple(dict(targets[arm]).get("correctness_redlines") or ())
            for arm in PORTFOLIO_ARMS
        ):
            raise SystemExit("CORRECTNESS_REDLINE in selector training dataset")
        rows.append({
            "partition": partition,
            "context_id": context_id,
            "instance_hash": instance_hash,
            "scale": int(raw["scale"]),
            "features": features,
            "targets": targets,
        })
    return rows


def _features(payload):
    row = QG2Features(
        instance_content_hash=str(payload["instance_content_hash"]),
        task_ids=tuple(payload["task_ids"]),
        arc_candidate_ids=tuple(payload["arc_candidate_ids"]),
        node_features=tuple(tuple(float(v) for v in values) for values in payload["node_features"]),
        edge_index=tuple(tuple(int(v) for v in values) for values in payload["edge_index"]),
        edge_features=tuple(tuple(float(v) for v in values) for values in payload["edge_features"]),
        context_features=tuple(float(v) for v in payload["context_features"]),
        schema_version=str(payload["schema_version"]),
    )
    if row.schema_version != PORTFOLIO_FEATURE_SCHEMA_V1:
        raise SystemExit("portfolio feature schema mismatch")
    return row


def _train_one(*, kind, seed, normalization, train_rows, calibration_rows,
               maximum_epochs, patience):
    torch.manual_seed(seed)
    random.seed(seed)
    model = MODEL_CLASSES[kind](normalization)
    if portfolio_parameter_count(model) >= 50_000:
        raise SystemExit("selector parameter count is not below 50k")
    optimizer = torch.optim.AdamW(model.parameters(), lr=1.0e-3, weight_decay=1.0e-4)
    best = None
    best_loss = float("inf")
    stale = 0
    curve = []
    for epoch in range(maximum_epochs):
        model.train()
        optimizer.zero_grad()
        train_loss = _instance_balanced_loss(model, train_rows)
        train_loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        optimizer.step()
        model.eval()
        with torch.inference_mode():
            calibration_loss = float(_instance_balanced_loss(model, calibration_rows))
        curve.append({
            "epoch": epoch + 1,
            "train_loss": float(train_loss.detach()),
            "calibration_loss": calibration_loss,
        })
        if calibration_loss < best_loss - 1.0e-7:
            best_loss = calibration_loss
            best = deepcopy(model.state_dict())
            stale = 0
        else:
            stale += 1
            if stale >= patience:
                break
    if best is None:
        raise SystemExit("training produced no checkpoint")
    model.load_state_dict(best, strict=True)
    model.eval()
    return {
        "kind": kind, "seed": seed, "model": model,
        "parameter_count": portfolio_parameter_count(model),
        "best_epoch": min(curve, key=lambda row: row["calibration_loss"])["epoch"],
        "curve": curve,
    }


def _instance_balanced_loss(model, rows):
    grouped = {}
    for row in rows:
        grouped.setdefault(row["instance_hash"], []).append(row)
    instance_losses = []
    for instance_rows in grouped.values():
        context_losses = []
        for row in instance_rows:
            output = model(**row["features"].to_tensors())
            targets = row["targets"]
            ratios = [
                float(targets[arm]["ratio"])
                if bool(targets[arm]["determined"]) else None
                for arm in PORTFOLIO_ARMS
            ]
            preferences = _preferences(ratios)
            loss = portfolio_training_loss(
                output,
                benefit_target=torch.tensor([
                    float(bool(targets[arm]["benefit"])) for arm in PORTFOLIO_ARMS
                ]),
                positive_gain_target=torch.tensor([
                    float(targets[arm].get("positive_gain") or 0.0)
                    for arm in PORTFOLIO_ARMS
                ]),
                adverse_target=torch.tensor([
                    float(bool(targets[arm]["adverse"])) for arm in PORTFOLIO_ARMS
                ]),
                determined_mask=torch.tensor([
                    float(bool(targets[arm]["determined"])) for arm in PORTFOLIO_ARMS
                ]),
                positive_mask=torch.tensor([
                    float(bool(targets[arm]["benefit"])) for arm in PORTFOLIO_ARMS
                ]),
                pairwise_preferences=preferences,
            )["loss"]
            context_losses.append(loss)
        instance_losses.append(torch.stack(context_losses).mean())
    return torch.stack(instance_losses).mean()


def _preferences(ratios):
    values = [1.0, *ratios]
    result = []
    for left, right in itertools.combinations(range(4), 2):
        if values[left] is None or values[right] is None or values[left] == values[right]:
            continue
        preferred, other = (left, right) if values[left] < values[right] else (right, left)
        result.append((preferred - 1, other - 1, 1.0))
    return result


def _fit_probability_calibration(model, rows):
    result = {
        "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_probability_calibration.v1",
        "fit_partition": "calibration_instances_only",
        "benefit": {}, "adverse": {}, "positive_gain_scale": {},
    }
    predictions = _raw_predictions(model, rows)
    for arm in PORTFOLIO_ARMS:
        determined = [row for row in predictions if row["targets"][arm]["determined"]]
        for field, target in (("benefit", "benefit"), ("adverse", "adverse")):
            probabilities = [float(row[field][arm]) for row in determined]
            labels = [float(bool(row["targets"][arm][target])) for row in determined]
            result[field][arm] = _platt(probabilities, labels)
        positive = [row for row in determined if row["targets"][arm]["benefit"]]
        predicted = sum(float(row["gain"][arm]) for row in positive)
        observed = sum(float(row["targets"][arm]["positive_gain"]) for row in positive)
        result["positive_gain_scale"][arm] = (
            max(0.1, min(10.0, observed / predicted)) if predicted > 0.0 else 1.0
        )
    return result


def _platt(probabilities, labels):
    if not probabilities or len(set(labels)) < 2:
        return {"slope": 1.0, "intercept": 0.0, "degenerate": True}
    x = torch.tensor([
        log(min(1 - 1e-6, max(1e-6, value)) / (1 - min(1 - 1e-6, max(1e-6, value))))
        for value in probabilities
    ])
    y = torch.tensor(labels)
    slope = torch.tensor(1.0, requires_grad=True)
    intercept = torch.tensor(0.0, requires_grad=True)
    optimizer = torch.optim.LBFGS([slope, intercept], max_iter=50, line_search_fn="strong_wolfe")
    def closure():
        optimizer.zero_grad()
        loss = torch.nn.functional.binary_cross_entropy_with_logits(
            slope.clamp_min(0.0) * x + intercept, y
        )
        loss.backward()
        return loss
    optimizer.step(closure)
    return {
        "slope": max(0.0, float(slope.detach())),
        "intercept": float(intercept.detach()),
        "degenerate": False,
    }


def _raw_predictions(model, rows):
    result = []
    model.eval()
    with torch.inference_mode():
        for row in rows:
            output = model(**row["features"].to_tensors())
            result.append({
                "row": row,
                "targets": row["targets"],
                "benefit": {arm: float(output["benefit_probability"][0, index]) for index, arm in enumerate(PORTFOLIO_ARMS)},
                "gain": {arm: float(output["conditional_positive_gain"][0, index]) for index, arm in enumerate(PORTFOLIO_ARMS)},
                "adverse": {arm: float(output["adverse_probability"][0, index]) for index, arm in enumerate(PORTFOLIO_ARMS)},
            })
    return result


def _prediction_metrics(model, calibration, rows):
    predictions = _raw_predictions(model, rows)
    classification = {"benefit": {}, "adverse": {}}
    for arm in PORTFOLIO_ARMS:
        determined = [row for row in predictions if row["targets"][arm]["determined"]]
        for field in ("benefit", "adverse"):
            probabilities = [
                _calibrate(row[field][arm], calibration[field][arm])
                for row in determined
            ]
            labels = [
                int(bool(row["targets"][arm][field]))
                for row in determined
            ]
            classification[field][arm] = _binary_metrics(probabilities, labels)
    arm_q0_hits = []
    arm_arm_hits = []
    for prediction in predictions:
        utility = {
            arm: (
                _calibrate(
                    prediction["benefit"][arm], calibration["benefit"][arm]
                )
                * prediction["gain"][arm]
                * calibration["positive_gain_scale"][arm]
                - _calibrate(
                    prediction["adverse"][arm], calibration["adverse"][arm]
                )
            ) for arm in PORTFOLIO_ARMS
        }
        targets = prediction["targets"]
        for arm in PORTFOLIO_ARMS:
            if targets[arm]["determined"] and float(targets[arm]["ratio"]) != 1.0:
                preferred_arm = float(targets[arm]["ratio"]) < 1.0
                arm_q0_hits.append((utility[arm] > 0.0) == preferred_arm)
        for left, right in itertools.combinations(PORTFOLIO_ARMS, 2):
            if not targets[left]["determined"] or not targets[right]["determined"]:
                continue
            left_ratio = float(targets[left]["ratio"])
            right_ratio = float(targets[right]["ratio"])
            if left_ratio == right_ratio:
                continue
            arm_arm_hits.append(
                (utility[left] > utility[right]) == (left_ratio < right_ratio)
            )
    return {
        "classification": classification,
        "arm_vs_q0_rank_accuracy": _accuracy(arm_q0_hits),
        "arm_vs_arm_rank_accuracy": _accuracy(arm_arm_hits),
        "context_count": len(rows),
        "instance_count": len({row["instance_hash"] for row in rows}),
        "aggregation_unit": "context_metrics_with_instance_count_reported",
    }


def _binary_metrics(probabilities, labels):
    if not labels:
        return {
            "count": 0, "balanced_accuracy": None, "precision": None,
            "recall": None, "specificity": None, "brier": None,
        }
    predictions = [int(value >= 0.5) for value in probabilities]
    tp = sum(predicted == 1 and target == 1 for predicted, target in zip(predictions, labels))
    tn = sum(predicted == 0 and target == 0 for predicted, target in zip(predictions, labels))
    fp = sum(predicted == 1 and target == 0 for predicted, target in zip(predictions, labels))
    fn = sum(predicted == 0 and target == 1 for predicted, target in zip(predictions, labels))
    recall = tp / (tp + fn) if tp + fn else None
    specificity = tn / (tn + fp) if tn + fp else None
    return {
        "count": len(labels),
        "balanced_accuracy": (
            (recall + specificity) / 2.0
            if recall is not None and specificity is not None else None
        ),
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": recall,
        "specificity": specificity,
        "brier": fmean(
            (probability - target) ** 2
            for probability, target in zip(probabilities, labels)
        ),
    }


def _accuracy(values):
    return fmean(float(value) for value in values) if values else None


def _candidate_actions(candidate, rows, *, allowed_arms_by_scale, variant=None):
    actions = []
    model = candidate["model"]
    calibration = candidate["probability_calibration"]
    thresholds = candidate["best_threshold"]["thresholds"]
    for row in rows:
        features = row["features"]
        output = _variant_output(model, features, variant)
        prediction = _calibrated_output(output, calibration)
        action = _action_from_values(
            prediction, thresholds, allowed_arms_by_scale[row["scale"]]
        )
        target = row["targets"].get(action, {}) if action != "Q0" else {}
        determined = action == "Q0" or bool(target.get("determined"))
        ratio = 1.0 if action == "Q0" or not determined else float(target["ratio"])
        actions.append({
            "context_id": row["context_id"], "action": action,
            "ratio": ratio, "determined": determined,
        })
    return actions


def _calibrated_output(output, calibration):
    return {
        arm: {
            "benefit": _calibrate(
                float(output["benefit_probability"][0, index]),
                calibration["benefit"][arm],
            ),
            "gain": float(output["conditional_positive_gain"][0, index])
                    * calibration["positive_gain_scale"][arm],
            "adverse": _calibrate(
                float(output["adverse_probability"][0, index]),
                calibration["adverse"][arm],
            ),
        }
        for index, arm in enumerate(PORTFOLIO_ARMS)
    }


def _action_from_values(values, thresholds, allowed):
    options = []
    for arm in allowed:
        row = values[arm]
        expected = row["benefit"] * row["gain"]
        score = expected - float(thresholds["risk_penalty"]) * row["adverse"]
        if (
            row["benefit"] >= float(thresholds["minimum_benefit_probability"])
            and row["adverse"] <= float(thresholds["maximum_adverse_probability"])
            and expected >= float(thresholds["minimum_expected_gain"])
            and score > 0.0
        ):
            options.append((score, arm))
    return max(options, default=(0.0, "Q0"))[1]


def _variant_output(model, features, variant):
    tensors = features.to_tensors()
    kwargs = {}
    if variant == "no_message" and getattr(model, "model_kind", "") == "gat":
        kwargs["disable_message_passing"] = True
    elif variant == "shuffled_topology" and getattr(model, "model_kind", "") == "gat":
        edge_index = tensors["edge_index"]
        kwargs["message_edge_index"] = torch.stack((
            edge_index[0], torch.roll(edge_index[1], shifts=1)
        ))
    with torch.inference_mode():
        return model(**tensors, **kwargs)


def _attribution(candidate, rows, normalization, *, allowed_arms_by_scale):
    baseline = _candidate_actions(
        candidate, rows, allowed_arms_by_scale=allowed_arms_by_scale
    )
    groups = {}
    for group in ("node", "edge", "context"):
        ablated = [
            {**row, "features": _ablate_features(
                row["features"], normalization, group=group
            )} for row in rows
        ]
        groups[group] = _action_comparison(
            baseline,
            _candidate_actions(
                candidate, ablated, allowed_arms_by_scale=allowed_arms_by_scale
            ),
        )
    features = {}
    for group, names in (
        ("node", PORTFOLIO_NODE_FEATURES),
        ("edge", PORTFOLIO_EDGE_FEATURES),
        ("context", PORTFOLIO_CONTEXT_FEATURES),
    ):
        for index, name in enumerate(names):
            ablated = [
                {**row, "features": _ablate_features(
                    row["features"], normalization, group=group, index=index
                )} for row in rows
            ]
            features[f"{group}:{name}"] = _action_comparison(
                baseline,
                _candidate_actions(
                    candidate, ablated,
                    allowed_arms_by_scale=allowed_arms_by_scale,
                ),
            )
    topology = {}
    if candidate["kind"] == "gat":
        for variant in ("no_message", "shuffled_topology"):
            topology[variant] = _action_comparison(
                baseline,
                _candidate_actions(
                    candidate, rows,
                    allowed_arms_by_scale=allowed_arms_by_scale,
                    variant=variant,
                ),
            )
    else:
        topology = {
            "not_applicable": "selected model has no message passing"
        }
    return {
        "partition": "calibration",
        "baseline": _action_summary(baseline),
        "group_ablation": groups,
        "per_feature_ablation": features,
        "topology_ablation": topology,
    }


def _ablate_features(features, normalization, *, group, index=None):
    means = tuple(float(value) for value in normalization[group]["mean"])
    if group == "node":
        rows = [list(row) for row in features.node_features]
        for row in rows:
            if index is None:
                row[:] = means
            else:
                row[index] = means[index]
        return replace(features, node_features=tuple(tuple(row) for row in rows))
    if group == "edge":
        rows = [list(row) for row in features.edge_features]
        for row in rows:
            if index is None:
                row[:] = means
            else:
                row[index] = means[index]
        return replace(features, edge_features=tuple(tuple(row) for row in rows))
    values = list(features.context_features)
    if index is None:
        values[:] = means
    else:
        values[index] = means[index]
    return replace(features, context_features=tuple(values))


def _action_comparison(baseline, variant):
    by_context = {row["context_id"]: row for row in baseline}
    disagreement = sum(
        row["action"] != by_context[row["context_id"]]["action"]
        for row in variant
    )
    return {
        **_action_summary(variant),
        "selected_action_disagreement_count": disagreement,
        "selected_action_disagreement_rate": disagreement / max(1, len(variant)),
    }


def _action_summary(rows):
    return {
        "action_counts": dict(sorted(Counter(row["action"] for row in rows).items())),
        "realized_wall_gm": geometric_mean([float(row["ratio"]) for row in rows]),
        "undetermined_activations": sum(
            row["action"] != "Q0" and not row["determined"] for row in rows
        ),
    }


def _candidate_disagreement(selected, candidates, rows, *, allowed_arms_by_scale):
    baseline = _candidate_actions(
        selected, rows, allowed_arms_by_scale=allowed_arms_by_scale
    )
    result = []
    for candidate in candidates:
        actions = _candidate_actions(
            candidate, rows, allowed_arms_by_scale=allowed_arms_by_scale
        )
        result.append({
            "model_kind": candidate["kind"], "seed": candidate["seed"],
            **_action_comparison(baseline, actions),
        })
    return result


def _seed_variance(candidates):
    result = {}
    for kind in MODEL_CLASSES:
        values = [
            row["best_threshold"]["combined_instance_weighted_gm"]
            for row in candidates if row["kind"] == kind
            and row["best_threshold"] is not None
        ]
        result[kind] = {
            "eligible_seed_count": len(values),
            "combined_gm_mean": fmean(values) if values else None,
            "combined_gm_std": pstdev(values) if len(values) > 1 else 0.0 if values else None,
            "combined_gm_min": min(values) if values else None,
            "combined_gm_max": max(values) if values else None,
        }
    return result


def _threshold_results(model, calibration, rows, grid, *, allowed_arms_by_scale):
    raw = _raw_predictions(model, rows)
    preparation = []
    for row in rows:
        started = perf_counter()
        with torch.inference_mode():
            model(**row["features"].to_tensors())
        preparation.append((perf_counter() - started) * 1000.0)
    results = []
    for probability, adverse, gain, penalty in itertools.product(
        grid["minimum_benefit_probability"],
        grid["maximum_adverse_probability"],
        grid["minimum_expected_gain"],
        grid["risk_penalty"],
    ):
        thresholds = {
            "minimum_benefit_probability": probability,
            "maximum_adverse_probability": adverse,
            "minimum_expected_gain": gain,
            "risk_penalty": penalty,
        }
        selected = []
        undetermined_activations = 0
        for prediction in raw:
            row = prediction["row"]
            options = []
            for arm in allowed_arms_by_scale[row["scale"]]:
                benefit = _calibrate(prediction["benefit"][arm], calibration["benefit"][arm])
                harm = _calibrate(prediction["adverse"][arm], calibration["adverse"][arm])
                positive = prediction["gain"][arm] * calibration["positive_gain_scale"][arm]
                expected = benefit * positive
                score = expected - penalty * harm
                if benefit >= probability and harm <= adverse and expected >= gain and score > 0.0:
                    options.append((score, arm))
            action = max(options, default=(0.0, "Q0"))[1]
            if action != "Q0" and not bool(row["targets"][action]["determined"]):
                undetermined_activations += 1
                ratio = 1.0
            else:
                ratio = 1.0 if action == "Q0" else float(row["targets"][action]["ratio"])
            selected.append((row, action, ratio))
        harmful = sum(action != "Q0" and ratio >= 1.05 for _row, action, ratio in selected)
        scale_gm = {
            scale: geometric_mean([ratio for row, _action, ratio in selected if row["scale"] == scale])
            for scale in (30, 50)
        }
        activated = sum(action != "Q0" for _row, action, _ratio in selected)
        n = max(1, activated)
        results.append({
            "thresholds": thresholds,
            "eligible": harmful == 0 and undetermined_activations == 0,
            "harmful_activations": harmful,
            "activation_count": activated,
            "undetermined_activations": undetermined_activations,
            "scale_gm": {str(key): value for key, value in scale_gm.items()},
            "worst_scale_gm": max(value for value in scale_gm.values() if value is not None),
            "combined_instance_weighted_gm": geometric_mean([ratio for _row, _action, ratio in selected]),
            "harmful_wilson95_upper": _wilson_upper(harmful, n),
            "preparation_p99_ms": percentile(preparation, 0.99),
        })
    return results


def _allowed_arms(admission):
    return {
        scale: [arm for arm, scales in admission["arm_scale_mask"].items() if scale in scales]
        for scale in (30, 50)
    }


def _calibrate(value, row):
    value = min(1 - 1e-7, max(1e-7, float(value)))
    score = float(row["slope"]) * log(value / (1 - value)) + float(row["intercept"])
    return 1.0 / (1.0 + exp(-max(-40.0, min(40.0, score))))


def _wilson_upper(successes, total):
    z = 1.959963984540054
    p = successes / total
    denominator = 1 + z * z / total
    center = p + z * z / (2 * total)
    radius = z * sqrt((p * (1 - p) + z * z / (4 * total)) / total)
    return (center + radius) / denominator


def _threshold_key(row):
    return (
        row["worst_scale_gm"], row["combined_instance_weighted_gm"],
        row["harmful_wilson95_upper"], row["preparation_p99_ms"],
        tuple(row["thresholds"].values()),
    )


def _candidate_key(row):
    threshold = row["best_threshold"]
    return (*_threshold_key(threshold)[:-1], row["parameter_count"], row["kind"], row["seed"])


def _checkpoint_payload(candidate, normalization):
    return {
        "schema_version": PORTFOLIO_CHECKPOINT_SCHEMA_V1,
        "feature_schema_version": PORTFOLIO_FEATURE_SCHEMA_V1,
        "input_parity_contract": PORTFOLIO_INPUT_PARITY_CONTRACT_V1,
        "model_kind": candidate["kind"],
        "action_universe": list(PORTFOLIO_ACTION_UNIVERSE),
        "normalization": normalization,
        "probability_calibration": candidate["probability_calibration"],
        "state_dict": candidate["model"].state_dict(),
        "parameter_count": candidate["parameter_count"],
        "seed": candidate["seed"],
        "activation_authority": False,
        "deployment_authorized": False,
    }


def _runtime_manifest(*, run_root, config, admission, selected,
                      selected_checkpoint, envelope, qgr1_ranker):
    source = _load(run_root / "source.freeze.json")
    corpus = _load(run_root / "corpus.freeze.json")
    engine_hashes = sorted({row["engine_hash"] for row in corpus["rows"]})
    policy_hashes = sorted({row["exact_action_policy_hash"] for row in corpus["rows"]})
    mask = admission["arm_scale_mask"]
    veto_by_scale = admission["forced_veto_arms_by_scale"]
    manifest = {
        "schema_version": PORTFOLIO_MANIFEST_SCHEMA_V1,
        "runtime_policy_id": PORTFOLIO_RUNTIME_POLICY_V1,
        "runtime_implementation_hash": context_queue_portfolio_runtime_implementation_hash(),
        "action_universe": list(PORTFOLIO_ACTION_UNIVERSE),
        "fallback_action": "Q0",
        "allowed_scales": [30, 50],
        "arm_scale_mask": mask,
        "forced_veto_arms": [],
        "forced_veto_arms_by_scale": veto_by_scale,
        "model_kind": selected["kind"],
        "selector_checkpoint_path": str(selected_checkpoint),
        "selector_checkpoint_sha256": _sha256(selected_checkpoint),
        "feature_schema_version": PORTFOLIO_FEATURE_SCHEMA_V1,
        "feature_envelope": envelope,
        "thresholds": selected["best_threshold"]["thresholds"],
        "allowed_exact_engine_hashes": engine_hashes,
        "allowed_exact_action_policy_hashes": policy_hashes,
        "torch_num_threads": 1,
        "development_e2e_authorized": True,
        "deployment_authorized": False,
        "development_only": True,
        "production_switch_authorized": False,
        "source_freeze_sha256": _sha256(run_root / "source.freeze.json"),
        "native_binary_sha256": source["native_binary_sha256"],
    }
    if mask.get("QGR1"):
        if qgr1_ranker is None or not qgr1_ranker.resolve().is_file():
            raise SystemExit("admitted QGR1 requires --qgr1-ranker")
        ranker = qgr1_ranker.resolve()
        manifest.update({
            "qgr1_ranker_checkpoint_path": str(ranker),
            "qgr1_ranker_checkpoint_sha256": _sha256(ranker),
            "qgr1_guidance_bucket_width": QGR1_BUCKET_WIDTH,
            "qgr1_label_state_schema_version": "lunar_spprc.qg2_label_state.v1",
        })
    else:
        manifest["forced_veto_arms"] = ["QGR1"]
    return manifest


def _candidate_summary(row):
    return {
        "model_kind": row["kind"], "seed": row["seed"],
        "parameter_count": row["parameter_count"], "best_epoch": row["best_epoch"],
        "checkpoint_path": str(row["checkpoint_path"]),
        "checkpoint_sha256": row["checkpoint_sha256"],
        "best_threshold": row["best_threshold"],
        "metrics": row["metrics"],
    }


def _verify_freezes(run_root):
    try:
        verify_portfolio_freezes(run_root, ROOT)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc


def _update_state(run_root, stage, status):
    state = _load(run_root / "state.json")
    state.update({"current_stage": stage, "status": status})
    (run_root / "state.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _terminal(run_root, reason, detail):
    _write_once(run_root / "terminal_decision.json", {
        "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_terminal.v1",
        "decision": "FAIL", "reason": reason, "detail": detail,
        "deployment_authorized": False, "production_switch_authorized": False,
    })
    _update_state(run_root, "TERMINAL", "FAIL")


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_once(path, payload):
    path = Path(path)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != text:
        raise SystemExit(f"immutable artifact drift: {path}")
    if not path.exists():
        path.write_text(text, encoding="utf-8")


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
