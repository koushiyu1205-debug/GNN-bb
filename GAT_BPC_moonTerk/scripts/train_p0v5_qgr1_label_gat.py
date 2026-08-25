#!/usr/bin/env python3
"""Train the QGR1 ordering-only label GAT from literal-Q0 future traces."""

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


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.exact.bpc.pricing.backends.base import (  # noqa: E402
    PRICING_LIFECYCLE_SCOPE_ROOT_CG,
)
from lunar_ice_bpc.exact.core.branching import branch_context_from_payload  # noqa: E402
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.guidance.proof_queue_label_state_gat import (  # noqa: E402
    build_qg2_features,
)
from lunar_ice_bpc.guidance.proof_queue_label_state_gat_v3 import (  # noqa: E402
    QG2V3TinyGAT, fit_qg2_v3_normalization, normalize_qg2_v3_features,
    qg2_v3_checkpoint_payload, qg2_v3_weighted_rank_loss,
)
from lunar_ice_bpc.guidance.qgr1_supervision import (  # noqa: E402
    QGR1_ACTION_SURFACE_V1, QGR1_FAMILIES, QGR1_SUPERVISION_SCHEMA_V1,
    build_qgr1_weighted_pairs,
)
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import (  # noqa: E402
    verify_portfolio_freezes,
)


