#!/usr/bin/env python3
"""Run a development-only matched end-to-end top-3 branch action gate.

The root pricing trajectory is solved once and frozen as the common source
state.  Three tree arms then select deterministic rank 0, 1, or 2 from the
unchanged P0 Ryan-Foster shortlist at every actionable branch node.  This is a
mechanistic action-headroom test, not a deployable branch policy and not a
trained GAT evaluation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from time import perf_counter


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.exact.bpc.solver.branch_tree_solver import (  # noqa: E402
    solve_b3_branch_price_tree_baseline,
)
from lunar_ice_bpc.exact.bpc.solver.pricing_tail_solver import (  # noqa: E402
    RELAXED_LABELING_WORKER,
    solve_node_pricing_with_b2b_r3,
)
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.exact.core.journey import (  # noqa: E402
    journey_column_from_solution_payload,
)
from lunar_ice_bpc.runners.b4_1_true_dual_proof_tail import (  # noqa: E402
    _diagnostic_b0_placeholder,
)


PROFILE_BY_SCALE = {
    5: {
        "root_harvest_target": 8,
        "root_max_rounds": 20,
        "tree_max_nodes": 15,
        "tree_max_depth": 4,
        "backend": "native_rcspp_inprocess",
        "memory_gb": 2,
    },
    10: {
        "root_harvest_target": 16,
        "root_max_rounds": 40,
        "tree_max_nodes": 63,
        "tree_max_depth": 6,
        "backend": "native_rcspp_inprocess",
        "memory_gb": 4,
    },
    20: {
        "root_harvest_target": 32,
        "root_max_rounds": 80,
        "tree_max_nodes": 127,
        "tree_max_depth": 8,
        "backend": "native_rcspp_inprocess",
        "memory_gb": 8,
    },
    30: {
        "root_harvest_target": 64,
        "root_max_rounds": 120,
        "tree_max_nodes": 255,
        "tree_max_depth": 12,
        "backend": "native_rcspp_host",
        "memory_gb": 10,
    },
}


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _development_hashes(path: Path) -> set[str]:
    manifest = _load_json(path)
    if not bool((manifest.get("audit") or {}).get("passed")):
        raise SystemExit("split manifest audit did not pass")
    return {
        str(row["instance_content_hash"])
        for row in manifest.get("development", ())
    }


def _configure_environment(*, scale: int, profile: dict) -> None:
    os.environ["LUNAR_ICE_EXACT_FINAL_JUDGE_FIRST"] = "1"
    os.environ["LUNAR_ICE_SPPRC_EXACT_BACKEND"] = str(
        profile["backend"]
    )
    os.environ["LUNAR_ICE_SPPRC_MEMORY_LIMIT_GB"] = str(
        profile["memory_gb"]
    )
    os.environ["LUNAR_ICE_SPPRC_GRAPH_CACHE_ENTRIES"] = "1"
    os.environ["LUNAR_ICE_SPPRC_COMPLETION_BOUND"] = "0"
    os.environ["LUNAR_ICE_SPPRC_SUBSET_DOMINANCE"] = "1"
    os.environ["LUNAR_ICE_SPPRC_CUT_STATE"] = "1"
    os.environ["LUNAR_ICE_LABELING_FINAL_JUDGE_PASS_POLICY"] = (
        "branch_adaptive_sparse_harvest_v1"
        if int(scale) >= 30
        else "harvest_then_proof"
    )


def _json_safe_top_level(payload: dict) -> dict:
    return {
        key: value
        for key, value in payload.items()
        if not str(key).startswith("_")
    }


def _sha256_json(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _tree_arm_summary(
    *,
    rank_index: int,
    root_wall_sec: float,
    tree_wall_sec: float,
    lifecycle_overhead_sec: float,
    result: dict,
) -> dict:
    nodes = list(result.get("nodes") or ())
    branch_nodes = [
        node for node in nodes if node.get("node_status") == "BRANCHED"
    ]
    actionable = [
        node
        for node in branch_nodes
        if len(
            (node.get("fractional_branch_probe") or {}).get(
                "candidates"
            )
            or ()
        )
        >= 2
    ]
    universe_safe = all(
        (
            node.get("legal_branch_shortlist_hash_before_sort")
            == node.get("legal_branch_shortlist_hash_after_sort")
            and int(node.get("guidance_branch_pair_drop_count") or 0)
            == 0
        )
        for node in branch_nodes
    )
    exact_safe = bool(
        result.get("algorithm_status") == "BPC_OPTIMAL"
        and result.get("certificate_scope") == "BPC_TREE_OPTIMAL"
        and result.get("pricing_state") == "CERTIFIED_NO_NEGATIVE"
        and result.get("uses_true_dual_bpc_certificate")
        and result.get("all_certificate_ledgers_valid")
        and int(result.get("incomplete_node_count") or 0) == 0
    )
    return {
        "rank_index": int(rank_index),
        "policy_id": f"fixed_p0_shortlist_rank_{rank_index}",
        "development_only": True,
        "deployable": False,
        "root_source_wall_sec": round(float(root_wall_sec), 6),
        "tree_wall_sec": round(float(tree_wall_sec), 6),
        "emulated_guidance_lifecycle_overhead_sec": round(
            float(lifecycle_overhead_sec), 6
        ),
        "matched_end_to_end_wall_sec": round(
            float(root_wall_sec)
            + float(tree_wall_sec)
            + (float(lifecycle_overhead_sec) if rank_index else 0.0),
            6,
        ),
        "algorithm_status": result.get("algorithm_status"),
        "certificate_scope": result.get("certificate_scope"),
        "pricing_state": result.get("pricing_state"),
        "exact_safe": exact_safe,
        "universe_safe": universe_safe,
        "objective": result.get("incumbent_objective"),
        "global_lower_bound": result.get("global_lower_bound"),
        "node_count": int(result.get("node_count") or 0),
        "expanded_node_count": int(
            result.get("expanded_node_count") or 0
        ),
        "branch_actionable_node_count": len(actionable),
        "branch_rank_fallback_count": int(
            result.get("development_branch_rank_fallback_count") or 0
        ),
        "incomplete_node_count": int(
            result.get("incomplete_node_count") or 0
        ),
        "tree_deadline_hit": bool(result.get("tree_deadline_hit")),
        "tree_result_sha256": _sha256_json(result),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", required=True)
    parser.add_argument(
        "--split-manifest",
        default="data/gat_p0v2/p0v2_gat_split_manifest.json",
    )
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--reuse-root-source",
        default="",
        help=(
            "Reuse a root_source.json produced by this script. The instance "
            "content hash and exact-safe source status are revalidated."
        ),
    )
    parser.add_argument(
        "--ranks",
        nargs="+",
        type=int,
        default=[0, 1, 2],
    )
    parser.add_argument("--root-wall-time-limit-sec", type=float, default=300.0)
    parser.add_argument("--tree-wall-time-limit-sec", type=float, default=300.0)
    parser.add_argument("--tree-max-rounds", type=int, default=16)
    parser.add_argument("--tree-max-columns-per-round", type=int, default=128)
    parser.add_argument(
        "--emulated-guidance-lifecycle-overhead-sec",
        type=float,
        default=0.02,
    )
    args = parser.parse_args()

    ranks = tuple(dict.fromkeys(int(value) for value in args.ranks))
    if not ranks or any(value not in {0, 1, 2} for value in ranks):
        raise SystemExit("branch oracle ranks must be drawn from 0, 1, 2")
    if 0 not in ranks:
        raise SystemExit("branch oracle requires rank 0 as the P0 control")

    instance_path = (ROOT / args.instance).resolve()
    split_path = (ROOT / args.split_manifest).resolve()
    output_dir = (ROOT / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    data = load_lunar_ice_data(_load_json(instance_path))
    if data.instance_content_hash not in _development_hashes(split_path):
        raise SystemExit("branch oracle accepts development instances only")
    profile = PROFILE_BY_SCALE.get(int(data.scale))
    if profile is None:
        raise SystemExit(
            f"branch oracle has no frozen profile for scale {data.scale}"
        )
    _configure_environment(scale=int(data.scale), profile=profile)

    if args.reuse_root_source:
        source_path = (ROOT / args.reuse_root_source).resolve()
        reused_source = _load_json(source_path)
        supplied_hash = str(
            reused_source.get("instance_content_hash") or ""
        )
        if supplied_hash:
            if supplied_hash != data.instance_content_hash:
                raise SystemExit(
                    "reused root source instance hash mismatch"
                )
        else:
            source_instance_path = Path(
                str(reused_source.get("instance_path") or "")
            )
            if (
                not source_instance_path.is_file()
                or load_lunar_ice_data(
                    _load_json(source_instance_path)
                ).instance_content_hash
                != data.instance_content_hash
            ):
                raise SystemExit(
                    "reused stage probe cannot prove the instance hash"
                )
        root_result = dict(
            reused_source.get("result") or reused_source
        )
        root_wall = float(
            reused_source.get("root_wall_sec")
            or reused_source.get("elapsed_sec")
            or 0.0
        )
        active_columns = tuple(
            journey_column_from_solution_payload(data, row)
            for row in root_result.get("active_columns") or ()
        )
        root_exact_safe = bool(
            reused_source.get("root_exact_safe")
            or (
                root_result.get("certificate_scope")
                == "BPC_NODE_LP_CERTIFIED"
                and root_result.get("pricing_state")
                == "CERTIFIED_NO_NEGATIVE"
                and (
                    root_result.get("uses_true_dual_bpc_certificate")
                    or (
                        root_result.get("final_judge") or {}
                    ).get("uses_true_dual_bpc_certificate")
                )
            )
        )
    else:
        root_started = perf_counter()
        root_result = solve_node_pricing_with_b2b_r3(
            data,
            node_id="root",
            max_direct_tasks=len(data.task_ids),
            max_rounds=int(profile["root_max_rounds"]),
            wall_time_limit_sec=float(args.root_wall_time_limit_sec),
            max_columns_per_round=int(profile["root_harvest_target"]),
            b0_direct=_diagnostic_b0_placeholder(data),
            tail_dual_stabilization_enabled=True,
            tail_dual_stabilization_alpha=0.7,
            tail_dual_stabilization_window=5,
            worker_pricer_kind=RELAXED_LABELING_WORKER,
            labeling_final_judge_enabled=True,
            labeling_final_judge_max_exact_tasks=len(data.task_ids),
            labeling_final_judge_exact_harvest_target=int(
                profile["root_harvest_target"]
            ),
            return_active_columns_payload=True,
        )
        root_wall = perf_counter() - root_started
        active_columns = tuple(
            root_result.get("_active_columns") or ()
        )
        root_exact_safe = bool(
            root_result.get("certificate_scope")
            == "BPC_NODE_LP_CERTIFIED"
            and root_result.get("pricing_state")
            == "CERTIFIED_NO_NEGATIVE"
            and root_result.get("uses_true_dual_bpc_certificate")
            and root_result.get("pricing_rc_audit_pass")
        )
    if not root_exact_safe or not active_columns:
        raise SystemExit(
            "common root source did not close exactly with active columns"
        )
    root_payload = {
        "schema_version": (
            "lunar_ice_bpc.development_branch_root_source.v1"
        ),
        "development_only": True,
        "deployable": False,
        "instance_path": str(instance_path),
        "instance_id": data.instance_id,
        "instance_content_hash": data.instance_content_hash,
        "root_wall_sec": round(float(root_wall), 6),
        "root_exact_safe": root_exact_safe,
        "active_column_count": len(active_columns),
        "result": _json_safe_top_level(root_result),
    }
    (output_dir / "root_source.json").write_text(
        json.dumps(
            root_payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    arms: list[dict] = []
    objective_values: set[float] = set()
    for rank_index in ranks:
        arm_started = perf_counter()
        tree = solve_b3_branch_price_tree_baseline(
            data,
            initial_columns=active_columns,
            max_direct_tasks=len(data.task_ids),
            max_rounds_per_node=int(args.tree_max_rounds),
            wall_time_limit_sec=float(args.tree_wall_time_limit_sec),
            max_columns_per_round=int(
                args.tree_max_columns_per_round
            ),
            max_tree_nodes=int(profile["tree_max_nodes"]),
            max_branch_depth=int(profile["tree_max_depth"]),
            use_complete_universe_audit=False,
            run_b2_root_diagnostic=False,
            solve_b0_direct_first=False,
            tail_dual_stabilization_enabled=True,
            tail_dual_stabilization_alpha=0.7,
            tail_dual_stabilization_window=5,
            worker_pricer_kind=RELAXED_LABELING_WORKER,
            labeling_final_judge_enabled=True,
            labeling_final_judge_max_exact_tasks=len(data.task_ids),
            labeling_final_judge_exact_harvest_target=int(
                profile["root_harvest_target"]
            ),
            live_sri_policy="P0",
            development_branch_rank_index=int(rank_index),
        )
        tree_wall = perf_counter() - arm_started
        tree_path = output_dir / f"rank_{rank_index}_tree.json"
        tree_path.write_text(
            json.dumps(
                tree,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        arm = _tree_arm_summary(
            rank_index=rank_index,
            root_wall_sec=root_wall,
            tree_wall_sec=tree_wall,
            lifecycle_overhead_sec=float(
                args.emulated_guidance_lifecycle_overhead_sec
            ),
            result=tree,
        )
        arms.append(arm)
        if arm["exact_safe"] and arm["objective"] is not None:
            objective_values.add(round(float(arm["objective"]), 9))
        print(json.dumps(arm, ensure_ascii=False, sort_keys=True))

    control = next(row for row in arms if row["rank_index"] == 0)
    eligible = [
        row
        for row in arms
        if row["exact_safe"] and row["universe_safe"]
    ]
    best = min(
        eligible or [control],
        key=lambda row: float(row["matched_end_to_end_wall_sec"]),
    )
    control_wall = float(control["matched_end_to_end_wall_sec"])
    best_wall = float(best["matched_end_to_end_wall_sec"])
    gain_sec = max(0.0, control_wall - best_wall)
    report = {
        "schema_version": (
            "lunar_ice_bpc.development_branch_top3_oracle_gate.v1"
        ),
        "development_only": True,
        "deployable": False,
        "instance_id": data.instance_id,
        "instance_content_hash": data.instance_content_hash,
        "scale": int(data.scale),
        "root_source_sha256": _sha256_json(root_payload),
        "arms": arms,
        "all_exact_objectives_equal": len(objective_values) <= 1,
        "p0_control_exact_safe": bool(control["exact_safe"]),
        "all_completed_arm_universes_safe": all(
            row["universe_safe"] for row in arms
        ),
        "oracle_selected_rank_index": int(best["rank_index"]),
        "oracle_net_gain_sec": round(gain_sec, 6),
        "oracle_net_gain_ratio": round(
            gain_sec / control_wall if control_wall > 0.0 else 0.0,
            9,
        ),
        "actionable": bool(
            int(control["branch_actionable_node_count"]) > 0
        ),
        "training_authorized": False,
        "training_authorization_reason": (
            "single_instance_mechanistic_gate_only"
        ),
    }
    (output_dir / "branch_top3_oracle_report.json").write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "instance_id": report["instance_id"],
                "scale": report["scale"],
                "actionable": report["actionable"],
                "oracle_selected_rank_index": report[
                    "oracle_selected_rank_index"
                ],
                "oracle_net_gain_ratio": report[
                    "oracle_net_gain_ratio"
                ],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if control["exact_safe"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
