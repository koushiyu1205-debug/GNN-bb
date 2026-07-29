#!/usr/bin/env python3
"""Matched E2E branch arms from one certified deep P0 tree snapshot."""

from __future__ import annotations

import argparse
import json
from math import isfinite
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from run_p0_no_task_wait_v3_branch_state_oracle import (  # noqa: E402
    BASELINE_ID,
    PROFILE_BY_SCALE,
    _arm_summary,
    _configure_environment,
    _development_hashes,
    _load_json,
    _sha256_json,
    _solver_binding,
    _tree_call,
    _write_json,
)
from run_p0v3_branch_parent_snapshot_e2e_oracle import (  # noqa: E402
    COLLECTION_SCHEMA_VERSION,
    _build_gold_report,
    _may_launch_new_arm,
    _parse_arm_order,
)
from lunar_ice_bpc.domain.scenario import (  # noqa: E402
    SERVICE_TIMING_POLICY_ID,
)
from lunar_ice_bpc.exact.core.data import (  # noqa: E402
    load_lunar_ice_data,
)
from lunar_ice_bpc.exact.core.journey import (  # noqa: E402
    journey_column_from_solution_payload,
)
from lunar_ice_bpc.guidance.branch_counterfactual_snapshot import (  # noqa: E402
    deep_target_node_exact_safe as _deep_target_node_exact_safe,
)


SNAPSHOT_SCHEMA_VERSION = (
    "lunar_ice_bpc.p0v3_branch_deep_parent_snapshot.v1"
)
ARM_BINDING_SCHEMA_VERSION = (
    "lunar_ice_bpc.p0v3_branch_deep_snapshot_arm_binding.v1"
)


