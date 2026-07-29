#!/usr/bin/env python3
"""Audit the two development-only GAT landing-point oracle gates.

This script does not train or deploy a model.  It joins the frozen development
split with the existing P0 tree artifacts, checks complete counterfactual
coverage for every exact/actionable scale-20/30 instance, and summarizes the
dual-center and top-3 branch action spaces separately.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import statistics
from pathlib import Path
from typing import Any, Iterable, Mapping


PRIMARY_BRANCH_DIRECTORY_RE = re.compile(r"^scale(?P<scale>20|30)_(?P<index>\d{3})$")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _round(value: float, digits: int = 9) -> float:
    return round(float(value), digits)


def _percentile(values: list[float], quantile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = quantile * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def _bootstrap_pooled_oracle_gain(
    rows: list[dict[str, Any]],
    *,
    seed: int = 20260725,
    samples: int = 10_000,
) -> dict[str, Any]:
    if not rows:
        return {
            "method": "instance_bootstrap",
            "sample_count": 0,
            "replicate_count": samples,
            "ci95": [0.0, 0.0],
        }
    rng = random.Random(seed)
    estimates: list[float] = []
    for _ in range(samples):
        draw = [rows[rng.randrange(len(rows))] for _ in rows]
        p0_total = sum(float(row["p0_wall_sec"]) for row in draw)
        oracle_total = sum(float(row["oracle_wall_sec"]) for row in draw)
        estimates.append(1.0 - oracle_total / p0_total)
    return {
        "method": "paired_instance_bootstrap_over_measured_fixed_policy_arms",
        "sample_count": len(rows),
        "replicate_count": samples,
        "seed": seed,
        "ci95": [
            _round(_percentile(estimates, 0.025)),
            _round(_percentile(estimates, 0.975)),
        ],
        "warning": (
            "This interval covers instance sampling only; it does not estimate "
            "within-instance runtime noise or GAT realizability."
        ),
    }


def _summarize_branch_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    p0_total = sum(float(row["p0_wall_sec"]) for row in rows)
    oracle_total = sum(float(row["oracle_wall_sec"]) for row in rows)
    fixed_rank_1_total = sum(float(row["rank_wall_sec"]["1"]) for row in rows)
    fixed_rank_2_total = sum(float(row["rank_wall_sec"]["2"]) for row in rows)
    gains = [float(row["oracle_net_gain_ratio"]) for row in rows]
    return {
        "instance_count": len(rows),
        "positive_instance_count": sum(gain > 1e-12 for gain in gains),
        "no_benefit_instance_count": sum(gain <= 1e-12 for gain in gains),
        "p0_total_wall_sec": _round(p0_total, 6),
        "instance_oracle_total_wall_sec": _round(oracle_total, 6),
        "instance_oracle_pooled_net_gain_ratio": _round(
            1.0 - oracle_total / p0_total if p0_total else 0.0
        ),
        "median_instance_oracle_net_gain_ratio": _round(
            statistics.median(gains) if gains else 0.0
        ),
        "fixed_rank_1_total_wall_sec": _round(fixed_rank_1_total, 6),
        "fixed_rank_1_vs_p0_ratio": _round(
            fixed_rank_1_total / p0_total if p0_total else 1.0
        ),
        "fixed_rank_2_total_wall_sec": _round(fixed_rank_2_total, 6),
        "fixed_rank_2_vs_p0_ratio": _round(
            fixed_rank_2_total / p0_total if p0_total else 1.0
        ),
        "oracle_selected_rank_counts": {
            str(rank): sum(int(row["oracle_selected_rank_index"]) == rank for row in rows)
            for rank in (0, 1, 2)
        },
        "instance_bootstrap": _bootstrap_pooled_oracle_gain(rows),
    }


def _tree_artifacts_by_instance(
    b0_root: Path,
) -> dict[str, tuple[Path, dict[str, Any]]]:
    artifacts: dict[str, tuple[Path, dict[str, Any]]] = {}
    for path in sorted(b0_root.glob("scale_*/instance_*/**/tree_closure_*.json")):
        payload = _load_json(path)
        instance_id = str(payload.get("instance_id", ""))
        if not instance_id:
            continue
        if instance_id in artifacts:
            raise ValueError(f"duplicate B0 tree artifact for {instance_id}")
        artifacts[instance_id] = (path, payload)
    return artifacts


def _primary_branch_reports(
    branch_root: Path,
) -> dict[str, tuple[Path, dict[str, Any]]]:
    reports: dict[str, tuple[Path, dict[str, Any]]] = {}
    for path in sorted(branch_root.glob("*/branch_top3_oracle_report.json")):
        if PRIMARY_BRANCH_DIRECTORY_RE.fullmatch(path.parent.name) is None:
            continue
        payload = _load_json(path)
        instance_id = str(payload.get("instance_id", ""))
        if not instance_id:
            raise ValueError(f"missing instance_id: {path}")
        if instance_id in reports:
            raise ValueError(f"duplicate primary branch report for {instance_id}")
        reports[instance_id] = (path, payload)
    return reports


def _arm_by_rank(report: Mapping[str, Any]) -> dict[int, Mapping[str, Any]]:
    arms = report.get("arms", [])
    if not isinstance(arms, list):
        raise ValueError("branch report arms must be a list")
    by_rank = {int(arm["rank_index"]): arm for arm in arms}
    if set(by_rank) != {0, 1, 2}:
        raise ValueError(f"expected branch ranks 0/1/2, got {sorted(by_rank)}")
    return by_rank


def _dual_pair(
    *,
    scale: int,
    control_path: Path,
    oracle_path: Path,
) -> dict[str, Any]:
    control = _load_json(control_path)
    oracle = _load_json(oracle_path)
    control_wall = float(control["net_wall_with_inference_sec"])
    oracle_wall = float(oracle["net_wall_with_inference_sec"])
    same_instance = (
        control.get("instance_content_hash") == oracle.get("instance_content_hash")
        and control.get("instance_id") == oracle.get("instance_id")
    )
    same_bound = abs(
        float(control.get("root_lp_bound", float("nan")))
        - float(oracle.get("root_lp_bound", float("nan")))
    ) <= 1e-8
    exact_safe = bool(control.get("exact_safe")) and bool(oracle.get("exact_safe"))
    return {
        "scale": scale,
        "instance_id": control.get("instance_id"),
        "control_path": str(control_path),
        "oracle_path": str(oracle_path),
        "same_instance": same_instance,
        "same_root_lp_bound": same_bound,
        "exact_safe": exact_safe,
        "p0_wall_sec": _round(control_wall, 6),
        "adaptive_oracle_wall_sec": _round(oracle_wall, 6),
        "adaptive_oracle_vs_p0_ratio": _round(oracle_wall / control_wall),
        "adaptive_oracle_net_gain_ratio": _round(1.0 - oracle_wall / control_wall),
        "p0_pricing_round_count": int(control["pricing_round_count"]),
        "adaptive_oracle_pricing_round_count": int(oracle["pricing_round_count"]),
        "adaptive_oracle_active_round_count": int(
            oracle.get("oracle_active_round_count", 0)
        ),
    }


def _development_rows(manifest: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
    rows = manifest.get("development", [])
    if not isinstance(rows, list):
        raise ValueError("split manifest development must be a list")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--split-manifest",
        type=Path,
        default=Path("data/gat_p0v2/p0v2_gat_split_manifest.json"),
    )
    parser.add_argument(
        "--b0-root",
        type=Path,
        default=Path("runs/p0v2_gat_binding_v2_b0_development"),
    )
    parser.add_argument(
        "--branch-root",
        type=Path,
        default=Path(
            "runs/p0v2_gat_landing_oracle_validation_20260725/branch_top3"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "runs/p0v2_gat_landing_oracle_validation_20260725/"
            "two_landing_oracle_audit.json"
        ),
    )
    args = parser.parse_args()

    manifest = _load_json(args.split_manifest)
    manifest_rows = {
        str(row["instance_id"]): row
        for row in _development_rows(manifest)
        if int(row["scale"]) in {20, 30}
    }
    tree_artifacts = _tree_artifacts_by_instance(args.b0_root)
    branch_reports = _primary_branch_reports(args.branch_root)

    opportunity_rows: list[dict[str, Any]] = []
    exact_actionable_ids: set[str] = set()
    for instance_id, manifest_row in sorted(manifest_rows.items()):
        scale = int(manifest_row["scale"])
        artifact_entry = tree_artifacts.get(instance_id)
        if artifact_entry is None:
            opportunity_rows.append(
                {
                    "instance_id": instance_id,
                    "scale": scale,
                    "artifact_found": False,
                    "exact": False,
                    "actionable": False,
                }
            )
            continue
        artifact_path, artifact = artifact_entry
        exact = (
            artifact.get("algorithm_status") == "BPC_OPTIMAL"
            and artifact.get("certificate_scope") == "BPC_TREE_OPTIMAL"
            and int(artifact.get("incomplete_node_count", 0)) == 0
        )
        actionable = int(artifact.get("branch_count", 0)) > 0
        if exact and actionable:
            exact_actionable_ids.add(instance_id)
        opportunity_rows.append(
            {
                "instance_id": instance_id,
                "scale": scale,
                "artifact_found": True,
                "artifact_path": str(artifact_path),
                "exact": exact,
                "actionable": actionable,
                "branch_count": int(artifact.get("branch_count", 0)),
                "expanded_node_count": int(artifact.get("expanded_node_count", 0)),
            }
        )

    census_by_scale: dict[str, Any] = {}
    for scale in (20, 30):
        rows = [row for row in opportunity_rows if row["scale"] == scale]
        exact_rows = [row for row in rows if row["exact"]]
        census_by_scale[str(scale)] = {
            "manifest_instance_count": len(rows),
            "tree_artifact_count": sum(row["artifact_found"] for row in rows),
            "exact_tree_count": len(exact_rows),
            "exact_actionable_instance_count": sum(
                row["exact"] and row["actionable"] for row in rows
            ),
            "exact_actionable_rate": _round(
                sum(row["exact"] and row["actionable"] for row in rows)
                / len(exact_rows)
                if exact_rows
                else 0.0
            ),
            "all_artifact_actionable_instance_count": sum(
                row["artifact_found"] and row["actionable"] for row in rows
            ),
        }

    branch_rows: list[dict[str, Any]] = []
    missing_reports = sorted(exact_actionable_ids - set(branch_reports))
    nonactionable_report_ids = sorted(set(branch_reports) - exact_actionable_ids)
    nonactionable_bypass_reports: list[dict[str, Any]] = []
    invalid_extra_reports: list[str] = []
    for instance_id in nonactionable_report_ids:
        report_path, report = branch_reports[instance_id]
        if (
            instance_id in manifest_rows
            and report.get("actionable") is False
            and report.get("p0_control_exact_safe") is True
            and report.get("all_completed_arm_universes_safe") is True
        ):
            nonactionable_bypass_reports.append(
                {
                    "instance_id": instance_id,
                    "scale": int(report["scale"]),
                    "report_path": str(report_path),
                    "actionable": False,
                    "p0_control_exact_safe": True,
                    "universe_safe": True,
                }
            )
        else:
            invalid_extra_reports.append(instance_id)
    for instance_id in sorted(exact_actionable_ids & set(branch_reports)):
        report_path, report = branch_reports[instance_id]
        manifest_row = manifest_rows[instance_id]
        arms = _arm_by_rank(report)
        rank_wall_sec = {
            str(rank): float(arms[rank]["matched_end_to_end_wall_sec"])
            for rank in (0, 1, 2)
        }
        oracle_rank = min((0, 1, 2), key=lambda rank: rank_wall_sec[str(rank)])
        p0_wall = rank_wall_sec["0"]
        oracle_wall = rank_wall_sec[str(oracle_rank)]
        all_arm_exact = all(bool(arms[rank]["exact_safe"]) for rank in (0, 1, 2))
        branch_rows.append(
            {
                "instance_id": instance_id,
                "instance_content_hash": report["instance_content_hash"],
                "manifest_content_hash": manifest_row["instance_content_hash"],
                "content_hash_matches_manifest": (
                    report["instance_content_hash"]
                    == manifest_row["instance_content_hash"]
                ),
                "scale": int(report["scale"]),
                "report_path": str(report_path),
                "all_arm_exact_safe": all_arm_exact,
                "all_exact_objectives_equal": bool(
                    report["all_exact_objectives_equal"]
                ),
                "all_completed_arm_universes_safe": bool(
                    report["all_completed_arm_universes_safe"]
                ),
                "rank_wall_sec": {
                    rank: _round(wall, 6) for rank, wall in rank_wall_sec.items()
                },
                "p0_wall_sec": _round(p0_wall, 6),
                "oracle_wall_sec": _round(oracle_wall, 6),
                "oracle_selected_rank_index": oracle_rank,
                "oracle_net_gain_ratio": _round(
                    1.0 - oracle_wall / p0_wall if p0_wall else 0.0
                ),
            }
        )

    branch_safety_passed = (
        not missing_reports
        and not invalid_extra_reports
        and all(
            row["all_arm_exact_safe"]
            and row["all_exact_objectives_equal"]
            and row["all_completed_arm_universes_safe"]
            and row["content_hash_matches_manifest"]
            for row in branch_rows
        )
    )
    branch_by_scale = {
        str(scale): _summarize_branch_rows(
            [row for row in branch_rows if row["scale"] == scale]
        )
        for scale in (20, 30)
    }
    branch_overall = _summarize_branch_rows(branch_rows)
    branch_action_space_validated = (
        branch_safety_passed
        and not missing_reports
        and branch_overall["instance_oracle_pooled_net_gain_ratio"] >= 0.02
        and branch_by_scale["20"]["positive_instance_count"] >= 2
        and branch_by_scale["30"]["positive_instance_count"] >= 1
    )

    dual_rows = [
        _dual_pair(
            scale=20,
            control_path=Path(
                "runs/p0v2_oracle_dual_center_root_gate_20260725/scale20_043/"
                "p0_exact_first_prefix_collected.json"
            ),
            oracle_path=Path(
                "runs/p0v2_gat_landing_oracle_validation_20260725/dual_center/"
                "scale20_043/oracle_ascg_adaptive.json"
            ),
        ),
        _dual_pair(
            scale=30,
            control_path=Path(
                "runs/p0v2_oracle_dual_center_root_gate_20260725/scale30_017/"
                "p0_exact_first_summary.json"
            ),
            oracle_path=Path(
                "runs/p0v2_gat_landing_oracle_validation_20260725/dual_center/"
                "scale30_017/oracle_ascg_adaptive.json"
            ),
        ),
    ]
    dual_p0_total = sum(float(row["p0_wall_sec"]) for row in dual_rows)
    dual_oracle_total = sum(
        float(row["adaptive_oracle_wall_sec"]) for row in dual_rows
    )
    dual_safety_passed = all(
        row["same_instance"] and row["same_root_lp_bound"] and row["exact_safe"]
        for row in dual_rows
    )
    dual_action_space_validated = (
        dual_safety_passed
        and all(float(row["adaptive_oracle_net_gain_ratio"]) > 0.0 for row in dual_rows)
        and dual_oracle_total < dual_p0_total
    )

    payload = {
        "schema_version": "lunar_ice_bpc.gat_two_landing_oracle_audit.v1",
        "development_only": True,
        "deployable": False,
        "split_manifest": str(args.split_manifest),
        "split_manifest_audit_passed": bool(manifest["audit"]["passed"]),
        "opportunity_census": {
            "by_scale": census_by_scale,
            "rows": opportunity_rows,
        },
        "dual_center": {
            "method": (
                "future-true-dual center with adaptive ASCG penalty update; "
                "strictly stronger information than a trainable GAT"
            ),
            "rows": dual_rows,
            "safety_passed": dual_safety_passed,
            "p0_total_wall_sec": _round(dual_p0_total, 6),
            "adaptive_oracle_total_wall_sec": _round(dual_oracle_total, 6),
            "adaptive_oracle_vs_p0_ratio": _round(
                dual_oracle_total / dual_p0_total
            ),
            "action_space_validated": dual_action_space_validated,
            "training_authorized": False,
            "decision": (
                "STOP_DUAL_CENTER_STABILIZATION"
                if not dual_action_space_validated
                else "COLLECT_MORE_BEFORE_TRAINING"
            ),
        },
        "branch_top3": {
            "method": (
                "same-root fixed rank-0/1/2 counterfactual tree closures over "
                "the unchanged P0 legal shortlist"
            ),
            "exact_actionable_instance_count": len(exact_actionable_ids),
            "primary_report_count": len(branch_reports),
            "covered_exact_actionable_instance_count": len(branch_rows),
            "missing_exact_actionable_reports": missing_reports,
            "nonactionable_bypass_reports": nonactionable_bypass_reports,
            "invalid_extra_primary_reports": invalid_extra_reports,
            "safety_passed": branch_safety_passed,
            "rows": branch_rows,
            "by_scale": branch_by_scale,
            "overall": branch_overall,
            "action_space_validated": branch_action_space_validated,
            "counterfactual_collection_authorized": branch_action_space_validated,
            "linear_baseline_authorized": branch_action_space_validated,
            "gat_training_authorized": False,
            "gat_training_blocker": (
                "Only instance-level fixed-policy trajectories are available; "
                "state-local labels, abstention targets, grouped validation, "
                "and a linear-ranker comparison are still required."
            ),
            "decision": (
                "VALIDATE_BRANCH_ACTION_SPACE_COLLECT_STATE_LOCAL_LABELS"
                if branch_action_space_validated
                else "STOP_BRANCH_TOP3"
            ),
        },
        "final_decision": {
            "dual_center": (
                "STOP" if not dual_action_space_validated else "NOT_YET_PROVEN"
            ),
            "branch_top3": (
                "ACTION_SPACE_VALIDATED_MODEL_NOT_YET_VALIDATED"
                if branch_action_space_validated
                else "STOP"
            ),
            "production_default_unchanged": True,
        },
    }
    _write_json(args.output, payload)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "dual_center": payload["final_decision"]["dual_center"],
                "branch_top3": payload["final_decision"]["branch_top3"],
                "branch_exact_actionable_coverage": (
                    f"{len(branch_rows)}/{len(exact_actionable_ids)}"
                ),
                "branch_oracle_pooled_gain_ratio": branch_overall[
                    "instance_oracle_pooled_net_gain_ratio"
                ],
                "branch_fixed_rank_1_vs_p0_ratio": branch_overall[
                    "fixed_rank_1_vs_p0_ratio"
                ],
                "branch_fixed_rank_2_vs_p0_ratio": branch_overall[
                    "fixed_rank_2_vs_p0_ratio"
                ],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
