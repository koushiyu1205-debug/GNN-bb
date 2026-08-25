#!/usr/bin/env python3
"""Grouped-CV training and scale-specific calibration for V6."""

from __future__ import annotations

from collections import defaultdict
import hashlib
import itertools
import json
from math import exp, log, sqrt
from pathlib import Path
import sys
from time import perf_counter

import torch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from scripts.p0v5_minimal_interaction_gat_qd1_v6_common import (  # noqa: E402
    DEFAULT_RUN_ROOT, assert_active, geometric_mean, load, sha256,
    terminal, update_state, verify_freezes, write_once,
)
import scripts.train_p0v5_interaction_gat_selector_v3 as shared  # noqa: E402
from lunar_ice_bpc.guidance.interaction_gat_queue_runtime_v6 import (  # noqa: E402
    INTERACTION_GAT_RUNTIME_POLICY_V6,
    interaction_gat_runtime_implementation_hash_v6,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_v2 import (  # noqa: E402
    INTERACTION_FEATURE_SCHEMA_V2, INTERACTION_GRAPH_SCHEMA_V1,
    INTERACTION_INPUT_PARITY_CONTRACT_V1, InteractionGraphFeatures,
    fit_interaction_envelope, fit_interaction_normalization,
    interaction_graph_builder_hash, interaction_parameter_count,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_v6 import (  # noqa: E402
    INTERACTION_CHECKPOINT_SCHEMA_V6, INTERACTION_DATASET_SCHEMA_V6,
    INTERACTION_MANIFEST_SCHEMA_V6, V6_ACTION_UNIVERSE, V6_MODEL_KINDS,
    build_model_v6, features_for_model_kind_v6,
    interaction_training_loss_v6,
)


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--dataset", type=Path)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    assert_active(run_root)
    verify_freezes(run_root)
    state = load(run_root / "state.json")
    if state.get("current_stage") != "SELECTOR_TRAINING":
        raise SystemExit("V6 selector trainer is not authorized in current stage")
    config = load(run_root / "config.freeze.json")
    dataset_path = (
        args.dataset.resolve() if args.dataset
        else run_root / "interaction_gat_qd1_training_dataset.freeze.json"
    )
    training_input = load(run_root / "training_input.freeze.json")
    if sha256(dataset_path) != str(training_input["dataset_sha256"]):
        raise SystemExit("FREEZE_HASH_DRIFT:V6 dataset")
    rows = _dataset_rows(load(dataset_path))
    train_rows = [row for row in rows if row["partition"] == "train"]
    calibration_rows = [row for row in rows if row["partition"] == "calibration"]
    folds = {
        str(row["instance_hash"]): int(row["fold"])
        for row in load(run_root / "grouped_cv_folds.freeze.json")["rows"]
    }
    if {row["instance_hash"] for row in train_rows} != set(folds):
        raise SystemExit("V6 grouped-CV fold binding mismatch")
    if set(folds.values()) != set(range(5)):
        raise SystemExit("V6 grouped-CV requires five nonempty folds")

    normalization = fit_interaction_normalization(
        [row["features"] for row in train_rows]
    )
    envelope = fit_interaction_envelope(
        [row["features"] for row in train_rows],
        relative_margin=float(config["selector_training"]["ood_relative_margin"]),
    )
    write_once(run_root / "selector_normalization.freeze.json", normalization)
    write_once(run_root / "selector_ood_envelope.freeze.json", envelope)
    _install_shared_hooks()
    torch.set_num_threads(1)
    output_dir = run_root / "selector_training"
    output_dir.mkdir(parents=True, exist_ok=True)
    candidates = []
    for kind in V6_MODEL_KINDS:
        for seed_value in config["selector_training"]["seeds"]:
            seed = int(seed_value)
            candidate = shared._grouped_cv_candidate(
                kind=kind, seed=seed, rows=train_rows, folds=folds,
                final_normalization=normalization,
                maximum_epochs=int(
                    config["selector_training"]["maximum_epochs"]
                ),
                patience=int(config["selector_training"]["patience"]),
            )
            calibration, degenerate = _fit_scale_calibration(
                candidate["oof_predictions"]
            )
            candidate["probability_calibration"] = calibration
            candidate["degenerate_scales"] = degenerate
            candidate["oof_metrics"] = _metrics(
                candidate["oof_predictions"], calibration
            )
            predictions, preparation = _predict_rows(
                candidate["model"], calibration_rows, kind=kind
            )
            candidate["calibration_predictions"] = predictions
            candidate["calibration_metrics"] = _metrics(predictions, calibration)
            candidate["scale_thresholds"] = {
                str(scale): _scale_threshold_candidates(
                    predictions, calibration, config["threshold_grid"], scale,
                    preparation,
                ) for scale in (30, 50)
            }
            candidate["best_threshold_pair"] = _best_threshold_pair(
                candidate["scale_thresholds"], allow_noop=(kind != "gat")
            )
            checkpoint = output_dir / f"{kind}_seed{seed}.pt"
            torch.save(
                _checkpoint(candidate, normalization, candidate_authorized=False),
                checkpoint,
            )
            candidate["checkpoint_path"] = str(checkpoint)
            candidate["checkpoint_sha256"] = sha256(checkpoint)
            write_once(output_dir / f"{kind}_seed{seed}.curve.json", {
                "schema_version": (
                    "lunar_ice_bpc.p0v5_interaction_gat_qd1_training_curve.v1"
                ),
                "model_kind": kind, "seed": seed,
                "fold_best_epochs": candidate["fold_best_epochs"],
                "refit_epoch": candidate["refit_epoch"],
                "fold_curves": candidate["fold_curves"],
                "refit_curve": candidate["refit_curve"],
                "parameter_count": candidate["parameter_count"],
                "best_threshold_pair": candidate["best_threshold_pair"],
            })
            candidates.append(candidate)

    controls = {}
    for kind in ("mlp", "linear", "no_message", "shuffled_topology"):
        values = [row for row in candidates if row["kind"] == kind]
        controls[kind] = min(values, key=_candidate_key)
    gat_values = [
        row for row in candidates
        if row["kind"] == "gat" and row["best_threshold_pair"] is not None
        and not row["degenerate_scales"]
    ]
    report_base = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_qd1_training_report.v1",
        "representation_training_partition": "train_instances_only",
        "probability_calibration_partition": "train_oof_predictions_by_scale_only",
        "calibration_use": "seed_and_scale_threshold_selection_only",
        "heldout_outcomes_read": 0, "formal_outcomes_read": 0,
        "all_controls_independently_trained": True,
        "candidates": [_report(row) for row in candidates],
    }
    if not gat_values:
        write_once(run_root / "selector_training_report.json", report_base)
        return terminal(
            run_root, "NO_SAFE_GAT_CALIBRATION_THRESHOLD",
            {"gat_candidates": [_report(row) for row in candidates if row["kind"] == "gat"]},
        )
    safe = [row for row in gat_values if _gat_advantage(row, controls)]
    if not safe:
        report_base["gat_advantage"] = {
            "gat": [_advantage_report(row, controls) for row in gat_values],
            "controls": {kind: _report(row) for kind, row in controls.items()},
        }
        write_once(run_root / "selector_training_report.json", report_base)
        return terminal(run_root, "NO_GAT_ADVANTAGE", report_base["gat_advantage"])

    selected = min(safe, key=_candidate_key)
    candidate_checkpoint = run_root / "interaction_gat_qd1_selector_candidate.pt"
    torch.save(
        _checkpoint(selected, normalization, candidate_authorized=True),
        candidate_checkpoint,
    )
    controls_freeze = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_qd1_controls.v1",
        "frozen_before_heldout": True,
        "controls_candidate_authorized": False,
        "all_controls_independently_trained": True,
        "controls": {
            kind: {
                "seed": row["seed"], "refit_epoch": row["refit_epoch"],
                "parameter_count": row["parameter_count"],
                "checkpoint_path": row["checkpoint_path"],
                "checkpoint_sha256": row["checkpoint_sha256"],
                "thresholds_by_scale": _threshold_payload(row),
                "probability_calibration": row["probability_calibration"],
                "no_op_scales": [
                    scale for scale, value in (
                        row["best_threshold_pair"] or {}
                    ).get("scales", {}).items() if bool(value.get("no_op"))
                ],
            } for kind, row in controls.items()
        },
    }
    write_once(run_root / "selector_controls.freeze.json", controls_freeze)
    manifest = _manifest(
        run_root, selected, candidate_checkpoint, envelope, dataset_path
    )
    manifest_path = run_root / "selector_heldout_candidate.manifest.json"
    write_once(manifest_path, manifest)
    report_base["selected_gat_advantage"] = _advantage_report(selected, controls)
    write_once(run_root / "selector_training_report.json", report_base)
    decision = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_qd1_selection.v1",
        "decision": "GAT_CANDIDATE_FROZEN",
        "selected_model_kind": "gat", "message_passing_required": True,
        "selected_seed": selected["seed"],
        "selected_refit_epoch": selected["refit_epoch"],
        "selected_parameter_count": selected["parameter_count"],
        "selected_checkpoint": str(candidate_checkpoint),
        "selected_checkpoint_sha256": sha256(candidate_checkpoint),
        "selected_thresholds_by_scale": _threshold_payload(selected),
        "heldout_manifest": str(manifest_path),
        "heldout_outcomes_read": 0,
        "development_only": True, "deployment_authorized": False,
        "production_switch_authorized": False,
    }
    write_once(run_root / "selector_selection.decision.json", decision)
    write_once(run_root / "preheldout.freeze.registry.json", {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_qd1_preheldout.v1",
        "heldout_outcomes_read": 0,
        "artifact_sha256": {
            name: sha256(run_root / name) for name in (
                "interaction_gat_qd1_training_dataset.freeze.json",
                "selector_normalization.freeze.json",
                "selector_ood_envelope.freeze.json",
                "selector_controls.freeze.json",
                "interaction_gat_qd1_selector_candidate.pt",
                "selector_heldout_candidate.manifest.json",
                "selector_training_report.json",
                "selector_selection.decision.json",
            )
        },
    })
    update_state(run_root, "SELECTOR_HELDOUT_FRESH", "READY")
    print(json.dumps(decision, ensure_ascii=False, indent=2))
    return 0