CORPUS_SCHEMA = "lunar_ice_bpc.p0v5_qgr1_q0_trace_corpus.v1"
REPORT_SCHEMA = "lunar_ice_bpc.p0v5_qgr1_label_gat_training.v1"
DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_context_queue_portfolio_v1_20260807_r1"


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
    try:
        verify_portfolio_freezes(args.run_root.resolve(), ROOT)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    corpus_path = args.trace_corpus.resolve()
    corpus = _load(corpus_path)
    _validate_corpus(corpus)
    examples = _examples(
        corpus, seed=int(args.seed),
        maximum_pairs=min(50_000, max(1, int(args.maximum_pairs_per_context))),
    )
    split = _inner_split(examples)
    training = [row for row in examples if split[row["instance_hash"]] == "train"]
    validation = [row for row in examples if split[row["instance_hash"]] == "validation"]
    if (
        len({row["instance_hash"] for row in training}) != 16
        or len({row["instance_hash"] for row in validation}) != 4
    ):
        raise SystemExit("QGR1 inner split must be 8/2 instances per scale")
    normalization = fit_qg2_v3_normalization(
        [row["features"] for row in training]
    )
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    normalization_path = output_dir / "train_normalization.json"
    envelope_path = output_dir / "train_feature_envelope.json"
    _write_once(normalization_path, normalization)
    _write_once(envelope_path, _feature_envelope(training))

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
        model.train()
        instance_losses = _train_epoch(
            model, optimizer, training,
            seed=int(args.seed) + epoch,
            maximum_pairs=min(50_000, max(1, int(args.maximum_pairs_per_context))),
        )
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
            "instance_balanced_train_loss": fmean(instance_losses),
            "validation": metrics,
            "is_best": improved,
        })
        if stale >= min(8, max(1, int(args.patience))):
            break
    if best_state is None:
        raise SystemExit("QGR1 training failed to select a validation epoch")
    model.load_state_dict(best_state, strict=True)
    model.eval()
    validation_metrics = _evaluate(model, validation)
    smoke_violations = []
    if float(validation_metrics["overall_actionable_pair_accuracy"]) < 0.70:
        smoke_violations.append("OVERALL_ACTIONABLE_PAIR_ACCURACY_LT_0_70")
    for family in QGR1_FAMILIES:
        accuracy = validation_metrics["per_family_accuracy"].get(family)
        if accuracy is None or float(accuracy) <= 0.55:
            smoke_violations.append(f"{family.upper()}_ACCURACY_NOT_GT_0_55")
    training_hash = _stable_hash({
        "corpus_sha256": _sha256(corpus_path),
        "inner_split": split,
        "normalization_sha256": _sha256(normalization_path),
        "example_supervision_hashes": sorted(row["supervision_hash"] for row in examples),
    })
    checkpoint_path = output_dir / "qgr1_label_gat.pt"
    metadata = {
        "training_data_hash": training_hash,
        "supervision_schema_version": QGR1_SUPERVISION_SCHEMA_V1,
        "queue_action_surface": QGR1_ACTION_SURFACE_V1,
        "activation_authority": False,
        "activation_training_source": "none_ranker_only",
        "trained_epoch": best_epoch,
        "inner_split": "per_scale_8_train_2_validation.v1",
        "pair_cap": 50_000,
        "family_weighting": "equal_total_mass_across_three_families.v1",
    }
    torch.save(qg2_v3_checkpoint_payload(
        model, normalization=normalization, metadata=metadata
    ), checkpoint_path)
    # Roundtrip is a hard smoke requirement.
    from lunar_ice_bpc.guidance.proof_queue_label_state_gat_v3 import (
        load_qg2_v3_checkpoint,
    )
    roundtrip_model, roundtrip_metadata, _ = load_qg2_v3_checkpoint(
        str(checkpoint_path)
    )
    if (
        str(getattr(roundtrip_model, "model_kind", "")) != "gat"
        or roundtrip_metadata != metadata
    ):
        raise SystemExit("QGR1 checkpoint roundtrip failed")
    curve_path = output_dir / "training_curve.json"
    _write_once(curve_path, {
        "schema_version": "lunar_ice_bpc.p0v5_qgr1_training_curve.v1",
        "curve": curve,
    })
    attribution_path = output_dir / "supervision_attribution.json"
    _write_once(attribution_path, {
        "schema_version": "lunar_ice_bpc.p0v5_qgr1_supervision_attribution.v1",
        "action_surface": QGR1_ACTION_SURFACE_V1,
        "family_counts": {
            family: sum(
                1 for example in examples for pair in example["pairs"]
                if pair.family == family
            ) for family in QGR1_FAMILIES
        },
        "family_weight_mass": {
            family: sum(
                pair.weight for example in examples for pair in example["pairs"]
                if pair.family == family
            ) for family in QGR1_FAMILIES
        },
        "validation_per_family_accuracy": validation_metrics["per_family_accuracy"],
        "all_pairs_native_actionable": True,
        "all_admitted_routes_represented": all(
            bool(example["supervision"]["all_admitted_routes_represented"])
            for example in examples
        ),
    })
    report = {
        "schema_version": REPORT_SCHEMA,
        "development_only": True,
        "deployment_authorized": False,
        "ranker_only": True,
        "activation_authority": False,
        "source_trace_corpus": str(corpus_path),
        "source_trace_corpus_sha256": _sha256(corpus_path),
        "training_data_hash": training_hash,
        "inner_split": split,
        "best_epoch": best_epoch,
        "epochs_completed": len(curve),
        "patience": min(8, max(1, int(args.patience))),
        "parameter_count": sum(parameter.numel() for parameter in model.parameters()),
        "checkpoint_path": str(checkpoint_path),
        "checkpoint_sha256": _sha256(checkpoint_path),
        "checkpoint_roundtrip_passed": True,
        "normalization_path": str(normalization_path),
        "normalization_sha256": _sha256(normalization_path),
        "feature_envelope_path": str(envelope_path),
        "feature_envelope_sha256": _sha256(envelope_path),
        "training_curve_path": str(curve_path),
        "training_curve_sha256": _sha256(curve_path),
        "attribution_path": str(attribution_path),
        "attribution_sha256": _sha256(attribution_path),
        "validation_metrics": validation_metrics,
        "smoke_gate": {
            "passed": not smoke_violations,
            "violations": smoke_violations,
        },
        "next_gate": "eight_distinct_instance_q0_vs_qgr1_force_on",
    }
    _write_once(output_dir / "training_report.json", report)
    if smoke_violations:
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def _validate_corpus(corpus):
    if (
        corpus.get("schema_version") != CORPUS_SCHEMA
        or not bool(corpus.get("literal_q0_future_trace_only"))
        or bool(corpus.get("performance_outcomes_used"))
        or bool(corpus.get("formal_benchmark_instances_used"))
        or bool(corpus.get("diagnostic_only_outcomes_used"))
    ):
        raise SystemExit("QGR1 trace corpus authority is invalid")