def _arm_binding(
    *,
    snapshot_sha256: str,
    split_manifest_hash: str,
    solver_binding_hash: str,
    rank_index: int,
    wall_time_limit_sec: float,
    max_rounds: int,
    max_columns_per_round: int,
) -> dict:
    payload = {
        "schema_version": ARM_BINDING_SCHEMA_VERSION,
        "snapshot_sha256": str(snapshot_sha256),
        "split_manifest_hash": str(split_manifest_hash),
        "solver_binding_hash": str(solver_binding_hash),
        "rank_index": int(rank_index),
        "wall_time_limit_sec": float(wall_time_limit_sec),
        "max_rounds": int(max_rounds),
        "max_columns_per_round": int(max_columns_per_round),
    }
    payload["binding_hash"] = _sha256_json(payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", required=True)
    parser.add_argument("--deep-parent-snapshot", required=True)
    parser.add_argument("--split-manifest", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--tree-wall-time-limit-sec",
        type=float,
        default=600.0,
    )
    parser.add_argument("--tree-max-rounds", type=int, default=16)
    parser.add_argument(
        "--tree-max-columns-per-round",
        type=int,
        default=128,
    )
    parser.add_argument(
        "--emulated-guidance-lifecycle-overhead-sec",
        type=float,
        default=0.02,
    )
    parser.add_argument(
        "--arm-order",
        type=_parse_arm_order,
        default=(0, 2, 1),
    )
    parser.add_argument(
        "--max-new-arms-per-process",
        type=int,
        default=1,
    )
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    if (
        not isfinite(float(args.tree_wall_time_limit_sec))
        or float(args.tree_wall_time_limit_sec) <= 0.0
    ):
        raise SystemExit("tree wall-time limit must be positive")
    if int(args.max_new_arms_per_process) < 0:
        raise SystemExit("max new arms per process cannot be negative")

    instance_path = (ROOT / args.instance).resolve()
    snapshot_path = (ROOT / args.deep_parent_snapshot).resolve()
    split_path = (ROOT / args.split_manifest).resolve()
    output_dir = (ROOT / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    data = load_lunar_ice_data(_load_json(instance_path))
    manifest = _load_json(split_path)
    split_manifest_hash = str(
        manifest.get("manifest_hash") or _sha256_json(manifest)
    )
    if data.instance_content_hash not in _development_hashes(manifest):
        raise SystemExit("deep-snapshot oracle accepts development only")
    if data.service_timing_policy_id != SERVICE_TIMING_POLICY_ID:
        raise SystemExit("instance service-timing policy mismatch")
    profile = PROFILE_BY_SCALE.get(int(data.scale))
    if profile is None:
        raise SystemExit("deep-snapshot oracle accepts scale20/30")
    _configure_environment(scale=int(data.scale), profile=profile)
    solver_binding = _solver_binding(
        data=data,
        profile=profile,
        tree_max_rounds=int(args.tree_max_rounds),
        tree_max_columns_per_round=int(
            args.tree_max_columns_per_round
        ),
    )

    snapshot = _load_json(snapshot_path)
    snapshot_without_hash = {
        key: value
        for key, value in snapshot.items()
        if key != "snapshot_sha256"
    }
    snapshot_sha256 = str(snapshot.get("snapshot_sha256") or "")
    target_node = dict(snapshot.get("target_node") or {})
    if (
        str(snapshot.get("schema_version") or "")
        != SNAPSHOT_SCHEMA_VERSION
        or snapshot.get("instance_content_hash")
        != data.instance_content_hash
        or str(snapshot.get("baseline_id") or "") != BASELINE_ID
        or str(snapshot.get("split_manifest_hash") or "")
        != split_manifest_hash
        or str(snapshot.get("solver_binding_hash") or "")
        != str(solver_binding["binding_hash"])
        or snapshot_sha256 != _sha256_json(snapshot_without_hash)
        or not _deep_target_node_exact_safe(target_node)
        or int(snapshot.get("target_depth") or 0) <= 0
    ):
        raise SystemExit("deep parent snapshot binding/exactness mismatch")

    global_payload = list(snapshot.get("global_columns") or ())
    target_active_payload = list(
        snapshot.get("target_active_columns") or ()
    )
    incumbent_payload = list(snapshot.get("incumbent_columns") or ())
    if (
        len(global_payload)
        != int(snapshot.get("global_column_count") or -1)
        or str(snapshot.get("global_columns_sha256") or "")
        != _sha256_json(global_payload)
        or len(target_active_payload)
        != int(snapshot.get("target_active_column_count") or -1)
        or str(snapshot.get("target_active_columns_sha256") or "")
        != _sha256_json(target_active_payload)
        or str(snapshot.get("incumbent_columns_sha256") or "")
        != _sha256_json(incumbent_payload)
    ):
        raise SystemExit("deep parent snapshot column binding mismatch")
    global_columns = tuple(
        journey_column_from_solution_payload(data, row)
        for row in global_payload
    )
    incumbent_columns = tuple(
        journey_column_from_solution_payload(data, row)
        for row in incumbent_payload
    )
    if not global_columns:
        raise SystemExit("deep parent snapshot has no global columns")

    target_path = tuple(
        str(value)
        for value in snapshot.get("target_path_signature") or ()
    )
    target_node_id = str(snapshot.get("target_node_id") or "")
    certified_tree_state = {
        "target_node": target_node,
        "processed_nodes": list(snapshot.get("processed_nodes") or ()),
        "open_nodes_before_target_branch": list(
            snapshot.get("open_nodes_before_target_branch") or ()
        ),
        "next_node_index": int(snapshot["next_node_index"]),
        "incumbent_objective": snapshot.get("incumbent_objective"),
        "incumbent_source": str(
            snapshot.get("incumbent_source") or ""
        ),
        "_incumbent_columns": incumbent_columns,
    }

    summaries: dict[int, dict] = {}
    new_arm_count = 0
    for rank in args.arm_order:
        binding = _arm_binding(
            snapshot_sha256=snapshot_sha256,
            split_manifest_hash=split_manifest_hash,
            solver_binding_hash=str(solver_binding["binding_hash"]),
            rank_index=rank,
            wall_time_limit_sec=float(
                args.tree_wall_time_limit_sec
            ),
            max_rounds=int(args.tree_max_rounds),
            max_columns_per_round=int(
                args.tree_max_columns_per_round
            ),
        )
        tree_path = output_dir / f"arm_rank{rank}_tree.json"
        summary_path = output_dir / f"arm_rank{rank}_summary.json"
        if args.resume and tree_path.is_file() and summary_path.is_file():
            tree = _load_json(tree_path)
            summary = _load_json(summary_path)
            if (
                str(summary.get("arm_binding_hash") or "")
                != binding["binding_hash"]
                or str(summary.get("tree_result_sha256") or "")
                != _sha256_json(tree)
            ):
                raise SystemExit(
                    f"persisted rank{rank} arm binding mismatch"
                )
            summaries[rank] = summary
            continue
        if not _may_launch_new_arm(
            new_arm_count=new_arm_count,
            max_new_arms_per_process=int(
                args.max_new_arms_per_process
            ),
        ):
            continue

        tree, tree_wall = _tree_call(
            data=data,
            active_columns=global_columns,
            profile=profile,
            wall_time_limit_sec=float(
                args.tree_wall_time_limit_sec
            ),
            max_rounds=int(args.tree_max_rounds),
            max_columns_per_round=int(
                args.tree_max_columns_per_round
            ),
            rank_by_path={target_path: int(rank)},
            certified_tree_state=certified_tree_state,
        )
        _write_json(tree_path, tree)
        summary = _arm_summary(
            result=tree,
            tree_wall_sec=tree_wall,
            root_wall_sec=0.0,
            lifecycle_overhead_sec=(
                0.0
                if rank == 0
                else float(
                    args.emulated_guidance_lifecycle_overhead_sec
                )
            ),
            target_path=target_path,
            requested_rank=rank,
        )
        summary.update(
            {
                "arm_binding_hash": binding["binding_hash"],
                "parent_source_sha256": snapshot_sha256,
                "matched_scope": (
                    "post_certified_deep_parent_continuation"
                ),
                "certified_parent_pricing_reused": True,
                "descendant_pricing_certificate_reused": False,
            }
        )
        _write_json(summary_path, summary)
        summaries[rank] = summary
        new_arm_count += 1

    missing = sorted({0, 1, 2}.difference(summaries))
    if missing:
        partial_report = None
        if 0 in summaries:
            partial_report = _build_gold_report(
                data=data,
                split_manifest_hash=split_manifest_hash,
                parent_source_sha256=snapshot_sha256,
                control_tree_sha256=snapshot_sha256,
                summaries=summaries,
                target_node_id=target_node_id,
                target_path_signature=target_path,
                target_depth=int(snapshot["target_depth"]),
                matched_scope=(
                    "post_certified_deep_parent_continuation"
                ),
            )
            _write_json(
                output_dir / "partial_state_oracle_report.json",
                partial_report,
            )
        status = {
            "schema_version": COLLECTION_SCHEMA_VERSION,
            "development_only": True,
            "deployable": False,
            "training_authorized": False,
            "instance_id": data.instance_id,
            "instance_content_hash": data.instance_content_hash,
            "target_node_id": target_node_id,
            "target_path_hash": snapshot["target_path_hash"],
            "completed_rank_indices": sorted(summaries),
            "missing_rank_indices": missing,
            "trusted_censored_pairwise_preference_count": (
                0
                if partial_report is None
                else len(
                    partial_report["state_reports"][0][
                        "trusted_censored_pairwise_preferences"
                    ]
                )
            ),
            "status": "PAUSED_PROCESS_ARM_BUDGET",
            "resume_required": True,
        }
        _write_json(output_dir / "collection_status.json", status)
        print(json.dumps(status, sort_keys=True))
        return 0

    report = _build_gold_report(
        data=data,
        split_manifest_hash=split_manifest_hash,
        parent_source_sha256=snapshot_sha256,
        control_tree_sha256=snapshot_sha256,
        summaries=summaries,
        target_node_id=target_node_id,
        target_path_signature=target_path,
        target_depth=int(snapshot["target_depth"]),
        matched_scope="post_certified_deep_parent_continuation",
    )
    _write_json(output_dir / "state_oracle_report.json", report)
    partial_path = output_dir / "partial_state_oracle_report.json"
    if partial_path.exists():
        partial_path.unlink()
    state = report["state_reports"][0]
    status = {
        "schema_version": COLLECTION_SCHEMA_VERSION,
        "development_only": True,
        "deployable": False,
        "training_authorized": False,
        "instance_id": data.instance_id,
        "instance_content_hash": data.instance_content_hash,
        "target_node_id": target_node_id,
        "target_path_hash": snapshot["target_path_hash"],
        "completed_rank_indices": [0, 1, 2],
        "missing_rank_indices": [],
        "complete_matched_e2e_gold": bool(
            state["complete_matched_e2e_gold"]
        ),
        "oracle_selected_rank_index": state[
            "oracle_selected_rank_index"
        ],
        "oracle_net_gain_sec": state["oracle_net_gain_sec"],
        "status": "COMPLETE",
        "resume_required": False,
    }
    _write_json(output_dir / "collection_status.json", status)
    print(json.dumps(status, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