def _install_shared_hooks():
    shared.PORTFOLIO_ARMS = ("QD1",)
    shared.build_model_v3 = build_model_v6
    shared.features_for_model_kind = features_for_model_kind_v6
    shared._instance_balanced_loss = _instance_balanced_loss
    shared._predict_rows = lambda model, rows, *, kind: _predict_rows(
        model, rows, kind=kind
    )


def _instance_balanced_loss(model, rows, kind):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["instance_hash"]].append(row)
    losses = []
    for values in grouped.values():
        context_losses = []
        context_weights = []
        for row in values:
            feature = features_for_model_kind_v6(
                row["features"], model_kind=kind, state_hash=row["state_hash"]
            )
            output = model(**feature.to_tensors())
            target = row["target"]
            ratio = float(target["ratio"])
            direction = 1.0 if ratio < 1.0 else -1.0
            context_losses.append(interaction_training_loss_v6(
                output,
                benefit_target=torch.tensor([float(target["benefit"])]),
                positive_gain_target=torch.tensor([float(target["positive_gain"])]),
                adverse_target=torch.tensor([float(target["adverse"])]),
                determined_mask=torch.tensor([float(target["determined"])]),
                positive_mask=torch.tensor([float(target["benefit"])]),
                rank_direction=torch.tensor([direction]),
                rank_mask=torch.tensor([float(ratio != 1.0)]),
            )["loss"])
            context_weights.append(float(row["training_context_weight"]))
        weight = torch.tensor(context_weights, dtype=context_losses[0].dtype)
        losses.append(
            (torch.stack(context_losses) * weight).sum() / weight.sum().clamp_min(1e-12)
        )
    return torch.stack(losses).mean()


