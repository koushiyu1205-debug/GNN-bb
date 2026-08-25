#!/usr/bin/env python3
"""Grouped-CV training for the unique censor-aware V4 GAT candidate."""

from __future__ import annotations

from collections import defaultdict
import hashlib
import itertools
import json
from math import isfinite
from pathlib import Path
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
from lunar_ice_bpc.guidance.interaction_gat_queue_runtime_v4 import (  # noqa: E402
    INTERACTION_GAT_RUNTIME_POLICY_V4,
    interaction_gat_runtime_implementation_hash_v4,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_v2 import (  # noqa: E402
    INTERACTION_FEATURE_SCHEMA_V2, INTERACTION_GRAPH_SCHEMA_V1,
    INTERACTION_INPUT_PARITY_CONTRACT_V1, InteractionGraphFeatures,
    fit_interaction_envelope, fit_interaction_normalization,
    interaction_graph_builder_hash, interaction_parameter_count,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_v4 import (  # noqa: E402
    INTERACTION_CHECKPOINT_SCHEMA_V3, INTERACTION_DATASET_SCHEMA_V4,
    INTERACTION_MANIFEST_SCHEMA_V3, V4_ACTION_UNIVERSE, V4_ARMS,
    V4_MODEL_KINDS, build_model_v4, features_for_model_kind_v4,
    interaction_training_loss_v4,
)
import scripts.train_p0v5_interaction_gat_selector_v3 as shared  # noqa: E402


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_residual_gat_censor_aware_selector_v4_20260815"


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--qgr1-ranker", type=Path)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    _verify_active(run_root)
    if not bool(_load(run_root / "portfolio_oracle.decision.json").get("passed")):
        raise SystemExit("V4 portfolio oracle did not authorize selector training")
    config = _load(run_root / "config.freeze.json")
    dataset_path = args.dataset.resolve()
    dataset = _load(dataset_path)
    rows = _dataset_rows(dataset)
    train_rows = [row for row in rows if row["partition"] == "train"]
    calibration_rows = [row for row in rows if row["partition"] == "calibration"]
    folds = {str(row["instance_hash"]): int(row["fold"])
             for row in _load(run_root / "grouped_cv_folds.freeze.json")["rows"]}
    if {row["instance_hash"] for row in train_rows} != set(folds):
        raise SystemExit("V4 grouped-CV fold binding mismatch")
    allowed = {
        scale: [arm for arm, scales in dataset["arm_scale_mask"].items()
                if scale in {int(value) for value in scales}]
        for scale in (30, 50)
    }
    normalization = fit_interaction_normalization([row["features"] for row in train_rows])
    envelope = fit_interaction_envelope([row["features"] for row in train_rows],
                                        relative_margin=0.05)
    _write_once(run_root / "selector_normalization.freeze.json", normalization)
    _write_once(run_root / "selector_ood_envelope.freeze.json", envelope)
    _install_shared_v4_training_hooks()
    torch.set_num_threads(1)
    candidates = []
    output_dir = run_root / "selector_training"
    output_dir.mkdir(parents=True, exist_ok=True)
    for kind in V4_MODEL_KINDS:
        for seed_value in config["selector_training"]["seeds"]:
            seed = int(seed_value)
            candidate = shared._grouped_cv_candidate(
                kind=kind, seed=seed, rows=train_rows, folds=folds,
                final_normalization=normalization,
                maximum_epochs=int(config["selector_training"]["maximum_epochs"]),
                patience=int(config["selector_training"]["patience"]),
            )
            calibration, degenerate = _fit_oof_calibration(
                candidate["oof_predictions"], allowed
            )
            candidate["probability_calibration"] = calibration
            candidate["degenerate_arm_scale_veto"] = degenerate
            candidate["allowed_arms_by_scale"] = {
                scale: [arm for arm in allowed[scale]
                        if arm not in set(degenerate[str(scale)])]
                for scale in (30, 50)
            }
            candidate["oof_metrics"] = _metrics(
                candidate["oof_predictions"], calibration
            )
            predictions, preparation = _predict_rows(
                candidate["model"], calibration_rows, kind=kind
            )
            candidate["calibration_predictions"] = predictions
            candidate["calibration_metrics"] = _metrics(predictions, calibration)
            thresholds = _threshold_results(
                predictions, calibration, config["threshold_grid"],
                candidate["allowed_arms_by_scale"], preparation,
            )
            candidate["threshold_candidates"] = thresholds
            eligible = [row for row in thresholds if row["calibration_gate_eligible"]]
            candidate["best_threshold"] = min(eligible, key=_threshold_key) if eligible else None
            checkpoint = output_dir / f"{kind}_seed{seed}.pt"
            torch.save(_checkpoint(candidate, normalization, candidate_authorized=False), checkpoint)
            candidate["checkpoint_path"] = str(checkpoint)
            candidate["checkpoint_sha256"] = _sha256(checkpoint)
            _write_once(output_dir / f"{kind}_seed{seed}.curve.json", {
                "schema_version": "lunar_ice_bpc.p0v5_residual_gat_training_curve.v4",
                "model_kind": kind, "seed": seed,
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
        values = [row for row in candidates if row["kind"] == kind
                  and row["best_threshold"] is not None]
        if not values:
            return _stop(run_root, "NO_GAT_ADVANTAGE", f"control_not_freezable:{kind}")
        controls[kind] = min(values, key=_candidate_key)
    gat_values = [row for row in candidates if row["kind"] == "gat"
                  and row["best_threshold"] is not None]
    if not gat_values:
        return _stop(run_root, "NO_SAFE_GAT_THRESHOLD", "no safe calibration threshold")
    safe = [row for row in gat_values if _gat_advantage(row, controls)]
    if not safe:
        return _stop(run_root, "NO_GAT_ADVANTAGE", {
            "gat": [_report(row) for row in gat_values],
            "controls": {kind: _report(row) for kind, row in controls.items()},
        })
    selected = min(safe, key=_candidate_key)
    candidate_checkpoint = run_root / "interaction_gat_selector_candidate.pt"
    torch.save(_checkpoint(selected, normalization, candidate_authorized=True),
               candidate_checkpoint)
    controls_freeze = {
        "schema_version": "lunar_ice_bpc.p0v5_residual_gat_controls_freeze.v4",
        "frozen_before_heldout": True, "controls_candidate_authorized": False,
        "all_controls_independently_trained": True,
        "controls": {kind: {
            "seed": row["seed"], "refit_epoch": row["refit_epoch"],
            "parameter_count": row["parameter_count"],
            "checkpoint_path": row["checkpoint_path"],
            "checkpoint_sha256": row["checkpoint_sha256"],
            "thresholds": row["best_threshold"]["thresholds"],
            "probability_calibration": row["probability_calibration"],
            "allowed_arms_by_scale": {
                str(scale): row["allowed_arms_by_scale"][scale] for scale in (30, 50)
            },
        } for kind, row in controls.items()},
    }
    _write_once(run_root / "selector_controls.freeze.json", controls_freeze)
    manifest = _manifest(
        run_root, selected, candidate_checkpoint, envelope, args.qgr1_ranker, dataset
    )
    manifest_path = run_root / "selector_heldout_candidate.manifest.json"
    _write_once(manifest_path, manifest)
    report = {
        "schema_version": "lunar_ice_bpc.p0v5_residual_gat_training_report.v4",
        "representation_training_partition": "train_instances_only",
        "probability_calibration_partition": "train_oof_predictions_only",
        "calibration_use": "seed_and_threshold_selection_only",
        "heldout_outcomes_read": 0, "formal_outcomes_read": 0,
        "all_controls_independently_trained": True,
        "candidates": [_report(row) for row in candidates],
        "selected_gat_advantage": _advantage_report(selected, controls),
    }
    _write_once(run_root / "selector_training_report.json", report)
    decision = {
        "schema_version": "lunar_ice_bpc.p0v5_residual_gat_model_selection.v4",
        "decision": "GAT_CANDIDATE_FROZEN", "selected_model_kind": "gat",
        "selected_seed": selected["seed"], "selected_refit_epoch": selected["refit_epoch"],
        "selected_parameter_count": selected["parameter_count"],
        "selected_checkpoint": str(candidate_checkpoint),
        "selected_checkpoint_sha256": _sha256(candidate_checkpoint),
        "selected_threshold": selected["best_threshold"]["thresholds"],
        "heldout_manifest": str(manifest_path), "heldout_outcomes_read": 0,
        "development_only": True, "deployment_authorized": False,
        "production_switch_authorized": False,
    }
    _write_once(run_root / "selector_selection.decision.json", decision)
    _set_state(run_root, "SELECTOR_HELDOUT_FRESH", "READY")
    print(json.dumps(decision, ensure_ascii=False, indent=2))
    return 0


def _install_shared_v4_training_hooks():
    shared.PORTFOLIO_ARMS = V4_ARMS
    shared.build_model_v3 = build_model_v4
    shared.features_for_model_kind = features_for_model_kind_v4
    shared._instance_balanced_loss = _instance_balanced_loss
    shared._predict_rows = lambda model, rows, *, kind: _predict_rows(model, rows, kind=kind)


def _instance_balanced_loss(model, rows, kind):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["instance_hash"]].append(row)
    instance_losses = []
    for instance_rows in grouped.values():
        context_losses = []
        for row in instance_rows:
            feature = features_for_model_kind_v4(
                row["features"], model_kind=kind, state_hash=row["state_hash"]
            )
            output = model(**feature.to_tensors())
            targets = row["targets"]
            ratios = [float(targets[arm]["ratio"])
                      if targets[arm]["determined"] else None for arm in V4_ARMS]
            context_losses.append(interaction_training_loss_v4(
                output,
                benefit_target=torch.tensor([float(targets[a]["benefit"]) for a in V4_ARMS]),
                positive_gain_target=torch.tensor([float(targets[a]["positive_gain"]) for a in V4_ARMS]),
                adverse_target=torch.tensor([float(targets[a]["adverse"]) for a in V4_ARMS]),
                resource_censor_target=torch.tensor([float(targets[a]["resource_censor"]) for a in V4_ARMS]),
                determined_mask=torch.tensor([float(targets[a]["determined"]) for a in V4_ARMS]),
                positive_mask=torch.tensor([float(targets[a]["benefit"]) for a in V4_ARMS]),
                resource_mask=torch.tensor([float(targets[a]["resource_observed"]) for a in V4_ARMS]),
                pairwise_preferences=_preferences(ratios),
            )["loss"])
        instance_losses.append(torch.stack(context_losses).mean())
    return torch.stack(instance_losses).mean()


def _preferences(ratios):
    values = [1.0, *ratios]
    result = []
    for left, right in itertools.combinations(range(len(values)), 2):
        if values[left] is None or values[right] is None or values[left] == values[right]:
            continue
        preferred, other = (left, right) if values[left] < values[right] else (right, left)
        result.append((preferred - 1, other - 1, 1.0))
    return result


def _predict_rows(model, rows, *, kind):
    result, walls = [], []
    model.eval()
    with torch.inference_mode():
        for row in rows:
            feature = features_for_model_kind_v4(
                row["features"], model_kind=kind, state_hash=row["state_hash"]
            )
            started = perf_counter()
            output = model(**feature.to_tensors())
            walls.append((perf_counter() - started) * 1000.0)
            result.append({
                "context_id": row["context_id"], "instance_hash": row["instance_hash"],
                "scale": row["scale"], "state_hash": row["state_hash"],
                "context_weight": row["context_weight"], "targets": row["targets"],
                "benefit": {arm: float(output["benefit_probability"][0, index])
                            for index, arm in enumerate(V4_ARMS)},
                "gain": {arm: float(output["conditional_positive_gain"][0, index])
                         for index, arm in enumerate(V4_ARMS)},
                "adverse": {arm: float(output["adverse_probability"][0, index])
                            for index, arm in enumerate(V4_ARMS)},
                "resource_censor": {
                    arm: float(output["resource_censor_probability"][0, index])
                    for index, arm in enumerate(V4_ARMS)
                },
            })
    return result, walls


def _fit_oof_calibration(predictions, allowed):
    result = {
        "schema_version": "lunar_ice_bpc.p0v5_residual_gat_oof_calibration.v4",
        "fit_partition": "train_oof_predictions_only", "instance_weighted": True,
        "benefit": {}, "adverse": {}, "resource_censor": {},
        "positive_gain_scale": {},
    }
    veto = {"30": [], "50": []}
    for arm in V4_ARMS:
        determined = [row for row in predictions if row["targets"][arm]["determined"]]
        resource_rows = [row for row in predictions if row["targets"][arm]["resource_observed"]]
        for field, values in (("benefit", determined), ("adverse", determined),
                              ("resource_censor", resource_rows)):
            result[field][arm] = shared._weighted_platt(
                [row[field][arm] for row in values],
                [float(row["targets"][arm][field]) for row in values],
                [float(row["context_weight"]) for row in values],
            )
        positive = [row for row in determined if row["targets"][arm]["benefit"]]
        predicted = sum(row["gain"][arm] * row["context_weight"] for row in positive)
        observed = sum(row["targets"][arm]["positive_gain"] * row["context_weight"]
                       for row in positive)
        result["positive_gain_scale"][arm] = (
            max(0.1, min(10.0, observed / predicted)) if predicted > 0 else 1.0
        )
        for scale in (30, 50):
            if arm not in allowed[scale]:
                continue
            for field, values in (("benefit", determined), ("adverse", determined),
                                  ("resource_censor", resource_rows)):
                selected = [row for row in values if row["scale"] == scale]
                if len({bool(row["targets"][arm][field]) for row in selected}) < 2:
                    veto[str(scale)].append(arm)
                    break
    return result, {key: sorted(set(value)) for key, value in veto.items()}


def _calibrated(row, calibration, arm):
    return {
        "benefit": shared._calibrate(row["benefit"][arm], calibration["benefit"][arm]),
        "gain": row["gain"][arm] * calibration["positive_gain_scale"][arm],
        "adverse": shared._calibrate(row["adverse"][arm], calibration["adverse"][arm]),
        "resource": shared._calibrate(
            row["resource_censor"][arm], calibration["resource_censor"][arm]
        ),
    }


def _threshold_results(predictions, calibration, grid, allowed, preparation):
    results = []
    for values in itertools.product(
        grid["minimum_benefit_probability"], grid["maximum_adverse_probability"],
        grid["minimum_expected_gain"], grid["risk_penalty"],
        grid["maximum_resource_probability"], grid["resource_risk_penalty"],
    ):
        threshold = dict(zip((
            "minimum_benefit_probability", "maximum_adverse_probability",
            "minimum_expected_gain", "risk_penalty",
            "maximum_resource_probability", "resource_risk_penalty",
        ), values, strict=True))
        selected = _select(predictions, calibration, threshold, allowed)
        harmful = sum(row["action"] != "Q0" and row["ratio"] >= 1.05 for row in selected)
        adverse = sum(row["action"] != "Q0" and row["adverse"] for row in selected)
        resource = sum(row["action"] != "Q0" and row["resource_censor"] for row in selected)
        censored = sum(row["action"] != "Q0" and not row["determined"] for row in selected)
        scales = {}
        for scale in (30, 50):
            selected_scale = [row for row in selected if row["scale"] == scale]
            folded = _fold(selected_scale)
            scales[str(scale)] = {
                "activation_instances": len({row["instance_hash"] for row in selected_scale
                                             if row["action"] != "Q0"}),
                "instance_ratios": folded,
                "instance_weighted_gm": geometric_mean(tuple(folded.values())),
            }
        scale_gms = [scales[str(scale)]["instance_weighted_gm"] for scale in (30, 50)]
        combined = geometric_mean(tuple(
            ratio for scale in (30, 50) for ratio in scales[str(scale)]["instance_ratios"].values()
        ))
        eligible = bool(
            harmful == adverse == resource == censored == 0
            and all(scales[str(scale)]["activation_instances"] >= 2 for scale in (30, 50))
            and all(value is not None and value < 1.0 for value in scale_gms)
        )
        results.append({
            "thresholds": threshold, "calibration_gate_eligible": eligible,
            "harmful_context_activations": harmful, "adverse_activations": adverse,
            "resource_censor_activations": resource, "undetermined_activations": censored,
            "activation_count": sum(row["action"] != "Q0" for row in selected),
            "scales": scales, "worst_scale_instance_gm": max(scale_gms)
            if all(value is not None for value in scale_gms) else None,
            "combined_instance_gm": combined,
            "harmful_wilson95_upper": shared._wilson_upper(
                harmful, max(1, sum(row["action"] != "Q0" for row in selected))
            ),
            "preparation_p99_ms": shared._percentile(preparation, 0.99),
            "selected_actions": selected,
        })
    return results


def _select(predictions, calibration, threshold, allowed):
    result = []
    for row in predictions:
        options = []
        for arm in allowed[row["scale"]]:
            value = _calibrated(row, calibration, arm)
            expected = value["benefit"] * value["gain"]
            score = (expected - threshold["risk_penalty"] * value["adverse"]
                     - threshold["resource_risk_penalty"] * value["resource"])
            if (
                value["benefit"] >= threshold["minimum_benefit_probability"]
                and expected >= threshold["minimum_expected_gain"]
                and value["adverse"] <= threshold["maximum_adverse_probability"]
                and value["resource"] <= threshold["maximum_resource_probability"]
                and score > 0.0
            ):
                options.append((score, arm))
        action = max(options, default=(0.0, "Q0"))[1]
        target = row["targets"].get(action, {}) if action != "Q0" else {}
        determined = action == "Q0" or bool(target.get("determined"))
        result.append({
            "context_id": row["context_id"], "instance_hash": row["instance_hash"],
            "scale": row["scale"], "action": action, "determined": determined,
            "ratio": 1.0 if action == "Q0" or not determined else float(target["ratio"]),
            "adverse": bool(target.get("adverse")),
            "resource_censor": bool(target.get("resource_censor")),
        })
    return result


def _fold(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["instance_hash"]].append(float(row["ratio"]))
    return {instance: geometric_mean(tuple(values)) for instance, values in grouped.items()}


def _metrics(predictions, calibration):
    macro = defaultdict(list)
    scale_macro = {30: defaultdict(list), 50: defaultdict(list)}
    classification = {field: {} for field in ("benefit", "adverse", "resource_censor")}
    for arm in V4_ARMS:
        for field in classification:
            key = "resource_observed" if field == "resource_censor" else "determined"
            rows = [row for row in predictions if row["targets"][arm][key]]
            classification[field][arm] = shared._context_binary_metrics(
                rows, arm, field, calibration
            )
        for row in predictions:
            target = row["targets"][arm]
            if not target["determined"] or float(target["ratio"]) == 1.0:
                continue
            value = _calibrated(row, calibration, arm)
            utility = value["benefit"] * value["gain"] - value["adverse"] - value["resource"]
            hit = (utility > 0.0) == (float(target["ratio"]) < 1.0)
            macro[row["instance_hash"]].append(hit)
            scale_macro[row["scale"]][row["instance_hash"]].append(hit)
    return {
        "classification": classification,
        "macro_instance_rank_accuracy": shared._macro_hits(macro),
        "scale_macro_instance_rank_accuracy": {
            str(scale): shared._macro_hits(values) for scale, values in scale_macro.items()
        },
    }


def _gat_advantage(gat, controls):
    report = _advantage_report(gat, controls)
    return all(report[key] for key in (
        "topology_rank_not_worse", "topology_drop_present",
        "scale50_strictly_beats_simple", "scale30_not_worse_than_simple",
        "combined_strictly_beats_simple",
    ))


def _advantage_report(gat, controls):
    gat_rank = gat["oof_metrics"]["macro_instance_rank_accuracy"]
    topology = [controls[name]["oof_metrics"]["macro_instance_rank_accuracy"]
                for name in ("no_message", "shuffled_topology")]
    gat_best = gat["best_threshold"]
    simple = [controls[name]["best_threshold"] for name in ("mlp", "linear")]
    scale50 = gat_best["scales"]["50"]["instance_weighted_gm"]
    scale30 = gat_best["scales"]["30"]["instance_weighted_gm"]
    return {
        "topology_rank_not_worse": all(gat_rank >= value for value in topology),
        "topology_drop_present": any(gat_rank - value >= 0.02 for value in topology),
        "scale50_strictly_beats_simple": all(
            scale50 < row["scales"]["50"]["instance_weighted_gm"] for row in simple
        ),
        "scale30_not_worse_than_simple": all(
            scale30 <= row["scales"]["30"]["instance_weighted_gm"] for row in simple
        ),
        "combined_strictly_beats_simple": all(
            gat_best["combined_instance_gm"] < row["combined_instance_gm"] for row in simple
        ),
        "gat_rank": gat_rank, "topology_ranks": topology,
    }


def _checkpoint(candidate, normalization, *, candidate_authorized):
    return {
        "schema_version": INTERACTION_CHECKPOINT_SCHEMA_V3,
        "feature_schema_version": INTERACTION_FEATURE_SCHEMA_V2,
        "graph_schema_version": INTERACTION_GRAPH_SCHEMA_V1,
        "input_parity_contract": INTERACTION_INPUT_PARITY_CONTRACT_V1,
        "model_kind": candidate["kind"],
        "message_passing_required": candidate["kind"] == "gat",
        "independently_trained": True, "controls_candidate_authorized": False,
        "candidate_authorized": bool(candidate_authorized and candidate["kind"] == "gat"),
        "action_universe": list(V4_ACTION_UNIVERSE),
        "architecture": {"hidden_dim": 16, "attention_heads": 2, "layers": 2,
                         "dropout": 0.1, "residual": True, "layer_norm": True},
        "normalization": normalization,
        "probability_calibration": candidate["probability_calibration"],
        "state_dict": candidate["model"].state_dict(),
        "parameter_count": candidate["parameter_count"], "seed": candidate["seed"],
        "trained_epoch": candidate["refit_epoch"],
        "development_only": True, "deployment_authorized": False,
        "production_switch_authorized": False,
    }


def _manifest(run_root, selected, checkpoint, envelope, qgr1_ranker, dataset):
    source = _load(run_root / "source.freeze.json")
    allowed = selected["allowed_arms_by_scale"]
    qgr1_scales = allowed[30] + allowed[50]
    qgr1_active = "QGR1" in qgr1_scales
    payload = {
        "schema_version": INTERACTION_MANIFEST_SCHEMA_V3,
        "runtime_policy_id": INTERACTION_GAT_RUNTIME_POLICY_V4,
        "runtime_implementation_hash": interaction_gat_runtime_implementation_hash_v4(),
        "graph_builder_hash": interaction_graph_builder_hash(),
        "graph_schema_version": INTERACTION_GRAPH_SCHEMA_V1,
        "feature_schema_version": INTERACTION_FEATURE_SCHEMA_V2,
        "checkpoint_schema_version": INTERACTION_CHECKPOINT_SCHEMA_V3,
        "dataset_schema_version": INTERACTION_DATASET_SCHEMA_V4,
        "corpus_schema_version": "lunar_ice_bpc.p0v5_interaction_gat_corpus_freeze.v4",
        "input_parity_contract": INTERACTION_INPUT_PARITY_CONTRACT_V1,
        "action_universe": list(V4_ACTION_UNIVERSE), "fallback_action": "Q0",
        "allowed_scales": [30, 50], "lifecycle_authority": ["root_cg"],
        "root_only_authority": True,
        "arm_scale_mask": {arm: [scale for scale in (30, 50) if arm in allowed[scale]]
                           for arm in V4_ARMS},
        "forced_veto_arms": [] if qgr1_active else ["QGR1"],
        "permanent_forced_veto_arms": ["QB1"],
        "forced_veto_arms_by_scale": {str(scale): [arm for arm in V4_ARMS
                                                    if arm not in allowed[scale]]
                                      for scale in (30, 50)},
        "model_kind": "gat", "message_passing_required": True,
        "controls_candidate_authorized": False,
        "architecture": {"hidden_dim": 16, "attention_heads": 2, "layers": 2,
                         "dropout": 0.1, "residual": True, "layer_norm": True},
        "selector_checkpoint_path": str(checkpoint),
        "selector_checkpoint_sha256": _sha256(checkpoint),
        "normalization_payload_sha256": _json_hash(
            torch.load(checkpoint, map_location="cpu", weights_only=False)["normalization"]
        ),
        "feature_envelope": envelope,
        "thresholds": selected["best_threshold"]["thresholds"],
        "allowed_exact_engine_hashes": sorted({row["source_engine_hash"]
                                                for row in _load(run_root / "corpus.freeze.json")["rows"]}),
        "allowed_exact_config_hashes": sorted({row["source_config_hash"]
                                                for row in _load(run_root / "corpus.freeze.json")["rows"]}),
        "allowed_exact_action_policy_hashes": sorted({row["source_exact_action_policy_hash"]
                                                       for row in _load(run_root / "corpus.freeze.json")["rows"]}),
        "source_freeze_sha256": _sha256(run_root / "source.freeze.json"),
        "native_binary_sha256": source["native_binary_sha256"], "torch_num_threads": 1,
        "development_e2e_authorized": True, "development_only": True,
        "deployment_authorized": False, "production_switch_authorized": False,
    }
    for prefix, name in (
        ("corpus_freeze", "corpus.freeze.json"),
        ("split_freeze", "instance_split.freeze.json"),
        ("cv_folds_freeze", "grouped_cv_folds.freeze.json"),
        ("normalization", "selector_normalization.freeze.json"),
        ("ood_envelope", "selector_ood_envelope.freeze.json"),
    ):
        payload[f"{prefix}_path"] = str(run_root / name)
        payload[f"{prefix}_sha256"] = _sha256(run_root / name)
    if qgr1_active:
        if qgr1_ranker is None or not qgr1_ranker.resolve().is_file():
            raise SystemExit("V4 active QGR1 requires frozen ranker")
        payload.update({
            "qgr1_ranker_checkpoint_path": str(qgr1_ranker.resolve()),
            "qgr1_ranker_checkpoint_sha256": _sha256(qgr1_ranker.resolve()),
            "qgr1_guidance_bucket_width": 0.0001,
            "qgr1_label_state_schema_version": "lunar_ice_bpc.p0v5_qg2_label_state.v1",
        })
    return payload


def _dataset_rows(payload):
    if payload.get("schema_version") != INTERACTION_DATASET_SCHEMA_V4:
        raise SystemExit("V4 training dataset schema mismatch")
    rows = []
    for raw in payload["rows"]:
        feature = raw["features"]
        rows.append({**raw, "features": InteractionGraphFeatures(
            instance_content_hash=str(feature["instance_content_hash"]),
            task_ids=tuple(feature["task_ids"]),
            node_features=tuple(tuple(map(float, row)) for row in feature["node_features"]),
            edge_index=tuple(tuple(map(int, row)) for row in feature["edge_index"]),
            edge_features=tuple(tuple(map(float, row)) for row in feature["edge_features"]),
            context_features=tuple(map(float, feature["context_features"]),),
            graph_schema_version=str(feature["graph_schema_version"]),
            schema_version=str(feature["schema_version"]),
        )})
    return rows


def _threshold_key(row):
    return (row["worst_scale_instance_gm"], row["combined_instance_gm"],
            row["harmful_wilson95_upper"], row["preparation_p99_ms"],
            tuple(row["thresholds"].values()))


def _candidate_key(row):
    best = row["best_threshold"]
    return (*_threshold_key(best), row["parameter_count"], row["seed"])


def _report(row):
    return {
        "kind": row["kind"], "seed": row["seed"],
        "parameter_count": row["parameter_count"],
        "fold_best_epochs": row["fold_best_epochs"],
        "refit_epoch": row["refit_epoch"], "oof_metrics": row["oof_metrics"],
        "calibration_metrics": row["calibration_metrics"],
        "best_threshold": row["best_threshold"],
    }


def _stop(run_root, reason, detail):
    path = run_root / "terminal_decision.json"
    if not path.exists():
        path.write_text(json.dumps({
            "schema_version": "lunar_ice_bpc.p0v5_residual_gat_terminal.v4",
            "decision": "FAIL", "reason": reason, "detail": detail,
            "development_only": True, "deployment_authorized": False,
            "production_switch_authorized": False,
        }, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _set_state(run_root, "TERMINAL", "FAIL", terminal=True, decision=path)
    return 2


def _verify_active(run_root):
    verify_portfolio_freezes(run_root, ROOT)
    if bool(_load(run_root / "state.json").get("terminal")):
        raise SystemExit("terminal V4 chain forbids selector trainer")


def _set_state(run_root, stage, status, *, terminal=False, decision=None):
    path = run_root / "state.json"
    payload = _load(path)
    payload.update({"current_stage": stage, "status": status, "terminal": terminal})
    if decision is not None:
        payload["terminal_decision"] = str(decision)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2,
                               sort_keys=True) + "\n", encoding="utf-8")


def _write_once(path, payload):
    path = Path(path)
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != encoded:
        raise SystemExit(f"immutable V4 trainer artifact drift:{path}")
    if not path.exists():
        path.write_text(encoded, encoding="utf-8")


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _json_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
