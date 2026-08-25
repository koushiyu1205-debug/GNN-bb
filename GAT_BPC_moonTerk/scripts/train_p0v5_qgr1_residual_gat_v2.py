#!/usr/bin/env python3
"""Train the conservative QGR1 residual GAT from literal-Q0 future traces."""

from __future__ import annotations

import argparse
from collections import defaultdict
from copy import deepcopy
import hashlib
import json
from math import isfinite
from pathlib import Path
import random
from statistics import fmean
import sys

import torch
from torch.nn import functional as F


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
import scripts.train_p0v5_qgr1_label_gat as legacy  # noqa: E402
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import verify_portfolio_freezes  # noqa: E402
from lunar_ice_bpc.guidance.proof_queue_label_state_gat_v3 import (  # noqa: E402
    QG2V3TinyGAT,
    fit_qg2_v3_normalization,
    load_qg2_v3_checkpoint,
    qg2_v3_checkpoint_payload,
)
from lunar_ice_bpc.guidance.qgr1_residual_supervision_v2 import (  # noqa: E402
    QGR1_RESIDUAL_SUPERVISION_SCHEMA_V2,
    build_qgr1_residual_pairs,
)
from lunar_ice_bpc.guidance.qgr1_supervision import (  # noqa: E402
    QGR1_ACTION_SURFACE_V1,
    QGR1_FAMILIES,
    QGR1_SUPERVISION_SCHEMA_V1,
)


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_interaction_gat_queue_selector_v2_20260807"
REPORT_SCHEMA = "lunar_ice_bpc.p0v5_qgr1_residual_gat_training.v2"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace-corpus", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--patience", type=int, default=8)
    parser.add_argument("--seed", type=int, default=61635)
    parser.add_argument("--learning-rate", type=float, default=0.002)
    parser.add_argument("--maximum-pairs-per-context", type=int, default=50_000)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    try:
        verify_portfolio_freezes(run_root, ROOT)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    if bool(_load(run_root / "state.json").get("terminal")):
        raise SystemExit("terminal chain forbids QGR1 training artifacts")
    corpus_path = args.trace_corpus.resolve()
    corpus = _load(corpus_path)
    legacy._validate_corpus(corpus)
    maximum = min(50_000, max(4, int(args.maximum_pairs_per_context)))
    examples = _examples(corpus, seed=int(args.seed), maximum=maximum)
    split = _inner_split(examples)
    training = [row for row in examples if split[row["instance_hash"]] == "train"]
    validation = [row for row in examples if split[row["instance_hash"]] == "validation"]
    normalization = fit_qg2_v3_normalization([row["features"] for row in training])

    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(int(args.seed))
    random.seed(int(args.seed))
    model = QG2V3TinyGAT(normalization, hidden_dim=32, heads=2)
    optimizer = torch.optim.Adam(model.parameters(), lr=float(args.learning_rate))
    best_state = None
    best_accuracy = -1.0
    best_epoch = 0
    stale = 0
    curve = []
    for epoch in range(1, min(40, max(1, int(args.epochs))) + 1):
        losses = _train_epoch(model, optimizer, training, seed=int(args.seed) + epoch)
        metrics = _evaluate(model, validation)
        accuracy = float(metrics["overall_actionable_pair_accuracy"])
        improved = accuracy > best_accuracy + 1.0e-7
        if improved:
            best_accuracy = accuracy
            best_epoch = epoch
            best_state = deepcopy(model.state_dict())
            stale = 0
        else:
            stale += 1
        curve.append({
            "epoch": epoch,
            "instance_balanced_train_loss": fmean(losses),
            "validation": metrics,
            "is_best": improved,
        })
        if stale >= min(8, max(1, int(args.patience))):
            break
    if best_state is None:
        raise SystemExit("QGR1 V2 failed to select an inner-validation epoch")
    model.load_state_dict(best_state, strict=True)
    model.eval()
    thresholds = _hard_zero_thresholds(model, training)
    validation_metrics = _evaluate(model, validation, thresholds=thresholds)
    violations = []
    if float(validation_metrics["overall_actionable_pair_accuracy"]) < 0.70:
        violations.append("OVERALL_ACTIONABLE_PAIR_ACCURACY_LT_0_70")
    for family in QGR1_FAMILIES:
        value = validation_metrics["per_family_accuracy"].get(family)
        if value is None or float(value) <= 0.55:
            violations.append(f"{family.upper()}_ACCURACY_NOT_GT_0_55")
    if float(validation_metrics["neutral_no_reorder_accuracy"]) < 0.70:
        violations.append("NEUTRAL_NO_REORDER_ACCURACY_LT_0_70")

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    normalization_path = output_dir / "train_normalization.json"
    envelope_path = output_dir / "train_feature_envelope.json"
    _write_once(normalization_path, normalization)
    _write_once(envelope_path, legacy._feature_envelope(training))
    metadata = {
        "training_data_hash": _stable_hash({
            "corpus_sha256": _sha256(corpus_path),
            "inner_split": split,
            "supervision_hashes": sorted(row["supervision_hash"] for row in examples),
        }),
        "supervision_schema_version": QGR1_SUPERVISION_SCHEMA_V1,
        "residual_supervision_schema_version": QGR1_RESIDUAL_SUPERVISION_SCHEMA_V2,
        "queue_action_surface": QGR1_ACTION_SURFACE_V1,
        "activation_authority": False,
        "activation_training_source": "none_ranker_only",
        "trained_epoch": best_epoch,
        "inner_split": "per_scale_10_train_2_validation.v2",
        "pair_cap": 50_000,
        "residual_training_contract": "supervised75_neutral25_pressure_weighted.v2",
        "loss_contract": "pairwise_logistic+0.1_neutral_huber+1e-5_potential_l1.v2",
        "hard_zero_thresholds": thresholds,
    }
    checkpoint_path = output_dir / "qgr1_residual_label_gat_v2.pt"
    torch.save(qg2_v3_checkpoint_payload(
        model, normalization=normalization, metadata=metadata
    ), checkpoint_path)
    roundtrip, roundtrip_metadata, _ = load_qg2_v3_checkpoint(str(checkpoint_path))
    if str(getattr(roundtrip, "model_kind", "")) != "gat" or roundtrip_metadata != metadata:
        raise SystemExit("QGR1 V2 checkpoint roundtrip failed")
    _write_once(output_dir / "training_curve.json", {
        "schema_version": "lunar_ice_bpc.p0v5_qgr1_residual_training_curve.v2",
        "curve": curve,
    })
    report = {
        "schema_version": REPORT_SCHEMA,
        "development_only": True,
        "deployment_authorized": False,
        "ranker_only": True,
        "activation_authority": False,
        "source_trace_corpus": str(corpus_path),
        "source_trace_corpus_sha256": _sha256(corpus_path),
        "inner_split": split,
        "best_epoch": best_epoch,
        "epochs_completed": len(curve),
        "parameter_count": sum(parameter.numel() for parameter in model.parameters()),
        "checkpoint_path": str(checkpoint_path),
        "checkpoint_sha256": _sha256(checkpoint_path),
        "checkpoint_roundtrip_passed": True,
        "hard_zero_thresholds": thresholds,
        "validation_metrics": validation_metrics,
        "smoke_gate": {"passed": not violations, "violations": violations},
        "next_gate": "eight_distinct_instance_q0_vs_qgr1_force_on",
    }
    _write_once(output_dir / "training_report.json", report)
    if violations:
        _record_qgr1_veto(run_root, violations, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not violations else 2


def _examples(corpus, *, seed, maximum):
    examples = []
    for source in corpus.get("rows") or ():
        if str(source.get("partition")) != "train":
            continue
        instance_path = Path(source["instance_path"]).resolve()
        snapshot_path = Path(source["snapshot_path"]).resolve()
        trace_path = Path(source["q0_trace_path"]).resolve()
        for path, name in (
            (instance_path, "instance"), (snapshot_path, "snapshot"),
            (trace_path, "q0_trace"),
        ):
            if _sha256(path) != str(source[f"{name}_sha256"]):
                raise SystemExit("QGR1 V2 corpus file hash drift")
        data = load_lunar_ice_data(_load(instance_path))
        snapshot = _load(snapshot_path)
        trace = _load(trace_path)
        if (
            data.instance_content_hash != str(source["instance_hash"])
            or str(snapshot["state_hash"]) != str(source["state_hash"])
            or str(trace.get("policy") or "") != "Q0"
            or not bool(trace.get("milestone_reached"))
        ):
            raise SystemExit("QGR1 V2 corpus binding mismatch")
        telemetry = dict(trace.get("proof_telemetry") or {})
        labels = {
            int(row["label_id"]): dict(row)
            for row in telemetry.get("proof_queue_label_state_trace") or ()
        }
        supervised, neutral, supervision = build_qgr1_residual_pairs(
            trace, labels, seed=seed, maximum=maximum
        )
        if (
            not supervised or not neutral
            or not bool(supervision.get("all_admitted_routes_represented"))
        ):
            raise SystemExit(
                "QGR1 V2 requires supervised/neutral pairs and every admitted route"
            )
        examples.append({
            "instance_hash": data.instance_content_hash,
            "state_hash": str(snapshot["state_hash"]),
            "scale": int(data.scale),
            "features": legacy._features(data, snapshot),
            "labels": labels,
            "pairs": supervised,
            "neutral_pairs": neutral,
            "supervision": supervision,
            "supervision_hash": _stable_hash(supervision),
        })
    for scale in (30, 50):
        count = len({row["instance_hash"] for row in examples if row["scale"] == scale})
        if count != 12:
            raise SystemExit(f"QGR1 V2 scale{scale} outer train instances != 12")
    return examples


def _inner_split(examples):
    result = {}
    for scale in (30, 50):
        instances = sorted(
            {row["instance_hash"] for row in examples if row["scale"] == scale},
            key=lambda value: hashlib.sha256(f"61635:{value}".encode()).hexdigest(),
        )
        result.update({value: "train" for value in instances[:10]})
        result.update({value: "validation" for value in instances[10:]})
    return result


def _train_epoch(model, optimizer, examples, *, seed):
    by_instance = defaultdict(list)
    for row in examples:
        by_instance[row["instance_hash"]].append(row)
    instances = list(by_instance)
    random.Random(seed).shuffle(instances)
    losses = []
    for instance in instances:
        optimizer.zero_grad()
        context_losses = []
        for example in by_instance[instance]:
            output = model(**example["features"].to_tensors())
            scores, arcs = {}, {}
            preferred = torch.stack([
                legacy._label_score(output, example, pair.preferred_label_id, scores, arcs)
                for pair in example["pairs"]
            ])
            other = torch.stack([
                legacy._label_score(output, example, pair.other_label_id, scores, arcs)
                for pair in example["pairs"]
            ])
            weights = torch.tensor([pair.weight for pair in example["pairs"]], dtype=torch.float32)
            supervised_loss = (
                F.softplus(-(preferred - other)) * weights
            ).sum() / weights.sum().clamp_min(1.0e-12)
            neutral_left = torch.stack([
                legacy._label_score(output, example, pair.left_label_id, scores, arcs)
                for pair in example["neutral_pairs"]
            ])
            neutral_right = torch.stack([
                legacy._label_score(output, example, pair.right_label_id, scores, arcs)
                for pair in example["neutral_pairs"]
            ])
            neutral_loss = F.huber_loss(
                neutral_left - neutral_right,
                torch.zeros_like(neutral_left), reduction="mean",
            )
            l1 = torch.cat((
                output["node_scores"].reshape(-1), output["arc_scores"].reshape(-1),
                output["label_state_coefficients"].reshape(-1),
            )).abs().mean()
            context_losses.append(supervised_loss + 0.1 * neutral_loss + 1.0e-5 * l1)
        loss = torch.stack(context_losses).mean()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        optimizer.step()
        losses.append(float(loss.detach()))
    return losses


def _hard_zero_thresholds(model, examples):
    groups = {"node": [], "arc": [], "state": []}
    with torch.inference_mode():
        for example in examples:
            output = model(**example["features"].to_tensors())
            groups["node"].append(output["node_scores"][1:].abs().reshape(-1))
            groups["arc"].append(output["arc_scores"].abs().reshape(-1))
            groups["state"].append(output["label_state_coefficients"].abs().reshape(-1))
    return {
        "quantile": 0.75,
        "fit_partition": "ranker_inner_train_instances_only",
        "frozen_before_wall_outcomes": True,
        **{
            name: float(torch.quantile(torch.cat(values), 0.75))
            for name, values in groups.items()
        },
    }


def _sparsify(output, thresholds):
    if thresholds is None:
        return output
    result = dict(output)
    for key, name in (
        ("node_scores", "node"), ("arc_scores", "arc"),
        ("label_state_coefficients", "state"),
    ):
        value = result[key]
        result[key] = torch.where(
            value.abs() >= float(thresholds[name]), value, torch.zeros_like(value)
        )
    return result


def _evaluate(model, examples, thresholds=None):
    by_instance = defaultdict(list)
    neutral_by_instance = defaultdict(list)
    family_instance = {family: defaultdict(list) for family in QGR1_FAMILIES}
    model.eval()
    with torch.inference_mode():
        for example in examples:
            output = _sparsify(model(**example["features"].to_tensors()), thresholds)
            scores, arcs = {}, {}
            hits = []
            local_family = defaultdict(list)
            for pair in example["pairs"]:
                margin = float(
                    legacy._label_score(output, example, pair.preferred_label_id, scores, arcs)
                    - legacy._label_score(output, example, pair.other_label_id, scores, arcs)
                )
                hits.append(float(margin > 0.0))
                local_family[pair.family].append(float(margin > 0.0))
            by_instance[example["instance_hash"]].append(fmean(hits))
            for family, values in local_family.items():
                family_instance[family][example["instance_hash"]].append(fmean(values))
            neutral_hits = []
            for pair in example["neutral_pairs"]:
                margin = float(
                    legacy._label_score(output, example, pair.left_label_id, scores, arcs)
                    - legacy._label_score(output, example, pair.right_label_id, scores, arcs)
                )
                neutral_hits.append(float(abs(margin) <= 1.0e-6))
            neutral_by_instance[example["instance_hash"]].append(fmean(neutral_hits))
    per_instance = {key: fmean(values) for key, values in by_instance.items()}
    return {
        "instance_count": len(per_instance),
        "overall_actionable_pair_accuracy": fmean(per_instance.values()),
        "per_family_accuracy": {
            family: (
                fmean(fmean(values) for values in family_instance[family].values())
                if family_instance[family] else None
            )
            for family in QGR1_FAMILIES
        },
        "neutral_no_reorder_accuracy": fmean(
            fmean(values) for values in neutral_by_instance.values()
        ),
        "aggregation_unit": "instance",
    }


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_once(path, payload):
    path = Path(path)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != text:
        raise SystemExit(f"immutable QGR1 V2 artifact drift:{path}")
    if not path.exists():
        path.write_text(text, encoding="utf-8")


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _stable_hash(payload):
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()


def _record_qgr1_veto(run_root, violations, report):
    admission = _load(run_root / "arm_admission.decision.json")["decision"]
    mask = dict(admission["arm_scale_mask"])
    mask["QGR1"] = []
    veto = {
        key: sorted(set((*values, "QGR1")))
        for key, values in admission["forced_veto_arms_by_scale"].items()
    }
    decision = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_qgr1_surrogate_veto.v2",
        "admitted": False,
        "hard_veto": True,
        "force_on_executed": False,
        "reason": "QGR1_SURROGATE_SMOKE_FAILED",
        "violations": list(violations),
        "arm_scale_mask": mask,
        "forced_veto_arms_by_scale": veto,
        "performance_failure_is_permanent_arm_veto": True,
        "qgr1_hyperparameter_reselection_forbidden": True,
        "correctness_redlines": [],
        "training_report": report,
    }
    _write_once(run_root / "qgr1_force_on.decision.json", {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_qgr1_force_on_decision.v2",
        "stage": "qgr1_force_on",
        "decision": decision,
        "development_only": True,
        "deployment_authorized": False,
        "production_switch_authorized": False,
    })
    path = run_root / "state.json"
    state = _load(path)
    state.update({
        "current_stage": "PORTFOLIO_ORACLE",
        "status": "READY",
        "terminal": False,
        "terminal_decision": None,
    })
    path.write_text(json.dumps(
        state, ensure_ascii=False, indent=2, sort_keys=True
    ) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