def _predict_rows(model, rows, *, kind):
    result, walls = [], []
    model.eval()
    with torch.inference_mode():
        for row in rows:
            feature = features_for_model_kind_v6(
                row["features"], model_kind=kind, state_hash=row["state_hash"]
            )
            started = perf_counter()
            output = model(**feature.to_tensors())
            walls.append((perf_counter() - started) * 1000.0)
            result.append({
                "context_id": row["context_id"],
                "instance_hash": row["instance_hash"], "scale": row["scale"],
                "state_hash": row["state_hash"],
                "context_weight": row["training_context_weight"],
                "target": row["target"],
                "benefit": float(output["benefit_probability"][0, 0]),
                "gain": float(output["conditional_positive_gain"][0, 0]),
                "adverse": float(output["adverse_probability"][0, 0]),
            })
    return result, walls


def _fit_scale_calibration(predictions):
    result = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_qd1_oof_calibration.v1",
        "fit_partition": "train_oof_predictions_by_scale_only",
        "instance_weighted": True, "by_scale": {},
    }
    degenerate = []
    for scale in (30, 50):
        rows = [row for row in predictions if row["scale"] == scale]
        fields = {}
        for field in ("benefit", "adverse"):
            labels = [float(row["target"][field]) for row in rows]
            fields[field] = shared._weighted_platt(
                [row[field] for row in rows], labels,
                [row["context_weight"] for row in rows],
            )
            if len(set(labels)) < 2:
                degenerate.append(scale)
        positive = [row for row in rows if row["target"]["benefit"]]
        predicted = sum(row["gain"] * row["context_weight"] for row in positive)
        observed = sum(
            row["target"]["positive_gain"] * row["context_weight"]
            for row in positive
        )
        fields["positive_gain_scale"] = (
            max(0.1, min(10.0, observed / predicted)) if predicted > 0 else 1.0
        )
        result["by_scale"][str(scale)] = fields
    return result, sorted(set(degenerate))


