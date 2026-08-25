"""Six-scale no-cheat native SPPRC acceptance orchestration."""

from __future__ import annotations

from dataclasses import asdict, replace
import hashlib
import json
from math import isfinite
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
from time import perf_counter

from lunar_ice_bpc.exact.bpc.pricing.backends.native_rcspp import effective_memory_limit_gb
from lunar_ice_bpc.exact.bpc.pricing.backends.base import (
    PROOF_QUEUE_EXPERIMENT_ENV,
    PROOF_QUEUE_EXPERIMENT_MODES,
)
from lunar_ice_bpc.exact.bpc.pricing.backends.scale_profiles import (
    NativeSpprcScaleProfile,
    native_spprc_scale_profile,
)
from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import spprc_engine_build_hash


SCHEMA_VERSION = "lunar_ice_bpc.native_spprc_acceptance.v2"
MODEL_ID = "NATIVE_SPPRC_ACCEPTANCE_V1"
LABELING_FINAL_JUDGE_ADAPTIVE_HARVEST_SCHEDULE_ENV = (
    "LUNAR_ICE_LABELING_FINAL_JUDGE_ADAPTIVE_HARVEST_SCHEDULE"
)


def run_native_spprc_acceptance(
    *,
    project_root: Path,
    config: dict,
    scales: tuple[int, ...],
    backend_override: str | None = None,
    instances: tuple[str, ...] = tuple(),
    limit: int = 0,
    output_dir: str | Path = "runs/native_spprc_acceptance",
    resume: bool = False,
    dry_run: bool = False,
    route_opportunity_collection_only_root_pool: bool = False,
    route_opportunity_collection_root_pool_time_cap_sec: float = 0.0,
    effective_memory_cap_gb: float = 0.0,
) -> dict:
    root = Path(project_root).resolve()
    output = _root_path(root, output_dir)
    output.mkdir(parents=True, exist_ok=True)
    selected_instances = _group_instances_by_scale(root, instances)
    rows = []
    started = perf_counter()
    baseline_commit_at_start = _git_head(root)
    for scale in scales:
        proof_queue_experiment = str(
            config.get(
                "native_proof_queue_experiment_policy", "off"
            )
            or "off"
        )
        if proof_queue_experiment not in PROOF_QUEUE_EXPERIMENT_MODES:
            raise ValueError(
                "unsupported native_proof_queue_experiment_policy "
                f"{proof_queue_experiment!r}"
            )
        profile = _profile_from_config(int(scale), config)
        backend_id = str(backend_override or profile.backend_id)
        engine_build_hash_at_start = spprc_engine_build_hash(backend_id)
        final_judge_pass_policy = _final_judge_pass_policy_for_scale(config, int(scale))
        adaptive_harvest_cap_sec = _adaptive_harvest_cap_for_scale(config, int(scale))
        adaptive_harvest_schedule = _adaptive_harvest_schedule_for_scale(
            config, int(scale)
        )
        scale_instances = selected_instances.get(int(scale), tuple())
        if not scale_instances:
            scale_instances = tuple(
                sorted(
                    (root / "data" / "instances" / f"lunar_ice_sp50_{int(scale):03d}").glob(
                        "instance_*_logical_graph.json"
                    )
                )
            )
        if limit:
            scale_instances = scale_instances[: max(0, int(limit))]
        scale_output = output / f"scale_{int(scale):03d}"
        effective_memory = effective_memory_limit_gb(profile.memory_limit_gb)
        if float(effective_memory_cap_gb) > 0.0:
            effective_memory = min(effective_memory, float(effective_memory_cap_gb))
        row = {
            "scale": int(scale),
            "backend_id": backend_id,
            "engine_build_hash_at_start": engine_build_hash_at_start,
            "final_judge_pass_policy": final_judge_pass_policy,
            "adaptive_harvest_cap_sec": adaptive_harvest_cap_sec,
            "adaptive_harvest_schedule": adaptive_harvest_schedule,
            "live_sri_policy": str(config.get("live_sri_policy", "no_cut")),
            "proof_queue_experiment_policy": proof_queue_experiment,
            "profile": asdict(profile),
            "effective_memory_limit_gb": round(effective_memory, 6),
            "externally_capped_memory_limit_gb": (
                float(effective_memory_cap_gb)
                if float(effective_memory_cap_gb) > 0.0 else None
            ),
            "instance_count": len(scale_instances),
            "instances": [str(path) for path in scale_instances],
            "output_dir": str(scale_output),
            "route_opportunity_collection_only_root_pool": bool(
                route_opportunity_collection_only_root_pool
            ),
            "route_opportunity_collection_root_pool_time_cap_sec": float(
                route_opportunity_collection_root_pool_time_cap_sec
            ),
        }
        if not scale_instances:
            row.update(
                {
                    "status": "NO_INSTANCES_AVAILABLE",
                    "returncode": None,
                    "note": "No checkout-local lunar_ice_sp50 directory exists for this scale.",
                }
            )
            rows.append(row)
            continue
        minimum_runtime_memory_gb = float(config.get("minimum_runtime_memory_gb", 1.0))
        available_memory_gb = _available_memory_gb()
        row["available_memory_gb_at_preflight"] = round(available_memory_gb, 6)
        if (
            row["effective_memory_limit_gb"] < minimum_runtime_memory_gb
            or available_memory_gb < minimum_runtime_memory_gb
        ):
            row.update(
                {
                    "status": "RESOURCE_INSUFFICIENT",
                    "returncode": None,
                    "note": (
                        f"Need at least {minimum_runtime_memory_gb:.3f} GiB; "
                        f"effective limit={row['effective_memory_limit_gb']:.3f} GiB, "
                        f"available={available_memory_gb:.3f} GiB."
                    ),
                }
            )
            rows.append(row)
            continue
        command = _b42_command(
            root,
            profile,
            backend_id=backend_id,
            model_id=str(config.get("model_id") or MODEL_ID),
            scale_output=scale_output,
            instances=scale_instances,
            resume=resume,
            live_sri_policy=str(config.get("live_sri_policy", "no_cut")),
            route_opportunity_collection_only_root_pool=bool(
                route_opportunity_collection_only_root_pool
            ),
            route_opportunity_collection_root_pool_time_cap_sec=float(
                route_opportunity_collection_root_pool_time_cap_sec
            ),
        )
        row["command"] = command
        if dry_run:
            row.update({"status": "DRY_RUN", "returncode": 0})
            rows.append(row)
            continue
        scale_output.mkdir(parents=True, exist_ok=True)
        environment = dict(os.environ)
        environment.pop("LUNAR_ICE_LABELING_FINAL_JUDGE_ADAPTIVE_HARVEST_CAP_SEC", None)
        environment.pop(
            LABELING_FINAL_JUDGE_ADAPTIVE_HARVEST_SCHEDULE_ENV,
            None,
        )
        environment.update(
            {
                "PYTHONPATH": _prepend_pythonpath(environment.get("PYTHONPATH"), root / "src"),
                "LUNAR_ICE_SPPRC_EXACT_BACKEND": backend_id,
                "LUNAR_ICE_SPPRC_MEMORY_LIMIT_GB": str(row["effective_memory_limit_gb"]),
                "LUNAR_ICE_SPPRC_GRAPH_CACHE_ENTRIES": str(profile.graph_cache_entries),
                "LUNAR_ICE_SPPRC_COMPLETION_BOUND": (
                    "1" if bool(config.get("native_completion_bound_enabled", False)) else "0"
                ),
                "LUNAR_ICE_SPPRC_SUBSET_DOMINANCE": (
                    "1" if bool(config.get("native_subset_dominance_enabled", False)) else "0"
                ),
                "LUNAR_ICE_SPPRC_CUT_STATE": (
                    "1" if bool(config.get("native_cut_state_enabled", False)) else "0"
                ),
                "LUNAR_ICE_EXACT_NEGATIVE_ESCAPE_ENABLED": (
                    "1"
                    if bool(
                        config.get(
                            "exact_negative_escape_enabled", False
                        )
                    )
                    else "0"
                ),
                "LUNAR_ICE_BATCH_MASTER_ADMISSION_ENABLED": (
                    "1"
                    if bool(
                        config.get(
                            "batch_master_admission_enabled", False
                        )
                    )
                    else "0"
                ),
                "LUNAR_ICE_SPPRC_DSSR_NEGATIVE_BATCH_TARGET": str(
                    max(
                        1,
                        min(
                            64,
                            int(
                                config.get(
                                    "dssr_negative_batch_target",
                                    16,
                                )
                            ),
                        ),
                    )
                ),
                "LUNAR_ICE_SPPRC_DSSR_PRESSURE_MAX_BUCKET_SIZE": str(
                    max(
                        1,
                        int(
                            config.get(
                                "dssr_pressure_max_bucket_size",
                                8192,
                            )
                        ),
                    )
                ),
                "LUNAR_ICE_SPPRC_DSSR_PRESSURE_MAX_CANDIDATE_CHECKS": str(
                    max(
                        1,
                        int(
                            config.get(
                                "dssr_pressure_max_candidate_checks",
                                200_000_000,
                            )
                        ),
                    )
                ),
                "LUNAR_ICE_SPPRC_NG_DSSR_INITIAL_NEIGHBORHOOD_SIZE": str(
                    max(
                        1,
                        min(
                            int(scale),
                            int(
                                config.get(
                                    "ng_dssr_initial_neighborhood_size",
                                    10,
                                )
                            ),
                        ),
                    )
                ),
                PROOF_QUEUE_EXPERIMENT_ENV: proof_queue_experiment,
                "LUNAR_ICE_LABELING_WORKER_NG_SIZES": ",".join(str(value) for value in profile.ng_sizes),
                # The row deadline owns the single clock.  v1 promotes the
                # root exact pricer first, so the candidate worker is skipped
                # at this gate (actual worker time is zero).  Its profile is
                # still carried for later worker-first experiments; those must
                # inherit the same remaining row clock.
                "LUNAR_ICE_LABELING_WORKER_HARD_TIME_CAP_SEC": str(
                    profile.worker_time_limit_sec
                ),
                "LUNAR_ICE_EXACT_FINAL_JUDGE_FIRST": "1",
                "LUNAR_ICE_LABELING_FINAL_JUDGE_PASS_POLICY": final_judge_pass_policy,
            }
        )
        if bool(config.get("pre_solve_exact_snapshot_enabled", False)):
            environment["LUNAR_ICE_PRE_SOLVE_EXACT_SNAPSHOT_DIR"] = str(
                (scale_output / "pre_solve_exact_snapshots").resolve()
            )
        if bool(
            config.get("pre_solve_pricing_snapshot_enabled", False)
        ):
            environment[
                "LUNAR_ICE_PRE_SOLVE_PRICING_SNAPSHOT_DIR"
            ] = str(
                (
                    scale_output / "pre_solve_pricing_snapshots"
                ).resolve()
            )
        _configure_one_deviation_environment(
            environment,
            config=config,
            root=root,
            scale=int(scale),
        )
        if adaptive_harvest_cap_sec is not None:
            environment[
                "LUNAR_ICE_LABELING_FINAL_JUDGE_ADAPTIVE_HARVEST_CAP_SEC"
            ] = str(adaptive_harvest_cap_sec)
        if adaptive_harvest_schedule is not None:
            environment[
                LABELING_FINAL_JUDGE_ADAPTIVE_HARVEST_SCHEDULE_ENV
            ] = adaptive_harvest_schedule
        scale_started = perf_counter()
        completed = subprocess.run(
            command,
            cwd=root,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )
        (scale_output / "native_acceptance_stdout.log").write_text(completed.stdout, encoding="utf-8")
        (scale_output / "native_acceptance_stderr.log").write_text(completed.stderr, encoding="utf-8")
        b42_summary = _read_json(scale_output / "b4_2_cold_exact_summary.json")
        b42_state = _read_json(scale_output / "b4_2_cold_exact_state.json")
        engine_build_hash_at_end = spprc_engine_build_hash(backend_id)
        engine_binding = _engine_binding_audit(
            expected_hash=engine_build_hash_at_start,
            end_hash=engine_build_hash_at_end,
            b42_summary=b42_summary,
        )
        scale_summary = (b42_summary.get("by_scale") or {}).get(str(scale), {})
        exact_count = int(scale_summary.get("exact_count") or 0)
        row_count = int(scale_summary.get("row_count") or 0)
        redlines = b42_summary.get("redlines") or {}
        redlines_zero = bool(redlines) and all(int(value or 0) == 0 for value in redlines.values())
        profile_gate = _profile_gate_metrics(
            profile,
            b42_state=b42_state,
            expected_count=len(scale_instances),
        )
        exact_closed = bool(
            completed.returncode == 0
            and engine_binding["valid"]
            and row_count == len(scale_instances)
            and exact_count == row_count
            and redlines_zero
            and profile_gate["all_exact"]
            and profile_gate["all_no_cheat"]
            and profile_gate["all_under_profile_time_limit"]
        )
        row.update(
            {
                "status": (
                    "RUNNER_FAILED"
                    if completed.returncode != 0
                    else "HASH_DRIFT"
                    if not engine_binding["valid"]
                    else "EXACT_CLOSED"
                    if exact_closed
                    else "FAIL_CLOSED"
                ),
                "returncode": int(completed.returncode),
                "wall_time_sec": round(perf_counter() - scale_started, 6),
                "exact_count": exact_count,
                "fail_closed_count": int(scale_summary.get("fail_closed_count") or 0),
                "redlines_zero": redlines_zero,
                "engine_build_hash_at_end": engine_build_hash_at_end,
                "engine_binding": engine_binding,
                "profile_gate": profile_gate,
                "b42_summary": b42_summary,
            }
        )
        rows.append(row)

    acceptance = _acceptance_metrics(rows)
    summary = {
        "schema_version": SCHEMA_VERSION,
        "model_id": MODEL_ID,
        "cold_start": True,
        "resume_enabled": bool(resume),
        "dry_run": bool(dry_run),
        "baseline_commit": baseline_commit_at_start,
        "baseline_commit_at_end": _git_head(root),
        "config_hash": hashlib.sha256(
            json.dumps(config, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "engine_build_hashes": {
            backend_id: next(
                row["engine_build_hash_at_start"]
                for row in rows
                if row["backend_id"] == backend_id
            )
            for backend_id in sorted({row["backend_id"] for row in rows})
        },
        "engine_hash_drift_count": sum(
            1 for row in rows if row.get("engine_binding", {}).get("valid") is False
        ),
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "cpu_count": os.cpu_count(),
            "physical_memory_gb": round(
                float(os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE"))
                / float(1024**3),
                6,
            ),
        },
        "scales": list(scales),
        "rows": rows,
        "acceptance": acceptance,
        "wall_time_sec": round(perf_counter() - started, 6),
        "all_available_runs_succeeded": all(
            row["status"] in {"EXACT_CLOSED", "DRY_RUN"}
            for row in rows
        ),
        "missing_scales": [row["scale"] for row in rows if row["status"] == "NO_INSTANCES_AVAILABLE"],
    }
    (output / "native_spprc_acceptance_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output / "native_spprc_acceptance_report_zh.md").write_text(
        _render_report(summary),
        encoding="utf-8",
    )
    return summary


def _profile_gate_metrics(
    profile: NativeSpprcScaleProfile,
    *,
    b42_state: dict,
    expected_count: int,
) -> dict:
    rows = list(b42_state.get("rows") or [])
    total_seconds = [
        float(row["cold_start_total_sec"])
        for row in rows
        if row.get("cold_start_total_sec") is not None
    ]
    exact_count = sum(
        bool(row.get("bpc_tree_optimal"))
        and str(row.get("algorithm_status") or "") == "BPC_OPTIMAL"
        for row in rows
    )
    no_cheat_count = sum(bool(row.get("no_cheat_pass")) for row in rows)
    under_limit_count = sum(
        float(row.get("cold_start_total_sec") or float("inf"))
        <= float(profile.row_time_limit_sec)
        for row in rows
    )
    complete = len(rows) == int(expected_count) and len(total_seconds) == len(rows)
    return {
        "profile_time_limit_sec": float(profile.row_time_limit_sec),
        "expected_count": int(expected_count),
        "row_count": len(rows),
        "exact_count": exact_count,
        "no_cheat_count": no_cheat_count,
        "under_profile_time_limit_count": under_limit_count,
        "all_exact": bool(complete and exact_count == len(rows)),
        "all_no_cheat": bool(complete and no_cheat_count == len(rows)),
        "all_under_profile_time_limit": bool(
            complete and under_limit_count == len(rows)
        ),
        "mean_cold_start_total_sec": (
            round(statistics.fmean(total_seconds), 6) if total_seconds else None
        ),
        "p50_cold_start_total_sec": (
            round(statistics.median(total_seconds), 6) if total_seconds else None
        ),
        "max_cold_start_total_sec": (
            round(max(total_seconds), 6) if total_seconds else None
        ),
    }


def _acceptance_metrics(rows: list[dict]) -> dict:
    available = [
        row for row in rows if row.get("status") != "NO_INSTANCES_AVAILABLE"
    ]
    all_profile_gates = bool(available) and all(
        bool((row.get("profile_gate") or {}).get("all_exact"))
        and bool((row.get("profile_gate") or {}).get("all_no_cheat"))
        and bool(
            (row.get("profile_gate") or {}).get("all_under_profile_time_limit")
        )
        and bool(row.get("redlines_zero"))
        and bool((row.get("engine_binding") or {}).get("valid"))
        for row in available
    )
    scale30 = next((row for row in rows if int(row.get("scale") or 0) == 30), None)
    scale30_gate = (scale30 or {}).get("profile_gate") or {}
    scale30_full20 = bool(
        scale30
        and int(scale30.get("instance_count") or 0) == 20
        and int(scale30_gate.get("row_count") or 0) == 20
        and int(scale30_gate.get("exact_count") or 0) == 20
    )
    scale30_p50 = scale30_gate.get("p50_cold_start_total_sec")
    scale30_max = scale30_gate.get("max_cold_start_total_sec")
    scale30_release = bool(
        scale30_full20
        and scale30_gate.get("all_no_cheat")
        and scale30_gate.get("all_under_profile_time_limit")
        and scale30
        and scale30.get("redlines_zero")
        and (scale30.get("engine_binding") or {}).get("valid")
        and scale30_p50 is not None
        and float(scale30_p50) <= 900.0
        and scale30_max is not None
        and float(scale30_max) <= 1800.0
    )
    return {
        "all_available_profile_gates_pass": all_profile_gates,
        "scale30_full20_exact": scale30_full20,
        "scale30_all_under_1800": bool(
            scale30_full20
            and scale30_gate.get("all_under_profile_time_limit")
            and float(scale30_gate.get("profile_time_limit_sec") or 0.0) == 1800.0
        ),
        "scale30_p50_le_900": bool(
            scale30_full20
            and scale30_p50 is not None
            and float(scale30_p50) <= 900.0
        ),
        "scale30_stretch_p50_le_600": bool(
            scale30_full20
            and scale30_p50 is not None
            and float(scale30_p50) <= 600.0
        ),
        "scale30_phase11_release_gate": scale30_release,
    }


def _profile_from_config(scale: int, config: dict) -> NativeSpprcScaleProfile:
    profile = native_spprc_scale_profile(scale)
    profiles = config.get("profiles") if isinstance(config.get("profiles"), dict) else {}
    row = profiles.get(str(scale), profiles.get(scale, {}))
    if not isinstance(row, dict):
        return profile
    replacements = {}
    for key in (
        "worker_max_tasks",
        "exact_max_tasks",
        "harvest_target",
        "graph_cache_entries",
        "tree_max_rounds",
        "tree_max_columns_per_round",
        "tree_max_nodes",
        "tree_max_branch_depth",
    ):
        if key in row:
            replacements[key] = int(row[key])
    for key in ("row_time_limit_sec", "worker_time_limit_sec", "memory_limit_gb"):
        if key in row:
            replacements[key] = float(row[key])
    if "ng_sizes" in row:
        replacements["ng_sizes"] = tuple(int(value) for value in row["ng_sizes"])
    if "backend_id" in row:
        replacements["backend_id"] = str(row["backend_id"])
    return replace(profile, **replacements)


def _b42_command(
    root: Path,
    profile: NativeSpprcScaleProfile,
    *,
    backend_id: str,
    model_id: str,
    scale_output: Path,
    instances: tuple[Path, ...],
    resume: bool,
    live_sri_policy: str = "no_cut",
    route_opportunity_collection_only_root_pool: bool = False,
    route_opportunity_collection_root_pool_time_cap_sec: float = 0.0,
) -> list[str]:
    if str(live_sri_policy) not in {
        "no_cut",
        "P0",
        "P0_GROUP_SCREEN_V1",
        "P1",
        "P2",
    }:
        raise ValueError(f"unsupported live_sri_policy {live_sri_policy!r}")
    command = [
        sys.executable,
        str(root / "scripts" / "run_lunar_ice_b4_2_cold_exact.py"),
        "--output-dir",
        str(scale_output),
        "--scales",
        str(profile.scale),
        "--model-id",
        f"{str(model_id)}_S{profile.scale}_{backend_id}",
        "--row-limit-sec",
        str(profile.row_time_limit_sec),
        "--threads",
        "4",
        "--root-engine",
        "b2b_r3_worker",
        "--worker-pricer-kind",
        "relaxed_labeling",
        "--labeling-worker-max-task-cap",
        str(profile.worker_max_tasks),
        "--labeling-final-judge-mode",
        "on",
        "--labeling-final-judge-max-exact-tasks",
        str(profile.exact_max_tasks),
        "--labeling-final-judge-exact-harvest-target",
        str(profile.harvest_target),
        "--pool-optimization-harvest-target",
        str(profile.harvest_target),
        "--pool-batch-target",
        str(profile.harvest_target),
        "--pool-stage-time-slice-sec",
        str(profile.row_time_limit_sec),
        "--pool-min-stage-sec",
        str(min(10.0, profile.worker_time_limit_sec)),
        "--pool-max-stages",
        "1",
        "--pool-max-rounds-per-stage",
        str(max(16, profile.scale * 4)),
        "--pool-negative-search-cap-sec",
        str(profile.worker_time_limit_sec),
        "--tree-closure-max-rounds",
        str(profile.tree_max_rounds),
        "--tree-closure-max-columns-per-round",
        str(profile.tree_max_columns_per_round),
        "--tree-closure-max-nodes",
        str(profile.tree_max_nodes),
        "--tree-closure-max-branch-depth",
        str(profile.tree_max_branch_depth),
        "--live-sri-policy",
        str(live_sri_policy),
        "--no-root-partition-proof",
        "--partition-feedback-rounds",
        "0",
        "--no-large-task-direct-worker",
        "--min-available-mem-gb",
        "1",
    ]
    if route_opportunity_collection_only_root_pool:
        command.append(
            "--route-opportunity-collection-only-root-pool"
        )
        if route_opportunity_collection_root_pool_time_cap_sec > 0.0:
            command.extend(
                (
                    "--route-opportunity-collection-root-pool-time-cap-sec",
                    str(
                        float(
                            route_opportunity_collection_root_pool_time_cap_sec
                        )
                    ),
                )
            )
    command.append("--resume" if resume else "--no-resume")
    for path in instances:
        command.extend(("--instance", str(path)))
    return command


def _final_judge_pass_policy_for_scale(config: dict, scale: int) -> str:
    default = str(config.get("native_final_judge_pass_policy", "harvest_then_proof"))
    overrides = config.get("native_final_judge_pass_policy_by_scale") or {}
    if not isinstance(overrides, dict):
        raise ValueError("native_final_judge_pass_policy_by_scale must be a mapping")
    value = str(overrides.get(str(int(scale)), overrides.get(int(scale), default))).strip().lower()
    allowed = {
        "harvest_then_proof",
        "adaptive_sparse_harvest_v1",
        "branch_adaptive_sparse_harvest_v1",
        "proof_only",
    }
    if value not in allowed:
        raise ValueError(
            f"unsupported native final-judge pass policy for scale {scale}: {value!r}; "
            f"expected one of {sorted(allowed)!r}"
        )
    return value


def _adaptive_harvest_cap_for_scale(config: dict, scale: int) -> float | None:
    overrides = config.get("native_adaptive_harvest_cap_sec_by_scale") or {}
    if not isinstance(overrides, dict):
        raise ValueError("native_adaptive_harvest_cap_sec_by_scale must be a mapping")
    raw = overrides.get(str(int(scale)), overrides.get(int(scale)))
    if raw is None or not str(raw).strip():
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"invalid native adaptive harvest cap for scale {scale}: {raw!r}"
        ) from exc
    if not isfinite(value) or value <= 0.0:
        raise ValueError(
            f"native adaptive harvest cap for scale {scale} must be a finite positive number"
        )
    return value


def _adaptive_harvest_schedule_for_scale(
    config: dict, scale: int
) -> str | None:
    """Return an explicitly bound final-judge batch schedule.

    The exact runner must not inherit this policy from the launch shell.  A
    fixed-E_K experiment uses ``disabled`` so an existing sparse-harvest
    schedule cannot silently shrink K after the active pool grows.
    """

    overrides = config.get("native_adaptive_harvest_schedule_by_scale") or {}
    if not isinstance(overrides, dict):
        raise ValueError(
            "native_adaptive_harvest_schedule_by_scale must be a mapping"
        )
    raw = overrides.get(
        str(int(scale)),
        overrides.get(
            int(scale),
            config.get("native_adaptive_harvest_schedule"),
        ),
    )
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        raise ValueError(
            "native adaptive harvest schedule cannot be empty"
        )
    if text.lower() in {
        "0",
        "off",
        "none",
        "disabled",
        "false",
    }:
        return "disabled"
    normalized: list[tuple[int, int]] = []
    for piece in text.split(","):
        value = piece.strip()
        if not value or ":" not in value:
            raise ValueError(
                f"invalid native adaptive harvest schedule {raw!r}"
            )
        threshold_text, cap_text = value.split(":", 1)
        try:
            threshold = int(threshold_text.strip())
            cap = int(cap_text.strip())
        except ValueError as exc:
            raise ValueError(
                f"invalid native adaptive harvest schedule {raw!r}"
            ) from exc
        if threshold < 0 or cap <= 0:
            raise ValueError(
                f"invalid native adaptive harvest schedule {raw!r}"
            )
        normalized.append((threshold, cap))
    return ",".join(
        f"{threshold}:{cap}"
        for threshold, cap in sorted(
            normalized, key=lambda row: row[0], reverse=True
        )
    )


def _engine_binding_audit(
    *,
    expected_hash: str,
    end_hash: str,
    b42_summary: dict,
) -> dict:
    runtime_binding = (
        (b42_summary.get("config") or {}).get("native_runtime_binding") or {}
    )
    observed_hash = str(runtime_binding.get("engine_build_hash") or "")
    issues = []
    if not observed_hash:
        issues.append("child_engine_build_hash_missing")
    elif observed_hash != str(expected_hash):
        issues.append("child_engine_build_hash_mismatch")
    if str(end_hash) != str(expected_hash):
        issues.append("engine_build_hash_changed_during_run")
    return {
        "expected_hash": str(expected_hash),
        "child_observed_hash": observed_hash,
        "end_hash": str(end_hash),
        "valid": not issues,
        "issues": issues,
    }


def _group_instances_by_scale(root: Path, instances: tuple[str, ...]) -> dict[int, tuple[Path, ...]]:
    grouped: dict[int, list[Path]] = {}
    for value in instances:
        path = _root_path(root, value)
        payload = _read_json(path)
        scale = int(payload.get("scale") or len(payload.get("tasks") or {}))
        grouped.setdefault(scale, []).append(path)
    return {key: tuple(value) for key, value in grouped.items()}


def _root_path(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def _prepend_pythonpath(current: str | None, path: Path) -> str:
    return str(path) if not current else os.pathsep.join((str(path), current))


def _configure_one_deviation_environment(
    environment: dict[str, str],
    *,
    config: dict,
    root: Path,
    scale: int | None = None,
) -> None:
    manifest_value = str(
        config.get("one_deviation_gat_deployment_manifest") or ""
    ).strip()
    if not manifest_value:
        environment.pop(
            "LUNAR_ICE_ONE_DEVIATION_MANIFEST", None
        )
        environment.pop(
            "LUNAR_ICE_ONE_DEVIATION_EVALUATION_MODE", None
        )
        return
    manifest_path = Path(manifest_value)
    if not manifest_path.is_absolute():
        manifest_path = root / manifest_path
    if not manifest_path.is_file():
        raise FileNotFoundError(
            "one-deviation GAT deployment manifest is missing: "
            f"{manifest_path}"
        )
    expected_hash = str(
        config.get(
            "one_deviation_gat_deployment_manifest_sha256"
        )
        or ""
    ).strip()
    if expected_hash and _file_sha256(manifest_path) != expected_hash:
        raise ValueError(
            "one-deviation GAT deployment manifest hash mismatch"
        )
    manifest = _read_json(manifest_path)
    evaluation_mode = bool(
        config.get("one_deviation_gat_evaluation_mode", False)
    )
    if evaluation_mode:
        if not bool(manifest.get("evaluation_authorized")):
            raise ValueError(
                "one-deviation manifest did not authorize evaluation"
            )
    elif not bool(manifest.get("deployment_authorized")):
        raise ValueError(
            "one-deviation manifest did not authorize deployment"
        )
    if scale is not None:
        allowed_scales = {
            int(value)
            for value in manifest.get("allowed_scales", ())
        }
        if int(scale) not in allowed_scales:
            environment.pop(
                "LUNAR_ICE_ONE_DEVIATION_MANIFEST", None
            )
            environment.pop(
                "LUNAR_ICE_ONE_DEVIATION_EVALUATION_MODE", None
            )
            return
    environment["LUNAR_ICE_ONE_DEVIATION_MANIFEST"] = str(
        manifest_path.resolve()
    )
    if evaluation_mode:
        environment["LUNAR_ICE_ONE_DEVIATION_EVALUATION_MODE"] = "1"
    else:
        environment.pop(
            "LUNAR_ICE_ONE_DEVIATION_EVALUATION_MODE", None
        )


def _available_memory_gb() -> float:
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("MemAvailable:"):
                return float(line.split()[1]) / float(1024**2)
    except (OSError, ValueError, IndexError):
        pass
    pages = os.sysconf("SC_AVPHYS_PAGES")
    page_size = os.sysconf("SC_PAGE_SIZE")
    return float(pages * page_size) / float(1024**3)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024), b""
        ):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _git_head(root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else ""


def _render_report(summary: dict) -> str:
    lines = [
        "# Native SPPRC 六规模验收报告",
        "",
        f"- model: `{summary['model_id']}`",
        f"- cold_start: `{summary['cold_start']}`",
        f"- baseline_commit: `{summary['baseline_commit']}`",
        f"- config_hash: `{summary['config_hash']}`",
        f"- engine_build_hashes: `{summary['engine_build_hashes']}`",
        f"- missing_scales: `{summary['missing_scales']}`",
        f"- acceptance: `{summary.get('acceptance', {})}`",
        "",
        "| scale | backend | instances | exact | limit-sec | p50-sec | max-sec | redlines-zero | status | wall-sec |",
        "|---:|---|---:|---:|---:|---:|---:|---|---|---:|",
    ]
    for row in summary["rows"]:
        gate = row.get("profile_gate") or {}
        lines.append(
            f"| {row['scale']} | {row['backend_id']} | {row['instance_count']} | "
            f"{row.get('exact_count', 0)} | {gate.get('profile_time_limit_sec', '')} | "
            f"{gate.get('p50_cold_start_total_sec', '')} | "
            f"{gate.get('max_cold_start_total_sec', '')} | "
            f"{row.get('redlines_zero', False)} | "
            f"{row['status']} | {row.get('wall_time_sec', 0)} |"
        )
    lines.extend(
        [
            "",
            "`NO_INSTANCES_AVAILABLE` 表示当前 checkout 缺少对应 scale 数据，不是 exact closure。",
            "`FAIL_CLOSED` 表示命令本身完成但 exact closure gate 未通过。",
            "`RESOURCE_INSUFFICIENT` 在启动 solver 前 fail closed，不会降低搜索语义。",
            "native gate 使用各 scale profile 的 row time limit；child B4.2 报告中的旧 300/500 秒展示字段不参与 native release 判定。",
            "任何 timeout、memory limit 或 runner failure 均不得提升为 certificate。",
            "",
        ]
    )
    return "\n".join(lines)
