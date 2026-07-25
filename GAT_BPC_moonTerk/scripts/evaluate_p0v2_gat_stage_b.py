#!/usr/bin/env python3
"""Evaluate paired P0/H/HA development runs against the Stage-B gate."""

from __future__ import annotations

import argparse
import json
from math import isfinite
from pathlib import Path
from statistics import mean, median

from lunar_ice_bpc.guidance.evaluation import (
    SafetyAudit,
    paired_runtime_summary,
    stage_b_gate,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--p0-results-jsonl", required=True)
    parser.add_argument("--h-results-jsonl", required=True)
    parser.add_argument("--ha-results-jsonl", required=True)
    parser.add_argument(
        "--split-manifest",
        required=True,
        help="Audited manifest used to restrict all ledgers to development.",
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--bootstrap-samples", type=int, default=5000)
    args = parser.parse_args()
    split = json.loads(
        Path(args.split_manifest).read_text(encoding="utf-8")
    )
    if not bool((split.get("audit") or {}).get("passed")):
        raise SystemExit("split manifest audit did not pass")
    development_hashes = {
        str(row["instance_content_hash"])
        for row in split.get("development", ())
    }
    fold_by_hash = {
        str(row["instance_content_hash"]): int(row["fold"])
        for row in split.get("development", ())
    }
    split_manifest_hash = str(split.get("manifest_hash") or "")
    if not split_manifest_hash:
        raise SystemExit("split manifest has no immutable manifest hash")
    controls = _load(
        args.p0_results_jsonl,
        selected_hashes=development_hashes,
        expected_variant="P0",
        expected_guidance_mode="off",
        expected_split_manifest_hash=None,
        expected_fold_by_hash=None,
    )
    variants = {
        "H": _load(
            args.h_results_jsonl,
            selected_hashes=development_hashes,
            expected_variant="H",
            expected_guidance_mode="harvest",
            expected_split_manifest_hash=split_manifest_hash,
            expected_fold_by_hash=fold_by_hash,
        ),
        "HA": _load(
            args.ha_results_jsonl,
            selected_hashes=development_hashes,
            expected_variant="HA",
            expected_guidance_mode="task_arc",
            expected_split_manifest_hash=split_manifest_hash,
            expected_fold_by_hash=fold_by_hash,
        ),
    }
    report = {
        "schema_version": "lunar_ice_bpc.p0v2_gat_stage_b_gate.v1",
        "control": str(Path(args.p0_results_jsonl).resolve()),
        "split_manifest_hash": split.get("manifest_hash"),
        "partition": "development_cross_validation_only",
        "variants": {},
        "promotion_rule": (
            "HA must pass independently before any exact proof queue work; "
            "a failed earlier stage cannot be masked by later modules."
        ),
    }
    for name, guided in variants.items():
        report["variants"][name] = _evaluate(
            controls,
            guided,
            bootstrap_samples=max(1, int(args.bootstrap_samples)),
        )
    report["ha_independently_passed"] = bool(
        report["variants"]["HA"]["gate"]["passed"]
    )
    report["proof_queue_online_unlocked"] = report[
        "ha_independently_passed"
    ]
    report["on_failure"] = "fallback_p0"
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    print(str(target.resolve()))
    return 0


def _load(
    path: str,
    *,
    selected_hashes: set[str],
    expected_variant: str,
    expected_guidance_mode: str,
    expected_split_manifest_hash: str | None,
    expected_fold_by_hash: dict[str, int] | None,
) -> dict[str, dict]:
    rows = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        content_hash = str(row["instance_content_hash"])
        if content_hash not in selected_hashes:
            continue
        if str(row.get("experiment_variant") or "") != expected_variant:
            raise SystemExit(
                f"result variant mismatch in {path}: {content_hash}"
            )
        if str(row.get("guidance_mode") or "") != expected_guidance_mode:
            raise SystemExit(
                f"guidance mode mismatch in {path}: {content_hash}"
            )
        if expected_split_manifest_hash is not None:
            if str(row.get("split_manifest_hash") or "") != str(
                expected_split_manifest_hash
            ):
                raise SystemExit(
                    f"split manifest mismatch in {path}: {content_hash}"
                )
            if str(row.get("partition") or "") != "development":
                raise SystemExit(
                    f"non-development guided row in {path}: {content_hash}"
                )
            try:
                observed_fold = int(row["fold"])
            except (KeyError, TypeError, ValueError) as exc:
                raise SystemExit(
                    f"guided row has no valid fold in {path}: {content_hash}"
                ) from exc
            if (
                expected_fold_by_hash is None
                or observed_fold != expected_fold_by_hash[content_hash]
            ):
                raise SystemExit(
                    f"guided row fold mismatch in {path}: {content_hash}"
                )
            if not str(row.get("guidance_checkpoint_id") or ""):
                raise SystemExit(
                    f"guided row lacks checkpoint ID in {path}: {content_hash}"
                )
            if not str(row.get("guidance_model_kind") or ""):
                raise SystemExit(
                    f"guided row lacks model kind in {path}: {content_hash}"
                )
        if content_hash in rows:
            raise SystemExit(f"duplicate result row {content_hash} in {path}")
        rows[content_hash] = row
    if not rows:
        raise SystemExit(f"empty result ledger {path}")
    if expected_split_manifest_hash is not None:
        model_kinds = {
            str(row["guidance_model_kind"]) for row in rows.values()
        }
        if len(model_kinds) != 1:
            raise SystemExit(
                f"guided ledger mixes model rungs in {path}: "
                + ",".join(sorted(model_kinds))
            )
    return rows


def _evaluate(
    controls: dict[str, dict],
    guided: dict[str, dict],
    *,
    bootstrap_samples: int,
) -> dict:
    if set(controls) != set(guided):
        missing = sorted(set(controls).symmetric_difference(guided))
        raise SystemExit(
            "paired result ledgers differ: " + ",".join(missing[:10])
        )
    pairs = [(controls[key], guided[key]) for key in sorted(controls)]
    for control, row in pairs:
        if int(control["scale"]) != int(row["scale"]):
            raise SystemExit("paired result scale mismatch")
        if str(control.get("source_baseline_id") or "") != str(
            row.get("source_baseline_id") or ""
        ):
            raise SystemExit("paired result source baseline mismatch")
        if str(control.get("config_hash") or "") != str(
            row.get("config_hash") or ""
        ):
            raise SystemExit("paired result exact config mismatch")
    medium_pairs = [
        pair for pair in pairs if int(pair[0]["scale"]) in {20, 30}
    ]
    small_pairs = [
        pair for pair in pairs if int(pair[0]["scale"]) in {5, 10}
    ]
    if not medium_pairs or not small_pairs:
        raise SystemExit("Stage B requires paired 5/10 and 20/30 rows")
    medium_runtime = paired_runtime_summary(
        [float(control["cold_start_total_sec"]) for control, _ in medium_pairs],
        [float(row["cold_start_total_sec"]) for _, row in medium_pairs],
        bootstrap_samples=bootstrap_samples,
    )
    small_runtime = paired_runtime_summary(
        [float(control["cold_start_total_sec"]) for control, _ in small_pairs],
        [float(row["cold_start_total_sec"]) for _, row in small_pairs],
        bootstrap_samples=bootstrap_samples,
    )
    first_ratio_rows = [
        row
        for control, guided in medium_pairs
        for row in [_paired_first_addable_ratio(control, guided)]
        if row is not None
    ]
    first_ratio = (
        float("inf")
        if not first_ratio_rows
        else median(row["instance_p50_ratio"] for row in first_ratio_rows)
    )
    trajectory_rows = [
        context
        for control, row in medium_pairs
        for context in _matched_budget_rc(control, row)
    ]
    trajectory_by_instance = {}
    for row in trajectory_rows:
        trajectory_by_instance.setdefault(
            row["instance_content_hash"], []
        ).append(float(row["guided_minus_p0_best_rc"]))
    trajectory_instance_deltas = [
        mean(values) for values in trajectory_by_instance.values()
    ]
    equal_budget_improved = bool(
        trajectory_instance_deltas
        and mean(trajectory_instance_deltas) < 0.0
        and mean(
            value <= 0.0 for value in trajectory_instance_deltas
        )
        >= 0.5
    )
    control_duplicate_rate = _aggregate_duplicate_rate(
        control for control, _ in pairs
    )
    guided_duplicate_rate = _aggregate_duplicate_rate(
        row for _, row in pairs
    )
    bound_rows = [
        (
            control.get("rmp_bound_gain_per_pricing_second"),
            row.get("rmp_bound_gain_per_pricing_second"),
        )
        for control, row in medium_pairs
    ]
    bound_rows = [
        (float(left), float(right))
        for left, right in bound_rows
        if left is not None and right is not None
    ]
    bound_improved = bool(
        bound_rows
        and mean(right for _, right in bound_rows)
        > mean(left for left, _ in bound_rows)
    )
    safety = _safety_audit(pairs)
    gate = stage_b_gate(
        safety=safety,
        first_addable_negative_p50_ratio_20_30=first_ratio,
        equal_budget_best_rc_improved=equal_budget_improved,
        duplicate_negative_rate_delta=(
            guided_duplicate_rate - control_duplicate_rate
        ),
        rmp_bound_gain_per_pricing_second_improved=bound_improved,
        medium_runtime=medium_runtime,
        small_runtime=small_runtime,
    )
    return {
        "pair_count": len(pairs),
        "pair_count_by_scale": {
            str(scale): sum(
                int(control["scale"]) == scale for control, _ in pairs
            )
            for scale in (5, 10, 20, 30)
        },
        "safety": safety.__dict__,
        "first_addable_negative_p50_ratio_20_30": (
            first_ratio if isfinite(first_ratio) else None
        ),
        "first_addable_negative_context_count": {
            "paired_instances": len(first_ratio_rows),
            "paired_contexts": sum(
                int(row["paired_context_count"])
                for row in first_ratio_rows
            ),
        },
        "first_addable_negative_instance_rows": first_ratio_rows,
        "equal_budget_best_rc_improved": equal_budget_improved,
        "matched_budget_rc_rows": trajectory_rows,
        "duplicate_negative_rate": {
            "P0": control_duplicate_rate,
            "guided": guided_duplicate_rate,
            "delta": guided_duplicate_rate - control_duplicate_rate,
        },
        "rmp_bound_gain_per_pricing_second_improved": bound_improved,
        "medium_runtime": medium_runtime,
        "small_runtime": small_runtime,
        "guidance_total_wall_sec_sum": sum(
            float(row.get("guidance_total_wall_sec") or 0.0)
            for _, row in pairs
        ),
        "guidance_incremental_wall_sec_vs_p0_sum": sum(
            float(row.get("guidance_total_wall_sec") or 0.0)
            - float(control.get("guidance_total_wall_sec") or 0.0)
            for control, row in pairs
        ),
        "gate": gate,
    }


def _safety_audit(pairs: list[tuple[dict, dict]]) -> SafetyAudit:
    induced_drop = 0
    binding_mismatch = 0
    nonfinite = 0
    universe_mismatch = 0
    labels_dropped = False
    extra_incomplete = 0
    objective_mismatch = 0
    reduced_cost_mismatch = 0
    certificate_mismatch = 0
    for control, guided in pairs:
        safety = dict(guided.get("stage_b_safety") or {})
        induced_drop += int(
            safety.get("guidance_induced_permanent_drop") or 0
        )
        binding_mismatch += int(
            safety.get("binding_mismatch_accepted") or 0
        )
        nonfinite += int(safety.get("nonfinite_hint_accepted") or 0)
        universe_mismatch += int(
            safety.get("legal_universe_hash_mismatch") or 0
        )
        labels_dropped = labels_dropped or bool(
            safety.get("labels_dropped")
        )
        control_optimal = (
            control.get("algorithm_status") == "BPC_OPTIMAL"
            and bool(control.get("bpc_tree_optimal"))
        )
        guided_optimal = (
            guided.get("algorithm_status") == "BPC_OPTIMAL"
            and bool(guided.get("bpc_tree_optimal"))
        )
        if control_optimal and not guided_optimal:
            extra_incomplete += 1
        if control_optimal and guided_optimal:
            left = control.get("global_ub")
            right = guided.get("global_ub")
            if (
                left is None
                or right is None
                or abs(float(left) - float(right)) > 1.0e-7
            ):
                objective_mismatch += 1
            if bool(control.get("row_terminal")) != bool(
                guided.get("row_terminal")
            ):
                certificate_mismatch += 1
        if not bool(guided.get("redlines_zero")):
            reduced_cost_mismatch += 1
    return SafetyAudit(
        guidance_induced_permanent_drop=induced_drop,
        binding_mismatch_accepted=binding_mismatch,
        nonfinite_hint_accepted=nonfinite,
        legal_universe_hash_mismatch=universe_mismatch,
        labels_dropped=labels_dropped,
        extra_incomplete=extra_incomplete,
        objective_mismatch=objective_mismatch,
        reduced_cost_mismatch=reduced_cost_mismatch,
        certificate_mismatch=certificate_mismatch,
    )


def _aggregate_duplicate_rate(rows) -> float:
    duplicate = 0
    candidate = 0
    for row in rows:
        duplicate += int(row.get("duplicate_negative_count") or 0)
        candidate += int(row.get("candidate_negative_count") or 0)
    return 0.0 if candidate <= 0 else duplicate / candidate


def _matched_budget_rc(control: dict, guided: dict) -> list[dict]:
    control_trajectories = _trajectories_by_context(control)
    guided_trajectories = _trajectories_by_context(guided)
    rows = []
    for context_id in sorted(
        set(control_trajectories).intersection(guided_trajectories)
    ):
        control_points = control_trajectories[context_id]
        guided_points = guided_trajectories[context_id]
        if not control_points or not guided_points:
            continue
        budget = min(
            max(point[0] for point in control_points),
            max(point[0] for point in guided_points),
        )
        control_best = min(
            point[1] for point in control_points if point[0] <= budget
        )
        guided_best = min(
            point[1] for point in guided_points if point[0] <= budget
        )
        rows.append(
            {
                "instance_content_hash": control[
                    "instance_content_hash"
                ],
                "scale": int(control["scale"]),
                "context_id": context_id,
                "matched_pricing_budget_sec": budget,
                "p0_best_rc": control_best,
                "guided_best_rc": guided_best,
                "guided_minus_p0_best_rc": guided_best - control_best,
            }
        )
    return rows


def _paired_first_addable_ratio(
    control: dict, guided: dict
) -> dict | None:
    control_rows = {
        str(row["context_id"]): float(row["pricing_sec"])
        for row in control.get("first_addable_negative_by_context", ())
        if float(row["pricing_sec"]) > 0.0
    }
    guided_rows = {
        str(row["context_id"]): float(row["pricing_sec"])
        for row in guided.get("first_addable_negative_by_context", ())
        if float(row["pricing_sec"]) > 0.0
    }
    shared = sorted(set(control_rows).intersection(guided_rows))
    if not shared:
        return None
    ratios = [
        guided_rows[context_id] / control_rows[context_id]
        for context_id in shared
    ]
    return {
        "instance_content_hash": control["instance_content_hash"],
        "scale": int(control["scale"]),
        "paired_context_count": len(shared),
        "instance_p50_ratio": median(ratios),
    }


def _trajectories_by_context(
    row: dict,
) -> dict[str, list[tuple[float, float]]]:
    output = {}
    for index, trajectory in enumerate(
        row.get("equal_budget_best_rc_trajectories", ())
    ):
        if isinstance(trajectory, dict):
            context_id = str(
                trajectory.get("context_id") or f"legacy-{index}"
            )
            points = trajectory.get("points", ())
        else:
            context_id = f"legacy-{index}"
            points = trajectory
        output[context_id] = [
            (
                float(point["pricing_budget_sec"]),
                float(point["best_true_rc"]),
            )
            for point in points
            if float(point["pricing_budget_sec"]) >= 0.0
        ]
    return output


if __name__ == "__main__":
    raise SystemExit(main())