def _calibrated(row, calibration):
    scale = dict(calibration["by_scale"][str(row["scale"])])
    return {
        "benefit": shared._calibrate(row["benefit"], scale["benefit"]),
        "gain": row["gain"] * float(scale["positive_gain_scale"]),
        "adverse": shared._calibrate(row["adverse"], scale["adverse"]),
    }


def _scale_threshold_candidates(predictions, calibration, grid, scale, preparation):
    rows = [row for row in predictions if row["scale"] == scale]
    result = []
    for values in itertools.product(
        grid["minimum_benefit_probability"],
        grid["maximum_adverse_probability"],
        grid["minimum_expected_gain"], grid["risk_penalty"],
    ):
        threshold = dict(zip((
            "minimum_benefit_probability", "maximum_adverse_probability",
            "minimum_expected_gain", "risk_penalty",
        ), values, strict=True))
        selected = _select(rows, calibration, threshold)
        folded = _fold(selected)
        activated = [row for row in selected if row["action"] == "QD1"]
        harmful = sum(row["ratio"] >= 1.05 for row in activated)
        adverse = sum(row["adverse"] for row in activated)
        censored = sum(not row["determined"] for row in activated)
        gm = geometric_mean(folded.values())
        eligible = bool(
            harmful == adverse == censored == 0
            and len({row["instance_hash"] for row in activated}) >= 2
            and gm < 1.0
        )
        result.append({
            "scale": scale, "thresholds": threshold, "eligible": eligible,
            "no_op": False, "activation_contexts": len(activated),
            "activation_instances": len({row["instance_hash"] for row in activated}),
            "harmful_activations": harmful, "adverse_activations": adverse,
            "censored_activations": censored, "instance_ratios": folded,
            "instance_weighted_gm": gm,
            "harmful_wilson95_upper": _wilson_upper(harmful, max(1, len(activated))),
            "preparation_p99_ms": _percentile(preparation, 0.99),
            "selected_actions": selected,
        })
    return result


