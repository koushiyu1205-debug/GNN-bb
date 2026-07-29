#!/usr/bin/env python3
"""Matched E2E branch arms from one certified P0 parent snapshot.

The runner is development-only.  It reuses no pricing certificate below the
frozen parent: only the already-certified parent node is accepted, one legal
top-3 pair is selected, and both child subtrees run the normal exact BPC path.
"""

from __future__ import annotations

import argparse
import json
from math import isfinite
from itertools import combinations
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from run_p0_no_task_wait_v3_branch_child_trajectory import (  # noqa: E402
    _bind_exact_opportunity_control,
    _node_probe_exact_safe,
)
from run_p0_no_task_wait_v3_branch_state_oracle import (  # noqa: E402
    BASELINE_ID,
    PROFILE_BY_SCALE,
    _arm_summary,
    _candidate_id,
    _configure_environment,
    _development_hashes,
    _load_json,
    _path_hash,
    _sha256_json,
    _solver_binding,
    _tree_call,
    _tree_exact_safe,
    _universe_safe,
    _write_json,
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
from lunar_ice_bpc.exact.bpc.guidance.contracts import (  # noqa: E402
    canonical_universe_hash,
)


SCHEMA_VERSION = (
    "lunar_ice_bpc.no_task_wait_v3_branch_state_oracle.v2"
)
COLLECTION_SCHEMA_VERSION = (
    "lunar_ice_bpc.p0v3_branch_parent_snapshot_e2e_collection.v1"
)
OBJECTIVE_TOLERANCE = 5.0e-6


def _public_node_payload(node: dict) -> dict:
    payload = {
        key: value
        for key, value in node.items()
        if not str(key).startswith("_")
    }
    integer_incumbent = payload.get("integer_incumbent")
    if isinstance(integer_incumbent, dict):
        payload["integer_incumbent"] = {
            key: value
            for key, value in integer_incumbent.items()
            if not str(key).startswith("_")
        }
    return payload


def _queued_node_payload(queued) -> dict:
    return {
        "node_id": str(queued.node_id),
        "parent_node_id": (
            None
            if queued.parent_node_id is None
            else str(queued.parent_node_id)
        ),
        "depth": int(queued.depth),
        "branch_context": queued.context.to_payload(),
        "branch_pair": queued.branch_pair,
        "branch_sense": queued.branch_sense,
        "inherited_lower_bound": queued.inherited_lower_bound,
        "cut_context": queued.cut_context.to_payload(),
        "cut_lineage": queued.cut_lineage.to_payload(),
    }


def _deep_snapshot_writer(
    *,
    data,
    destination: Path,
    parent_source_sha256: str,
    control_tree_sha256: str,
    split_manifest_hash: str,
    solver_binding_hash: str,
):
    destination.mkdir(parents=True, exist_ok=True)

    def write(runtime: dict) -> None:
        target = _public_node_payload(
            dict(runtime.get("target_node") or {})
        )
        path_signature = tuple(
            str(value)
            for value in target.get(
                "development_branch_path_signature"
            )
            or ()
        )
        global_columns = tuple(runtime.get("global_columns") or ())
        global_payload = [
            column.to_solution_payload(
                vehicle_id=f"deep_snapshot_column_{index:06d}"
            )
            for index, column in enumerate(global_columns, start=1)
        ]
        target_active_payload = [
            column.to_solution_payload(
                vehicle_id=f"deep_snapshot_target_{index:06d}"
            )
            for index, column in enumerate(
                tuple(runtime.get("target_active_columns") or ()),
                start=1,
            )
        ]
        incumbent_payload = [
            column.to_solution_payload(
                vehicle_id=f"deep_snapshot_incumbent_{index:06d}"
            )
            for index, column in enumerate(
                tuple(runtime.get("incumbent_columns") or ()),
                start=1,
            )
        ]
        payload = {
            "schema_version": (
                "lunar_ice_bpc.p0v3_branch_deep_parent_snapshot.v1"
            ),
            "development_only": True,
            "deployable": False,
            "training_authorized": False,
            "instance_id": data.instance_id,
            "instance_content_hash": data.instance_content_hash,
            "scale": int(data.scale),
            "baseline_id": BASELINE_ID,
            "parent_source_sha256": str(parent_source_sha256),
            "control_tree_sha256": str(control_tree_sha256),
            "split_manifest_hash": str(split_manifest_hash),
            "solver_binding_hash": str(solver_binding_hash),
            "target_node": target,
            "target_node_id": str(target.get("node_id") or ""),
            "target_depth": int(target.get("depth") or 0),
            "target_path_signature": list(path_signature),
            "target_path_hash": _path_hash(path_signature),
            "processed_nodes": [
                _public_node_payload(dict(row))
                for row in runtime.get("processed_nodes") or ()
            ],
            "open_nodes_before_target_branch": [
                _queued_node_payload(row)
                for row in runtime.get(
                    "open_nodes_before_target_branch"
                )
                or ()
            ],
            "global_columns": global_payload,
            "global_column_count": len(global_payload),
            "global_columns_sha256": _sha256_json(global_payload),
            "target_active_columns": target_active_payload,
            "target_active_column_count": len(
                target_active_payload
            ),
            "target_active_columns_sha256": _sha256_json(
                target_active_payload
            ),
            "incumbent_objective": runtime.get(
                "incumbent_objective"
            ),
            "incumbent_source": str(
                runtime.get("incumbent_source") or ""
            ),
            "incumbent_columns": incumbent_payload,
            "incumbent_columns_sha256": _sha256_json(
                incumbent_payload
            ),
            "next_node_index": int(runtime["next_node_index"]),
            "active_live_policy": runtime[
                "active_live_policy"
            ].to_payload(),
        }
        payload["snapshot_sha256"] = _sha256_json(payload)
        target_path = destination / (
            f"depth{payload['target_depth']:02d}_"
            f"{payload['target_node_id']}_"
            f"{payload['target_path_hash'][:12]}.json"
        )
        _write_json(target_path, payload)

    return write


def _parse_arm_order(value: str) -> tuple[int, int, int]:
    try:
        order = tuple(int(part.strip()) for part in value.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "arm order must be a comma-separated permutation of 0,1,2"
        ) from exc
    if len(order) != 3 or set(order) != {0, 1, 2}:
        raise argparse.ArgumentTypeError(
            "arm order must be a comma-separated permutation of 0,1,2"
        )
    return order


def _may_launch_new_arm(
    *, new_arm_count: int, max_new_arms_per_process: int
) -> bool:
    if int(new_arm_count) < 0 or int(max_new_arms_per_process) < 0:
        raise ValueError("arm counts cannot be negative")
    return int(new_arm_count) < int(max_new_arms_per_process)


def _arm_binding(
    *,
    parent_source_sha256: str,
    control_tree_sha256: str,
    split_manifest_hash: str,
    solver_binding_hash: str,
    rank_index: int,
    wall_time_limit_sec: float,
    max_rounds: int,
    max_columns_per_round: int,
) -> dict:
    payload = {
        "schema_version": (
            "lunar_ice_bpc.p0v3_branch_parent_snapshot_arm_binding.v1"
        ),
        "parent_source_sha256": str(parent_source_sha256),
        "control_tree_sha256": str(control_tree_sha256),
        "split_manifest_hash": str(split_manifest_hash),
        "solver_binding_hash": str(solver_binding_hash),
        "rank_index": int(rank_index),
        "wall_time_limit_sec": float(wall_time_limit_sec),
        "max_rounds": int(max_rounds),
        "max_columns_per_round": int(max_columns_per_round),
    }
    payload["binding_hash"] = _sha256_json(payload)
    return payload


def _same_parent_universe(control: dict, alternative: dict) -> bool:
    return bool(
        list(control.get("target_top3_candidate_ids") or ())
        == list(alternative.get("target_top3_candidate_ids") or ())
        and str(
            control.get(
                "target_legal_branch_shortlist_hash_before_sort"
            )
            or ""
        )
        == str(
            alternative.get(
                "target_legal_branch_shortlist_hash_before_sort"
            )
            or ""
        )
        and str(
            control.get(
                "target_legal_branch_shortlist_hash_after_sort"
            )
            or ""
        )
        == str(
            alternative.get(
                "target_legal_branch_shortlist_hash_after_sort"
            )
            or ""
        )
        and bool(control.get("target_path_reached_once"))
        and bool(alternative.get("target_path_reached_once"))
        and not bool(control.get("target_fallback_to_p0"))
        and not bool(alternative.get("target_fallback_to_p0"))
    )


def _build_gold_report(
    *,
    data,
    split_manifest_hash: str,
    parent_source_sha256: str,
    control_tree_sha256: str,
    summaries: dict[int, dict],
    target_node_id: str = "node_000",
    target_path_signature: tuple[str, ...] = tuple(),
    target_depth: int = 0,
    matched_scope: str = "post_certified_parent_continuation",
) -> dict:
    if 0 not in summaries:
        raise ValueError("partial E2E report requires the P0 control arm")
    control = dict(summaries[0])
    alternatives = []
    for rank in (1, 2):
        if rank not in summaries:
            continue
        arm = dict(summaries[rank])
        arm["counterfactual_universe_matches_control"] = (
            _same_parent_universe(control, arm)
        )
        alternatives.append(arm)

    all_summaries = [control, *alternatives]
    exact = bool(
        len(all_summaries) == 3
        and all(bool(row.get("exact_safe")) for row in all_summaries)
    )
    universe = bool(
        bool(control.get("universe_safe"))
        and all(bool(row.get("universe_safe")) for row in alternatives)
        and all(
            bool(row["counterfactual_universe_matches_control"])
            for row in alternatives
        )
    )
    objectives = [
        float(row["objective"])
        for row in all_summaries
        if row.get("objective") is not None
    ]
    objective_match = bool(
        len(objectives) == 3
        and max(objectives) - min(objectives)
        <= OBJECTIVE_TOLERANCE
    )
    complete = bool(
        len(all_summaries) == 3
        and exact
        and universe
        and objective_match
    )

    trusted_preferences = []
    by_rank = {
        int(row["requested_rank_index"]): row
        for row in all_summaries
    }
    rank_universe_safe = {
        0: bool(control.get("universe_safe")),
        **{
            int(row["requested_rank_index"]): bool(
                row.get("universe_safe")
                and row.get(
                    "counterfactual_universe_matches_control"
                )
            )
            for row in alternatives
        },
    }
    for left_rank, right_rank in combinations(sorted(by_rank), 2):
        if not (
            rank_universe_safe.get(left_rank, False)
            and rank_universe_safe.get(right_rank, False)
        ):
            continue
        left = by_rank[left_rank]
        right = by_rank[right_rank]
        left_exact = bool(left.get("exact_safe"))
        right_exact = bool(right.get("exact_safe"))
        left_wall = float(left["matched_end_to_end_wall_sec"])
        right_wall = float(right["matched_end_to_end_wall_sec"])
        winner = None
        loser = None
        evidence = ""
        if left_exact and right_exact:
            left_objective = left.get("objective")
            right_objective = right.get("objective")
            if (
                left_objective is not None
                and right_objective is not None
                and abs(
                    float(left_objective) - float(right_objective)
                )
                <= OBJECTIVE_TOLERANCE
                and abs(left_wall - right_wall) > 1.0e-9
            ):
                winner, loser = (
                    (left_rank, right_rank)
                    if left_wall < right_wall
                    else (right_rank, left_rank)
                )
                evidence = "BOTH_EXACT_OBJECTIVE_MATCH"
        elif (
            left_exact
            and not right_exact
            and left_wall < right_wall - 1.0e-9
        ):
            winner, loser = left_rank, right_rank
            evidence = "EXACT_BEFORE_OTHER_CENSOR_HORIZON"
        elif (
            right_exact
            and not left_exact
            and right_wall < left_wall - 1.0e-9
        ):
            winner, loser = right_rank, left_rank
            evidence = "EXACT_BEFORE_OTHER_CENSOR_HORIZON"
        if winner is not None:
            trusted_preferences.append(
                {
                    "winner_rank_index": int(winner),
                    "loser_rank_index": int(loser),
                    "evidence": evidence,
                    "winner_observed_wall_sec": float(
                        by_rank[winner][
                            "matched_end_to_end_wall_sec"
                        ]
                    ),
                    "loser_observed_or_censor_wall_sec": float(
                        by_rank[loser][
                            "matched_end_to_end_wall_sec"
                        ]
                    ),
                    "same_parent_snapshot": True,
                    "unexplored_arm_used_as_negative": False,
                }
            )

    selected_rank = None
    net_gain_sec = None
    net_gain_ratio = None
    if complete:
        wall_by_rank = {
            int(row["requested_rank_index"]): float(
                row["matched_end_to_end_wall_sec"]
            )
            for row in all_summaries
        }
        selected_rank = min(
            wall_by_rank,
            key=lambda rank: (wall_by_rank[rank], rank),
        )
        net_gain_sec = max(
            0.0,
            wall_by_rank[0] - wall_by_rank[selected_rank],
        )
        net_gain_ratio = (
            0.0
            if wall_by_rank[0] <= 0.0
            else net_gain_sec / wall_by_rank[0]
        )

    path_hash = str(control.get("target_path_hash") or "")
    top3_ids = list(control.get("target_top3_candidate_ids") or ())
    state = {
        "node_id": str(target_node_id),
        "path_signature": list(target_path_signature),
        "path_hash": path_hash,
        "depth": int(target_depth),
        "candidate_count": len(top3_ids),
        "top3_candidate_ids": top3_ids,
        "legal_branch_shortlist_hash_before_sort": control.get(
            "target_legal_branch_shortlist_hash_before_sort"
        ),
        "legal_branch_shortlist_hash_after_sort": control.get(
            "target_legal_branch_shortlist_hash_after_sort"
        ),
        "control_tree_elapsed_sec_at_exit": 0.0,
        "eligible_alternative_count": len(alternatives),
        "arms": alternatives,
        "observed_rank_indices": sorted(by_rank),
        "missing_rank_indices": sorted(
            {0, 1, 2}.difference(by_rank)
        ),
        "trusted_censored_pairwise_preferences": (
            trusted_preferences
        ),
        "complete_matched_e2e_gold": complete,
        "objective_matches_across_arms": objective_match,
        "oracle_selected_rank_index": selected_rank,
        "oracle_net_gain_sec": (
            None if net_gain_sec is None else round(net_gain_sec, 6)
        ),
        "oracle_net_gain_ratio": (
            None if net_gain_ratio is None else round(net_gain_ratio, 9)
        ),
        "matched_scope": str(matched_scope),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "development_only": True,
        "deployable": False,
        "training_authorized": False,
        "instance_id": data.instance_id,
        "instance_content_hash": data.instance_content_hash,
        "service_timing_policy_id": data.service_timing_policy_id,
        "scale": int(data.scale),
        "split_manifest_hash": str(split_manifest_hash),
        "baseline_id": BASELINE_ID,
        "root_exact_safe": True,
        "root_source_sha256": str(parent_source_sha256),
        "control_tree_sha256": str(control_tree_sha256),
        "control_exact_safe": bool(control.get("exact_safe")),
        "control_universe_safe": bool(control.get("universe_safe")),
        "control": control,
        "actionable_state_count": 1,
        "selected_state_count": 1,
        "observed_rank_indices": sorted(by_rank),
        "missing_rank_indices": sorted(
            {0, 1, 2}.difference(by_rank)
        ),
        "one_deviation_only": True,
        "post_deviation_policy": "p0_rank0",
        "matched_scope": str(matched_scope),
        "certified_parent_pricing_reused": True,
        "descendant_pricing_certificate_reused": False,
        "guidance_filter_count": 0,
        "guidance_branch_pair_drop_count": 0,
        "state_reports": [state],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", required=True)
    parser.add_argument("--opportunity-dir", required=True)
    parser.add_argument(
        "--certified-parent-snapshot-file",
        default=None,
        help=(
            "Optional branch_parent_snapshot_file.v1. Its fresh top-3 "
            "replaces the historical opportunity shortlist only after the "
            "snapshot root/control bindings and exact result validate."
        ),
    )
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
    opportunity_dir = (ROOT / args.opportunity_dir).resolve()
    split_path = (ROOT / args.split_manifest).resolve()
    output_dir = (ROOT / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    data = load_lunar_ice_data(_load_json(instance_path))
    manifest = _load_json(split_path)
    split_manifest_hash = str(
        manifest.get("manifest_hash") or _sha256_json(manifest)
    )
    if data.instance_content_hash not in _development_hashes(manifest):
        raise SystemExit("parent-snapshot oracle accepts development only")
    if data.service_timing_policy_id != SERVICE_TIMING_POLICY_ID:
        raise SystemExit("instance service-timing policy mismatch")
    profile = PROFILE_BY_SCALE.get(int(data.scale))
    if profile is None:
        raise SystemExit("parent-snapshot oracle accepts scale20/30")
    _configure_environment(scale=int(data.scale), profile=profile)
    solver_binding = _solver_binding(
        data=data,
        profile=profile,
        tree_max_rounds=int(args.tree_max_rounds),
        tree_max_columns_per_round=int(
            args.tree_max_columns_per_round
        ),
    )

    root_payload = _load_json(opportunity_dir / "root_source.json")
    opportunity_control = _load_json(
        opportunity_dir / "control_rank0_tree.json"
    )
    root_binding = root_payload.get("solver_binding") or {}
    if (
        root_payload.get("instance_content_hash")
        != data.instance_content_hash
        or str(root_payload.get("split_manifest_hash") or "")
        != split_manifest_hash
        or str(root_binding.get("binding_hash") or "")
        != str(solver_binding.get("binding_hash") or "")
    ):
        raise SystemExit("opportunity root binding mismatch")

    if args.certified_parent_snapshot_file:
        snapshot_path = (
            ROOT / args.certified_parent_snapshot_file
        ).resolve()
        snapshot_file = _load_json(snapshot_path)
        snapshot_summary = snapshot_file.get("summary") or {}
        parent_result = snapshot_file.get("result") or {}
        if (
            str(snapshot_file.get("schema_version") or "")
            != "lunar_ice_bpc.branch_parent_snapshot_file.v1"
            or snapshot_file.get("instance_content_hash")
            != data.instance_content_hash
            or str(snapshot_file.get("root_source_sha256") or "")
            != _sha256_json(root_payload)
            or str(snapshot_file.get("control_tree_sha256") or "")
            != _sha256_json(opportunity_control)
            or not bool(snapshot_summary.get("exact_safe"))
            or not bool(
                snapshot_summary.get("columns_reconstructed_exactly")
            )
            or not _node_probe_exact_safe(parent_result)
        ):
            raise SystemExit(
                "certified parent snapshot binding/exactness mismatch"
            )
        candidates = list(
            snapshot_summary.get("reconstructed_top3_candidates")
            or ()
        )
        candidate_ids = [
            _candidate_id(candidate) for candidate in candidates
        ]
        if (
            len(candidates) != 3
            or candidate_ids
            != list(snapshot_summary.get("top3_candidate_ids") or ())
        ):
            raise SystemExit(
                "certified parent snapshot top-3 binding mismatch"
            )
        universe_hash = canonical_universe_hash(
            candidate_ids,
            universe_kind="p0_branch_shortlist",
        )
        certified_root_node = {
            **parent_result,
            "node_id": "node_000",
            "parent_node_id": None,
            "depth": 0,
            "fractional_branch_probe": {
                "candidate_count": 3,
                "candidates": candidates,
            },
            "legal_branch_shortlist_hash_before_sort": universe_hash,
            "legal_branch_shortlist_hash_after_sort": universe_hash,
            "guidance_branch_pair_drop_count": 0,
            "guidance_filter_count": 0,
        }
        parent_source_sha256 = str(
            snapshot_summary.get("source_sha256") or ""
        )
        if not parent_source_sha256:
            raise SystemExit(
                "certified parent snapshot has no source hash"
            )
        bound_control = {
            "schema_version": (
                "lunar_ice_bpc.certified_parent_decision_state.v1"
            ),
            "instance_id": data.instance_id,
            "instance_content_hash": data.instance_content_hash,
            "nodes": [certified_root_node],
        }
    else:
        opportunity = _load_json(
            opportunity_dir / "branch_opportunity_report.json"
        )
        try:
            bound_control, parent_bound = (
                _bind_exact_opportunity_control(
                    opportunity_control,
                    opportunity,
                )
            )
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        if not parent_bound:
            raise SystemExit(
                "opportunity control is not exact-parent bound"
            )
        root_nodes = list(bound_control.get("nodes") or ())
        if len(root_nodes) != 1:
            raise SystemExit(
                "exact opportunity must bind one parent node"
            )
        certified_root_node = root_nodes[0]
        parent_path = Path(
            str(opportunity.get("p0_parent_source_path") or "")
        ).resolve()
        parent_source = _load_json(parent_path)
        parent_binding = parent_source.get("solver_binding") or {}
        if (
            parent_source.get("instance_content_hash")
            != data.instance_content_hash
            or str(parent_source.get("split_manifest_hash") or "")
            != split_manifest_hash
            or str(parent_binding.get("binding_hash") or "")
            != str(solver_binding.get("binding_hash") or "")
            or not bool(parent_source.get("root_exact_safe"))
            or not _node_probe_exact_safe(
                parent_source.get("result") or {}
            )
        ):
            raise SystemExit(
                "certified parent source binding/exactness mismatch"
            )
        parent_result = parent_source.get("result") or {}
        parent_source_sha256 = _sha256_json(parent_source)

    initial_columns = tuple(
        journey_column_from_solution_payload(data, row)
        for row in parent_result.get("active_columns") or ()
    )
    if not initial_columns:
        raise SystemExit("certified parent source has no active columns")

    control_tree_sha256 = _sha256_json(bound_control)
    summaries: dict[int, dict] = {}
    new_arm_count = 0
    for rank in args.arm_order:
        binding = _arm_binding(
            parent_source_sha256=parent_source_sha256,
            control_tree_sha256=control_tree_sha256,
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
            active_columns=initial_columns,
            profile=profile,
            wall_time_limit_sec=float(
                args.tree_wall_time_limit_sec
            ),
            max_rounds=int(args.tree_max_rounds),
            max_columns_per_round=int(
                args.tree_max_columns_per_round
            ),
            rank_by_path={tuple(): int(rank)},
            certified_root_node=certified_root_node,
            branch_snapshot_callback=(
                None
                if int(rank) != 0
                else _deep_snapshot_writer(
                    data=data,
                    destination=(
                        output_dir / "deep_parent_snapshots"
                    ),
                    parent_source_sha256=parent_source_sha256,
                    control_tree_sha256=control_tree_sha256,
                    split_manifest_hash=split_manifest_hash,
                    solver_binding_hash=str(
                        solver_binding["binding_hash"]
                    ),
                )
            ),
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
            target_path=tuple(),
            requested_rank=rank,
        )
        summary.update(
            {
                "arm_binding_hash": binding["binding_hash"],
                "parent_source_sha256": parent_source_sha256,
                "matched_scope": (
                    "post_certified_parent_continuation"
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
                parent_source_sha256=parent_source_sha256,
                control_tree_sha256=control_tree_sha256,
                summaries=summaries,
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
        parent_source_sha256=parent_source_sha256,
        control_tree_sha256=control_tree_sha256,
        summaries=summaries,
    )
    _write_json(output_dir / "state_oracle_report.json", report)
    partial_path = output_dir / "partial_state_oracle_report.json"
    if partial_path.exists():
        partial_path.unlink()
    status = {
        "schema_version": COLLECTION_SCHEMA_VERSION,
        "development_only": True,
        "deployable": False,
        "training_authorized": False,
        "instance_id": data.instance_id,
        "instance_content_hash": data.instance_content_hash,
        "completed_rank_indices": [0, 1, 2],
        "missing_rank_indices": [],
        "complete_matched_e2e_gold": bool(
            report["state_reports"][0][
                "complete_matched_e2e_gold"
            ]
        ),
        "oracle_selected_rank_index": report["state_reports"][0][
            "oracle_selected_rank_index"
        ],
        "oracle_net_gain_sec": report["state_reports"][0][
            "oracle_net_gain_sec"
        ],
        "status": "COMPLETE",
        "resume_required": False,
    }
    _write_json(output_dir / "collection_status.json", status)
    print(json.dumps(status, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
