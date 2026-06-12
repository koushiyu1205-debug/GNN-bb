#!/usr/bin/env python3
"""Run audit-only Sharded Pulse ROI calibration on a small fixed matrix."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from BPC_future.core.data import load_future_data
from BPC_future.core.fleet_bound import apply_fleet_bound_override
from BPC_future.pricing.trip_pricing import _clear_sequence_resource_precheck_cache
from BPC_future.solver.journey_driver import solve_bpc_future_journey
from BPC_future.solver.logger import FutureLogger


BALANCED_ROOT = Path("BPC_future/data/generated/moon_trek_balanced_60_20260609/logical_graphs")

INSTANCE_PRESETS: dict[str, str] = {
    "very_small": "very_small",
    "apollo5": str(
        BALANCED_ROOT
        / "apollo15_20km/tasks_05/apollo15_20km_balanced_tasks05_01_seed36000_logical_graph.json"
    ),
    "tranq5": str(
        BALANCED_ROOT
        / "tranquillitatis_balmer_like_20km/tasks_05/"
        / "tranquillitatis_balmer_like_20km_balanced_tasks05_01_seed136000_logical_graph.json"
    ),
    "apollo10": str(
        BALANCED_ROOT
        / "apollo15_20km/tasks_10/apollo15_20km_balanced_tasks10_01_seed41002_logical_graph.json"
    ),
    "tranq10_09": str(
        BALANCED_ROOT
        / "tranquillitatis_balmer_like_20km/tasks_10/"
        / "tranquillitatis_balmer_like_20km_balanced_tasks10_09_seed141817_logical_graph.json"
    ),
}

ROI_PRESETS: dict[str, dict[str, float | int]] = {
    "low": {
        "prune_rate_floor": 0.001,
        "min_expanded": 10,
        "min_time": 0.0,
    },
    "mid": {
        "prune_rate_floor": 0.01,
        "min_expanded": 25,
        "min_time": 0.01,
    },
    "high": {
        "prune_rate_floor": 0.05,
        "min_expanded": 50,
        "min_time": 0.02,
    },
}

PROFILE_ORDER = (
    "baseline",
    "audit_no_refine",
    "audit_refine",
    "audit_refine_roi_low",
    "audit_refine_roi_mid",
    "audit_refine_roi_high",
)
VALID_PROFILES = (*PROFILE_ORDER, "audit_only", "audit_plus_strict_worker")

SUMMARY_FIELDS = (
    "instance",
    "profile",
    "tasks",
    "official_status",
    "official_primal_bound",
    "official_dual_bound",
    "official_gap",
    "official_pricing_state",
    "official_best_rc",
    "official_unchanged_vs_baseline",
    "audit_events",
    "pulse_audit_skipped",
    "pulse_audit_skip_reason",
    "pulse_audit_trigger",
    "pulse_audit_status",
    "pulse_audit_comparison_type",
    "pulse_audit_disagreement_severity",
    "pulse_audit_time",
    "pulse_audit_recursions",
    "pulse_audit_shards_total",
    "pulse_audit_shards_certified",
    "pulse_audit_shards_incomplete",
    "pulse_audit_shards_negative",
    "pulse_audit_shards_refined",
    "pulse_audit_low_roi_shards",
    "pulse_audit_bound_pruned",
    "pulse_audit_archive_pruned",
    "pulse_audit_time_window_pruned",
    "pulse_audit_energy_pruned",
    "pulse_audit_return_pruned",
    "pulse_audit_capacity_pruned",
    "pulse_audit_pulse_energy_pruned",
    "pulse_audit_negative_pool_size",
    "pulse_audit_harvested_count",
    "worker_events",
    "pulse_worker_skipped",
    "pulse_worker_skip_reason",
    "pulse_worker_trigger",
    "pulse_worker_previous_audit_signal",
    "pulse_worker_status",
    "pulse_worker_returned_journeys",
    "pulse_worker_added_journeys",
    "pulse_worker_true_rc_filtered",
    "pulse_worker_time",
    "pulse_worker_recursions",
    "pulse_worker_shards_negative",
    "pulse_worker_context_hash",
    "critical_disagreement",
    "log_path",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit-only Sharded Pulse ROI calibration.")
    parser.add_argument("--output-dir", default="BPC_future/results/sharded_pulse_phase7l_roi_calibration_20260612")
    parser.add_argument("--instances", nargs="*", default=list(INSTANCE_PRESETS))
    parser.add_argument("--profiles", nargs="*", default=list(PROFILE_ORDER))
    parser.add_argument("--time-limit", type=float, default=8.0)
    parser.add_argument("--audit-time-limit", type=float, default=0.5)
    parser.add_argument("--worker-time-limit", type=float, default=0.5)
    parser.add_argument("--pricing-time-limit", type=float, default=0.2)
    parser.add_argument("--max-cg-iterations", type=int, default=3)
    parser.add_argument("--audit-max-recursions", type=int, default=100000)
    parser.add_argument("--worker-max-recursions", type=int, default=100000)
    parser.add_argument("--audit-negative-harvest-limit", type=int, default=16)
    parser.add_argument("--worker-negative-harvest-limit", type=int, default=16)
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    log_dir = output_dir / "logs"
    output_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    summaries: list[dict[str, Any]] = []
    baseline_by_instance: dict[str, dict[str, Any]] = {}
    for instance_key in args.instances:
        instance_name, locator = _resolve_instance(instance_key)
        for profile in args.profiles:
            if profile not in VALID_PROFILES:
                raise ValueError(f"Unknown profile {profile!r}; expected one of {VALID_PROFILES}")
            row = _run_profile(
                instance_name,
                locator,
                profile,
                args,
                log_dir=log_dir,
            )
            if profile == "baseline":
                baseline_by_instance[instance_name] = row
                row["official_unchanged_vs_baseline"] = True
            else:
                row["official_unchanged_vs_baseline"] = _official_unchanged(
                    baseline_by_instance.get(instance_name),
                    row,
                )
            summaries.append(row)
            if not bool(args.quiet):
                print(
                    f"{instance_name}/{profile}: status={row['official_status']} "
                    f"pricing={row['official_pricing_state']} audit={row['pulse_audit_status']} "
                    f"severity={row['pulse_audit_disagreement_severity']} "
                    f"unchanged={row['official_unchanged_vs_baseline']}",
                    flush=True,
                )

    summary_json = output_dir / "summary.json"
    summary_csv = output_dir / "summary.csv"
    summary_json.write_text(json.dumps(summaries, indent=2, ensure_ascii=False), encoding="utf-8")
    with summary_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(SUMMARY_FIELDS))
        writer.writeheader()
        writer.writerows([{key: row.get(key) for key in SUMMARY_FIELDS} for row in summaries])
    print(f"Phase 7L ROI calibration summary written: {summary_json}")
    print(f"Phase 7L ROI calibration CSV written: {summary_csv}")


def _resolve_instance(instance: str) -> tuple[str, str]:
    if instance in INSTANCE_PRESETS:
        return instance, INSTANCE_PRESETS[instance]
    path = Path(instance)
    if path.exists():
        return path.stem.replace("_logical_graph", ""), str(path)
    raise ValueError(f"Unknown instance {instance!r}; expected preset or existing logical graph path")


def _run_profile(
    instance_name: str,
    locator: str,
    profile: str,
    args: argparse.Namespace,
    *,
    log_dir: Path,
) -> dict[str, Any]:
    _clear_sequence_resource_precheck_cache()
    config = _base_config(args)
    _apply_profile(config, profile, args)
    data = load_future_data(locator)
    data, _fleet_diag = apply_fleet_bound_override(data, config)
    log_path = log_dir / f"{instance_name}__{profile}.jsonl"
    logger = FutureLogger(log_path, console=False)
    try:
        result = solve_bpc_future_journey(data, config, logger=logger)
    finally:
        logger.close()
        _clear_sequence_resource_precheck_cache()
    records = _read_jsonl(log_path)
    official_pricing = _last_official_pricing(records)
    audits = [record for record in records if record.get("event") == "journey_sharded_pulse_audit"]
    audit = _last_real_audit(audits) or (audits[-1] if audits else {})
    worker_events = [
        record
        for record in records
        if record.get("event") == "journey_sharded_pulse_hidden_negative_worker"
    ]
    worker = _last_real_worker(worker_events) or (worker_events[-1] if worker_events else {})
    inferred_skip_reason = ""
    if profile != "baseline" and not audits:
        inferred_skip_reason = "legacy_not_called"
    row = {
        "instance": instance_name,
        "profile": profile,
        "tasks": len(tuple(data.tasks)),
        "official_status": str(result.status),
        "official_primal_bound": result.primal_bound,
        "official_dual_bound": result.dual_bound,
        "official_gap": result.gap,
        "official_pricing_state": official_pricing.get("pricing_state", ""),
        "official_best_rc": official_pricing.get("best_reduced_cost"),
        "official_unchanged_vs_baseline": False,
        "audit_events": len(audits),
        "pulse_audit_skipped": bool(audit.get("pulse_audit_skipped", False)) or bool(inferred_skip_reason),
        "pulse_audit_skip_reason": str(audit.get("pulse_audit_skip_reason", inferred_skip_reason)),
        "pulse_audit_trigger": str(audit.get("pulse_audit_trigger", "")),
        "pulse_audit_status": str(audit.get("pulse_audit_status", "")),
        "pulse_audit_comparison_type": str(audit.get("pulse_audit_comparison_type", "")),
        "pulse_audit_disagreement_severity": str(audit.get("pulse_audit_disagreement_severity", "")),
        "pulse_audit_time": audit.get("pulse_audit_time"),
        "pulse_audit_recursions": _as_int(audit.get("pulse_audit_recursions")),
        "pulse_audit_shards_total": _as_int(audit.get("pulse_audit_shards_total")),
        "pulse_audit_shards_certified": _as_int(audit.get("pulse_audit_shards_certified")),
        "pulse_audit_shards_incomplete": _as_int(audit.get("pulse_audit_shards_incomplete")),
        "pulse_audit_shards_negative": _as_int(audit.get("pulse_audit_shards_negative")),
        "pulse_audit_shards_refined": _as_int(audit.get("pulse_audit_shards_refined")),
        "pulse_audit_low_roi_shards": _as_int(audit.get("pulse_audit_low_roi_shards")),
        "pulse_audit_bound_pruned": _as_int(audit.get("pulse_audit_bound_pruned")),
        "pulse_audit_archive_pruned": _as_int(audit.get("pulse_audit_archive_pruned")),
        "pulse_audit_time_window_pruned": _as_int(audit.get("pulse_audit_time_window_pruned")),
        "pulse_audit_energy_pruned": _as_int(audit.get("pulse_audit_energy_pruned")),
        "pulse_audit_return_pruned": _as_int(audit.get("pulse_audit_return_pruned")),
        "pulse_audit_capacity_pruned": _as_int(audit.get("pulse_audit_capacity_pruned")),
        "pulse_audit_pulse_energy_pruned": _as_int(audit.get("pulse_audit_pulse_energy_pruned")),
        "pulse_audit_negative_pool_size": _as_int(audit.get("pulse_audit_negative_pool_size")),
        "pulse_audit_harvested_count": _as_int(audit.get("pulse_audit_harvested_count")),
        "worker_events": len(worker_events),
        "pulse_worker_skipped": bool(worker.get("pulse_worker_skipped", False)),
        "pulse_worker_skip_reason": str(worker.get("pulse_worker_skip_reason", "")),
        "pulse_worker_trigger": str(worker.get("pulse_worker_trigger", "")),
        "pulse_worker_previous_audit_signal": bool(
            worker.get("pulse_worker_previous_audit_signal", False)
        ),
        "pulse_worker_status": str(worker.get("pulse_worker_status", "")),
        "pulse_worker_returned_journeys": _as_int(worker.get("pulse_worker_returned_journeys")),
        "pulse_worker_added_journeys": _worker_added_journeys(records),
        "pulse_worker_true_rc_filtered": _as_int(worker.get("pulse_worker_true_rc_filtered")),
        "pulse_worker_time": worker.get("pulse_worker_time"),
        "pulse_worker_recursions": _as_int(worker.get("pulse_worker_recursions")),
        "pulse_worker_shards_negative": _as_int(worker.get("pulse_worker_shards_negative")),
        "pulse_worker_context_hash": str(worker.get("pulse_worker_context_hash", "")),
        "critical_disagreement": str(audit.get("pulse_audit_disagreement_severity", "")) == "critical",
        "log_path": str(log_path),
    }
    return row


def _base_config(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "time_limit": float(args.time_limit),
        "journey_max_cg_iterations": int(args.max_cg_iterations),
        "journey_initial_pool_integer_enabled": False,
        "journey_pool_integer_heuristic_enabled": False,
        "journey_pool_time_limit": 0.2,
        "initial_single_task_starts_per_task": 3,
        "journey_initial_source_trip_limit": 500,
        "journey_initial_max_columns": 250,
        "journey_pool_max_columns": 250,
        "journey_pool_max_extensions_per_prefix": 80,
        "journey_pricing_time_limit": float(args.pricing_time_limit),
        "journey_min_pricing_time": 0.0,
        "journey_post_pricing_time_reserve": 0.0,
        "journey_certificate_no_reserve_enabled": True,
        "journey_certificate_no_reserve_min_cg_iter": 1,
        "journey_pricing_profile_pricing_enabled": False,
        "journey_pricing_direct_journey_label_pricing_enabled": False,
        "journey_pricing_max_sequences": 1,
        "journey_pricing_max_timed_evaluations": 1,
        "journey_pricing_max_candidate_trips": 1,
        "journey_pricing_max_dp_states": 1,
        "journey_static_fleet_lb_cut_enabled": False,
        "fleet_bound_mode": "computed",
        "fleet_bound_slack": 1,
        "fleet_bound_cost_safe": True,
        "fleet_bound_max": None,
        "pricing_eps": 1.0e-6,
        "integer_tol": 1.0e-6,
    }


def _apply_profile(config: dict[str, Any], profile: str, args: argparse.Namespace) -> None:
    if profile == "baseline":
        return
    config.update(
        {
            "journey_sharded_pulse_audit_enabled": True,
            "journey_sharded_pulse_audit_after_legacy_final_judge": True,
            "journey_sharded_pulse_audit_trigger": "after_each_final_pricing",
            "journey_sharded_pulse_audit_force_on_root": True,
            "journey_sharded_pulse_audit_log_skips": True,
            "journey_sharded_pulse_audit_time_limit": float(args.audit_time_limit),
            "journey_sharded_pulse_audit_max_recursions": int(args.audit_max_recursions),
            "journey_sharded_pulse_audit_log_disagreements": True,
            "journey_sharded_pulse_audit_allow_certificate_effect": False,
            "journey_sharded_pulse_audit_archive_enabled": True,
            "journey_sharded_pulse_audit_bound_pruning_enabled": True,
            "journey_sharded_pulse_audit_support_aware_harvesting_enabled": True,
            "journey_sharded_pulse_audit_negative_harvest_limit": int(
                args.audit_negative_harvest_limit
            ),
            "journey_sharded_pulse_audit_shard_scheduling_enabled": True,
            "journey_sharded_pulse_hidden_negative_worker_enabled": False,
        }
    )
    if profile in {"audit_no_refine", "audit_only"}:
        return
    config.update(
        {
            "journey_sharded_pulse_audit_adaptive_sharding_enabled": True,
            "journey_sharded_pulse_audit_refine_incomplete_first_task_shards": True,
            "journey_sharded_pulse_audit_refinement_min_recursions": 1,
            "journey_sharded_pulse_audit_refinement_min_expanded": 1,
            "journey_sharded_pulse_audit_refinement_max_children": 64,
        }
    )
    if profile == "audit_refine":
        return
    if profile == "audit_plus_strict_worker":
        config.update(
            {
                "journey_sharded_pulse_audit_shard_roi_gate_enabled": True,
                "journey_sharded_pulse_audit_shard_roi_prune_rate_floor": float(
                    ROI_PRESETS["mid"]["prune_rate_floor"]
                ),
                "journey_sharded_pulse_audit_shard_roi_min_expanded": int(
                    ROI_PRESETS["mid"]["min_expanded"]
                ),
                "journey_sharded_pulse_audit_shard_roi_min_time": float(
                    ROI_PRESETS["mid"]["min_time"]
                ),
                "journey_sharded_pulse_hidden_negative_worker_enabled": True,
                "journey_sharded_pulse_hidden_negative_worker_trigger": "hard_tail_only",
                "journey_sharded_pulse_hidden_negative_worker_log_skips": True,
                "journey_sharded_pulse_hidden_negative_worker_min_tasks": 5,
                "journey_sharded_pulse_hidden_negative_worker_min_remaining_time": 0.0,
                "journey_sharded_pulse_hidden_negative_worker_audit_signal_max_age": 3,
                "journey_sharded_pulse_hidden_negative_worker_time_limit": float(
                    args.worker_time_limit
                ),
                "journey_sharded_pulse_hidden_negative_worker_max_recursions": int(
                    args.worker_max_recursions
                ),
                "journey_sharded_pulse_hidden_negative_worker_archive_enabled": True,
                "journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled": True,
                "journey_sharded_pulse_hidden_negative_worker_harvesting_enabled": True,
                "journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit": int(
                    args.worker_negative_harvest_limit
                ),
                "journey_sharded_pulse_hidden_negative_worker_shard_scheduling_enabled": True,
                "journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled": True,
                "journey_sharded_pulse_hidden_negative_worker_shard_roi_prune_rate_floor": float(
                    ROI_PRESETS["mid"]["prune_rate_floor"]
                ),
                "journey_sharded_pulse_hidden_negative_worker_shard_roi_min_expanded": int(
                    ROI_PRESETS["mid"]["min_expanded"]
                ),
                "journey_sharded_pulse_hidden_negative_worker_shard_roi_min_time": float(
                    ROI_PRESETS["mid"]["min_time"]
                ),
            }
        )
        return
    suffix = profile.removeprefix("audit_refine_roi_")
    preset = ROI_PRESETS[suffix]
    config.update(
        {
            "journey_sharded_pulse_audit_shard_roi_gate_enabled": True,
            "journey_sharded_pulse_audit_shard_roi_prune_rate_floor": float(
                preset["prune_rate_floor"]
            ),
            "journey_sharded_pulse_audit_shard_roi_min_expanded": int(preset["min_expanded"]),
            "journey_sharded_pulse_audit_shard_roi_min_time": float(preset["min_time"]),
        }
    )


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if raw.strip():
            records.append(json.loads(raw))
    return records


def _last_official_pricing(records: list[dict[str, Any]]) -> dict[str, Any]:
    for record in reversed(records):
        if record.get("event") != "journey_pricing":
            continue
        if record.get("pricing_kind") == "sharded_pulse_hidden_negative_worker":
            continue
        if record.get("final_judge_engine") in {"sharded_pulse", "sharded_pulse_dummy"}:
            continue
        return record
    return {}


def _last_real_audit(records: list[dict[str, Any]]) -> dict[str, Any] | None:
    for record in reversed(records):
        if not bool(record.get("pulse_audit_skipped", False)):
            return record
    return None


def _last_real_worker(records: list[dict[str, Any]]) -> dict[str, Any] | None:
    for record in reversed(records):
        if not bool(record.get("pulse_worker_skipped", False)):
            return record
    return None


def _worker_added_journeys(records: list[dict[str, Any]]) -> int:
    total = 0
    for record in records:
        if record.get("event") != "journey_column_addition":
            continue
        if record.get("pricing_kind") != "sharded_pulse_hidden_negative_worker":
            continue
        total += _as_int(record.get("added_journeys"))
    return total


def _official_unchanged(baseline: dict[str, Any] | None, row: dict[str, Any]) -> bool:
    if not baseline:
        return False
    keys = (
        "official_status",
        "official_dual_bound",
        "official_primal_bound",
        "official_pricing_state",
        "official_best_rc",
    )
    return all(_same_value(baseline.get(key), row.get(key)) for key in keys)


def _same_value(left: Any, right: Any) -> bool:
    if left is None or right is None:
        return left is None and right is None
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=1.0e-6)
    return left == right


def _as_int(value: Any) -> int:
    if value is None or value == "":
        return 0
    return int(value)


if __name__ == "__main__":
    main()