def _examples(corpus, *, seed, maximum_pairs):
    examples = []
    for source in corpus.get("rows") or ():
        if str(source.get("partition")) != "train":
            continue
        instance_path = Path(source["instance_path"]).resolve()
        snapshot_path = Path(source["snapshot_path"]).resolve()
        trace_path = Path(source["q0_trace_path"]).resolve()
        if any(_sha256(path) != str(source[f"{name}_sha256"]) for path, name in (
            (instance_path, "instance"), (snapshot_path, "snapshot"), (trace_path, "q0_trace")
        )):
            raise SystemExit("QGR1 corpus file hash drift")
        data = load_lunar_ice_data(_load(instance_path))
        snapshot = _load(snapshot_path)
        trace = _load(trace_path)
        if (
            data.instance_content_hash != str(source["instance_hash"])
            or str(snapshot["state_hash"]) != str(source["state_hash"])
            or str(trace.get("policy") or "") != "Q0"
            or not bool(trace.get("milestone_reached"))
        ):
            raise SystemExit("QGR1 corpus binding mismatch")
        telemetry = dict(trace.get("proof_telemetry") or {})
        labels = {
            int(row["label_id"]): dict(row)
            for row in telemetry.get("proof_queue_label_state_trace") or ()
        }
        pairs, supervision = build_qgr1_weighted_pairs(
            trace, labels, seed=seed, maximum=maximum_pairs
        )
        if not pairs or abs(sum(pair.weight for pair in pairs) - 1.0) > 1e-6:
            raise SystemExit("QGR1 actionable supervision is invalid")
        examples.append({
            "instance_hash": data.instance_content_hash,
            "state_hash": str(snapshot["state_hash"]),
            "scale": int(data.scale),
            "features": _features(data, snapshot),
            "labels": labels,
            "pairs": pairs,
            "supervision": supervision,
            "supervision_hash": _stable_hash(supervision),
        })
    instances = {row["instance_hash"] for row in examples}
    if len(instances) != 20:
        raise SystemExit("QGR1 outer-train corpus must cover 10+10 instances")
    return examples


def _inner_split(examples):
    result = {}
    for scale in (30, 50):
        instances = sorted(
            {row["instance_hash"] for row in examples if row["scale"] == scale},
            key=lambda value: hashlib.sha256(f"61635:{value}".encode()).hexdigest(),
        )
        if len(instances) != 10:
            raise SystemExit(f"QGR1 scale{scale} outer train instances != 10")
        result.update({value: "train" for value in instances[:8]})
        result.update({value: "validation" for value in instances[8:]})
    return result


def _train_epoch(model, optimizer, examples, *, seed, maximum_pairs):
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
            pairs = _systematic_sample(example["pairs"], maximum_pairs, seed)
            scores = {}
            arcs = {}
            preferred = torch.stack([
                _label_score(output, example, pair.preferred_label_id, scores, arcs)
                for pair in pairs
            ])
            other = torch.stack([
                _label_score(output, example, pair.other_label_id, scores, arcs)
                for pair in pairs
            ])
            weights = torch.tensor([pair.weight for pair in pairs], dtype=torch.float32)
            context_losses.append(qg2_v3_weighted_rank_loss(preferred, other, weights))
        loss = torch.stack(context_losses).mean()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        optimizer.step()
        losses.append(float(loss.detach()))
    return losses


def _evaluate(model, examples):
    by_instance = defaultdict(list)
    family_instance = {family: defaultdict(list) for family in QGR1_FAMILIES}
    model.eval()
    with torch.inference_mode():
        for example in examples:
            output = model(**example["features"].to_tensors())
            scores, arcs = {}, {}
            correct, total = 0.0, 0.0
            local_family = {family: [0.0, 0.0] for family in QGR1_FAMILIES}
            for pair in example["pairs"]:
                margin = float(
                    _label_score(output, example, pair.preferred_label_id, scores, arcs)
                    - _label_score(output, example, pair.other_label_id, scores, arcs)
                )
                hit = float(margin > 0.0)
                correct += hit * pair.weight
                total += pair.weight
                local_family[pair.family][0] += hit * pair.weight
                local_family[pair.family][1] += pair.weight
            by_instance[example["instance_hash"]].append(correct / max(1e-12, total))
            for family, (hits, mass) in local_family.items():
                if mass:
                    family_instance[family][example["instance_hash"]].append(hits / mass)
    per_instance = {key: fmean(values) for key, values in by_instance.items()}
    family_accuracy = {}
    for family in QGR1_FAMILIES:
        per = [fmean(values) for values in family_instance[family].values()]
        family_accuracy[family] = fmean(per) if per else None
    return {
        "instance_count": len(per_instance),
        "overall_actionable_pair_accuracy": fmean(per_instance.values()),
        "per_family_accuracy": family_accuracy,
        "aggregation_unit": "instance",
    }


