#!/usr/bin/env python3
"""Evaluate a leakage-safe Q0/QD1/QB1 context-level selector.

This is a post-training development diagnostic.  It reuses the matched QD1
and QB1 outcomes already collected by the bounded QG2 Oracle and the frozen
instance split emitted by the QG2 trainer.  It never starts Native, never
changes QG2 label supervision, and never authorizes deployment.

The selector is intentionally small: two linear two-head policies predict
P(arm is at least five percent faster) and the conditional positive fractional
gain.  Calibration chooses a single pair of activation thresholds.  If no arm
passes both thresholds, the literal action is Q0.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

SCHEMA = "lunar_ice_bpc.p0v5_qg2_context_arm_selector_feasibility.v1"
ORACLE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_bounded_oracle.v5"
TRAINING_SCHEMA = "lunar_ice_bpc.p0v5_qg2_model_comparison.v3"
SPLIT_SCHEMA = "lunar_ice_bpc.p0v5_qg2_instance_split.v1"
ARMS = ("QD1", "QB1")
MILESTONES = {"ADMISSION_BATCH_READY", "EXACT_PROOF_COMPLETION"}
BENEFICIAL_RATIO = 0.95
HARMFUL_RATIO = 1.05
ONE_SIDED_95_Z = 1.6448536269514722
MINIMUM_DEVELOPMENT_CALIBRATION_ACTIONS = 5


@dataclass(frozen=True)
class ArmOutcome:
    wall_sec: float
    ratio: float
    milestone_matched: bool
    right_censored: bool
    beneficial: bool
    harmful: bool
    positive_gain_fraction: float


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--oracle-summary", required=True)
    parser.add_argument("--training-report", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--epochs", type=int, default=300)
    parser.add_argument("--learning-rate", type=float, default=0.01)
    parser.add_argument("--seed", type=int, default=20260801)
    args = parser.parse_args()

    oracle_path = _resolve(args.oracle_summary)
    training_path = _resolve(args.training_report)
    output_dir = _resolve(args.output_dir)
    output_path = _resolve(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    oracle = _load(oracle_path)
    training = _load(training_path)
    split_path, assignments = _validate_contract(
        oracle_path=oracle_path,
        oracle=oracle,
        training_path=training_path,
        training=training,
    )
    examples, rejections = _load_examples(oracle, assignments)
    partitions = {
        name: [row for row in examples if row["partition"] == name]
        for name in ("train", "calibration", "heldout")
    }
    if not partitions["train"] or not partitions["calibration"]:
        raise SystemExit("context-arm selector has no train/calibration rows")

    model_path = output_dir / "context_arm_selector_linear.pt"
    model, normalization, training_metrics = _fit_model(
        partitions["train"],
        epochs=max(1, int(args.epochs)),
        learning_rate=float(args.learning_rate),
        seed=int(args.seed),
    )
    import torch

    torch.save({
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_context_arm_selector_checkpoint.v1"
        ),
        "arms": list(ARMS),
        "feature_dimension": len(normalization["mean"]),
        "normalization": normalization,
        "state_dict": model.state_dict(),
        "fallback_action": "Q0",
        "deployment_authorized": False,
    }, model_path)

    calibration_predictions = _predict(model, partitions["calibration"], normalization)
    thresholds = choose_thresholds(calibration_predictions)
    partition_reports = {}
    for name, rows in partitions.items():
        predictions = _predict(model, rows, normalization)
        partition_reports[name] = evaluate_policy(predictions, thresholds)

    heldout = partition_reports["heldout"]
    enough_heldout = all(
        int((heldout.get("per_scale") or {}).get(str(scale), {}).get(
            "context_count", 0
        )) >= 10
        for scale in (30, 50)
    )
    continued_development_recommended = bool(
        thresholds.get("calibration_gate_passed")
        and enough_heldout
        and int(heldout.get("activated_count") or 0) > 0
        and float(heldout.get("net_geomean_ratio") or math.inf) <= 0.95
        and all(
            float((heldout.get("per_scale") or {}).get(str(scale), {}).get(
                "net_geomean_ratio", math.inf
            )) <= 1.0
            for scale in (30, 50)
        )
    )
    payload = {
        "schema_version": SCHEMA,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "development_only": True,
        "deployable": False,
        "starts_solver_process": False,
        "changes_qg2": False,
        "training_authority": False,
        "calibration_authority": False,
        "fallback_action": "Q0",
        "all_arms_rejected_action": "Q0",
        "candidate_arms": list(ARMS),
        "oracle_summary": str(oracle_path),
        "oracle_summary_sha256": _sha256(oracle_path),
        "training_report": str(training_path),
        "training_report_sha256": _sha256(training_path),
        "instance_split": str(split_path),
        "instance_split_sha256": _sha256(split_path),
        "model_path": str(model_path),
        "model_sha256": _sha256(model_path),
        "feature_schema_version": training.get("feature_schema_version"),
        "selector_model": "per_arm_linear_two_head_v1",
        "threshold_authority": (
            "development_only_formal_wilson_bounds_reported_separately"
        ),
        "outcome_semantics": {
            "beneficial": "same_milestone_and_arm_over_q0_ratio_le_0.95",
            "harmful": "right_censored_or_arm_over_q0_ratio_ge_1.05",
            "right_censored_role": "known_not_to_reach_q0_milestone_within_matched_budget",
        },
        "context_count": len(examples),
        "instance_count": len({row["instance_hash"] for row in examples}),
        "rejection_counts": rejections,
        "partition_counts": {
            name: {
                "context_count": len(rows),
                "instance_count": len({row["instance_hash"] for row in rows}),
                "scale30": sum(row["scale"] == 30 for row in rows),
                "scale50": sum(row["scale"] == 50 for row in rows),
            }
            for name, rows in partitions.items()
        },
        "normalization": normalization,
        "training_metrics": training_metrics,
        "thresholds": thresholds,
        "partition_reports": partition_reports,
        "continued_development_recommended": continued_development_recommended,
        "recommendation": (
            "evaluate_combined_qg2_plus_context_selector_in_fresh_process"
            if continued_development_recommended
            else "retain_qg2_only_and_literal_q0_fallback"
        ),
        "deployment_authorized": False,
    }
    _write(output_path, payload)
    print(json.dumps({
        "status": "COMPLETE",
        "continued_development_recommended": continued_development_recommended,
        "heldout_net_geomean_ratio": heldout.get("net_geomean_ratio"),
        "heldout_activated_count": heldout.get("activated_count"),
        "output": str(output_path),
    }, sort_keys=True), flush=True)
    return 0


def _validate_contract(
    *,
    oracle_path: Path,
    oracle: dict,
    training_path: Path,
    training: dict,
) -> tuple[Path, dict[str, str]]:
    errors = []
    if oracle.get("schema_version") != ORACLE_SCHEMA:
        errors.append("oracle_schema_mismatch")
    if training.get("schema_version") != TRAINING_SCHEMA:
        errors.append("training_schema_mismatch")
    if not bool(training.get("oracle_gate_passed")):
        errors.append("training_not_authorized")
    if bool(oracle.get("deployable")) or bool(training.get("deployable")):
        errors.append("development_safety_mismatch")
    if str(training.get("oracle_summary_sha256") or "") != _sha256(oracle_path):
        errors.append("training_oracle_hash_mismatch")
    if _resolve(training.get("oracle_summary") or "") != oracle_path:
        errors.append("training_oracle_path_mismatch")
    split_path = _resolve(training.get("split_path") or "")
    if not split_path.is_file():
        errors.append("split_missing")
        split = {}
    else:
        split = _load(split_path)
        if split.get("schema_version") != SPLIT_SCHEMA:
            errors.append("split_schema_mismatch")
        if str(training.get("split_sha256") or "") != _sha256(split_path):
            errors.append("split_hash_mismatch")
    assignments = {
        str(key): str(value)
        for key, value in dict(split.get("assignments") or {}).items()
    }
    if not assignments or any(
        value not in {"train", "calibration", "heldout"}
        for value in assignments.values()
    ):
        errors.append("split_assignments_invalid")
    if errors:
        raise ValueError("context-arm selector contract failed: " + ",".join(errors))
    return split_path, assignments


def _load_examples(
    oracle: dict,
    assignments: dict[str, str],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    examples = []
    rejections: dict[str, int] = {}
    for source in oracle.get("initial_rows") or ():
        reason = _source_rejection(source, assignments)
        if reason:
            rejections[reason] = rejections.get(reason, 0) + 1
            continue
        q0 = _load(_resolve(source["q0_path"]))
        if not bool(q0.get("milestone_reached")) or str(
            q0.get("milestone_kind") or ""
        ) not in MILESTONES:
            rejections["q0_milestone_unavailable"] = (
                rejections.get("q0_milestone_unavailable", 0) + 1
            )
            continue
        q0_wall = _effective_wall(q0)
        snapshot = _load(_resolve(source["snapshot_path"]))
        features = _context_features(source, snapshot)
        outcomes = {}
        invalid = False
        for arm in ARMS:
            path = _resolve(dict(source.get("arm_paths") or {}).get(arm) or "")
            if not path.is_file():
                rejections[f"{arm.lower()}_missing"] = (
                    rejections.get(f"{arm.lower()}_missing", 0) + 1
                )
                invalid = True
                break
            outcomes[arm] = arm_outcome(q0, _load(path), q0_wall=q0_wall)
        if invalid:
            continue
        examples.append({
            "state_hash": str(source["state_hash"]),
            "instance_hash": str(source["instance_hash"]),
            "scale": int(source["scale"]),
            "partition": assignments[str(source["instance_hash"])],
            "features": features,
            "q0_wall_sec": q0_wall,
            "outcomes": outcomes,
        })
    examples.sort(key=lambda row: (row["scale"], row["state_hash"]))
    return examples, dict(sorted(rejections.items()))


def _source_rejection(source: dict, assignments: dict[str, str]) -> str | None:
    if not bool(source.get("compliant_context")):
        return "noncompliant_context"
    if not bool(source.get("all_initial_arms_safe")):
        return "initial_arm_safety_failed"
    instance = str(source.get("instance_hash") or "")
    if instance not in assignments:
        return "instance_not_in_frozen_split"
    if not str(source.get("snapshot_path") or ""):
        return "snapshot_path_missing"
    return None


def _context_features(source: dict, snapshot: dict) -> tuple[float, ...]:
    from lunar_ice_bpc.exact.bpc.pricing.backends.base import (
        PRICING_LIFECYCLE_SCOPE_ROOT_CG,
    )
    from lunar_ice_bpc.exact.core.branching import branch_context_from_payload
    from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
    from lunar_ice_bpc.guidance.proof_queue_label_state_gat import (
        build_qg2_features,
    )

    data = load_lunar_ice_data(_load(_resolve(source["instance_path"])))
    true_duals = dict(snapshot.get("true_duals") or {})
    trajectory = dict(snapshot.get("trajectory_features") or {})
    features = build_qg2_features(
        data,
        cover_duals=dict(
            true_duals.get("task_duals") or true_duals.get("cover") or {}
        ),
        fleet_dual=float(
            true_duals.get("fleet_dual")
            or true_duals.get("fleet_limit")
            or 0.0
        ),
        active_column_count=_optional_int(snapshot.get("active_column_count")),
        active_task_sets=_active_task_sets(snapshot.get("active_task_sets")),
        round_index=_optional_int(snapshot.get("round")),
        previous_proof_wall_sec=_optional_float(
            trajectory.get("previous_proof_pass_wall_time")
        ),
        previous_processed_labels=_optional_int(
            trajectory.get("previous_proof_processed_labels")
            if trajectory.get("previous_proof_processed_labels") is not None
            else trajectory.get("previous_harvest_processed_labels")
        ),
        dual_l1_delta_from_previous=_optional_float(
            trajectory.get("dual_l1_delta_from_previous")
        ),
        branch_decisions=tuple(
            branch_context_from_payload(
                snapshot.get("branch_context") or {}
            ).pair_decisions
        ),
        cut_duals=dict(
            true_duals.get("cut_duals") or true_duals.get("cuts") or {}
        ),
        v5_midpoint_wall_sec=_optional_float(
            snapshot.get("bidirectional_midpoint_prepass_wall_sec")
            if snapshot.get("bidirectional_midpoint_prepass_wall_sec") is not None
            else trajectory.get("v5_midpoint_wall_sec")
        ),
        root_lifecycle_scope=(
            str(
                snapshot.get("pricing_lifecycle_scope")
                or PRICING_LIFECYCLE_SCOPE_ROOT_CG
            )
            == PRICING_LIFECYCLE_SCOPE_ROOT_CG
        ),
    )
    return tuple(float(value) for value in features.context_features)


def arm_outcome(q0: dict, arm: dict, *, q0_wall: float) -> ArmOutcome:
    q0_kind = str(q0.get("milestone_kind") or "")
    arm_kind = str(arm.get("milestone_kind") or "")
    matched = bool(
        arm.get("milestone_reached")
        and arm_kind == q0_kind
        and q0_kind in MILESTONES
    )
    arm_wall = _effective_wall(arm)
    ratio = arm_wall / max(1.0e-9, float(q0_wall))
    censored = not matched
    beneficial = bool(matched and ratio <= BENEFICIAL_RATIO)
    harmful = bool(censored or ratio >= HARMFUL_RATIO)
    return ArmOutcome(
        wall_sec=arm_wall,
        ratio=ratio,
        milestone_matched=matched,
        right_censored=censored,
        beneficial=beneficial,
        harmful=harmful,
        positive_gain_fraction=(max(0.0, 1.0 - ratio) if matched else 0.0),
    )


def _effective_wall(row: dict) -> float:
    measured = max(1.0e-9, float(
        row.get("admission_milestone_wall_sec")
        or row.get("milestone_wall_sec")
        or row.get("total_fresh_process_wall_sec")
        or 0.0
    ))
    if row.get("milestone_reached"):
        return measured
    return max(measured, float(row.get("requested_wall_time_limit_sec") or 0.0))


class _LinearTwoHead:
    def __new__(cls, dimension: int):
        import torch
        from torch import nn

        class Model(nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.head = nn.Linear(dimension, len(ARMS) * 2)

            def forward(self, features):
                values = self.head(features).reshape(-1, len(ARMS), 2)
                return values[..., 0], torch.nn.functional.softplus(values[..., 1])

        return Model()


def _fit_model(
    rows: list[dict[str, Any]],
    *,
    epochs: int,
    learning_rate: float,
    seed: int,
):
    import torch
    from torch.nn import functional as F

    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    random.seed(seed)
    torch.manual_seed(seed)
    dimension = len(rows[0]["features"])
    if any(len(row["features"]) != dimension for row in rows):
        raise ValueError("context-arm selector feature dimension drift")
    mean = [statistics.fmean(row["features"][index] for row in rows) for index in range(dimension)]
    std = []
    for index in range(dimension):
        values = [row["features"][index] for row in rows]
        variance = statistics.fmean((value - mean[index]) ** 2 for value in values)
        std.append(max(1.0e-6, math.sqrt(variance)))
    normalization = {"mean": mean, "std": std, "fit_partition": "train_instances_only"}
    features, targets, gains = _training_tensors(rows, normalization)
    model = _LinearTwoHead(dimension)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    final_loss = math.inf
    for _epoch in range(epochs):
        optimizer.zero_grad()
        logits, magnitudes = model(features)
        probability_loss = F.binary_cross_entropy_with_logits(logits, targets)
        positive = targets > 0.5
        magnitude_loss = (
            F.smooth_l1_loss(magnitudes[positive], gains[positive])
            if bool(positive.any())
            else magnitudes.sum() * 0.0
        )
        loss = probability_loss + 0.1 * magnitude_loss
        loss.backward()
        optimizer.step()
        final_loss = float(loss.detach())
    return model, normalization, {
        "epochs": epochs,
        "learning_rate": learning_rate,
        "final_loss": final_loss,
        "train_context_count": len(rows),
    }


def _training_tensors(rows, normalization):
    import torch

    features = torch.tensor([
        _normalize(row["features"], normalization) for row in rows
    ], dtype=torch.float32)
    targets = torch.tensor([
        [1.0 if row["outcomes"][arm].beneficial else 0.0 for arm in ARMS]
        for row in rows
    ], dtype=torch.float32)
    gains = torch.tensor([
        [row["outcomes"][arm].positive_gain_fraction for arm in ARMS]
        for row in rows
    ], dtype=torch.float32)
    return features, targets, gains


def _predict(model, rows, normalization) -> list[dict[str, Any]]:
    import torch

    if not rows:
        return []
    features = torch.tensor([
        _normalize(row["features"], normalization) for row in rows
    ], dtype=torch.float32)
    with torch.inference_mode():
        logits, magnitudes = model(features)
        probabilities = torch.sigmoid(logits)
    result = []
    for index, row in enumerate(rows):
        arm_predictions = {}
        for arm_index, arm in enumerate(ARMS):
            probability = float(probabilities[index, arm_index])
            magnitude = float(magnitudes[index, arm_index])
            arm_predictions[arm] = {
                "benefit_probability": probability,
                "conditional_positive_gain": magnitude,
                "expected_gain": probability * magnitude,
                "outcome": row["outcomes"][arm],
            }
        result.append({
            "state_hash": row["state_hash"],
            "instance_hash": row["instance_hash"],
            "scale": row["scale"],
            "q0_wall_sec": row["q0_wall_sec"],
            "arms": arm_predictions,
        })
    return result


def choose_thresholds(predictions: list[dict[str, Any]]) -> dict[str, Any]:
    strict_candidates = []
    development_candidates = []
    probabilities = sorted({
        round(float(arm["benefit_probability"]), 12)
        for row in predictions for arm in row["arms"].values()
    })
    scores = sorted({
        round(float(arm["expected_gain"]), 12)
        for row in predictions for arm in row["arms"].values()
    })
    for probability in [0.5, *probabilities]:
        for score in [0.0, *scores]:
            report = evaluate_policy(
                predictions,
                {"benefit_probability": probability, "expected_gain": score},
            )
            if not report["activated_count"]:
                continue
            strict = bool(
                float(report["harmful_rate_95_upper"]) <= 0.05
                and float(report["beneficial_precision_95_lower"]) >= 0.80
            )
            development = bool(
                int(report["activated_count"])
                >= MINIMUM_DEVELOPMENT_CALIBRATION_ACTIONS
                and int(report["harmful_action_count"]) == 0
                and float(report["beneficial_precision"]) >= 0.80
                and float(report["net_geomean_ratio"]) <= 0.95
            )
            candidate = (
                float(report["net_geomean_ratio"]),
                -int(report["activated_count"]),
                -probability,
                -score,
                probability,
                score,
                report,
            )
            if strict:
                strict_candidates.append(candidate)
            if development:
                development_candidates.append(candidate)
    candidates = strict_candidates or development_candidates
    if not candidates:
        return {
            "benefit_probability": 2.0,
            "expected_gain": 1.0e30,
            "calibration_gate_passed": False,
            "strict_deployment_risk_gate_passed": False,
            "reason": (
                "no_nonempty_threshold_satisfies_development_precision_harm_and_gain"
            ),
            "fallback_action": "Q0",
        }
    selected = min(candidates)
    strict_selected = bool(strict_candidates)
    return {
        "benefit_probability": selected[4],
        "expected_gain": selected[5],
        "calibration_gate_passed": True,
        "strict_deployment_risk_gate_passed": strict_selected,
        "reason": (
            "best_strict_safe_calibration_geomean"
            if strict_selected
            else "best_development_only_zero_observed_harm_geomean"
        ),
        "fallback_action": "Q0",
        "calibration_report": selected[6],
    }


def evaluate_policy(
    predictions: list[dict[str, Any]],
    thresholds: dict[str, Any],
) -> dict[str, Any]:
    actions = []
    ratios = []
    p_threshold = float(thresholds.get("benefit_probability", math.inf))
    s_threshold = float(thresholds.get("expected_gain", math.inf))
    per_scale_rows: dict[int, list[tuple[float, bool, bool, bool]]] = {
        30: [], 50: []
    }
    for row in predictions:
        eligible = [
            (float(payload["expected_gain"]), arm, payload)
            for arm, payload in row["arms"].items()
            if float(payload["benefit_probability"]) >= p_threshold
            and float(payload["expected_gain"]) >= s_threshold
        ]
        if eligible:
            _score, arm, payload = max(eligible, key=lambda item: (item[0], item[1]))
            outcome: ArmOutcome = payload["outcome"]
            ratio = float(outcome.ratio)
            beneficial = bool(outcome.beneficial)
            harmful = bool(outcome.harmful)
            activated_action = True
            actions.append({"arm": arm, "beneficial": beneficial, "harmful": harmful})
        else:
            ratio = 1.0
            beneficial = False
            harmful = False
            activated_action = False
        ratios.append(ratio)
        per_scale_rows[int(row["scale"])].append(
            (ratio, beneficial, harmful, activated_action)
        )
    harmful_count = sum(bool(row["harmful"]) for row in actions)
    beneficial_count = sum(bool(row["beneficial"]) for row in actions)
    activated = len(actions)
    return {
        "context_count": len(predictions),
        "instance_count": len({row["instance_hash"] for row in predictions}),
        "activated_count": activated,
        "no_op_count": len(predictions) - activated,
        "beneficial_action_count": beneficial_count,
        "harmful_action_count": harmful_count,
        "harmful_rate": harmful_count / max(1, activated),
        "harmful_rate_95_upper": wilson_bound(harmful_count, activated, upper=True),
        "beneficial_precision": beneficial_count / max(1, activated),
        "beneficial_precision_95_lower": wilson_bound(beneficial_count, activated, upper=False),
        "net_geomean_ratio": _geomean(ratios),
        "fallback_action": "Q0",
        "per_scale": {
            str(scale): {
                "context_count": len(rows),
                "activated_count": sum(
                    activated_action
                    for _ratio, _beneficial, _harmful, activated_action in rows
                ),
                "net_geomean_ratio": _geomean([
                    ratio for ratio, _beneficial, _harmful, _activated in rows
                ]),
                "harmful_action_count": sum(
                    harmful for _ratio, _beneficial, harmful, _activated in rows
                ),
            }
            for scale, rows in per_scale_rows.items()
        },
    }


def wilson_bound(successes: int, trials: int, *, upper: bool) -> float:
    if trials <= 0:
        return 1.0 if upper else 0.0
    p = successes / trials
    z = ONE_SIDED_95_Z
    denominator = 1.0 + z * z / trials
    center = (p + z * z / (2.0 * trials)) / denominator
    radius = z * math.sqrt(
        p * (1.0 - p) / trials + z * z / (4.0 * trials * trials)
    ) / denominator
    return min(1.0, center + radius) if upper else max(0.0, center - radius)


def _normalize(features, normalization):
    return [
        (float(value) - float(mean)) / float(std)
        for value, mean, std in zip(
            features, normalization["mean"], normalization["std"], strict=True
        )
    ]


def _geomean(values) -> float:
    return (
        1.0
        if not values
        else math.exp(statistics.fmean(math.log(max(1.0e-12, float(value))) for value in values))
    )


def _optional_int(value):
    return None if value is None else max(0, int(value))


def _optional_float(value):
    return None if value is None else max(0.0, float(value))


def _active_task_sets(value):
    if value is None:
        return None
    return tuple(tuple(str(task_id) for task_id in row) for row in value)


def _resolve(value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
