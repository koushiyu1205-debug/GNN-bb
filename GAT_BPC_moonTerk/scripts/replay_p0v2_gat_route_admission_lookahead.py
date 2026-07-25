#!/usr/bin/env python3
"""Replay P0 batch and boundary swaps through the next exact RMP.

This is an offline label collector.  It cannot certify pricing or mutate the
live solver, and it never treats unmeasured/censored actions as negatives.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
from time import perf_counter

from lunar_ice_bpc.exact.bpc.master.journey_master import (
    solve_root_journey_master,
)
from lunar_ice_bpc.exact.core.branching import branch_context_from_payload
from lunar_ice_bpc.exact.core.cuts import cut_context_from_payload
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.core.journey import (
    journey_column_from_solution_payload,
)
from lunar_ice_bpc.exact.master.journey_rmp import (
    manual_journey_reduced_cost,
)
from lunar_ice_bpc.guidance.route_admission import (
    ROUTE_ADMISSION_LEXICOGRAPHIC_OBJECTIVE_SPEC_V2,
    ROUTE_ADMISSION_LOOKAHEAD_SCHEMA_V1,
    build_boundary_swap_actions,
    materialize_next_rmp_pairwise_targets,
    validate_route_admission_snapshot,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", required=True)
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--replicates", type=int, default=1)
    parser.add_argument("--selected-boundary-width", type=int, default=4)
    parser.add_argument("--omitted-contest-cap", type=int, default=8)
    parser.add_argument("--max-swap-actions", type=int, default=24)
    parser.add_argument("--seed", type=int, default=20260724)
    parser.add_argument("--negative-eps", type=float, default=1.0e-6)
    args = parser.parse_args()

    data = load_lunar_ice_data(
        json.loads(Path(args.instance).read_text(encoding="utf-8"))
    )
    snapshot = validate_route_admission_snapshot(
        json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    )
    if data.instance_content_hash != str(
        snapshot["instance_content_hash"]
    ):
        raise SystemExit("instance/snapshot content hash mismatch")
    binding = dict(snapshot["canonical_solve_binding"])
    if str(binding.get("objective_mode") or "") != "official":
        raise SystemExit(
            "route-admission next-RMP replay currently requires official mode"
        )
    action_manifest = build_boundary_swap_actions(
        snapshot,
        selected_boundary_width=args.selected_boundary_width,
        omitted_contest_cap=args.omitted_contest_cap,
        max_swap_actions=args.max_swap_actions,
    )
    active = tuple(
        journey_column_from_solution_payload(data, payload)
        for payload in snapshot["active_column_payloads"]
    )
    candidates = {
        str(row["candidate_id"]): journey_column_from_solution_payload(
            data, row["column_payload"]
        )
        for row in snapshot["candidate_rows"]
    }
    branch_context = branch_context_from_payload(
        snapshot.get("branch_context")
    )
    cut_context = cut_context_from_payload(
        snapshot.get("full_cut_context")
    )
    scheduled = [
        (replicate, action)
        for replicate in range(max(1, int(args.replicates)))
        for action in action_manifest["actions"]
    ]
    random.Random(int(args.seed)).shuffle(scheduled)
    measurements = []
    for replicate, action in scheduled:
        action_id = str(action["action_id"])
        admitted = tuple(
            candidates[str(candidate_id)]
            for candidate_id in action["admitted_candidate_ids"]
        )
        started = perf_counter()
        try:
            solved = solve_root_journey_master(
                data,
                (*active, *admitted),
                rmp_iteration_id=(
                    f"{binding.get('rmp_iteration_id')}:"
                    f"route-admission:{action_id}:{replicate}"
                ),
                branch_context=branch_context,
                cut_context=cut_context,
                live_cut_policy_hash=str(
                    snapshot.get("live_cut_policy_hash") or ""
                ),
                separator_policy_version=str(
                    snapshot.get("separator_policy_version") or ""
                ),
            )
            status = (
                "RMP_OPTIMAL"
                if solved.rmp.status == "RESTRICTED_RMP_OPTIMAL"
                and solved.rmp.objective_bound is not None
                else "RMP_INCOMPLETE"
            )
            objective = (
                float(solved.rmp.objective_bound)
                if status == "RMP_OPTIMAL"
                else None
            )
            deferred_ids = tuple(
                candidate_id
                for candidate_id in snapshot["legal_candidate_ids"]
                if candidate_id
                not in set(action["admitted_candidate_ids"])
            )
            deferred_rcs = tuple(
                float(
                    manual_journey_reduced_cost(
                        candidates[candidate_id],
                        solved.rmp.duals,
                        cut_coefficients=cut_context.coefficients_for(
                            candidates[candidate_id]
                        ),
                    )
                )
                for candidate_id in deferred_ids
            )
            negative_rcs = tuple(
                value
                for value in deferred_rcs
                if value < -abs(float(args.negative_eps))
            )
            deferred_negative_count = len(negative_rcs)
            deferred_negative_mass = sum(-value for value in negative_rcs)
            deferred_best_true_rc = (
                None if not deferred_rcs else min(deferred_rcs)
            )
            error = ""
        except Exception as exc:
            status = "RMP_FAILED"
            objective = None
            deferred_ids = tuple()
            deferred_negative_count = None
            deferred_negative_mass = None
            deferred_best_true_rc = None
            error = repr(exc)
        measurements.append(
            {
                "schema_version": ROUTE_ADMISSION_LOOKAHEAD_SCHEMA_V1,
                "snapshot_hash": snapshot["snapshot_hash"],
                "objective_spec_id": (
                    ROUTE_ADMISSION_LEXICOGRAPHIC_OBJECTIVE_SPEC_V2
                ),
                "action_id": action_id,
                "swap_out_candidate_id": action[
                    "swap_out_candidate_id"
                ],
                "swap_in_candidate_id": action[
                    "swap_in_candidate_id"
                ],
                "replicate_id": f"replicate-{replicate:03d}",
                "status": status,
                "next_rmp_objective": objective,
                "deferred_candidate_count": len(deferred_ids),
                "deferred_negative_count": deferred_negative_count,
                "deferred_negative_mass": deferred_negative_mass,
                "deferred_best_true_rc": deferred_best_true_rc,
                "censored": status != "RMP_OPTIMAL",
                "censored_reason": (
                    "" if status == "RMP_OPTIMAL" else status
                ),
                "wall_sec": perf_counter() - started,
                "error": error,
                "can_certify": False,
                "mutates_solver": False,
            }
        )
    targets = materialize_next_rmp_pairwise_targets(
        snapshot, measurements
    )
    output = {
        "schema_version": ROUTE_ADMISSION_LOOKAHEAD_SCHEMA_V1,
        "snapshot_hash": snapshot["snapshot_hash"],
        "instance_content_hash": data.instance_content_hash,
        "objective_spec_id": (
            ROUTE_ADMISSION_LEXICOGRAPHIC_OBJECTIVE_SPEC_V2
        ),
        "action_manifest": action_manifest,
        "measurements": measurements,
        "targets": targets,
        "legal_universe_preserved": True,
        "guidance_filter_count": 0,
        "legacy_four_coefficient_cost_used": False,
        "fixed_censoring_penalty_used": False,
        "can_certify": False,
        "linear_training_authorized": False,
    }
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    print(str(target.resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
