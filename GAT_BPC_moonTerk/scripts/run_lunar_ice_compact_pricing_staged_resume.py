#!/usr/bin/env python3
"""Run resumable compact-pricing batch stages for a single lunar-ice instance."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
BATCH_PROBE = ROOT / "scripts" / "run_lunar_ice_compact_pricing_batch_probe.py"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--stage-count", type=int, default=1)
    parser.add_argument("--stage-time-limit-sec", type=float, default=120.0)
    parser.add_argument("--max-rounds-per-stage", type=int, default=4)
    parser.add_argument("--max-direct-tasks", type=int, default=30)
    parser.add_argument("--seed-mode", default="b0_incumbent_plus_singletons")
    parser.add_argument("--initial-resume-probe", default="")
    parser.add_argument("--batch-target", type=int, default=2)
    parser.add_argument("--negative-search-cap-sec", type=float, default=60.0)
    parser.add_argument(
        "--compact-optimization-harvest-target",
        type=int,
        default=5,
        help="Target for restricted optimization-proof harvesting after the first unrestricted negative.",
    )
    parser.add_argument(
        "--compact-optimization-harvest-no-good-scope",
        choices=("arc", "task_set", "arc_and_task_set"),
        default="task_set",
        help=(
            "No-good scope for restricted optimization harvest. The default task_set "
            "matches B4.1's new-task-set tail objective."
        ),
    )
    parser.add_argument(
        "--compact-final-judge-profile",
        choices=(
            "B4V2",
            "V4",
            "V4S",
            "V4SR",
            "V4SC",
            "V4SZ",
            "V4SZW",
            "V4SZCAP",
            "V4SZPC",
            "V4SL",
            "V4ST",
            "V4SZT",
            "V4SZTP",
            "V4SH",
        ),
        default="",
        help="Optional compact final judge diagnostic profile. Empty preserves current environment/default.",
    )
    parser.add_argument(
        "--compact-final-judge-phase-mode",
        choices=("harvest_then_proof", "proof_only", "feasibility_proof_only"),
        default="",
        help=(
            "Optional compact final judge phase mode. proof_only skips negative-feasibility discovery; "
            "feasibility_proof_only runs a full-space RC<=-eps feasibility proof."
        ),
    )
    parser.add_argument(
        "--compact-service-start-depot-travel-lb",
        action="store_true",
        help="Opt in to exact-safe compact pricing service-start depot-travel lower-bound rows.",
    )
    parser.add_argument(
        "--compact-task-to-depot-return-travel-lb",
        action="store_true",
        help="Opt in to exact-safe compact pricing task-to-depot return lower-bound rows.",
    )
    parser.add_argument(
        "--compact-pair-route-duration-lb",
        action="store_true",
        help="Opt in to exact-safe compact pricing same-sortie task-pair route-duration lower-bound rows.",
    )
    parser.add_argument(
        "--compact-pair-weighted-completion-lb",
        action="store_true",
        help="Opt in to exact-safe compact pricing same-sortie task-pair weighted-completion lower-bound rows.",
    )
    parser.add_argument(
        "--compact-sortie-slot-position-bounds",
        action="store_true",
        help="Opt in to exact-safe compact pricing slot-position start/end bound rows.",
    )
    parser.add_argument(
        "--compact-demand-cover-cut",
        action="store_true",
        help="Opt in to sparse exact-safe same-sortie demand cover cuts.",
    )
    parser.add_argument(
        "--compact-single-task-energy-lb",
        action="store_true",
        help="Opt in to exact-safe compact pricing single-task sortie energy lower-bound rows.",
    )
    parser.add_argument(
        "--compact-single-task-shadow-lb",
        action="store_true",
        help="Opt in to exact-safe compact pricing single-task sortie shadow-exposure lower-bound rows.",
    )
    parser.add_argument(
        "--compact-pair-energy-lb",
        action="store_true",
        help="Opt in to exact-safe compact pricing same-sortie task-pair energy lower-bound rows.",
    )
    parser.add_argument(
        "--compact-pair-energy-infeasible-cut",
        action="store_true",
        help="Opt in to sparse exact-safe same-sortie cuts for task pairs whose energy lower bound exceeds the sortie limit.",
    )
    parser.add_argument(
        "--compact-pair-shadow-infeasible-cut",
        action="store_true",
        help="Opt in to sparse exact-safe same-sortie cuts for task pairs whose shadow lower bound exceeds the sortie limit.",
    )
    parser.add_argument(
        "--compact-triple-time-window-infeasible-cut",
        action="store_true",
        help="Opt in to exact-safe same-sortie cuts for task triples infeasible under all time-window orderings.",
    )
    parser.add_argument(
        "--compact-quad-time-window-infeasible-cut",
        action="store_true",
        help="Opt in to exact-safe same-sortie cuts for task quads infeasible under all time-window orderings.",
    )
    parser.add_argument(
        "--compact-triple-shadow-infeasible-cut",
        action="store_true",
        help="Opt in to sparse exact-safe same-sortie cuts for task triples whose shadow lower bound exceeds the sortie limit.",
    )
    parser.add_argument(
        "--compact-triple-energy-infeasible-cut",
        action="store_true",
        help="Opt in to sparse exact-safe same-sortie cuts for task triples whose energy lower bound exceeds the sortie limit.",
    )
    parser.add_argument("--stop-on-certificate", dest="stop_on_certificate", action="store_true", default=True)
    parser.add_argument("--no-stop-on-certificate", dest="stop_on_certificate", action="store_false")
    args = parser.parse_args()

    instance_path = _resolve(args.instance)
    output_dir = _resolve(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "staged_resume_manifest.json"
    report_path = output_dir / "staged_resume_report_zh.md"

    manifest = _load_manifest(manifest_path)
    resume_probe = _initial_resume_probe(args, manifest)
    rows = list(manifest.get("stages") or [])
    rows = _refresh_stage_rows(rows)
    if rows:
        manifest = {**manifest, "stages": rows}
        _write_manifest(manifest_path, manifest)
    next_index = _next_stage_index(output_dir, rows)

    for offset in range(max(0, int(args.stage_count))):
        stage_index = next_index + offset
        stage_dir = output_dir / f"stage_{stage_index:03d}"
        stage_dir.mkdir(parents=True, exist_ok=True)
        stage_config = {
            "stage_time_limit_sec": float(args.stage_time_limit_sec),
            "max_rounds_per_stage": int(args.max_rounds_per_stage),
            "max_direct_tasks": int(args.max_direct_tasks),
            "seed_mode": str(args.seed_mode),
            "batch_target": int(args.batch_target),
            "negative_search_cap_sec": float(args.negative_search_cap_sec),
            "compact_optimization_harvest_target": int(args.compact_optimization_harvest_target),
            "compact_optimization_harvest_no_good_scope": str(
                args.compact_optimization_harvest_no_good_scope
            ),
            "compact_final_judge_profile": str(args.compact_final_judge_profile or ""),
            "compact_final_judge_phase_mode": str(args.compact_final_judge_phase_mode or ""),
            "compact_service_start_depot_travel_lb": bool(args.compact_service_start_depot_travel_lb),
            "compact_task_to_depot_return_travel_lb": bool(args.compact_task_to_depot_return_travel_lb),
            "compact_pair_route_duration_lb": bool(args.compact_pair_route_duration_lb),
            "compact_pair_weighted_completion_lb": bool(args.compact_pair_weighted_completion_lb),
            "compact_sortie_slot_position_bounds": bool(args.compact_sortie_slot_position_bounds),
            "compact_demand_cover_cut": bool(args.compact_demand_cover_cut),
            "compact_single_task_energy_lb": bool(args.compact_single_task_energy_lb),
            "compact_single_task_shadow_lb": bool(args.compact_single_task_shadow_lb),
            "compact_pair_energy_lb": bool(args.compact_pair_energy_lb),
            "compact_pair_energy_infeasible_cut": bool(args.compact_pair_energy_infeasible_cut),
            "compact_pair_shadow_infeasible_cut": bool(args.compact_pair_shadow_infeasible_cut),
            "compact_triple_time_window_infeasible_cut": bool(args.compact_triple_time_window_infeasible_cut),
            "compact_quad_time_window_infeasible_cut": bool(args.compact_quad_time_window_infeasible_cut),
            "compact_triple_shadow_infeasible_cut": bool(args.compact_triple_shadow_infeasible_cut),
            "compact_triple_energy_infeasible_cut": bool(args.compact_triple_energy_infeasible_cut),
        }
        command = [
            sys.executable,
            str(BATCH_PROBE),
            "--instance",
            str(instance_path),
            "--output-dir",
            str(stage_dir),
            "--time-limit-sec",
            str(float(args.stage_time_limit_sec)),
            "--max-rounds",
            str(int(args.max_rounds_per_stage)),
            "--max-direct-tasks",
            str(int(args.max_direct_tasks)),
            "--seed-mode",
            str(args.seed_mode),
            "--write-active-columns",
        ]
        if resume_probe:
            command.extend(["--resume-probe", str(resume_probe)])

        env = os.environ.copy()
        env["PYTHONPATH"] = _prepend_pythonpath(env.get("PYTHONPATH", ""), ROOT / "src")
        env["LUNAR_ICE_COMPACT_NEGATIVE_BATCH_TARGET"] = str(int(args.batch_target))
        env["LUNAR_ICE_COMPACT_NEGATIVE_SEARCH_CAP_SEC"] = str(float(args.negative_search_cap_sec))
        env["LUNAR_ICE_COMPACT_OPTIMIZATION_HARVEST_TARGET"] = str(
            max(1, int(args.compact_optimization_harvest_target))
        )
        env["LUNAR_ICE_COMPACT_OPTIMIZATION_HARVEST_NO_GOOD_SCOPE"] = str(
            args.compact_optimization_harvest_no_good_scope
        )
        if str(args.compact_final_judge_profile or ""):
            env["LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE"] = str(args.compact_final_judge_profile)
        if str(args.compact_final_judge_phase_mode or ""):
            env["LUNAR_ICE_COMPACT_FINAL_JUDGE_PHASE_MODE"] = str(args.compact_final_judge_phase_mode)
        if bool(args.compact_service_start_depot_travel_lb):
            env["LUNAR_ICE_COMPACT_SERVICE_START_DEPOT_TRAVEL_LB"] = "1"
        if bool(args.compact_task_to_depot_return_travel_lb):
            env["LUNAR_ICE_COMPACT_TASK_TO_DEPOT_RETURN_TRAVEL_LB"] = "1"
        if bool(args.compact_pair_route_duration_lb):
            env["LUNAR_ICE_COMPACT_PAIR_ROUTE_DURATION_LB"] = "1"
        if bool(args.compact_pair_weighted_completion_lb):
            env["LUNAR_ICE_COMPACT_PAIR_WEIGHTED_COMPLETION_LB"] = "1"
        if bool(args.compact_sortie_slot_position_bounds):
            env["LUNAR_ICE_COMPACT_SORTIE_SLOT_POSITION_BOUNDS"] = "1"
        if bool(args.compact_demand_cover_cut):
            env["LUNAR_ICE_COMPACT_DEMAND_COVER_CUT"] = "1"
        if bool(args.compact_single_task_energy_lb):
            env["LUNAR_ICE_COMPACT_SINGLE_TASK_ENERGY_LB"] = "1"
        if bool(args.compact_single_task_shadow_lb):
            env["LUNAR_ICE_COMPACT_SINGLE_TASK_SHADOW_LB"] = "1"
        if bool(args.compact_pair_energy_lb):
            env["LUNAR_ICE_COMPACT_PAIR_ENERGY_LB"] = "1"
        if bool(args.compact_pair_energy_infeasible_cut):
            env["LUNAR_ICE_COMPACT_PAIR_ENERGY_INFEASIBLE_CUT"] = "1"
        if bool(args.compact_pair_shadow_infeasible_cut):
            env["LUNAR_ICE_COMPACT_PAIR_SHADOW_INFEASIBLE_CUT"] = "1"
        if bool(args.compact_triple_time_window_infeasible_cut):
            env["LUNAR_ICE_COMPACT_TRIPLE_TIME_WINDOW_INFEASIBLE_CUT"] = "1"
        if bool(args.compact_quad_time_window_infeasible_cut):
            env["LUNAR_ICE_COMPACT_QUAD_TIME_WINDOW_INFEASIBLE_CUT"] = "1"
        if bool(args.compact_triple_shadow_infeasible_cut):
            env["LUNAR_ICE_COMPACT_TRIPLE_SHADOW_INFEASIBLE_CUT"] = "1"
        if bool(args.compact_triple_energy_infeasible_cut):
            env["LUNAR_ICE_COMPACT_TRIPLE_ENERGY_INFEASIBLE_CUT"] = "1"

        completed = subprocess.run(
            command,
            cwd=str(ROOT),
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        (stage_dir / "stdout.txt").write_text(completed.stdout, encoding="utf-8")
        (stage_dir / "stderr.txt").write_text(completed.stderr, encoding="utf-8")
        if completed.returncode != 0:
            _write_manifest(
                manifest_path,
                {
                    **manifest,
                    "stages": rows,
                    "last_error": {
                        "stage_index": stage_index,
                        "returncode": completed.returncode,
                        "stdout": completed.stdout[-4000:],
                        "stderr": completed.stderr[-4000:],
                    },
                },
            )
            raise SystemExit(completed.returncode)

        probe_path = stage_dir / "probe.json"
        probe = json.loads(probe_path.read_text(encoding="utf-8"))
        row = _stage_row(stage_index, probe_path, probe, stage_config=stage_config)
        rows.append(row)
        resume_probe = probe_path
        manifest = {
            "schema_version": "lunar_ice_bpc.compact_pricing_staged_resume.v1",
            "instance_path": str(instance_path),
            "output_dir": str(output_dir),
            "config": {
                "stage_time_limit_sec": float(args.stage_time_limit_sec),
                "max_rounds_per_stage": int(args.max_rounds_per_stage),
                "max_direct_tasks": int(args.max_direct_tasks),
                "seed_mode": str(args.seed_mode),
                "batch_target": int(args.batch_target),
                "negative_search_cap_sec": float(args.negative_search_cap_sec),
                "compact_optimization_harvest_target": int(args.compact_optimization_harvest_target),
                "compact_optimization_harvest_no_good_scope": str(
                    args.compact_optimization_harvest_no_good_scope
                ),
                "compact_final_judge_profile": str(args.compact_final_judge_profile or ""),
                "compact_final_judge_phase_mode": str(args.compact_final_judge_phase_mode or ""),
                "compact_service_start_depot_travel_lb": bool(args.compact_service_start_depot_travel_lb),
                "compact_task_to_depot_return_travel_lb": bool(args.compact_task_to_depot_return_travel_lb),
                "compact_pair_route_duration_lb": bool(args.compact_pair_route_duration_lb),
                "compact_pair_weighted_completion_lb": bool(args.compact_pair_weighted_completion_lb),
                "compact_sortie_slot_position_bounds": bool(args.compact_sortie_slot_position_bounds),
                "compact_demand_cover_cut": bool(args.compact_demand_cover_cut),
                "compact_single_task_energy_lb": bool(args.compact_single_task_energy_lb),
                "compact_single_task_shadow_lb": bool(args.compact_single_task_shadow_lb),
                "compact_pair_energy_lb": bool(args.compact_pair_energy_lb),
                "compact_pair_energy_infeasible_cut": bool(args.compact_pair_energy_infeasible_cut),
                "compact_pair_shadow_infeasible_cut": bool(args.compact_pair_shadow_infeasible_cut),
                "compact_triple_time_window_infeasible_cut": bool(args.compact_triple_time_window_infeasible_cut),
                "compact_quad_time_window_infeasible_cut": bool(args.compact_quad_time_window_infeasible_cut),
                "compact_triple_shadow_infeasible_cut": bool(args.compact_triple_shadow_infeasible_cut),
                "compact_triple_energy_infeasible_cut": bool(args.compact_triple_energy_infeasible_cut),
            },
            "latest_probe": str(resume_probe),
            "stages": rows,
        }
        _write_manifest(manifest_path, manifest)
        report_path.write_text(_render_report(manifest), encoding="utf-8")

        if bool(args.stop_on_certificate) and row["certificate_scope"] == "BPC_NODE_LP_CERTIFIED":
            break

    report_path.write_text(_render_report(manifest), encoding="utf-8")
    print(json.dumps(_console_summary(manifest), ensure_ascii=False))
    print(f"report {report_path}")
    return 0


def _resolve(path: str | Path) -> Path:
    raw = Path(path)
    return raw if raw.is_absolute() else ROOT / raw


def _prepend_pythonpath(existing: str, path: Path) -> str:
    if not existing:
        return str(path)
    return f"{path}{os.pathsep}{existing}"


def _load_manifest(path: Path) -> dict:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"manifest must contain a JSON object: {path}")
    return payload


def _initial_resume_probe(args: argparse.Namespace, manifest: dict) -> Path | None:
    latest = manifest.get("latest_probe")
    if latest:
        return _resolve(latest)
    if str(args.initial_resume_probe):
        return _resolve(args.initial_resume_probe)
    return None


def _next_stage_index(output_dir: Path, rows: list[dict]) -> int:
    from_rows = [int(row.get("stage_index", 0)) for row in rows if int(row.get("stage_index", 0)) > 0]
    from_dirs = []
    for path in output_dir.glob("stage_*"):
        if path.is_dir():
            try:
                from_dirs.append(int(path.name.split("_", 1)[1]))
            except (IndexError, ValueError):
                pass
    return max([0, *from_rows, *from_dirs]) + 1


def _refresh_stage_rows(rows: list[dict]) -> list[dict]:
    refreshed: list[dict] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        probe_path_value = row.get("probe_path")
        if not probe_path_value:
            refreshed.append(row)
            continue
        probe_path = _resolve(probe_path_value)
        if not probe_path.exists():
            refreshed.append(row)
            continue
        try:
            probe = json.loads(probe_path.read_text(encoding="utf-8"))
            rebuilt = _stage_row(
                int(row.get("stage_index") or len(refreshed) + 1),
                probe_path,
                probe,
                stage_config=row,
            )
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            refreshed.append(row)
            continue
        merged = dict(row)
        merged.update(rebuilt)
        refreshed.append(merged)
    return refreshed


def _stage_row(stage_index: int, probe_path: Path, probe: dict, *, stage_config: dict | None = None) -> dict:
    history = list(probe.get("history") or [])
    best_rc_values = [
        row.get("best_reduced_cost")
        for row in history
        if isinstance(row.get("best_reduced_cost"), (int, float))
    ]
    negative_rc_values = [value for value in best_rc_values if float(value) < 0.0]
    final_judge = probe.get("final_judge") if isinstance(probe.get("final_judge"), dict) else {}
    optimization_phase_summary = _optimization_phase_summary(final_judge)
    proof_phase_summary = _proof_phase_summary(final_judge)
    config = dict(stage_config or {})
    return {
        "stage_index": int(stage_index),
        "probe_path": str(probe_path),
        "stage_time_limit_sec": config.get("stage_time_limit_sec"),
        "max_rounds_per_stage": config.get("max_rounds_per_stage"),
        "batch_target": config.get("batch_target"),
        "negative_search_cap_sec": config.get("negative_search_cap_sec"),
        "compact_final_judge_profile": (probe.get("final_judge") or {}).get(
            "compact_final_judge_profile",
            (probe.get("config") or {}).get("env_compact_final_judge_profile") or config.get("compact_final_judge_profile"),
        ),
        "compact_final_judge_formulation_profile": (probe.get("final_judge") or {}).get(
            "compact_final_judge_formulation_profile"
        ),
        "compact_final_judge_phase_mode": (probe.get("final_judge") or {}).get(
            "compact_final_judge_phase_mode",
            (probe.get("config") or {}).get("env_compact_final_judge_phase_mode") or config.get("compact_final_judge_phase_mode"),
        ),
        "negative_feasibility_skipped_for_proof_only": bool(
            (probe.get("final_judge") or {}).get("negative_feasibility_skipped_for_proof_only")
        ),
        "negative_feasibility_full_space_proof_attempted": bool(
            (probe.get("final_judge") or {}).get("negative_feasibility_full_space_proof_attempted")
        ),
        "negative_feasibility_full_space_proof_can_certify": bool(
            (probe.get("final_judge") or {}).get("negative_feasibility_full_space_proof_can_certify")
        ),
        "elapsed_sec": probe.get("elapsed_sec"),
        "algorithm_status": probe.get("algorithm_status"),
        "certificate_scope": probe.get("certificate_scope"),
        "pricing_state": probe.get("pricing_state"),
        "pricing_round_count": probe.get("pricing_round_count"),
        "added_column_count": probe.get("added_column_count"),
        "active_column_count": len(probe.get("active_columns") or []),
        "resume_initial_column_count": (probe.get("config") or {}).get("resume_initial_column_count", 0),
        "final_judge_found_negative_count": probe.get("final_judge_found_negative_count"),
        "final_judge_incomplete_count": probe.get("final_judge_incomplete_count"),
        "best_negative_reduced_cost": min(negative_rc_values) if negative_rc_values else None,
        "final_compact_phase": final_judge.get("compact_pricing_phase"),
        "compact_optimization_harvest_target": final_judge.get(
            "compact_optimization_harvest_target",
            config.get("compact_optimization_harvest_target"),
        ),
        "compact_optimization_harvest_no_good_scope": final_judge.get(
            "compact_optimization_harvest_no_good_scope",
            config.get("compact_optimization_harvest_no_good_scope"),
        ),
        "compact_optimization_harvest_found_count": final_judge.get(
            "compact_optimization_harvest_found_count"
        ),
        "compact_optimization_harvest_search_call_count": final_judge.get(
            "compact_optimization_harvest_search_call_count"
        ),
        **optimization_phase_summary,
        **proof_phase_summary,
        "final_best_reduced_cost": final_judge.get("best_reduced_cost"),
        "final_dual_bound": final_judge.get("dual_bound", final_judge.get("bound")),
        "final_can_certify_no_negative": bool(final_judge.get("can_certify_no_negative")),
        "sortie_slot_position_bounds_enabled": bool(final_judge.get("sortie_slot_position_bounds_enabled")),
        "sortie_slot_position_bound_count": final_judge.get("sortie_slot_position_bound_count"),
    }


def _optimization_phase_summary(final_judge: dict) -> dict:
    phase_payloads = final_judge.get("compact_pricing_phase_payloads")
    if not isinstance(phase_payloads, dict):
        phase_payloads = {}
    optimization_rows = [
        row
        for key, row in phase_payloads.items()
        if str(key).startswith("optimization") and isinstance(row, dict)
    ]
    exact_negative = 0
    time_limit_negative = 0
    time_limit_no_negative = 0
    total_wall = 0.0
    for row in optimization_rows:
        status = str(row.get("status") or "")
        pricing_state = str(row.get("pricing_state") or "")
        negative_found = bool(row.get("negative_found") or pricing_state == "FOUND_NEGATIVE")
        try:
            total_wall += float(row.get("wall_time_sec") or 0.0)
        except (TypeError, ValueError):
            pass
        if status == "COMPACT_HIGHS_PRICING_OPTIMAL" and negative_found:
            exact_negative += 1
        elif status == "COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED" and negative_found:
            time_limit_negative += 1
        elif status == "COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED":
            time_limit_no_negative += 1
    return {
        "optimization_phase_count": len(optimization_rows),
        "optimization_exact_negative_count": exact_negative,
        "optimization_time_limit_negative_count": time_limit_negative,
        "optimization_time_limit_no_negative_count": time_limit_no_negative,
        "optimization_phase_total_wall_time": round(total_wall, 6),
    }


def _proof_phase_summary(final_judge: dict) -> dict:
    phase_payloads = final_judge.get("compact_pricing_phase_payloads")
    if not isinstance(phase_payloads, dict):
        phase_payloads = {}
    feasibility = phase_payloads.get("negative_feasibility_proof")
    if not isinstance(feasibility, dict):
        feasibility = {}
    status = str(feasibility.get("status") or "")
    pricing_state = str(feasibility.get("pricing_state") or "")
    negative_found = bool(feasibility.get("negative_found") or pricing_state == "FOUND_NEGATIVE")
    return {
        "feasibility_proof_status": status,
        "feasibility_proof_exact_status": feasibility.get("exact_status") or "",
        "feasibility_proof_negative_found": negative_found,
        "feasibility_proof_best_reduced_cost": feasibility.get("best_reduced_cost"),
        "feasibility_proof_dual_bound": feasibility.get("dual_bound", feasibility.get("bound")),
        "feasibility_proof_wall_time": feasibility.get("wall_time_sec"),
        "feasibility_proof_can_certify": bool(
            final_judge.get("negative_feasibility_full_space_proof_can_certify")
        ),
        "feasibility_proof_time_limit_negative_count": int(
            status == "COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED" and negative_found
        ),
        "feasibility_proof_exact_negative_count": int(
            status in {
                "COMPACT_HIGHS_PRICING_OPTIMAL",
                "COMPACT_HIGHS_NEGATIVE_FEASIBILITY_FOUND",
            }
            and negative_found
        ),
        "feasibility_proof_infeasible_count": int(
            status in {
                "COMPACT_HIGHS_PRICING_INFEASIBLE",
                "COMPACT_HIGHS_NEGATIVE_FEASIBILITY_INFEASIBLE",
            }
            and bool(final_judge.get("negative_feasibility_full_space_proof_can_certify"))
        ),
    }


def _write_manifest(path: Path, manifest: dict) -> None:
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _render_report(manifest: dict) -> str:
    rows = list(manifest.get("stages") or [])
    lines = [
        "# Compact Pricing Staged Resume Report",
        "",
        "该 staged run 只复用 active column pool；每个 stage 都重新解 RMP 和 final judge。",
        "因此 staged resume 不是证书放松，也不会把上一阶段 dual/certificate 带入下一阶段。",
        "",
        f"- instance: `{manifest.get('instance_path', '')}`",
        f"- latest_probe: `{manifest.get('latest_probe', '')}`",
        f"- stage_count: `{len(rows)}`",
        f"- compact_final_judge_profile: `{(manifest.get('config') or {}).get('compact_final_judge_profile', '')}`",
        f"- compact_final_judge_phase_mode: `{(manifest.get('config') or {}).get('compact_final_judge_phase_mode', '')}`",
        f"- compact_optimization_harvest_target: `{(manifest.get('config') or {}).get('compact_optimization_harvest_target', 5)}`",
        f"- compact_optimization_harvest_no_good_scope: `{(manifest.get('config') or {}).get('compact_optimization_harvest_no_good_scope', 'task_set')}`",
        f"- compact_service_start_depot_travel_lb: `{(manifest.get('config') or {}).get('compact_service_start_depot_travel_lb', False)}`",
        f"- compact_task_to_depot_return_travel_lb: `{(manifest.get('config') or {}).get('compact_task_to_depot_return_travel_lb', False)}`",
        f"- compact_pair_route_duration_lb: `{(manifest.get('config') or {}).get('compact_pair_route_duration_lb', False)}`",
        f"- compact_sortie_slot_position_bounds: `{(manifest.get('config') or {}).get('compact_sortie_slot_position_bounds', False)}`",
        f"- compact_demand_cover_cut: `{(manifest.get('config') or {}).get('compact_demand_cover_cut', False)}`",
        f"- compact_single_task_energy_lb: `{(manifest.get('config') or {}).get('compact_single_task_energy_lb', False)}`",
        f"- compact_single_task_shadow_lb: `{(manifest.get('config') or {}).get('compact_single_task_shadow_lb', False)}`",
        f"- compact_pair_energy_lb: `{(manifest.get('config') or {}).get('compact_pair_energy_lb', False)}`",
        f"- compact_pair_energy_infeasible_cut: `{(manifest.get('config') or {}).get('compact_pair_energy_infeasible_cut', False)}`",
        f"- compact_pair_shadow_infeasible_cut: `{(manifest.get('config') or {}).get('compact_pair_shadow_infeasible_cut', False)}`",
        f"- compact_triple_time_window_infeasible_cut: `{(manifest.get('config') or {}).get('compact_triple_time_window_infeasible_cut', False)}`",
        f"- compact_quad_time_window_infeasible_cut: `{(manifest.get('config') or {}).get('compact_quad_time_window_infeasible_cut', False)}`",
        f"- compact_triple_shadow_infeasible_cut: `{(manifest.get('config') or {}).get('compact_triple_shadow_infeasible_cut', False)}`",
        f"- compact_triple_energy_infeasible_cut: `{(manifest.get('config') or {}).get('compact_triple_energy_infeasible_cut', False)}`",
        "",
        "| stage | profile | mode | opt harvest | opt scope | opt found | opt exact neg | opt tl neg | opt tl no-neg | feas status | feas neg | feas cert | feas RC | feas bound | batch | round cap | resume cols | active cols | added | rounds | state | scope | best neg RC | final phase | final RC | final bound | elapsed s |",
        "|---:|---|---|---:|---|---:|---:|---:|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---:|---|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| "
            f"{row.get('stage_index')} | "
            f"{row.get('compact_final_judge_profile', '')} | "
            f"{row.get('compact_final_judge_phase_mode', '')} | "
            f"{row.get('compact_optimization_harvest_target', '')} | "
            f"{row.get('compact_optimization_harvest_no_good_scope', '')} | "
            f"{row.get('compact_optimization_harvest_found_count', '')} | "
            f"{row.get('optimization_exact_negative_count', '')} | "
            f"{row.get('optimization_time_limit_negative_count', '')} | "
            f"{row.get('optimization_time_limit_no_negative_count', '')} | "
            f"{row.get('feasibility_proof_status', '')} | "
            f"{row.get('feasibility_proof_negative_found', '')} | "
            f"{row.get('feasibility_proof_can_certify', '')} | "
            f"{row.get('feasibility_proof_best_reduced_cost', '')} | "
            f"{row.get('feasibility_proof_dual_bound', '')} | "
            f"{row.get('batch_target', '')} | "
            f"{row.get('max_rounds_per_stage', '')} | "
            f"{row.get('resume_initial_column_count')} | "
            f"{row.get('active_column_count')} | "
            f"{row.get('added_column_count')} | "
            f"{row.get('pricing_round_count')} | "
            f"{row.get('pricing_state')} | "
            f"{row.get('certificate_scope')} | "
            f"{row.get('best_negative_reduced_cost')} | "
            f"{row.get('final_compact_phase')} | "
            f"{row.get('final_best_reduced_cost')} | "
            f"{row.get('final_dual_bound')} | "
            f"{row.get('elapsed_sec')} |"
        )
    return "\n".join(lines) + "\n"


def _console_summary(manifest: dict) -> dict:
    rows = list(manifest.get("stages") or [])
    latest = rows[-1] if rows else {}
    return {
        "stage_count": len(rows),
        "latest_stage": latest.get("stage_index"),
        "latest_scope": latest.get("certificate_scope"),
        "latest_state": latest.get("pricing_state"),
        "latest_compact_final_judge_profile": latest.get("compact_final_judge_profile"),
        "latest_compact_final_judge_phase_mode": latest.get("compact_final_judge_phase_mode"),
        "latest_final_best_reduced_cost": latest.get("final_best_reduced_cost"),
        "latest_final_dual_bound": latest.get("final_dual_bound"),
        "latest_active_column_count": latest.get("active_column_count"),
        "latest_added_column_count": latest.get("added_column_count"),
    }


if __name__ == "__main__":
    raise SystemExit(main())