def _label_score(output, example, label_id, scores, arcs):
    label_id = int(label_id)
    if label_id in scores:
        return scores[label_id]
    labels = example["labels"]
    row = labels[label_id]
    node_id = int(row.get("node_id", 0))
    node = output["node_scores"][node_id] if 0 < node_id < output["node_scores"].numel() else output["node_scores"].new_zeros(())
    def arc_score(cursor):
        if cursor in arcs:
            return arcs[cursor]
        current = labels[cursor]
        parent = int(current.get("parent_label_id", 2**64 - 1))
        value = output["arc_scores"].new_zeros(())
        if parent in labels and parent != cursor:
            value = arc_score(parent)
        index = int(current.get("incoming_arc_index", 2**64 - 1))
        if 0 <= index < output["arc_scores"].numel():
            value = value + output["arc_scores"][index]
        arcs[cursor] = value
        return value
    result = node + arc_score(label_id) + torch.dot(
        output["label_state_coefficients"],
        torch.tensor(row["features"], dtype=torch.float32),
    )
    scores[label_id] = result
    return result


def _systematic_sample(rows, maximum, seed):
    if len(rows) <= maximum:
        return tuple(rows)
    total = sum(max(0.0, row.weight) for row in rows)
    offset = random.Random(seed).random()
    cumulative, running = [], 0.0
    for row in rows:
        running += max(0.0, row.weight)
        cumulative.append(running)
    selected, cursor = [], 0
    for index in range(maximum):
        target = (index + offset) * total / maximum
        while cursor + 1 < len(rows) and cumulative[cursor] < target:
            cursor += 1
        selected.append(rows[cursor])
    return tuple(selected)


def _features(data, snapshot):
    duals = dict(snapshot.get("true_duals") or {})
    trajectory = dict(snapshot.get("trajectory_features") or {})
    previous_q0 = str(trajectory.get("previous_queue_policy_id") or "") == "Q0"
    return normalize_qg2_v3_features(data, build_qg2_features(
        data,
        cover_duals=dict(duals.get("task_duals") or duals.get("cover") or {}),
        fleet_dual=float(duals.get("fleet_dual") if duals.get("fleet_dual") is not None else duals.get("fleet_limit") or 0.0),
        active_column_count=_optional_int(snapshot.get("active_column_count")),
        active_task_sets=(None if snapshot.get("active_task_sets") is None else tuple(tuple(str(v) for v in row) for row in snapshot["active_task_sets"])),
        round_index=_optional_int(snapshot.get("round")),
        previous_proof_wall_sec=_optional_float(trajectory.get("previous_proof_pass_wall_time")) if previous_q0 else None,
        previous_processed_labels=_optional_int(trajectory.get("previous_proof_processed_labels")) if previous_q0 else None,
        dual_l1_delta_from_previous=_optional_float(trajectory.get("dual_l1_delta_from_previous")),
        branch_decisions=tuple(branch_context_from_payload(snapshot.get("branch_context") or {}).pair_decisions),
        cut_duals=dict(duals.get("cut_duals") or duals.get("cuts") or {}),
        v5_midpoint_wall_sec=_optional_float(snapshot.get("bidirectional_midpoint_prepass_wall_sec")),
        root_lifecycle_scope=str(snapshot.get("pricing_lifecycle_scope") or PRICING_LIFECYCLE_SCOPE_ROOT_CG) == PRICING_LIFECYCLE_SCOPE_ROOT_CG,
    ))


def _feature_envelope(examples):
    groups = {
        "node": [row for example in examples for row in example["features"].node_features],
        "edge": [row for example in examples for row in example["features"].edge_features],
        "context": [example["features"].context_features for example in examples],
    }
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_qgr1_train_feature_envelope.v1",
        "fit_partition": "inner_train_instances_only", "relative_margin": 0.05,
    }
    for group, rows in groups.items():
        if not rows:
            raise SystemExit("QGR1 feature envelope group is empty")
        payload[f"{group}_min"] = [min(row[i] for row in rows) for i in range(len(rows[0]))]
        payload[f"{group}_max"] = [max(row[i] for row in rows) for i in range(len(rows[0]))]
    return payload


def _validate_numeric(row):
    return all(isfinite(float(value)) for value in row)


def _optional_int(value):
    return None if value is None else int(value)


def _optional_float(value):
    return None if value is None else float(value)


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_once(path, payload):
    path = Path(path)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != text:
        raise SystemExit(f"immutable QGR1 training artifact drift:{path}")
    if not path.exists():
        path.write_text(text, encoding="utf-8")


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _stable_hash(payload):
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