def _best_threshold_pair(by_scale, *, allow_noop):
    values = {}
    for scale in ("30", "50"):
        eligible = [row for row in by_scale[scale] if row["eligible"]]
        if eligible:
            values[scale] = eligible
        elif allow_noop:
            instance_hashes = {
                row["instance_hash"]
                for candidate in by_scale[scale]
                for row in candidate["selected_actions"]
            }
            values[scale] = [{
                "scale": int(scale), "thresholds": None, "eligible": True,
                "no_op": True, "activation_contexts": 0,
                "activation_instances": 0, "harmful_activations": 0,
                "adverse_activations": 0, "censored_activations": 0,
                "instance_ratios": {instance: 1.0 for instance in instance_hashes},
                "instance_weighted_gm": 1.0, "harmful_wilson95_upper": 1.0,
                "preparation_p99_ms": 0.0, "selected_actions": [],
            }]
        else:
            return None
    pairs = []
    for scale30, scale50 in itertools.product(values["30"], values["50"]):
        combined = geometric_mean((
            *scale30["instance_ratios"].values(),
            *scale50["instance_ratios"].values(),
        ))
        pairs.append({
            "scales": {"30": scale30, "50": scale50},
            "worst_scale_gm": max(
                scale30["instance_weighted_gm"], scale50["instance_weighted_gm"]
            ),
            "combined_instance_gm": combined,
            "harmful_wilson95_upper": max(
                scale30["harmful_wilson95_upper"],
                scale50["harmful_wilson95_upper"],
            ),
            "preparation_p99_ms": max(
                scale30["preparation_p99_ms"], scale50["preparation_p99_ms"]
            ),
        })
    return min(pairs, key=lambda row: (
        row["worst_scale_gm"], row["combined_instance_gm"],
        row["harmful_wilson95_upper"], row["preparation_p99_ms"],
    ))


def _select(rows, calibration, threshold):
    result = []
    for row in rows:
        value = _calibrated(row, calibration)
        expected = value["benefit"] * value["gain"]
        score = expected - threshold["risk_penalty"] * value["adverse"]
        action = "QD1" if (
            value["benefit"] >= threshold["minimum_benefit_probability"]
            and expected >= threshold["minimum_expected_gain"]
            and value["adverse"] <= threshold["maximum_adverse_probability"]
            and score > 0.0
        ) else "Q0"
        target = row["target"]
        result.append({
            "context_id": row["context_id"],
            "instance_hash": row["instance_hash"], "scale": row["scale"],
            "action": action, "determined": True,
            "ratio": float(target["ratio"]) if action == "QD1" else 1.0,
            "adverse": bool(target["adverse"]) if action == "QD1" else False,
        })
    return result


def _fold(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["instance_hash"]].append(float(row["ratio"]))
    return {instance: geometric_mean(values) for instance, values in grouped.items()}


def _metrics(predictions, calibration):
    classification = {field: {} for field in ("benefit", "adverse")}
    hits, scale_hits = defaultdict(list), {30: defaultdict(list), 50: defaultdict(list)}
    for field in classification:
        for scale in (30, 50):
            rows = [row for row in predictions if row["scale"] == scale]
            classification[field][str(scale)] = _binary_metrics(
                rows, calibration, field
            )
    for row in predictions:
        value = _calibrated(row, calibration)
        utility = value["benefit"] * value["gain"] - value["adverse"]
        target = float(row["target"]["ratio"])
        if target == 1.0:
            continue
        hit = (utility > 0.0) == (target < 1.0)
        hits[row["instance_hash"]].append(hit)
        scale_hits[row["scale"]][row["instance_hash"]].append(hit)
    return {
        "classification": classification,
        "macro_instance_rank_accuracy": _macro_hits(hits),
        "scale_macro_instance_rank_accuracy": {
            str(scale): _macro_hits(values) for scale, values in scale_hits.items()
        },
        "context_count": len(predictions),
        "instance_count": len({row["instance_hash"] for row in predictions}),
    }


