#!/usr/bin/env python3
"""Cheap development-only scheduler for V3 branch-label collection.

The screen runs a bounded no-cut root pricing prefix, re-solves the restricted
RMP over the observed active columns, and records Ryan-Foster fractionality.
It also replays P0's SRI-3 cut-commit loop on that fixed column pool before
computing a cut-aware proxy.  Neither restricted replay runs pricing or creates
a certificate.  This is not a branch label, exact opportunity decision,
deployment gate, or estimate of the natural opportunity rate.

Screened-out development instances must retain an explicit exploration quota;
the screen may prioritize collection but may never permanently filter it.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from time import perf_counter


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from run_p0_no_task_wait_v3_branch_state_oracle import (  # noqa: E402
    BASELINE_ID,
    PROFILE_BY_SCALE,
    _configure_environment,
    _development_hashes,
    _load_json,
    _json_safe_top_level,
    _root_exact_safe,
    _sha256_json,
    _write_json,
)
from lunar_ice_bpc.domain.scenario import SERVICE_TIMING_POLICY_ID  # noqa: E402
from lunar_ice_bpc.exact.bpc.master.journey_master import (  # noqa: E402
    solve_root_journey_master,
)
from lunar_ice_bpc.exact.bpc.cuts.live_sri import (  # noqa: E402
    LiveSriPolicy,
    activate_separated_cuts,
    separate_live_sri,
)
from lunar_ice_bpc.exact.bpc.solver.pricing_tail_solver import (  # noqa: E402
    RELAXED_LABELING_WORKER,
    solve_node_pricing_with_b2b_r3,
)
from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import (  # noqa: E402
    spprc_engine_build_hash,
)
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.exact.core.cuts import CutContext, CutLineage  # noqa: E402
from lunar_ice_bpc.exact.core.journey import (  # noqa: E402
    journey_column_from_solution_payload,
)
from lunar_ice_bpc.exact.solver.branch_probe import (  # noqa: E402
    build_fractional_branch_probe,
)
from lunar_ice_bpc.runners.b4_1_true_dual_proof_tail import (  # noqa: E402
    _diagnostic_b0_placeholder,
)


SCHEMA_VERSION = (
    "lunar_ice_bpc.no_task_wait_v3_branch_priority_screen.v3"
)
DEFAULT_EXPLORATION_QUOTA = 0.25
BASELINE_REGISTRY_PATH = ROOT / "runs/native_bpc_baseline_registry.json"


def _compact_history(payload: dict) -> list[dict]:
    fields = (
        "round",
        "pricing_state",
        "node_lp_bound",
        "added_column_count",
        "addable_negative_count",
        "duplicate_negative_count",
        "final_judge_wall_time",
    )
    return [
        {
            key: row.get(key)
            for key in fields
            if key in row
        }
        for row in payload.get("history") or ()
    ]


def _priority_key(
    *,
    candidates: list[dict],
    active_column_count: int,
    final_round_added_column_count: int,
    instance_content_hash: str,
) -> tuple:
    top3 = candidates[:3]
    return (
        0 if len(top3) >= 3 else 1,
        -round(
            sum(float(row.get("fractionality") or 0.0) for row in top3),
            9,
        ),
        int(final_round_added_column_count),
        -int(active_column_count),
        str(instance_content_hash),
    )


def _active_baseline_binding(registry: dict) -> dict:
    active_id = str(registry.get("active_experiment_baseline_id") or "")
    if active_id != BASELINE_ID:
        raise ValueError("active experiment baseline id mismatch")
    matches = [
        row
        for row in registry.get("baselines") or ()
        if str(row.get("freeze_id") or "") == active_id
    ]
    if len(matches) != 1:
        raise ValueError("active experiment baseline record is not unique")
    engine_hash = str(matches[0].get("engine_hash") or "")
    if not engine_hash:
        raise ValueError("active experiment baseline engine hash missing")
    return {
        "baseline_id": active_id,
        "engine_hash": engine_hash,
        "registry_sha256": _sha256_json(registry),
    }


def _screen_from_root_result(*, data, root_result: dict) -> dict:
    active_columns = tuple(
        journey_column_from_solution_payload(data, row)
        for row in root_result.get("active_columns") or ()
    )
    if not active_columns:
        return {
            "restricted_rmp_status": "NO_ACTIVE_COLUMNS",
            "restricted_rmp_objective_bound": None,
            "restricted_rmp_primal_column_count": 0,
            "proxy_candidate_count": 0,
            "proxy_top3_candidates": [],
            "proxy_top3_fractionality_sum": 0.0,
            "active_column_count": 0,
        }
    master = solve_root_journey_master(
        data,
        active_columns,
        rmp_iteration_id=(
            f"v3_branch_priority_screen:{data.instance_content_hash}"
        ),
    )
    if master.rmp.status != "RESTRICTED_RMP_OPTIMAL":
        return {
            "restricted_rmp_status": master.rmp.status,
            "restricted_rmp_objective_bound": master.rmp.objective_bound,
            "restricted_rmp_primal_column_count": len(
                master.rmp.primal_columns
            ),
            "proxy_candidate_count": 0,
            "proxy_top3_candidates": [],
            "proxy_top3_fractionality_sum": 0.0,
            "active_column_count": len(active_columns),
        }
    probe = build_fractional_branch_probe(
        data.task_ids,
        master.rmp.primal_columns,
        active_columns,
        max_candidates=3,
    )
    candidates = list(probe.get("candidates") or ())
    return {
        "restricted_rmp_status": master.rmp.status,
        "restricted_rmp_objective_bound": master.rmp.objective_bound,
        "restricted_rmp_primal_column_count": len(
            master.rmp.primal_columns
        ),
        "proxy_candidate_count": len(candidates),
        "proxy_top3_candidates": candidates,
        "proxy_top3_fractionality_sum": round(
            sum(
                float(row.get("fractionality") or 0.0)
                for row in candidates[:3]
            ),
            9,
        ),
        "active_column_count": len(active_columns),
    }


def _primal_lambdas_integral(rows) -> bool:
    values = tuple(float(row.get("lambda_value") or 0.0) for row in rows)
    return bool(values) and all(
        abs(value) <= 1.0e-7 or abs(value - 1.0) <= 1.0e-7
        for value in values
    )


def _p0_restricted_cut_screen(*, data, root_result: dict) -> dict:
    """Replay P0 cut commits on a fixed observed column pool.

    This deliberately mirrors the official restricted-RMP cut commit rule, but
    never calls pricing and therefore has no certificate role.
    """

    active_columns = tuple(
        journey_column_from_solution_payload(data, row)
        for row in root_result.get("active_columns") or ()
    )
    if not active_columns:
        return {
            "cut_aware_restricted_rmp_status": "NO_ACTIVE_COLUMNS",
            "cut_aware_restricted_rmp_objective_bound": None,
            "cut_aware_restricted_rmp_primal_column_count": 0,
            "cut_aware_candidate_count": 0,
            "cut_aware_top3_candidates": [],
            "cut_aware_top3_fractionality_sum": 0.0,
            "cut_aware_active_cut_count": 0,
            "cut_aware_commit_history": [],
            "cut_aware_replay_completed": True,
            "cut_aware_certificate_role": "none",
        }

    policy = LiveSriPolicy.named("P0")
    context = CutContext()
    lineage = CutLineage(policy_version=policy.version)
    history: list[dict] = []
    terminal_reason = ""
    master = None
    for separation_round in range(
        1, max(1, int(policy.max_separation_rounds)) + 2
    ):
        master = solve_root_journey_master(
            data,
            active_columns,
            rmp_iteration_id=(
                "v3_branch_priority_cut_screen:"
                f"{data.instance_content_hash}:{separation_round}"
            ),
            cut_context=context,
            cut_lineage=lineage,
            live_cut_policy_hash=policy.policy_hash,
        )
        if master.rmp.status != "RESTRICTED_RMP_OPTIMAL":
            terminal_reason = "RESTRICTED_RMP_NOT_OPTIMAL"
            break
        scope_remaining = int(policy.global_cap) - sum(
            1 for row in lineage.entries if row.scope == "global"
        )
        selection_capacity = max(
            0,
            min(
                scope_remaining,
                int(policy.active_cap) - len(context.cuts),
            ),
        )
        separated = separate_live_sri(
            data.task_ids,
            master.rmp.primal_columns,
            subset_sizes=policy.subset_sizes_for_depth(0),
            selection_capacity=selection_capacity,
            existing_cut_context=context,
            violation_eps=policy.violation_eps,
        )
        next_context, next_lineage, activation = activate_separated_cuts(
            context,
            lineage,
            separated,
            policy=policy,
            node_id="priority_screen_root",
            depth=0,
            ancestor_path=(),
        )
        row = {
            "separation_round": int(separation_round),
            "rmp_bound_before": master.rmp.objective_bound,
            "separation": separated.to_payload(),
            "activation": activation,
        }
        if not activation["added_cut_count"]:
            activation["committed"] = False
            terminal_reason = (
                "POLICY_CAP_REACHED_WITH_UNSELECTED_VIOLATIONS"
                if separated.violated_candidate_count > 0
                else "COMPLETE_ENUMERATION_NO_NEW_VIOLATED_SRI"
            )
            row["terminal_reason"] = terminal_reason
            history.append(row)
            break
        proposed = solve_root_journey_master(
            data,
            active_columns,
            rmp_iteration_id=(
                "v3_branch_priority_cut_screen_proposed:"
                f"{data.instance_content_hash}:{separation_round}"
            ),
            cut_context=next_context,
            cut_lineage=next_lineage,
            live_cut_policy_hash=policy.policy_hash,
        )
        before_bound = master.rmp.objective_bound
        after_bound = proposed.rmp.objective_bound
        bound_gain = (
            None
            if before_bound is None or after_bound is None
            else float(after_bound) - float(before_bound)
        )
        integral = _primal_lambdas_integral(proposed.rmp.primal_columns)
        commit = bool(
            proposed.rmp.status == "RESTRICTED_RMP_OPTIMAL"
            and (
                integral
                or (
                    bound_gain is not None
                    and bound_gain + 1.0e-12
                    >= float(policy.min_restricted_rmp_gain)
                )
            )
        )
        row["pre_activation_screen"] = {
            "status": proposed.rmp.status,
            "rmp_bound_after_proposed_cuts": after_bound,
            "restricted_rmp_bound_gain": bound_gain,
            "restricted_primal_integral": integral,
            "min_restricted_rmp_gain": float(
                policy.min_restricted_rmp_gain
            ),
            "commit": commit,
            "certificate_role": "heuristic_cut_commit_gate_only",
            "mutates_official_bound": False,
        }
        activation["committed"] = commit
        history.append(row)
        if not commit:
            terminal_reason = "RESTRICTED_RMP_GAIN_BELOW_POLICY_THRESHOLD"
            break
        if separation_round > int(policy.max_separation_rounds):
            terminal_reason = "POLICY_MAX_SEPARATION_ROUNDS"
            break
        context, lineage = next_context, next_lineage

    final_master = solve_root_journey_master(
        data,
        active_columns,
        rmp_iteration_id=(
            "v3_branch_priority_cut_screen_final:"
            f"{data.instance_content_hash}"
        ),
        cut_context=context,
        cut_lineage=lineage,
        live_cut_policy_hash=policy.policy_hash,
    )
    if final_master.rmp.status == "RESTRICTED_RMP_OPTIMAL":
        probe = build_fractional_branch_probe(
            data.task_ids,
            final_master.rmp.primal_columns,
            active_columns,
            max_candidates=3,
        )
        candidates = list(probe.get("candidates") or ())
    else:
        candidates = []
    return {
        "cut_aware_restricted_rmp_status": final_master.rmp.status,
        "cut_aware_restricted_rmp_objective_bound": (
            final_master.rmp.objective_bound
        ),
        "cut_aware_restricted_rmp_primal_column_count": len(
            final_master.rmp.primal_columns
        ),
        "cut_aware_candidate_count": len(candidates),
        "cut_aware_top3_candidates": candidates,
        "cut_aware_top3_fractionality_sum": round(
            sum(
                float(row.get("fractionality") or 0.0)
                for row in candidates[:3]
            ),
            9,
        ),
        "cut_aware_active_cut_count": len(context.cuts),
        "cut_aware_active_cut_context_hash": (
            context.active_cut_context_hash
        ),
        "cut_aware_cut_lineage_hash": lineage.cut_lineage_hash,
        "cut_aware_commit_history": history,
        "cut_aware_terminal_reason": terminal_reason,
        "cut_aware_replay_completed": True,
        "cut_aware_certificate_role": "none",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", required=True)
    parser.add_argument(
        "--split-manifest",
        default=(
            "data/gat_p0v2/"
            "p0_no_task_wait_v3_gat_split_rebind_manifest.json"
        ),
    )
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--screen-budget-sec", type=float, default=30.0)
    parser.add_argument("--max-rounds", type=int, default=80)
    parser.add_argument("--max-columns-per-round", type=int, default=32)
    parser.add_argument(
        "--warm-start-source",
        default=None,
        help=(
            "Earlier priority-screen warm source. Only bound columns are "
            "reused; status and certificate fields are ignored."
        ),
    )
    parser.add_argument(
        "--persist-warm-source",
        action="store_true",
        help=(
            "Persist observed columns for a later exact solve. This never "
            "persists or reuses a certificate."
        ),
    )
    args = parser.parse_args()

    if float(args.screen_budget_sec) <= 0.0:
        raise SystemExit("screen budget must be positive")
    instance_path = (ROOT / args.instance).resolve()
    split_path = (ROOT / args.split_manifest).resolve()
    output_dir = (ROOT / args.output_dir).resolve()
    data = load_lunar_ice_data(_load_json(instance_path))
    manifest = _load_json(split_path)
    manifest_hash = str(
        manifest.get("manifest_hash") or _sha256_json(manifest)
    )
    if data.instance_content_hash not in _development_hashes(manifest):
        raise SystemExit("priority screen accepts development instances only")
    if data.service_timing_policy_id != SERVICE_TIMING_POLICY_ID:
        raise SystemExit("instance service-timing policy mismatch")
    profile = PROFILE_BY_SCALE.get(int(data.scale))
    if profile is None:
        raise SystemExit("priority screen currently accepts scale20/30")
    _configure_environment(scale=int(data.scale), profile=profile)
    baseline_binding = _active_baseline_binding(
        _load_json(BASELINE_REGISTRY_PATH)
    )
    observed_engine_hash = spprc_engine_build_hash(
        str(profile["backend"])
    )
    if observed_engine_hash != baseline_binding["engine_hash"]:
        raise SystemExit(
            "priority screen engine hash does not match active V3 baseline"
        )
    warm_columns = tuple()
    warm_metadata = None
    if args.warm_start_source:
        warm_path = (ROOT / args.warm_start_source).resolve()
        warm = _load_json(warm_path)
        warm_binding = warm.get("solver_binding") or {}
        if (
            str(warm.get("instance_content_hash") or "")
            != data.instance_content_hash
            or str(warm.get("split_manifest_hash") or "") != manifest_hash
            or str(warm_binding.get("baseline_id") or "") != BASELINE_ID
            or str(warm_binding.get("engine_hash") or "")
            != observed_engine_hash
            or str(warm_binding.get("service_timing_policy_id") or "")
            != data.service_timing_policy_id
        ):
            raise SystemExit("priority screen warm source binding mismatch")
        warm_columns = tuple(
            journey_column_from_solution_payload(data, row)
            for row in (warm.get("result") or {}).get(
                "active_columns"
            )
            or ()
        )
        if not warm_columns:
            raise SystemExit(
                "priority screen warm source contains no columns"
            )
        warm_metadata = {
            "source_path": str(warm_path),
            "source_sha256": _sha256_json(warm),
            "source_screen_wall_sec": float(
                warm.get("root_wall_sec") or 0.0
            ),
            "active_column_count": len(warm_columns),
            "certificate_reused": False,
            "columns_only": True,
        }

    started = perf_counter()
    root_result = solve_node_pricing_with_b2b_r3(
        data,
        node_id="priority_screen_root",
        initial_columns=warm_columns or None,
        max_direct_tasks=len(data.task_ids),
        max_rounds=int(args.max_rounds),
        wall_time_limit_sec=float(args.screen_budget_sec),
        max_columns_per_round=int(args.max_columns_per_round),
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
    screen_wall = perf_counter() - started
    proxy = _screen_from_root_result(data=data, root_result=root_result)
    cut_aware = _p0_restricted_cut_screen(
        data=data,
        root_result=root_result,
    )
    history = _compact_history(root_result)
    final_added = int(
        (history[-1] if history else {}).get("added_column_count") or 0
    )
    recent_added = [
        int(row.get("added_column_count") or 0)
        for row in history[-2:]
    ]
    near_saturation = bool(
        len(recent_added) == 2
        and all(
            value < int(args.max_columns_per_round)
            for value in recent_added
        )
    )
    priority_key = _priority_key(
        candidates=list(proxy["proxy_top3_candidates"]),
        active_column_count=int(proxy["active_column_count"]),
        final_round_added_column_count=final_added,
        instance_content_hash=data.instance_content_hash,
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "development_only": True,
        "deployable": False,
        "training_authorized": False,
        "is_branch_training_label": False,
        "is_exact_opportunity_decision": False,
        "is_certificate": False,
        "is_natural_opportunity_rate_evidence": False,
        "may_permanently_filter_development_instance": False,
        "required_hash_order_exploration_quota": (
            DEFAULT_EXPLORATION_QUOTA
        ),
        "instance_id": data.instance_id,
        "instance_content_hash": data.instance_content_hash,
        "scale": int(data.scale),
        "service_timing_policy_id": data.service_timing_policy_id,
        "baseline_id": BASELINE_ID,
        "engine_hash": observed_engine_hash,
        "baseline_registry_sha256": baseline_binding[
            "registry_sha256"
        ],
        "split_manifest_hash": manifest_hash,
        "screen_budget_sec": float(args.screen_budget_sec),
        "screen_wall_sec": round(float(screen_wall), 6),
        "screen_warm_start": warm_metadata,
        "screen_warm_start_certificate_reused": False,
        "cumulative_screen_wall_sec": round(
            float(screen_wall)
            + float(
                (warm_metadata or {}).get(
                    "source_screen_wall_sec"
                )
                or 0.0
            ),
            6,
        ),
        "root_prefix_exact_safe": _root_exact_safe(root_result),
        "root_prefix_pricing_state": root_result.get("pricing_state"),
        "root_prefix_certificate_scope": root_result.get(
            "certificate_scope"
        ),
        "root_prefix_round_count": int(
            root_result.get("pricing_round_count") or 0
        ),
        "root_prefix_added_column_count": int(
            root_result.get("added_column_count") or 0
        ),
        "root_prefix_history": history,
        **proxy,
        **cut_aware,
        "recent_round_added_column_counts": recent_added,
        "restricted_frontier_near_saturation": near_saturation,
        "exact_promotion_recommended": bool(
            int(cut_aware["cut_aware_candidate_count"]) >= 3
            and near_saturation
        ),
        "exact_promotion_recommendation_is_training_target": False,
        "priority_key_fields": [
            "missing_top3_proxy",
            "negative_top3_fractionality_sum",
            "final_round_added_column_count",
            "negative_active_column_count",
            "instance_content_hash",
        ],
        "priority_key": list(priority_key),
        "priority_key_is_training_target": False,
        "guidance_filter_count": 0,
        "guidance_branch_pair_drop_count": 0,
        "note": (
            "No-cut and fixed-pool P0 cut-aware restricted-RMP "
            "fractionality are collection schedulers only. Exact promotion "
            "requires cut-aware top-3 plus near saturation. "
            "At least 25% of development attempts remain content-hash-first "
            "to measure screen false negatives."
        ),
    }
    warm_source_path = output_dir / "root_prefix_warm_source.json"
    if args.persist_warm_source:
        _write_json(
            warm_source_path,
            {
                "schema_version": (
                    "lunar_ice_bpc.branch_priority_warm_source.v2"
                ),
                "development_only": True,
                "deployable": False,
                "training_authorized": False,
                "instance_id": data.instance_id,
                "instance_content_hash": data.instance_content_hash,
                "split_manifest_hash": manifest_hash,
                "solver_binding": {
                    "baseline_id": BASELINE_ID,
                    "engine_hash": observed_engine_hash,
                    "service_timing_policy_id": (
                        data.service_timing_policy_id
                    ),
                },
                # ``root_wall_sec`` is cumulative so the exact collector's
                # existing warm-source accounting includes every prefix.
                "root_wall_sec": round(
                    float(screen_wall)
                    + float(
                        (warm_metadata or {}).get(
                            "source_screen_wall_sec"
                        )
                        or 0.0
                    ),
                    6,
                ),
                "incremental_screen_wall_sec": round(
                    float(screen_wall),
                    6,
                ),
                "previous_cumulative_screen_wall_sec": float(
                    (warm_metadata or {}).get(
                        "source_screen_wall_sec"
                    )
                    or 0.0
                ),
                "root_exact_safe": False,
                "certificate_reused": False,
                "columns_only": True,
                "result": _json_safe_top_level(root_result),
            },
        )
        report["root_prefix_warm_source_path"] = str(warm_source_path)
        report["root_prefix_warm_source_certificate_reused"] = False
        report["root_prefix_warm_source_columns_only"] = True
    _write_json(output_dir / "branch_priority_screen.json", report)
    print(
        json.dumps(
            {
                "instance_id": data.instance_id,
                "scale": int(data.scale),
                "proxy_candidate_count": report[
                    "proxy_candidate_count"
                ],
                "proxy_top3_fractionality_sum": report[
                    "proxy_top3_fractionality_sum"
                ],
                "cut_aware_candidate_count": report[
                    "cut_aware_candidate_count"
                ],
                "cut_aware_top3_fractionality_sum": report[
                    "cut_aware_top3_fractionality_sum"
                ],
                "root_prefix_exact_safe": report[
                    "root_prefix_exact_safe"
                ],
                "is_branch_training_label": False,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
