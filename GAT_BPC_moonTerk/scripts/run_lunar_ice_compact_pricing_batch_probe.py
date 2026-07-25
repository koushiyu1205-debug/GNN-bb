#!/usr/bin/env python3
"""Run a bounded B1B compact-pricing batch negative-discovery probe."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.exact.bpc.solver.pricing_tail_solver import (  # noqa: E402
    DIRECT_LABEL_WORKER,
    RELAXED_LABELING_WORKER,
    solve_node_pricing_with_b2b_r3,
)
from lunar_ice_bpc.exact.bpc.solver.root_node_solver import (  # noqa: E402
    _reference_seed_direct_placeholder,
    build_b1_seed_columns,
    solve_b1_root_node_baseline,
)
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.exact.core.journey import journey_column_from_solution_payload  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--time-limit-sec", type=float, default=120.0)
    parser.add_argument("--max-rounds", type=int, default=1)
    parser.add_argument("--max-direct-tasks", type=int, default=30)
    parser.add_argument("--seed-mode", default="b0_incumbent_plus_singletons")
    parser.add_argument("--solve-b0-direct-first", action="store_true")
    parser.add_argument("--resume-probe", default="")
    parser.add_argument("--write-active-columns", action="store_true")
    parser.add_argument("--batch-target", type=int, default=2)
    parser.add_argument(
        "--harvest-micro-batch-size",
        type=int,
        default=None,
        help=(
            "Opt-in U0 experiment: admit only this many final-judge "
            "columns per RMP round and reprice all deferred columns under "
            "the next true dual."
        ),
    )
    parser.add_argument(
        "--harvest-deferred-candidate-limit",
        type=int,
        default=10000,
    )
    parser.add_argument(
        "--root-engine",
        choices=("b1_compact_final_judge", "b2b_r3_worker"),
        default="b1_compact_final_judge",
    )
    parser.add_argument(
        "--worker-pricer-kind",
        choices=(DIRECT_LABEL_WORKER, RELAXED_LABELING_WORKER),
        default=DIRECT_LABEL_WORKER,
    )
    parser.add_argument("--tail-dual-stabilization-enabled", action="store_true")
    parser.add_argument("--tail-dual-stabilization-alpha", type=float, default=0.7)
    parser.add_argument("--tail-dual-stabilization-window", type=int, default=5)
    args = parser.parse_args()

    instance_path = _resolve(args.instance)
    output_dir = _resolve(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    data = load_lunar_ice_data(json.loads(instance_path.read_text(encoding="utf-8")))
    resume_payload = _load_resume_payload(args.resume_probe)
    initial_columns = _resume_initial_columns(data, resume_payload)
    started = perf_counter()
    b0_seed = None
    if str(args.root_engine) == "b2b_r3_worker":
        if initial_columns is None:
            b0_seed = _reference_seed_direct_placeholder(data)
            initial_columns, _seed_report = build_b1_seed_columns(
                data,
                b0_direct=b0_seed,
                seed_mode=str(args.seed_mode),
                max_direct_tasks=int(args.max_direct_tasks),
            )
        else:
            b0_seed = _reference_seed_direct_placeholder(data)
        result = solve_node_pricing_with_b2b_r3(
            data,
            initial_columns=initial_columns,
            b0_direct=b0_seed,
            max_direct_tasks=int(args.max_direct_tasks),
            max_rounds=int(args.max_rounds),
            wall_time_limit_sec=float(args.time_limit_sec),
            seed_mode=str(args.seed_mode),
            max_columns_per_round=int(args.batch_target),
            worker_pricer_kind=str(args.worker_pricer_kind),
            tail_dual_stabilization_enabled=bool(args.tail_dual_stabilization_enabled),
            tail_dual_stabilization_alpha=float(args.tail_dual_stabilization_alpha),
            tail_dual_stabilization_window=int(args.tail_dual_stabilization_window),
            return_active_columns_payload=bool(args.write_active_columns or initial_columns),
            harvest_micro_batch_size=args.harvest_micro_batch_size,
            harvest_deferred_candidate_limit=int(
                args.harvest_deferred_candidate_limit
            ),
        )
    else:
        result = solve_b1_root_node_baseline(
            data,
            initial_columns=initial_columns,
            max_direct_tasks=int(args.max_direct_tasks),
            max_rounds=int(args.max_rounds),
            wall_time_limit_sec=float(args.time_limit_sec),
            seed_mode=str(args.seed_mode),
            solve_b0_direct_first=bool(args.solve_b0_direct_first),
            return_active_columns_payload=bool(args.write_active_columns or initial_columns),
        )
    elapsed = perf_counter() - started
    final_judge = result.get("final_judge") or {}
    payload = {
        "schema_version": "lunar_ice_bpc.compact_pricing_batch_probe.v1",
        "instance_path": str(instance_path),
        "instance_id": data.instance_id,
        "config": {
            "max_direct_tasks": int(args.max_direct_tasks),
            "max_rounds": int(args.max_rounds),
            "wall_time_limit_sec": float(args.time_limit_sec),
            "seed_mode": str(args.seed_mode),
            "solve_b0_direct_first": bool(args.solve_b0_direct_first),
            "root_engine": str(args.root_engine),
            "worker_pricer_kind": str(args.worker_pricer_kind),
            "tail_dual_stabilization_enabled": bool(args.tail_dual_stabilization_enabled),
            "tail_dual_stabilization_alpha": float(args.tail_dual_stabilization_alpha),
            "tail_dual_stabilization_window": int(args.tail_dual_stabilization_window),
            "harvest_micro_batch_size": args.harvest_micro_batch_size,
            "harvest_deferred_candidate_limit": int(
                args.harvest_deferred_candidate_limit
            ),
            "env_compact_negative_batch_target": os.environ.get("LUNAR_ICE_COMPACT_NEGATIVE_BATCH_TARGET", ""),
            "env_compact_negative_search_cap_sec": os.environ.get("LUNAR_ICE_COMPACT_NEGATIVE_SEARCH_CAP_SEC", ""),
            "env_compact_negative_no_good_scope": os.environ.get("LUNAR_ICE_COMPACT_NEGATIVE_NO_GOOD_SCOPE", ""),
            "env_compact_optimization_harvest_target": os.environ.get(
                "LUNAR_ICE_COMPACT_OPTIMIZATION_HARVEST_TARGET",
                "",
            ),
            "env_compact_optimization_harvest_no_good_scope": os.environ.get(
                "LUNAR_ICE_COMPACT_OPTIMIZATION_HARVEST_NO_GOOD_SCOPE",
                "",
            ),
            "env_compact_final_judge_profile": os.environ.get("LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE", ""),
            "env_compact_final_judge_phase_mode": os.environ.get("LUNAR_ICE_COMPACT_FINAL_JUDGE_PHASE_MODE", ""),
            "env_labeling_final_judge": os.environ.get("LUNAR_ICE_LABELING_FINAL_JUDGE", ""),
            "env_labeling_final_judge_max_tasks": os.environ.get("LUNAR_ICE_LABELING_FINAL_JUDGE_MAX_TASKS", ""),
            "env_exact_final_judge_first": os.environ.get("LUNAR_ICE_EXACT_FINAL_JUDGE_FIRST", ""),
            "env_compact_service_start_depot_travel_lb": os.environ.get(
                "LUNAR_ICE_COMPACT_SERVICE_START_DEPOT_TRAVEL_LB",
                "",
            ),
            "env_compact_task_to_depot_return_travel_lb": os.environ.get(
                "LUNAR_ICE_COMPACT_TASK_TO_DEPOT_RETURN_TRAVEL_LB",
                "",
            ),
            "env_compact_pair_route_duration_lb": os.environ.get(
                "LUNAR_ICE_COMPACT_PAIR_ROUTE_DURATION_LB",
                "",
            ),
            "env_compact_sortie_slot_position_bounds": os.environ.get(
                "LUNAR_ICE_COMPACT_SORTIE_SLOT_POSITION_BOUNDS",
                "",
            ),
            "env_compact_demand_cover_cut": os.environ.get(
                "LUNAR_ICE_COMPACT_DEMAND_COVER_CUT",
                "",
            ),
            "env_compact_single_task_energy_lb": os.environ.get(
                "LUNAR_ICE_COMPACT_SINGLE_TASK_ENERGY_LB",
                "",
            ),
            "env_compact_single_task_shadow_lb": os.environ.get(
                "LUNAR_ICE_COMPACT_SINGLE_TASK_SHADOW_LB",
                "",
            ),
            "env_compact_pair_energy_lb": os.environ.get(
                "LUNAR_ICE_COMPACT_PAIR_ENERGY_LB",
                "",
            ),
            "env_compact_pair_energy_infeasible_cut": os.environ.get(
                "LUNAR_ICE_COMPACT_PAIR_ENERGY_INFEASIBLE_CUT",
                "",
            ),
            "env_compact_pair_shadow_infeasible_cut": os.environ.get(
                "LUNAR_ICE_COMPACT_PAIR_SHADOW_INFEASIBLE_CUT",
                "",
            ),
            "env_compact_triple_shadow_infeasible_cut": os.environ.get(
                "LUNAR_ICE_COMPACT_TRIPLE_SHADOW_INFEASIBLE_CUT",
                "",
            ),
            "env_compact_triple_energy_infeasible_cut": os.environ.get(
                "LUNAR_ICE_COMPACT_TRIPLE_ENERGY_INFEASIBLE_CUT",
                "",
            ),
            "env_compact_triple_time_window_infeasible_cut": os.environ.get(
                "LUNAR_ICE_COMPACT_TRIPLE_TIME_WINDOW_INFEASIBLE_CUT",
                "",
            ),
            "env_compact_quad_time_window_infeasible_cut": os.environ.get(
                "LUNAR_ICE_COMPACT_QUAD_TIME_WINDOW_INFEASIBLE_CUT",
                "",
            ),
            "resume_probe": "" if not resume_payload else str(_resolve(args.resume_probe)),
            "resume_initial_column_count": len(initial_columns) if initial_columns is not None else 0,
            "write_active_columns": bool(args.write_active_columns or initial_columns),
        },
        "elapsed_sec": round(elapsed, 6),
        "algorithm_status": result.get("algorithm_status"),
        "certificate_scope": result.get("certificate_scope"),
        "pricing_state": result.get("pricing_state"),
        "root_engine": str(args.root_engine),
        "worker_pricer_kind": str(args.worker_pricer_kind),
        "root_lp_bound": result.get("root_lp_bound", result.get("node_lp_bound")),
        "root_rmp_objective": result.get("root_rmp_objective", result.get("node_lp_bound")),
        "root_lp_vs_direct_dp_gap": result.get("root_lp_vs_direct_dp_gap"),
        "integral_root": result.get("integral_root"),
        "b0_ablation": result.get("b0_ablation") or {},
        "pricing_round_count": result.get("pricing_round_count"),
        "added_column_count": result.get("added_column_count"),
        "final_judge_call_count": result.get("final_judge_call_count"),
        "final_judge_found_negative_count": result.get("final_judge_found_negative_count"),
        "final_judge_incomplete_count": result.get("final_judge_incomplete_count"),
        "hidden_negative_count": result.get("hidden_negative_count"),
        "hidden_negative_audit": result.get("hidden_negative_audit") or {},
        "final_judge": final_judge,
        "history": result.get("history"),
        "active_columns_payload_version": result.get("active_columns_payload_version"),
        "active_columns": result.get("active_columns") or [],
    }
    (output_dir / "probe.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / "probe_report_zh.md").write_text(_render_report(payload), encoding="utf-8")
    print(json.dumps(_console_summary(payload), ensure_ascii=False))
    print(f"report {output_dir / 'probe_report_zh.md'}")
    return 0


def _console_summary(payload: dict) -> dict:
    return {
        "elapsed_sec": payload.get("elapsed_sec"),
        "algorithm_status": payload.get("algorithm_status"),
        "certificate_scope": payload.get("certificate_scope"),
        "pricing_state": payload.get("pricing_state"),
        "pricing_round_count": payload.get("pricing_round_count"),
        "added_column_count": payload.get("added_column_count"),
        "active_column_count": len(payload.get("active_columns") or []),
    }


def _render_report(payload: dict) -> str:
    final_judge = payload.get("final_judge") or {}
    lines = [
        "# 30-scale Compact Pricing Batch Probe",
        "",
        "该 probe 只验证 batch negative discovery，不是 BPC certificate。",
        "",
        f"- instance: `{payload['instance_id']}`",
        f"- elapsed: `{payload['elapsed_sec']}` s",
        f"- algorithm_status: `{payload['algorithm_status']}`",
        f"- certificate_scope: `{payload['certificate_scope']}`",
        f"- pricing_state: `{payload['pricing_state']}`",
        f"- root_engine: `{payload.get('root_engine')}`",
        f"- worker_pricer_kind: `{payload.get('worker_pricer_kind')}`",
        f"- tail_dual_stabilization_enabled: `{payload.get('config', {}).get('tail_dual_stabilization_enabled')}`",
        f"- pricing_round_count: `{payload['pricing_round_count']}`",
        f"- added_column_count: `{payload['added_column_count']}`",
        f"- final_judge_call_count: `{payload['final_judge_call_count']}`",
        f"- final_judge phase: `{final_judge.get('compact_pricing_phase')}`",
        f"- final_judge profile: `{final_judge.get('compact_final_judge_profile')}`",
        f"- final_judge formulation profile: `{final_judge.get('compact_final_judge_formulation_profile')}`",
        f"- final_judge phase mode: `{final_judge.get('compact_final_judge_phase_mode')}`",
        f"- proof-only skipped negative feasibility: `{final_judge.get('negative_feasibility_skipped_for_proof_only')}`",
        f"- full-space negative feasibility proof attempted: `{final_judge.get('negative_feasibility_full_space_proof_attempted')}`",
        f"- full-space negative feasibility proof can certify: `{final_judge.get('negative_feasibility_full_space_proof_can_certify')}`",
        f"- final_judge negative_column_count: `{final_judge.get('negative_column_count')}`",
        f"- sortie slot-position bounds enabled: `{final_judge.get('sortie_slot_position_bounds_enabled')}`",
        f"- sortie slot-position bounds rows: `{final_judge.get('sortie_slot_position_bound_count')}`",
        f"- single-task energy LB enabled: `{final_judge.get('single_task_energy_lb_enabled')}`",
        f"- single-task energy LB rows: `{final_judge.get('single_task_energy_lb_count')}`",
        f"- single-task shadow LB enabled: `{final_judge.get('single_task_shadow_lb_enabled')}`",
        f"- single-task shadow LB rows: `{final_judge.get('single_task_shadow_lb_count')}`",
        f"- triple time-window infeasible cut enabled: `{final_judge.get('triple_time_window_infeasible_cut_enabled')}`",
        f"- triple time-window infeasible cut rows: `{final_judge.get('triple_time_window_infeasible_cut_count')}`",
        f"- quad time-window infeasible cut enabled: `{final_judge.get('quad_time_window_infeasible_cut_enabled')}`",
        f"- quad time-window infeasible cut rows: `{final_judge.get('quad_time_window_infeasible_cut_count')}`",
        f"- hidden_negative_count: `{payload.get('hidden_negative_count')}`",
        f"- hidden_negative_audit status: `{(payload.get('hidden_negative_audit') or {}).get('status')}`",
        f"- compact batch found count: `{final_judge.get('compact_negative_batch_found_count')}`",
        f"- compact batch search calls: `{final_judge.get('compact_negative_batch_search_call_count')}`",
        f"- compact no-good scope: `{final_judge.get('compact_negative_no_good_scope')}`",
        f"- optimization harvest target: `{final_judge.get('compact_optimization_harvest_target')}`",
        f"- optimization harvest no-good scope: `{final_judge.get('compact_optimization_harvest_no_good_scope')}`",
        f"- optimization harvest found count: `{final_judge.get('compact_optimization_harvest_found_count')}`",
        f"- forbidden task-set count: `{final_judge.get('forbidden_task_set_count')}`",
        f"- can_certify_no_negative: `{final_judge.get('can_certify_no_negative')}`",
        f"- best_reduced_cost: `{final_judge.get('best_reduced_cost')}`",
        f"- final_judge_wall_time: `{final_judge.get('final_judge_wall_time')}`",
        f"- resume source: `{payload.get('config', {}).get('resume_probe', '')}`",
        f"- resume initial columns: `{payload.get('config', {}).get('resume_initial_column_count', 0)}`",
        f"- active columns saved: `{len(payload.get('active_columns') or [])}`",
        "",
        "证书边界：restricted negative-feasibility discovery 只能返回人工 RC 审计过的负列；不能证明 no-negative。",
    ]
    history = payload.get("history") or []
    if history:
        lines.extend(["", "## Pricing History", ""])
        lines.append("| round | state | added | best RC | dual bound | phase |")
        lines.append("|---:|---|---:|---:|---:|---|")
        for row in history:
            lines.append(
                "| "
                f"{row.get('round')} | "
                f"{row.get('pricing_state')} | "
                f"{row.get('added_column_count')} | "
                f"{row.get('best_reduced_cost')} | "
                f"{row.get('dual_bound')} | "
                f"{(final_judge if row is history[-1] else {}).get('compact_pricing_phase', '')} |"
            )
    return "\n".join(lines) + "\n"


def _resolve(path: str | Path) -> Path:
    raw = Path(path)
    return raw if raw.is_absolute() else ROOT / raw


def _load_resume_payload(path: str | Path) -> dict:
    if not str(path):
        return {}
    resume_path = _resolve(path)
    payload = json.loads(resume_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"resume probe must contain a JSON object: {resume_path}")
    return payload


def _resume_initial_columns(data, resume_payload: dict) -> tuple | None:
    if not resume_payload:
        return None
    if resume_payload.get("instance_id") not in {None, "", data.instance_id}:
        raise ValueError(
            f"resume probe instance_id={resume_payload.get('instance_id')!r} "
            f"does not match current instance_id={data.instance_id!r}"
        )
    active_payloads = resume_payload.get("active_columns") or []
    if not active_payloads:
        raise ValueError("resume probe does not contain active_columns; rerun with --write-active-columns")
    return tuple(journey_column_from_solution_payload(data, row) for row in active_payloads)


if __name__ == "__main__":
    raise SystemExit(main())