def _binary_metrics(rows, calibration, field):
    values = [
        (_calibrated(row, calibration)[field], int(row["target"][field]))
        for row in rows
    ]
    tp = sum(p >= 0.5 and y == 1 for p, y in values)
    tn = sum(p < 0.5 and y == 0 for p, y in values)
    fp = sum(p >= 0.5 and y == 0 for p, y in values)
    fn = sum(p < 0.5 and y == 1 for p, y in values)
    recall = tp / (tp + fn) if tp + fn else None
    specificity = tn / (tn + fp) if tn + fp else None
    context = {
        "balanced_accuracy": (
            (recall + specificity) / 2
            if recall is not None and specificity is not None else None
        ),
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": recall, "specificity": specificity,
        "brier": sum((p - y) ** 2 for p, y in values) / max(1, len(values)),
        "context_count": len(values),
    }
    grouped = defaultdict(list)
    for row, value in zip(rows, values, strict=True):
        grouped[row["instance_hash"]].append(value)
    instance_brier = [
        sum((p - y) ** 2 for p, y in rows_) / len(rows_)
        for rows_ in grouped.values()
    ]
    return {
        "context_level": context,
        "instance_level": {
            "brier": sum(instance_brier) / max(1, len(instance_brier)),
            "instance_count": len(grouped),
        },
    }


def _macro_hits(grouped):
    if not grouped:
        return None
    return sum(sum(values) / len(values) for values in grouped.values()) / len(grouped)


def _gat_advantage(gat, controls):
    report = _advantage_report(gat, controls)
    return all(report.values())


def _advantage_report(gat, controls):
    gat_rank = gat["oof_metrics"]["macro_instance_rank_accuracy"]
    gat_scale50_rank = gat["oof_metrics"]["scale_macro_instance_rank_accuracy"]["50"]
    topology = [controls[name] for name in ("no_message", "shuffled_topology")]
    simple = [controls[name] for name in ("mlp", "linear")]
    gat_pair = gat["best_threshold_pair"]
    return {
        "topology_rank_not_worse": all(
            gat_rank >= row["oof_metrics"]["macro_instance_rank_accuracy"]
            for row in topology
        ),
        "topology_drop_present": any(
            gat_rank - row["oof_metrics"]["macro_instance_rank_accuracy"] >= 0.02
            or gat_scale50_rank - row["oof_metrics"][
                "scale_macro_instance_rank_accuracy"
            ]["50"] >= 0.02
            for row in topology
        ),
        "scale50_strictly_beats_simple": all(
            gat_pair["scales"]["50"]["instance_weighted_gm"]
            < row["best_threshold_pair"]["scales"]["50"]["instance_weighted_gm"]
            for row in simple
        ),
        "scale30_not_worse_than_simple": all(
            gat_pair["scales"]["30"]["instance_weighted_gm"]
            <= row["best_threshold_pair"]["scales"]["30"]["instance_weighted_gm"]
            for row in simple
        ),
        "combined_strictly_beats_simple": all(
            gat_pair["combined_instance_gm"]
            < row["best_threshold_pair"]["combined_instance_gm"]
            for row in simple
        ),
    }


def _candidate_key(row):
    pair = row["best_threshold_pair"]
    if pair is None:
        return (float("inf"), float("inf"), row["parameter_count"], row["seed"])
    return (
        pair["worst_scale_gm"], pair["combined_instance_gm"],
        pair["harmful_wilson95_upper"], pair["preparation_p99_ms"],
        row["parameter_count"], row["seed"],
    )


