#!/usr/bin/env python3
"""Grouped-CV training and immutable selection for Interaction-GAT V3."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from dataclasses import replace
import hashlib
import itertools
import json
from math import exp, isfinite, log, sqrt
from pathlib import Path
import random
from statistics import median
import sys
from time import perf_counter

import torch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import (  # noqa: E402
    verify_portfolio_freezes,
)
from lunar_ice_bpc.guidance.context_queue_portfolio_gates import geometric_mean  # noqa: E402
from lunar_ice_bpc.guidance.context_queue_portfolio_v1 import (  # noqa: E402
    PORTFOLIO_ACTION_UNIVERSE,
    PORTFOLIO_ARMS,
    portfolio_training_loss,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_gates_v3 import (  # noqa: E402
    assess_v3_calibration,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_runtime_v3 import (  # noqa: E402
    INTERACTION_GAT_MANIFEST_SCHEMA_V2,
    INTERACTION_GAT_RUNTIME_POLICY_V3,
    interaction_gat_runtime_implementation_hash_v3,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_v2 import (  # noqa: E402
    INTERACTION_CONTEXT_FEATURES,
    INTERACTION_EDGE_FEATURES,
    INTERACTION_FEATURE_SCHEMA_V2,
    INTERACTION_GRAPH_SCHEMA_V1,
    INTERACTION_INPUT_PARITY_CONTRACT_V1,
    INTERACTION_NODE_FEATURES,
    InteractionGraphFeatures,
    fit_interaction_envelope,
    fit_interaction_normalization,
    interaction_graph_builder_hash,
    interaction_parameter_count,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_v3 import (  # noqa: E402
    INTERACTION_CHECKPOINT_SCHEMA_V2,
    INTERACTION_DATASET_SCHEMA_V3,
    V3_MODEL_KINDS,
    build_model_v3,
    features_for_model_kind,
)


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_interaction_gat_queue_selector_v3_20260814"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--qgr1-ranker", type=Path)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    _verify_active(run_root)
    oracle = _load(run_root / "base_portfolio_oracle.decision.json")
    if not bool(oracle.get("selector_training_authorized")):
        raise SystemExit("V3 base portfolio did not authorize GAT training")
    config = _load(run_root / "config.freeze.json")
    dataset_path = args.dataset.resolve()
    dataset = _load(dataset_path)
    rows = _dataset_rows(dataset)
    train_rows = [row for row in rows if row["partition"] == "train"]
    calibration_rows = [row for row in rows if row["partition"] == "calibration"]
    _validate_partition_counts(train_rows, calibration_rows)
    folds = _fold_binding(run_root, train_rows)
    allowed = {
        scale: [
            arm for arm, scales in dict(dataset["arm_scale_mask"]).items()
            if scale in {int(value) for value in scales}
        ] for scale in (30, 50)
    }
    normalization = fit_interaction_normalization(
        [row["features"] for row in train_rows]
    )
    envelope = fit_interaction_envelope(
        [row["features"] for row in train_rows], relative_margin=0.05
    )
    _write_once(run_root / "selector_normalization.freeze.json", normalization)
    _write_once(run_root / "selector_ood_envelope.freeze.json", envelope)

    torch.set_num_threads(1)
    candidates = []
    training_dir = run_root / "selector_training"
    training_dir.mkdir(parents=True, exist_ok=True)
    for kind in V3_MODEL_KINDS:
        for seed in config["selector_training"]["seeds"]:
            candidate = _grouped_cv_candidate(
                kind=kind, seed=int(seed), rows=train_rows, folds=folds,
                final_normalization=normalization,
                maximum_epochs=int(config["selector_training"]["maximum_epochs"]),
                patience=int(config["selector_training"]["patience"]),
            )
            candidate["probability_calibration"], degenerate = _fit_oof_calibration(
                candidate["oof_predictions"], allowed
            )
            candidate["degenerate_arm_scale_veto"] = degenerate
            candidate_allowed = {
                scale: [arm for arm in allowed[scale]
                        if arm not in set(degenerate.get(str(scale), ())) ]
                for scale in (30, 50)
            }
            candidate["allowed_arms_by_scale"] = candidate_allowed
            candidate["oof_metrics"] = _prediction_metrics(
                candidate["oof_predictions"], candidate["probability_calibration"]
            )
            calibration_predictions, preparation = _predict_rows(
                candidate["model"], calibration_rows, kind=kind
            )
            candidate["calibration_predictions"] = calibration_predictions
            candidate["calibration_metrics"] = _prediction_metrics(
                calibration_predictions, candidate["probability_calibration"]
            )
            thresholds = _threshold_results(
                calibration_predictions, candidate["probability_calibration"],
                config["threshold_grid"], candidate_allowed, preparation,
            )
            eligible = [row for row in thresholds if row["calibration_gate_eligible"]]
            candidate["threshold_candidates"] = thresholds
            candidate["best_threshold"] = min(eligible, key=_threshold_key) if eligible else None
            checkpoint_path = training_dir / f"{kind}_seed{seed}.pt"
            torch.save(_checkpoint(candidate, normalization, candidate_authorized=False), checkpoint_path)
            candidate["checkpoint_path"] = checkpoint_path
            candidate["checkpoint_sha256"] = _sha256(checkpoint_path)
            _write_once(training_dir / f"{kind}_seed{seed}.curve.json", {
                "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_training_curve.v3",
                "model_kind": kind, "seed": int(seed),
                "fold_best_epochs": candidate["fold_best_epochs"],
                "refit_epoch": candidate["refit_epoch"],
                "fold_curves": candidate["fold_curves"],
                "refit_curve": candidate["refit_curve"],
                "parameter_count": candidate["parameter_count"],
                "best_threshold": candidate["best_threshold"],
            })
            candidates.append(candidate)

    controls = {}
    for kind in ("mlp", "linear", "no_message", "shuffled_topology"):
        eligible = [row for row in candidates if row["kind"] == kind and row["best_threshold"]]
        if not eligible:
            _terminal(run_root, "NO_GAT_ADVANTAGE", {
                "reason": f"INDEPENDENT_CONTROL_NOT_FREEZABLE:{kind}"
            })
            return 2
        controls[kind] = min(eligible, key=_candidate_key)

    gat_candidates = [
        row for row in candidates if row["kind"] == "gat" and row["best_threshold"]
    ]
    if not gat_candidates:
        _terminal(run_root, "NO_SAFE_GAT_CALIBRATION_THRESHOLD", {
            "candidate_count": len(candidates)
        })
        return 2
    safe_gat = []
    for candidate in gat_candidates:
        summaries = {
            "full": _candidate_summary_for_gate(candidate),
            "no_message": _candidate_summary_for_gate(controls["no_message"]),
            "shuffled_topology": _candidate_summary_for_gate(
                controls["shuffled_topology"]
            ),
        }
        gate = assess_v3_calibration(
            full=summaries["full"], no_message=summaries["no_message"],
            shuffled_topology=summaries["shuffled_topology"],
        )
        candidate["topology_gate"] = {**summaries, "gate": gate}
        if gate["passed"]:
            safe_gat.append(candidate)
    if not safe_gat:
        _terminal(run_root, "NO_GAT_ADVANTAGE", {
            "gat_candidates": [_candidate_report(row) for row in gat_candidates]
        })
        return 2
    selected = min(safe_gat, key=_candidate_key)

    candidate_checkpoint = run_root / "interaction_gat_selector_candidate.pt"
    torch.save(_checkpoint(selected, normalization, candidate_authorized=True), candidate_checkpoint)
    controls_freeze = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_controls_freeze.v3",
        "frozen_before_heldout": True,
        "controls_candidate_authorized": False,
        "all_controls_independently_trained": True,
        "controls": {
            kind: {
                "seed": row["seed"], "refit_epoch": row["refit_epoch"],
                "parameter_count": row["parameter_count"],
                "checkpoint_path": str(row["checkpoint_path"]),
                "checkpoint_sha256": row["checkpoint_sha256"],
                "thresholds": row["best_threshold"]["thresholds"],
                "probability_calibration": row["probability_calibration"],
                "allowed_arms_by_scale": {
                    str(scale): row["allowed_arms_by_scale"][scale]
                    for scale in (30, 50)
                },
                "degenerate_arm_scale_veto": row["degenerate_arm_scale_veto"],
            } for kind, row in controls.items()
        },
    }
    _write_once(run_root / "selector_controls.freeze.json", controls_freeze)
    manifest = _manifest(
        run_root, selected, candidate_checkpoint, envelope,
        args.qgr1_ranker, dataset,
    )
    manifest_path = run_root / "selector_heldout_candidate.manifest.json"
    _write_once(manifest_path, manifest)
    attribution = _attribution(selected, calibration_rows, normalization)
    _write_once(run_root / "selector_attribution.calibration.json", attribution)
    report = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_training_report.v3",
        "representation_training_partition": "train_instances_only",
        "probability_calibration_partition": "train_oof_predictions_only",
        "calibration_use": "seed_and_threshold_selection_only",
        "heldout_outcomes_read": 0,
        "formal_outcomes_read": 0,
        "all_controls_independently_trained": True,
        "seed_variance": _seed_variance(candidates),
        "candidates": [_candidate_report(row) for row in candidates],
        "selected_gat_topology_gate": selected["topology_gate"],
        "selected_action_disagreement": _action_disagreement(selected, controls),
        "attribution": str(run_root / "selector_attribution.calibration.json"),
    }
    _write_once(run_root / "selector_training_report.json", report)
    decision = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_model_selection.v3",
        "decision": "GAT_CANDIDATE_FROZEN",
        "selected_model_kind": "gat",
        "selected_seed": selected["seed"],
        "selected_refit_epoch": selected["refit_epoch"],
        "selected_parameter_count": selected["parameter_count"],
        "selected_checkpoint": str(candidate_checkpoint),
        "selected_checkpoint_sha256": _sha256(candidate_checkpoint),
        "selected_threshold": selected["best_threshold"]["thresholds"],
        "controls_freeze": str(run_root / "selector_controls.freeze.json"),
        "heldout_manifest": str(manifest_path),
        "heldout_outcomes_read": 0,
        "formal_outcomes_read": 0,
        "development_only": True,
        "deployment_authorized": False,
        "production_switch_authorized": False,
    }
    _write_once(run_root / "selector_selection.decision.json", decision)
    _set_state(run_root, "SELECTOR_HELDOUT_FRESH", "READY")
    print(json.dumps(decision, ensure_ascii=False, indent=2))
    return 0


def _grouped_cv_candidate(
    *, kind, seed, rows, folds, final_normalization, maximum_epochs, patience,
):
    oof = []
    best_epochs = []
    fold_curves = []
    for fold in range(5):
        fit_rows = [row for row in rows if folds[row["instance_hash"]] != fold]
        validation_rows = [row for row in rows if folds[row["instance_hash"]] == fold]
        normalization = fit_interaction_normalization(
            [row["features"] for row in fit_rows]
        )
        model, best_epoch, curve = _fit_with_early_stopping(
            kind=kind, seed=seed + 1009 * fold, normalization=normalization,
            fit_rows=fit_rows, validation_rows=validation_rows,
            maximum_epochs=maximum_epochs, patience=patience,
        )
        predictions, _ = _predict_rows(model, validation_rows, kind=kind)
        for row in predictions:
            row["oof_fold"] = fold
        oof.extend(predictions)
        best_epochs.append(best_epoch)
        fold_curves.append({"fold": fold, "curve": curve})
    if {row["context_id"] for row in oof} != {row["context_id"] for row in rows}:
        raise SystemExit("V3 OOF predictions do not cover train contexts exactly once")
    refit_epoch = max(1, int(median(best_epochs)))
    model, refit_curve = _fit_exact_epochs(
        kind=kind, seed=seed, normalization=final_normalization,
        rows=rows, epochs=refit_epoch,
    )
    return {
        "kind": kind, "seed": seed, "model": model,
        "parameter_count": interaction_parameter_count(model),
        "fold_best_epochs": best_epochs, "refit_epoch": refit_epoch,
        "fold_curves": fold_curves, "refit_curve": refit_curve,
        "oof_predictions": oof,
    }


def _fit_with_early_stopping(
    *, kind, seed, normalization, fit_rows, validation_rows,
    maximum_epochs, patience,
):
    _seed(seed)
    model = build_model_v3(kind, normalization)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1.0e-3, weight_decay=1.0e-4)
    best_state = None
    best_loss = float("inf")
    best_epoch = 0
    stale = 0
    curve = []
    for epoch in range(1, maximum_epochs + 1):
        model.train()
        optimizer.zero_grad()
        train_loss = _instance_balanced_loss(model, fit_rows, kind)
        train_loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        optimizer.step()
        model.eval()
        with torch.inference_mode():
            validation_loss = float(_instance_balanced_loss(model, validation_rows, kind))
        curve.append({
            "epoch": epoch, "train_loss": float(train_loss.detach()),
            "validation_loss": validation_loss,
        })
        if validation_loss < best_loss - 1.0e-7:
            best_loss, best_epoch = validation_loss, epoch
            best_state = deepcopy(model.state_dict())
            stale = 0
        else:
            stale += 1
            if stale >= patience:
                break
    if best_state is None:
        raise SystemExit("V3 fold training produced no checkpoint")
    model.load_state_dict(best_state, strict=True)
    model.eval()
    return model, best_epoch, curve


def _fit_exact_epochs(*, kind, seed, normalization, rows, epochs):
    _seed(seed)
    model = build_model_v3(kind, normalization)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1.0e-3, weight_decay=1.0e-4)
    curve = []
    for epoch in range(1, epochs + 1):
        model.train()
        optimizer.zero_grad()
        loss = _instance_balanced_loss(model, rows, kind)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        optimizer.step()
        curve.append({"epoch": epoch, "train_loss": float(loss.detach())})
    model.eval()
    return model, curve


def _instance_balanced_loss(model, rows, kind):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["instance_hash"]].append(row)
    instance_losses = []
    for instance_rows in grouped.values():
        context_losses = []
        for row in instance_rows:
            feature = features_for_model_kind(
                row["features"], model_kind=kind, state_hash=row["state_hash"]
            )
            output = model(**feature.to_tensors())
            targets = row["targets"]
            ratios = [
                float(targets[arm]["ratio"]) if targets[arm]["determined"] else None
                for arm in PORTFOLIO_ARMS
            ]
            loss = portfolio_training_loss(
                output,
                benefit_target=torch.tensor([
                    float(targets[arm]["benefit"]) for arm in PORTFOLIO_ARMS
                ]),
                positive_gain_target=torch.tensor([
                    float(targets[arm]["positive_gain"]) for arm in PORTFOLIO_ARMS
                ]),
                adverse_target=torch.tensor([
                    float(targets[arm]["adverse"]) for arm in PORTFOLIO_ARMS
                ]),
                determined_mask=torch.tensor([
                    float(targets[arm]["determined"]) for arm in PORTFOLIO_ARMS
                ]),
                positive_mask=torch.tensor([
                    float(targets[arm]["benefit"]) for arm in PORTFOLIO_ARMS
                ]),
                pairwise_preferences=_preferences(ratios),
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


def _predict_rows(model, rows, *, kind):
    output_rows = []
    preparations = []
    model.eval()
    with torch.inference_mode():
        for row in rows:
            features = features_for_model_kind(
                row["features"], model_kind=kind, state_hash=row["state_hash"]
            )
            started = perf_counter()
            output = model(**features.to_tensors())
            preparations.append((perf_counter() - started) * 1000.0)
            output_rows.append({
                "context_id": row["context_id"], "instance_hash": row["instance_hash"],
                "scale": row["scale"], "state_hash": row["state_hash"],
                "context_weight": row["context_weight"], "targets": row["targets"],
                "benefit": {arm: float(output["benefit_probability"][0, index])
                            for index, arm in enumerate(PORTFOLIO_ARMS)},
                "gain": {arm: float(output["conditional_positive_gain"][0, index])
                         for index, arm in enumerate(PORTFOLIO_ARMS)},
                "adverse": {arm: float(output["adverse_probability"][0, index])
                            for index, arm in enumerate(PORTFOLIO_ARMS)},
            })
    return output_rows, preparations


def _fit_oof_calibration(predictions, allowed):
    calibration = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_oof_calibration.v3",
        "fit_partition": "train_oof_predictions_only",
        "instance_weighted": True, "benefit": {}, "adverse": {},
        "positive_gain_scale": {},
    }
    veto = {"30": [], "50": []}
    for arm in PORTFOLIO_ARMS:
        determined = [row for row in predictions if row["targets"][arm]["determined"]]
        for field in ("benefit", "adverse"):
            calibration[field][arm] = _weighted_platt(
                [row[field][arm] for row in determined],
                [float(row["targets"][arm][field]) for row in determined],
                [float(row["context_weight"]) for row in determined],
            )
        positive = [row for row in determined if row["targets"][arm]["benefit"]]
        predicted = sum(row["gain"][arm] * row["context_weight"] for row in positive)
        observed = sum(
            row["targets"][arm]["positive_gain"] * row["context_weight"]
            for row in positive
        )
        calibration["positive_gain_scale"][arm] = (
            max(0.1, min(10.0, observed / predicted)) if predicted > 0.0 else 1.0
        )
        for scale in (30, 50):
            if arm not in allowed[scale]:
                continue
            selected = [
                row for row in determined if row["scale"] == scale
            ]
            if any(len({bool(row["targets"][arm][field]) for row in selected}) < 2
                   for field in ("benefit", "adverse")):
                veto[str(scale)].append(arm)
    return calibration, {key: sorted(set(value)) for key, value in veto.items()}


def _weighted_platt(probabilities, labels, weights):
    if not probabilities or len(set(labels)) < 2:
        return {"slope": 1.0, "intercept": 0.0, "degenerate": True}
    x = torch.tensor([
        log(min(1 - 1e-6, max(1e-6, value)) /
            (1 - min(1 - 1e-6, max(1e-6, value))))
        for value in probabilities
    ])
    y = torch.tensor(labels)
    weight = torch.tensor(weights)
    slope = torch.tensor(1.0, requires_grad=True)
    intercept = torch.tensor(0.0, requires_grad=True)
    optimizer = torch.optim.LBFGS(
        [slope, intercept], max_iter=50, line_search_fn="strong_wolfe"
    )

    def closure():
        optimizer.zero_grad()
        losses = torch.nn.functional.binary_cross_entropy_with_logits(
            slope.clamp_min(0.0) * x + intercept, y, reduction="none"
        )
        loss = (losses * weight).sum() / weight.sum().clamp_min(1.0e-9)
        loss.backward()
        return loss

    optimizer.step(closure)
    return {
        "slope": max(0.0, float(slope.detach())),
        "intercept": float(intercept.detach()), "degenerate": False,
    }


def _prediction_metrics(predictions, calibration):
    classification = {"benefit": {}, "adverse": {}}
    for arm in PORTFOLIO_ARMS:
        determined = [row for row in predictions if row["targets"][arm]["determined"]]
        for field in ("benefit", "adverse"):
            classification[field][arm] = {
                "context_level": _context_binary_metrics(
                    determined, arm, field, calibration
                ),
                "instance_level": _instance_binary_metrics(
                    determined, arm, field, calibration
                ),
            }
    by_instance_q0 = defaultdict(list)
    by_instance_arm = defaultdict(list)
    for row in predictions:
        utility = _utilities(row, calibration)
        targets = row["targets"]
        for arm in PORTFOLIO_ARMS:
            if targets[arm]["determined"] and float(targets[arm]["ratio"]) != 1.0:
                by_instance_q0[row["instance_hash"]].append(
                    (utility[arm] > 0.0) == (float(targets[arm]["ratio"]) < 1.0)
                )
        for left, right in itertools.combinations(PORTFOLIO_ARMS, 2):
            if not targets[left]["determined"] or not targets[right]["determined"]:
                continue
            if float(targets[left]["ratio"]) == float(targets[right]["ratio"]):
                continue
            by_instance_arm[row["instance_hash"]].append(
                (utility[left] > utility[right]) ==
                (float(targets[left]["ratio"]) < float(targets[right]["ratio"]))
            )
    return {
        "classification": classification,
        "arm_vs_q0_macro_instance_rank_accuracy": _macro_hits(by_instance_q0),
        "arm_vs_arm_macro_instance_rank_accuracy": _macro_hits(by_instance_arm),
        "macro_instance_rank_accuracy": _macro_hits({
            key: by_instance_q0[key] + by_instance_arm[key]
            for key in set(by_instance_q0) | set(by_instance_arm)
        }),
        "context_count": len(predictions),
        "instance_count": len({row["instance_hash"] for row in predictions}),
        "aggregation_unit": "instance_first",
    }


def _instance_binary_metrics(rows, arm, field, calibration):
    grouped = defaultdict(list)
    for row in rows:
        probability = _calibrate(row[field][arm], calibration[field][arm])
        grouped[row["instance_hash"]].append((probability, int(row["targets"][arm][field])))
    if not grouped:
        return {key: None for key in (
            "balanced_accuracy", "precision", "recall", "specificity", "brier"
        )} | {"instance_count": 0, "context_count": 0}
    values = []
    for instance_rows in grouped.values():
        tp = sum(p >= 0.5 and y == 1 for p, y in instance_rows)
        tn = sum(p < 0.5 and y == 0 for p, y in instance_rows)
        fp = sum(p >= 0.5 and y == 0 for p, y in instance_rows)
        fn = sum(p < 0.5 and y == 1 for p, y in instance_rows)
        recall = tp / (tp + fn) if tp + fn else None
        specificity = tn / (tn + fp) if tn + fp else None
        values.append({
            "precision": tp / (tp + fp) if tp + fp else None,
            "recall": recall, "specificity": specificity,
            "balanced_accuracy": (
                (recall + specificity) / 2 if recall is not None and specificity is not None
                else None
            ),
            "brier": sum((p - y) ** 2 for p, y in instance_rows) / len(instance_rows),
        })
    return {
        key: _mean([row[key] for row in values if row[key] is not None])
        for key in ("balanced_accuracy", "precision", "recall", "specificity", "brier")
    } | {"instance_count": len(grouped), "context_count": len(rows)}


def _context_binary_metrics(rows, arm, field, calibration):
    values = [
        (_calibrate(row[field][arm], calibration[field][arm]),
         int(row["targets"][arm][field]))
        for row in rows
    ]
    if not values:
        return {key: None for key in (
            "balanced_accuracy", "precision", "recall", "specificity", "brier"
        )} | {"context_count": 0}
    tp = sum(p >= 0.5 and y == 1 for p, y in values)
    tn = sum(p < 0.5 and y == 0 for p, y in values)
    fp = sum(p >= 0.5 and y == 0 for p, y in values)
    fn = sum(p < 0.5 and y == 1 for p, y in values)
    recall = tp / (tp + fn) if tp + fn else None
    specificity = tn / (tn + fp) if tn + fp else None
    return {
        "balanced_accuracy": (
            (recall + specificity) / 2
            if recall is not None and specificity is not None else None
        ),
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": recall, "specificity": specificity,
        "brier": sum((p - y) ** 2 for p, y in values) / len(values),
        "context_count": len(values),
    }


def _threshold_results(predictions, calibration, grid, allowed, preparation):
    results = []
    for probability, adverse, gain, penalty in itertools.product(
        grid["minimum_benefit_probability"],
        grid["maximum_adverse_probability"],
        grid["minimum_expected_gain"], grid["risk_penalty"],
    ):
        thresholds = {
            "minimum_benefit_probability": probability,
            "maximum_adverse_probability": adverse,
            "minimum_expected_gain": gain, "risk_penalty": penalty,
        }
        selected = _select_actions(predictions, calibration, thresholds, allowed)
        scale_summary = {}
        harmful = sum(row["action"] != "Q0" and row["ratio"] >= 1.05 for row in selected)
        undetermined = sum(row["action"] != "Q0" and not row["determined"] for row in selected)
        for scale in (30, 50):
            rows = [row for row in selected if row["scale"] == scale]
            folded = _fold_selected(rows)
            scale_summary[str(scale)] = {
                "activation_instances": len({
                    row["instance_hash"] for row in rows if row["action"] != "Q0"
                }),
                "instance_ratios": folded,
                "instance_weighted_gm": geometric_mean(tuple(folded.values())),
            }
        scale_gms = [scale_summary[str(scale)]["instance_weighted_gm"] for scale in (30, 50)]
        combined = geometric_mean([
            ratio for scale in (30, 50)
            for ratio in scale_summary[str(scale)]["instance_ratios"].values()
        ])
        activated = sum(row["action"] != "Q0" for row in selected)
        eligible = bool(
            harmful == 0 and undetermined == 0
            and all(scale_summary[str(scale)]["activation_instances"] >= 2 for scale in (30, 50))
            and all(value is not None and value < 1.0 for value in scale_gms)
        )
        results.append({
            "thresholds": thresholds, "calibration_gate_eligible": eligible,
            "harmful_context_activations": harmful,
            "undetermined_activations": undetermined,
            "activation_count": activated,
            "scales": scale_summary,
            "worst_scale_instance_gm": max(scale_gms) if all(v is not None for v in scale_gms) else None,
            "combined_instance_gm": combined,
            "harmful_wilson95_upper": _wilson_upper(harmful, max(1, activated)),
            "preparation_p99_ms": _percentile(preparation, 0.99),
            "selected_actions": selected,
        })
    return results


def _select_actions(predictions, calibration, thresholds, allowed):
    selected = []
    for row in predictions:
        utilities = _calibrated_values(row, calibration)
        options = []
        for arm in allowed[row["scale"]]:
            value = utilities[arm]
            expected = value["benefit"] * value["gain"]
            score = expected - float(thresholds["risk_penalty"]) * value["adverse"]
            if (
                value["benefit"] >= float(thresholds["minimum_benefit_probability"])
                and value["adverse"] <= float(thresholds["maximum_adverse_probability"])
                and expected >= float(thresholds["minimum_expected_gain"])
                and score > 0.0
            ):
                options.append((score, arm))
        action = max(options, default=(0.0, "Q0"))[1]
        target = row["targets"].get(action, {}) if action != "Q0" else {}
        determined = action == "Q0" or bool(target.get("determined"))
        ratio = 1.0 if action == "Q0" or not determined else float(target["ratio"])
        selected.append({
            "context_id": row["context_id"], "instance_hash": row["instance_hash"],
            "scale": row["scale"], "action": action, "ratio": ratio,
            "determined": determined,
        })
    return selected


def _candidate_summary_for_gate(candidate):
    best = candidate["best_threshold"]
    return {
        "scales": {
            scale: {
                "activation_instances": row["activation_instances"],
                "net_gm": row["instance_weighted_gm"],
            } for scale, row in best["scales"].items()
        },
        "combined_gm": best["combined_instance_gm"],
        "harmful_activations": best["harmful_context_activations"],
        "train_oof_macro_rank_accuracy": candidate["oof_metrics"]["macro_instance_rank_accuracy"],
        "correctness_redlines": [],
    }


def _attribution(candidate, rows, normalization):
    baseline_predictions, _ = _predict_rows(candidate["model"], rows, kind="gat")
    baseline = _select_actions(
        baseline_predictions, candidate["probability_calibration"],
        candidate["best_threshold"]["thresholds"], candidate["allowed_arms_by_scale"],
    )
    groups = {}
    per_feature = {}
    for group, names in (
        ("node", INTERACTION_NODE_FEATURES),
        ("edge", INTERACTION_EDGE_FEATURES),
        ("context", INTERACTION_CONTEXT_FEATURES),
    ):
        groups[group] = _ablation_comparison(
            candidate, rows, baseline, normalization, group=group, index=None
        )
        for index, name in enumerate(names):
            per_feature[f"{group}:{name}"] = _ablation_comparison(
                candidate, rows, baseline, normalization, group=group, index=index
            )
    return {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_attribution.v3",
        "partition": "calibration_instances_only",
        "selected_model_kind": "gat", "selected_seed": candidate["seed"],
        "heldout_outcomes_read": 0, "formal_outcomes_read": 0,
        "baseline": _action_rows_summary(baseline),
        "group_ablation": groups, "per_feature_ablation": per_feature,
        "independent_topology_controls_reported_separately": True,
    }


def _ablation_comparison(candidate, rows, baseline, normalization, *, group, index):
    changed = [
        {**row, "features": _ablated_features(
            row["features"], normalization, group=group, index=index
        )} for row in rows
    ]
    predictions, _ = _predict_rows(candidate["model"], changed, kind="gat")
    actions = _select_actions(
        predictions, candidate["probability_calibration"],
        candidate["best_threshold"]["thresholds"], candidate["allowed_arms_by_scale"],
    )
    by_context = {row["context_id"]: row for row in baseline}
    return {
        **_action_rows_summary(actions),
        "selected_action_disagreement_count": sum(
            row["action"] != by_context[row["context_id"]]["action"] for row in actions
        ),
    }


def _ablated_features(features, normalization, *, group, index):
    means = tuple(float(value) for value in normalization[group]["mean"])
    if group == "node":
        rows = [list(row) for row in features.node_features]
        for row in rows:
            if index is None: row[:] = means
            else: row[index] = means[index]
        return replace(features, node_features=tuple(tuple(row) for row in rows))
    if group == "edge":
        rows = [list(row) for row in features.edge_features]
        for row in rows:
            if index is None: row[:] = means
            else: row[index] = means[index]
        return replace(features, edge_features=tuple(tuple(row) for row in rows))
    values = list(features.context_features)
    if index is None: values[:] = means
    else: values[index] = means[index]
    return replace(features, context_features=tuple(values))


def _action_rows_summary(rows):
    scale_instance = {}
    for scale in (30, 50):
        scale_instance[str(scale)] = _fold_selected([
            row for row in rows if row["scale"] == scale
        ])
    return {
        "action_counts": dict(sorted(Counter(row["action"] for row in rows).items())),
        "combined_instance_gm": geometric_mean([
            ratio for values in scale_instance.values() for ratio in values.values()
        ]),
        "instance_ratios_by_scale": scale_instance,
    }


def _checkpoint(candidate, normalization, *, candidate_authorized):
    return {
        "schema_version": INTERACTION_CHECKPOINT_SCHEMA_V2,
        "feature_schema_version": INTERACTION_FEATURE_SCHEMA_V2,
        "graph_schema_version": INTERACTION_GRAPH_SCHEMA_V1,
        "input_parity_contract": INTERACTION_INPUT_PARITY_CONTRACT_V1,
        "model_kind": candidate["kind"],
        "message_passing_required": candidate["kind"] == "gat",
        "independently_trained": True,
        "controls_candidate_authorized": False,
        "candidate_authorized": bool(candidate_authorized and candidate["kind"] == "gat"),
        "action_universe": list(PORTFOLIO_ACTION_UNIVERSE),
        "architecture": {
            "hidden_dim": 16, "attention_heads": 2, "layers": 2, "dropout": 0.1
        },
        "normalization": normalization,
        "probability_calibration": candidate["probability_calibration"],
        "degenerate_arm_scale_veto": candidate["degenerate_arm_scale_veto"],
        "state_dict": candidate["model"].state_dict(),
        "parameter_count": candidate["parameter_count"],
        "seed": candidate["seed"], "refit_epoch": candidate["refit_epoch"],
        "activation_authority": False,
        "development_only": True, "deployment_authorized": False,
        "production_switch_authorized": False,
    }


def _manifest(run_root, selected, checkpoint, envelope, qgr1_ranker, dataset):
    source = _load(run_root / "source.freeze.json")
    corpus = _load(run_root / "corpus.freeze.json")
    mask = {
        arm: sorted(
            scale for scale in (30, 50)
            if arm in selected["allowed_arms_by_scale"][scale]
        ) for arm in PORTFOLIO_ARMS
    }
    forced_by_scale = {
        str(scale): sorted(set(PORTFOLIO_ARMS) - set(selected["allowed_arms_by_scale"][scale]))
        for scale in (30, 50)
    }
    normalization_path = run_root / "selector_normalization.freeze.json"
    envelope_path = run_root / "selector_ood_envelope.freeze.json"
    manifest = {
        "schema_version": INTERACTION_GAT_MANIFEST_SCHEMA_V2,
        "runtime_policy_id": INTERACTION_GAT_RUNTIME_POLICY_V3,
        "runtime_implementation_hash": interaction_gat_runtime_implementation_hash_v3(),
        "graph_builder_hash": interaction_graph_builder_hash(),
        "graph_schema_version": INTERACTION_GRAPH_SCHEMA_V1,
        "feature_schema_version": INTERACTION_FEATURE_SCHEMA_V2,
        "checkpoint_schema_version": INTERACTION_CHECKPOINT_SCHEMA_V2,
        "dataset_schema_version": INTERACTION_DATASET_SCHEMA_V3,
        "corpus_schema_version": "lunar_ice_bpc.p0v5_interaction_gat_corpus_freeze.v3",
        "input_parity_contract": INTERACTION_INPUT_PARITY_CONTRACT_V1,
        "action_universe": list(PORTFOLIO_ACTION_UNIVERSE),
        "fallback_action": "Q0", "allowed_scales": [30, 50],
        "arm_scale_mask": mask, "forced_veto_arms": [],
        "forced_veto_arms_by_scale": forced_by_scale,
        "model_kind": "gat", "message_passing_required": True,
        "controls_candidate_authorized": False, "root_only_authority": True,
        "lifecycle_authority": ["root_cg"],
        "architecture": {
            "hidden_dim": 16, "attention_heads": 2, "layers": 2, "dropout": 0.1
        },
        "selector_checkpoint_path": str(checkpoint),
        "selector_checkpoint_sha256": _sha256(checkpoint),
        "feature_envelope": envelope,
        "thresholds": selected["best_threshold"]["thresholds"],
        "allowed_exact_engine_hashes": sorted({str(row["source_engine_hash"]) for row in corpus["rows"]}),
        "allowed_exact_action_policy_hashes": sorted({str(row["source_exact_action_policy_hash"]) for row in corpus["rows"]}),
        "allowed_exact_config_hashes": sorted({str(row["source_config_hash"]) for row in corpus["rows"]}),
        "torch_num_threads": 1, "development_e2e_authorized": True,
        "development_only": True, "deployment_authorized": False,
        "production_switch_authorized": False,
        "source_freeze_path": str(run_root / "source.freeze.json"),
        "source_freeze_sha256": _sha256(run_root / "source.freeze.json"),
        "corpus_freeze_path": str(run_root / "corpus.freeze.json"),
        "corpus_freeze_sha256": _sha256(run_root / "corpus.freeze.json"),
        "split_freeze_path": str(run_root / "instance_split.freeze.json"),
        "split_freeze_sha256": _sha256(run_root / "instance_split.freeze.json"),
        "cv_folds_freeze_path": str(run_root / "grouped_cv_folds.freeze.json"),
        "cv_folds_freeze_sha256": _sha256(run_root / "grouped_cv_folds.freeze.json"),
        "normalization_path": str(normalization_path),
        "normalization_sha256": _sha256(normalization_path),
        "normalization_payload_sha256": _json_sha256(
            _load(normalization_path)
        ),
        "ood_envelope_path": str(envelope_path),
        "ood_envelope_sha256": _sha256(envelope_path),
        "native_binary_sha256": source["native_binary_sha256"],
    }
    if mask["QGR1"]:
        if qgr1_ranker is None or not qgr1_ranker.resolve().is_file():
            raise SystemExit("admitted V3 QGR1 requires --qgr1-ranker")
        ranker = qgr1_ranker.resolve()
        manifest.update({
            "qgr1_ranker_checkpoint_path": str(ranker),
            "qgr1_ranker_checkpoint_sha256": _sha256(ranker),
            "qgr1_guidance_bucket_width": 0.0001,
            "qgr1_label_state_schema_version": "lunar_spprc.qg2_label_state.v1",
        })
    else:
        manifest["forced_veto_arms"] = ["QGR1"]
    return manifest


def _dataset_rows(payload):
    if payload.get("schema_version") != INTERACTION_DATASET_SCHEMA_V3:
        raise SystemExit("V3 dataset schema mismatch")
    rows = []
    seen = set()
    for raw in payload.get("rows") or ():
        partition = str(raw.get("partition") or "")
        if partition not in {"train", "calibration"}:
            raise SystemExit("V3 dataset contains prohibited partition")
        context_id = str(raw.get("context_id") or "")
        if not context_id or context_id in seen:
            raise SystemExit("V3 dataset repeats context")
        seen.add(context_id)
        targets = dict(raw.get("targets") or {})
        if set(targets) != set(PORTFOLIO_ARMS):
            raise SystemExit("V3 dataset arm target mismatch")
        if any(targets[arm].get("correctness_redlines") for arm in PORTFOLIO_ARMS):
            raise SystemExit("CORRECTNESS_REDLINE in V3 dataset")
        rows.append({
            "partition": partition, "context_id": context_id,
            "instance_hash": str(raw["instance_hash"]), "scale": int(raw["scale"]),
            "state_hash": str(raw["state_hash"]),
            "context_weight": float(raw["context_weight"]),
            "cv_fold": raw.get("cv_fold"), "features": _features(raw["features"]),
            "targets": targets,
        })
    return rows


def _features(payload):
    return InteractionGraphFeatures(
        instance_content_hash=str(payload["instance_content_hash"]),
        task_ids=tuple(payload["task_ids"]),
        node_features=tuple(tuple(map(float, row)) for row in payload["node_features"]),
        edge_index=tuple(tuple(map(int, row)) for row in payload["edge_index"]),
        edge_features=tuple(tuple(map(float, row)) for row in payload["edge_features"]),
        context_features=tuple(map(float, payload["context_features"])),
        graph_schema_version=str(payload["graph_schema_version"]),
        schema_version=str(payload["schema_version"]),
    )


def _fold_binding(run_root, train_rows):
    freeze = _load(run_root / "grouped_cv_folds.freeze.json")
    folds = {str(row["instance_hash"]): int(row["fold"]) for row in freeze["rows"]}
    if set(folds) != {row["instance_hash"] for row in train_rows}:
        raise SystemExit("V3 grouped-CV instance binding mismatch")
    if any(int(row["cv_fold"]) != folds[row["instance_hash"]] for row in train_rows):
        raise SystemExit("V3 dataset CV-fold binding drift")
    return folds


def _validate_partition_counts(train_rows, calibration_rows):
    expected = {
        "train": {30: (22, 14), 50: (33, 14)},
        "calibration": {30: (6, 4), 50: (10, 4)},
    }
    for name, rows in (("train", train_rows), ("calibration", calibration_rows)):
        for scale in (30, 50):
            selected = [row for row in rows if row["scale"] == scale]
            observed = (len(selected), len({row["instance_hash"] for row in selected}))
            if observed != expected[name][scale]:
                raise SystemExit(f"V3 {name} scale{scale} count drift:{observed}")


def _candidate_report(row):
    return {
        "model_kind": row["kind"], "seed": row["seed"],
        "parameter_count": row["parameter_count"],
        "fold_best_epochs": row["fold_best_epochs"], "refit_epoch": row["refit_epoch"],
        "checkpoint_path": str(row["checkpoint_path"]),
        "checkpoint_sha256": row["checkpoint_sha256"],
        "degenerate_arm_scale_veto": row["degenerate_arm_scale_veto"],
        "oof_metrics": row["oof_metrics"],
        "calibration_metrics": row["calibration_metrics"],
        "best_threshold": row["best_threshold"],
        "topology_gate": row.get("topology_gate"),
    }


def _seed_variance(candidates):
    result = {}
    for kind in V3_MODEL_KINDS:
        values = [
            row["best_threshold"]["combined_instance_gm"]
            for row in candidates if row["kind"] == kind and row["best_threshold"]
        ]
        result[kind] = {
            "eligible_seed_count": len(values),
            "combined_gm_min": min(values) if values else None,
            "combined_gm_max": max(values) if values else None,
            "combined_gm_mean": _mean(values),
        }
    return result


def _action_disagreement(selected, controls):
    baseline = {row["context_id"]: row for row in selected["best_threshold"]["selected_actions"]}
    result = {}
    for kind, candidate in controls.items():
        rows = candidate["best_threshold"]["selected_actions"]
        result[kind] = {
            "disagreement_count": sum(
                row["action"] != baseline[row["context_id"]]["action"] for row in rows
            ),
            "control_realized_instance_gm": candidate["best_threshold"]["combined_instance_gm"],
        }
    return result


def _calibrated_values(row, calibration):
    return {
        arm: {
            "benefit": _calibrate(row["benefit"][arm], calibration["benefit"][arm]),
            "gain": row["gain"][arm] * calibration["positive_gain_scale"][arm],
            "adverse": _calibrate(row["adverse"][arm], calibration["adverse"][arm]),
        } for arm in PORTFOLIO_ARMS
    }


def _utilities(row, calibration):
    values = _calibrated_values(row, calibration)
    return {arm: values[arm]["benefit"] * values[arm]["gain"] - values[arm]["adverse"]
            for arm in PORTFOLIO_ARMS}


def _calibrate(value, row):
    probability = min(1.0 - 1.0e-7, max(1.0e-7, float(value)))
    score = float(row["slope"]) * log(probability / (1.0 - probability)) + float(row["intercept"])
    return 1.0 / (1.0 + exp(-max(-40.0, min(40.0, score))))


def _fold_selected(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["instance_hash"]].append(float(row["ratio"]))
    return {instance: float(geometric_mean(values)) for instance, values in sorted(grouped.items())}


def _macro_hits(grouped):
    values = [sum(map(float, rows)) / len(rows) for rows in grouped.values() if rows]
    return _mean(values)


def _mean(values):
    return sum(values) / len(values) if values else None


def _wilson_upper(successes, total):
    z = 1.959963984540054
    p = successes / total
    denominator = 1 + z * z / total
    center = p + z * z / (2 * total)
    radius = z * sqrt((p * (1 - p) + z * z / (4 * total)) / total)
    return (center + radius) / denominator


def _percentile(values, quantile):
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int((len(ordered) - 1) * quantile + 0.999999)))
    return ordered[index]


def _threshold_key(row):
    return (
        row["worst_scale_instance_gm"], row["combined_instance_gm"],
        row["harmful_wilson95_upper"], row["preparation_p99_ms"],
        tuple(row["thresholds"].values()),
    )


def _candidate_key(row):
    return (*_threshold_key(row["best_threshold"]), row["parameter_count"], row["seed"])


def _seed(value):
    torch.manual_seed(int(value))
    random.seed(int(value))


def _json_sha256(value):
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")).hexdigest()


def _verify_active(run_root):
    try:
        verify_portfolio_freezes(run_root, ROOT)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    if bool(_load(run_root / "state.json").get("terminal")):
        raise SystemExit("terminal V3 chain forbids selector training")


def _set_state(run_root, stage, status):
    path = run_root / "state.json"
    state = _load(path)
    state.update({"current_stage": stage, "status": status})
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _terminal(run_root, reason, detail):
    _write_once(run_root / "terminal_decision.json", {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_terminal.v3",
        "decision": "FAIL", "reason": reason, "detail": detail,
        "development_only": True, "deployment_authorized": False,
        "production_switch_authorized": False,
    })
    path = run_root / "state.json"
    state = _load(path)
    state.update({
        "current_stage": "TERMINAL", "status": "FAIL", "terminal": True,
        "terminal_decision": reason,
    })
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_once(path, payload):
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != encoded:
        raise SystemExit(f"immutable V3 training artifact differs:{path}")
    if not path.exists():
        path.write_text(encoded, encoding="utf-8")


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
