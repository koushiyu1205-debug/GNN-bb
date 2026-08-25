#!/usr/bin/env python3
"""Ablation diagnostics for the context-level QG2 V3 GAT selector."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
SCHEMA = "lunar_ice_bpc.p0v5_qg2_v3_selector_attribution.v1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selector-training-report", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--partitions", nargs="+", default=("calibration", "heldout")
    )
    args = parser.parse_args()

    import torch
    from lunar_ice_bpc.guidance.proof_queue_label_state_gat import (
        QG2_CONTEXT_FEATURES,
        QG2_NODE_DYNAMIC_FEATURES,
    )
    from lunar_ice_bpc.guidance.qg2_unified_arm_selector_v3 import (
        QG2V3GraphArmSelector,
        QG2_V4_SELECTOR_CHECKPOINT_SCHEMA,
    )
    from lunar_ice_bpc.guidance.tensorization import (
        EDGE_STATIC_FEATURES,
        NODE_STATIC_FEATURES,
    )

    report_path = _resolve(args.selector_training_report)
    report = _load(report_path)
    if str(report.get("trained_model") or "") != "gat":
        raise SystemExit("selector attribution requires the GAT selector")
    helper = _training_helpers()
    oracle = _load(_resolve(report["oracle_summary"]))
    ranker = _load(_resolve(report["ranker_training_report"]))
    split = _load(_resolve(ranker["split_path"]))["assignments"]
    normalization = _load(_resolve(ranker["normalization_path"]))
    force_reports = [
        _load(_resolve(path))
        for path in report.get("qg2_force_on_reports") or ()
    ]
    matched = (
        None if not report.get("matched_arm_report")
        else _load(_resolve(report["matched_arm_report"]))
    )
    examples, _ = helper._load_examples(
        oracle, split,
        qg2_records=helper._force_records(force_reports),
        qg2_enabled="QG2" in set(report.get("trainable_arms") or ()),
        matched_arm_records=(
            {} if matched is None else {
                str(row["state_hash"]): dict(row)
                for row in matched.get("records") or ()
            }
        ),
        matched_arms_required=matched is not None,
    )
    allowed = {str(value) for value in args.partitions}
    examples = [row for row in examples if row["partition"] in allowed]
    checkpoint = torch.load(
        _resolve(report["checkpoint_path"]), map_location="cpu",
        weights_only=False,
    )
    if checkpoint.get("schema_version") != QG2_V4_SELECTOR_CHECKPOINT_SCHEMA:
        raise SystemExit("QG2 V4 attribution checkpoint schema mismatch")
    if str(checkpoint.get("input_parity_contract") or "") != (
        "node_edge_context_identical_gat_topology_only_difference.v1"
    ):
        raise SystemExit("QG2 V4 attribution input-parity contract mismatch")
    if str(checkpoint.get("model_kind") or "") != "gat":
        raise SystemExit("QG2 V4 attribution requires a GAT checkpoint")
    if tuple(checkpoint.get("action_universe") or ()) != (
        "Q0", "QG2", "QD1", "QB1"
    ):
        raise SystemExit("QG2 V4 attribution action universe mismatch")
    if str(checkpoint.get("fallback_action") or "") != "Q0":
        raise SystemExit("QG2 V4 attribution lost literal Q0 fallback")
    model = QG2V3GraphArmSelector(normalization)
    model.load_state_dict(checkpoint["state_dict"], strict=True)
    model.eval()
    thresholds = dict(report["thresholds"])

    baseline_predictions = _predict(model, examples)
    baseline = _metrics(helper, baseline_predictions, thresholds)
    group_rows = []
    transforms = (
        ("node_to_train_mean", _to_mean("node", normalization)),
        ("edge_to_train_mean", _to_mean("edge", normalization)),
        ("context_to_train_mean", _to_mean("context", normalization)),
        ("shuffled_message_topology", _shuffle_topology),
    )
    for name, transform in transforms:
        prediction = _predict(model, examples, transform=transform)
        group_rows.append(_ablation_row(
            name, _metrics(helper, prediction, thresholds), baseline,
        ))
    no_message = copy.deepcopy(model)
    no_message.attention_layers = torch.nn.ModuleList()
    group_rows.append(_ablation_row(
        "no_message_passing",
        _metrics(helper, _predict(no_message, examples), thresholds),
        baseline,
    ))

    feature_rows = []
    feature_groups = (
        ("node", (*NODE_STATIC_FEATURES, *QG2_NODE_DYNAMIC_FEATURES)),
        ("edge", tuple(EDGE_STATIC_FEATURES)),
        ("context", tuple(QG2_CONTEXT_FEATURES)),
    )
    group_by_name = {row["ablation"].split("_to_train_mean")[0]: row
                     for row in group_rows if "_to_train_mean" in row["ablation"]}
    for group, names in feature_groups:
        means = list(dict(normalization[group])["mean"])
        group_drop = float(
            dict(group_by_name.get(group) or {}).get(
                "arm_rank_accuracy_drop", 0.0
            )
        )
        for index, name in enumerate(names):
            prediction = _predict(
                model, examples,
                transform=_single_feature_to_mean(
                    group, index, float(means[index])
                ),
            )
            row = _ablation_row(
                str(name), _metrics(helper, prediction, thresholds), baseline,
            )
            row["group"] = group
            row["share_of_positive_group_accuracy_drop"] = (
                max(0.0, float(row["arm_rank_accuracy_drop"]))
                / group_drop
                if group_drop > 0.0 else None
            )
            row["share_of_positive_group_rank_accuracy_drop"] = row[
                "share_of_positive_group_accuracy_drop"
            ]
            feature_rows.append(row)
    feature_rows.sort(key=lambda row: (
        -row["arm_rank_accuracy_drop"],
        -row["classification_accuracy_drop"],
        -row["selected_action_disagreement_rate"], row["ablation"],
    ))
    context_rows = [
        row for row in feature_rows if row["group"] == "context"
    ]
    positive = [
        row for row in feature_rows
        if float(row["arm_rank_accuracy_drop"]) > 0.0
        or float(row["classification_accuracy_drop"]) > 0.0
    ]
    result = {
        "schema_version": SCHEMA,
        "development_only": True,
        "deployable": False,
        "selector_training_report": str(report_path),
        "partitions": sorted(allowed),
        "context_count": len(examples),
        "thresholds": thresholds,
        "baseline": baseline,
        "group_ablations": group_rows,
        "single_feature_ablations": feature_rows,
        "context_feature_ablations": context_rows,
        "top_positive_contributors": positive[:15],
        "single_feature_dominance_diagnostic": {
            "candidate": None if not positive else {
                "group": positive[0]["group"],
                "feature": positive[0]["ablation"],
                "classification_accuracy_drop": positive[0][
                    "classification_accuracy_drop"
                ],
                "arm_rank_accuracy_drop": positive[0][
                    "arm_rank_accuracy_drop"
                ],
                "selected_action_disagreement_rate": positive[0][
                    "selected_action_disagreement_rate"
                ],
                "share_of_positive_group_accuracy_drop": positive[0][
                    "share_of_positive_group_accuracy_drop"
                ],
            },
            "interpretation": (
                "a large single-feature share is a diagnostic candidate, not "
                "a causal or performance claim"
            ),
        },
        "interpretation_boundary": (
            "offline attribution only; fresh-process matched wall is the "
            "performance authority"
        ),
    }
    _write(_resolve(args.output), result)
    print(json.dumps({
        "baseline": baseline,
        "group_ablations": group_rows,
        "top_features": feature_rows[:8],
    }, sort_keys=True))
    return 0


def _predict(model, examples, transform=None):
    import torch
    result = []
    with torch.inference_mode():
        for row in examples:
            tensors = row["features"].to_tensors()
            if transform is not None:
                tensors = transform(tensors)
            output = model(**tensors)
            arms = {}
            for index, arm in enumerate(("QG2", "QD1", "QB1")):
                probability = float(output["benefit_probability"][0, index])
                magnitude = float(output["conditional_positive_gain"][0, index])
                arms[arm] = {
                    "benefit_probability": probability,
                    "conditional_positive_gain": magnitude,
                    "expected_gain": probability * magnitude,
                    "adverse_probability": float(
                        output["adverse_probability"][0, index]
                    ),
                    "outcome": row["outcomes"].get(arm),
                }
            result.append({
                "state_hash": row["state_hash"],
                "instance_hash": row["instance_hash"],
                "scale": row["scale"],
                "milestone_kind": row["milestone_kind"],
                "arms": arms,
            })
    return result


def _metrics(helper, rows, thresholds):
    active_arms = tuple(
        arm for arm in ("QG2", "QD1", "QB1")
        if arm not in set(thresholds.get("forced_veto_arms") or ())
        and all(row["arms"][arm]["outcome"] is not None for row in rows)
    )
    classification = helper._classification_metrics(
        rows, trainable_arms=active_arms
    )
    arm_rank = helper._arm_rank_metrics(
        rows, trainable_arms=active_arms
    )
    policy = helper._evaluate_policy(rows, thresholds)
    actions = [helper._selected_arm(row, thresholds) for row in rows]
    values = [
        value
        for arm in active_arms
        for value in (
            classification[arm]["benefit_accuracy"],
            classification[arm]["adverse_accuracy"],
        )
    ]
    return {
        "mean_classification_accuracy": sum(values) / max(1, len(values)),
        "mean_context_arm_rank_accuracy": float(
            arm_rank.get("mean_context_pair_accuracy")
            if arm_rank.get("mean_context_pair_accuracy") is not None
            else 0.0
        ),
        "net_geomean_ratio": float(policy["net_geomean_ratio"]),
        "activated_count": int(policy["activated_count"]),
        "harmful_count": int(policy["harmful_count"]),
        "actions": actions,
    }


def _ablation_row(name, metrics, baseline):
    changed = sum(
        left != right
        for left, right in zip(metrics["actions"], baseline["actions"], strict=True)
    )
    return {
        "ablation": name,
        "mean_classification_accuracy": metrics["mean_classification_accuracy"],
        "mean_context_arm_rank_accuracy": metrics[
            "mean_context_arm_rank_accuracy"
        ],
        "arm_rank_accuracy_drop": (
            baseline["mean_context_arm_rank_accuracy"]
            - metrics["mean_context_arm_rank_accuracy"]
        ),
        "classification_accuracy_drop": (
            baseline["mean_classification_accuracy"]
            - metrics["mean_classification_accuracy"]
        ),
        "selected_action_disagreement_rate": (
            changed / max(1, len(metrics["actions"]))
        ),
        "net_geomean_ratio": metrics["net_geomean_ratio"],
        "activated_count": metrics["activated_count"],
        "harmful_count": metrics["harmful_count"],
    }


def _to_mean(group, normalization):
    means = list(dict(normalization[group])["mean"])
    key = f"{group}_features"
    if group == "context":
        key = "context_features"
    def transform(tensors):
        import torch
        result = dict(tensors)
        value = torch.tensor(means, dtype=result[key].dtype)
        result[key] = (
            value if result[key].ndim == 1
            else value.expand_as(result[key]).clone()
        )
        return result
    return transform


def _single_feature_to_mean(group, index, mean):
    key = f"{group}_features"
    if group == "context":
        key = "context_features"
    def transform(tensors):
        result = dict(tensors)
        values = result[key].clone()
        if values.ndim == 1:
            values[index] = float(mean)
        else:
            values[:, index] = float(mean)
        result[key] = values
        return result
    return transform


def _shuffle_topology(tensors):
    import torch
    result = dict(tensors)
    edge_index = result["edge_index"]
    if int(edge_index.shape[1]) > 1:
        result["edge_index"] = torch.stack(
            (edge_index[0], torch.roll(edge_index[1], shifts=1)), dim=0
        )
    return result


def _training_helpers():
    path = ROOT / "scripts/train_p0v5_qg2_v3_gat_arm_selector.py"
    spec = importlib.util.spec_from_file_location("qg2_v3_selector_helpers", path)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError("cannot load selector training helpers")
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _resolve(value):
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