def _checkpoint(candidate, normalization, *, candidate_authorized):
    return {
        "schema_version": INTERACTION_CHECKPOINT_SCHEMA_V6,
        "feature_schema_version": INTERACTION_FEATURE_SCHEMA_V2,
        "graph_schema_version": INTERACTION_GRAPH_SCHEMA_V1,
        "input_parity_contract": INTERACTION_INPUT_PARITY_CONTRACT_V1,
        "model_kind": candidate["kind"],
        "message_passing_required": candidate["kind"] == "gat",
        "independently_trained": True,
        "controls_candidate_authorized": False,
        "candidate_authorized": bool(
            candidate_authorized and candidate["kind"] == "gat"
        ),
        "action_universe": list(V6_ACTION_UNIVERSE),
        "architecture": {
            "hidden_dim": 16, "attention_heads": 2, "layers": 2,
            "dropout": 0.1, "residual": True, "layer_norm": True,
        },
        "normalization": normalization,
        "probability_calibration": candidate["probability_calibration"]["by_scale"],
        "state_dict": candidate["model"].state_dict(),
        "parameter_count": candidate["parameter_count"],
        "seed": candidate["seed"], "refit_epoch": candidate["refit_epoch"],
        "activation_authority": False,
        "development_only": True, "deployment_authorized": False,
        "production_switch_authorized": False,
    }


def _manifest(run_root, selected, checkpoint, envelope, dataset_path):
    source = load(run_root / "source.freeze.json")
    corpus = load(run_root / "corpus.freeze.json")
    normalization_path = run_root / "selector_normalization.freeze.json"
    envelope_path = run_root / "selector_ood_envelope.freeze.json"
    evidence_path = run_root / "v5_qd1_evidence_import.freeze.json"
    return {
        "schema_version": INTERACTION_MANIFEST_SCHEMA_V6,
        "runtime_policy_id": INTERACTION_GAT_RUNTIME_POLICY_V6,
        "runtime_implementation_hash": interaction_gat_runtime_implementation_hash_v6(),
        "graph_builder_hash": interaction_graph_builder_hash(),
        "graph_schema_version": INTERACTION_GRAPH_SCHEMA_V1,
        "feature_schema_version": INTERACTION_FEATURE_SCHEMA_V2,
        "checkpoint_schema_version": INTERACTION_CHECKPOINT_SCHEMA_V6,
        "dataset_schema_version": INTERACTION_DATASET_SCHEMA_V6,
        "input_parity_contract": INTERACTION_INPUT_PARITY_CONTRACT_V1,
        "action_universe": list(V6_ACTION_UNIVERSE), "fallback_action": "Q0",
        "allowed_scales": [30, 50], "arm_scale_mask": {"QD1": [30, 50]},
        "forced_veto_arms": [],
        "forced_veto_arms_by_scale": {"30": [], "50": []},
        "permanent_forced_veto_arms": ["QB1", "QGR1"],
        "model_kind": "gat", "message_passing_required": True,
        "controls_candidate_authorized": False, "root_only_authority": True,
        "lifecycle_authority": ["root_cg"],
        "architecture": {
            "hidden_dim": 16, "attention_heads": 2, "layers": 2,
            "dropout": 0.1, "residual": True, "layer_norm": True,
        },
        "selector_checkpoint_path": str(checkpoint),
        "selector_checkpoint_sha256": sha256(checkpoint),
        "feature_envelope": envelope,
        "thresholds_by_scale": _threshold_payload(selected),
        "allowed_exact_engine_hashes": sorted({
            str(row["source_engine_hash"]) for row in corpus["rows"]
        }),
        "allowed_exact_action_policy_hashes": sorted({
            str(row["source_exact_action_policy_hash"]) for row in corpus["rows"]
        }),
        "allowed_exact_config_hashes": sorted({
            str(row["source_config_hash"]) for row in corpus["rows"]
        }),
        "torch_num_threads": 1, "development_e2e_authorized": True,
        "development_only": True, "deployment_authorized": False,
        "production_switch_authorized": False,
        "evidence_import_path": str(evidence_path),
        "evidence_import_sha256": sha256(evidence_path),
        "corpus_freeze_path": str(run_root / "corpus.freeze.json"),
        "corpus_freeze_sha256": sha256(run_root / "corpus.freeze.json"),
        "split_freeze_path": str(run_root / "instance_split.freeze.json"),
        "split_freeze_sha256": sha256(run_root / "instance_split.freeze.json"),
        "cv_folds_freeze_path": str(run_root / "grouped_cv_folds.freeze.json"),
        "cv_folds_freeze_sha256": sha256(
            run_root / "grouped_cv_folds.freeze.json"
        ),
        "normalization_path": str(normalization_path),
        "normalization_sha256": sha256(normalization_path),
        "normalization_payload_sha256": _json_sha256(load(normalization_path)),
        "ood_envelope_path": str(envelope_path),
        "ood_envelope_sha256": sha256(envelope_path),
        "native_binary_sha256": source["native_binary_sha256"],
        "training_dataset_path": str(dataset_path),
        "training_dataset_sha256": sha256(dataset_path),
    }


def _threshold_payload(candidate):
    pair = candidate.get("best_threshold_pair")
    if not pair:
        return {}
    return {
        scale: value["thresholds"] for scale, value in pair["scales"].items()
        if not value.get("no_op")
    }


def _dataset_rows(payload):
    if payload.get("schema_version") != INTERACTION_DATASET_SCHEMA_V6:
        raise SystemExit("V6 dataset schema mismatch")
    rows, seen = [], set()
    for raw in payload.get("rows") or ():
        row = dict(raw)
        context = str(row.get("context_id") or "")
        if not context or context in seen:
            raise SystemExit("V6 dataset context duplication")
        seen.add(context)
        if row.get("partition") not in {"train", "calibration"}:
            raise SystemExit("V6 dataset contains prohibited partition")
        feature = dict(row["features"])
        row["features"] = InteractionGraphFeatures(
            instance_content_hash=str(feature["instance_content_hash"]),
            task_ids=tuple(feature["task_ids"]),
            node_features=tuple(tuple(value) for value in feature["node_features"]),
            edge_index=tuple(tuple(value) for value in feature["edge_index"]),
            edge_features=tuple(tuple(value) for value in feature["edge_features"]),
            context_features=tuple(feature["context_features"]),
            graph_schema_version=str(feature["graph_schema_version"]),
            schema_version=str(feature["schema_version"]),
        )
        rows.append(row)
    return rows


def _report(row):
    return {
        "model_kind": row["kind"], "seed": row["seed"],
        "parameter_count": row["parameter_count"],
        "fold_best_epochs": row["fold_best_epochs"],
        "refit_epoch": row["refit_epoch"],
        "degenerate_scales": row["degenerate_scales"],
        "oof_metrics": row["oof_metrics"],
        "calibration_metrics": row["calibration_metrics"],
        "best_threshold_pair": row["best_threshold_pair"],
        "checkpoint_path": row.get("checkpoint_path"),
        "checkpoint_sha256": row.get("checkpoint_sha256"),
    }


def _wilson_upper(successes, total):
    if total <= 0:
        return 1.0
    z, p = 1.959963984540054, successes / total
    denominator = 1 + z * z / total
    center = p + z * z / (2 * total)
    radius = z * sqrt((p * (1 - p) + z * z / (4 * total)) / total)
    return min(1.0, (center + radius) / denominator)


def _percentile(values, probability):
    values = sorted(float(value) for value in values)
    if not values:
        return 0.0
    index = min(len(values) - 1, max(0, int((len(values) - 1) * probability + 0.999999)))
    return values[index]


def _json_sha256(value):
    return hashlib.sha256(json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
