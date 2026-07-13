"""Six-scale no-cheat native SPPRC acceptance orchestration."""

from __future__ import annotations

from dataclasses import asdict, replace
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from time import perf_counter

from lunar_ice_bpc.exact.bpc.pricing.backends.native_rcspp import effective_memory_limit_gb
from lunar_ice_bpc.exact.bpc.pricing.backends.scale_profiles import (
    NativeSpprcScaleProfile,
    native_spprc_scale_profile,
)
from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import spprc_engine_build_hash


SCHEMA_VERSION = "lunar_ice_bpc.native_spprc_acceptance.v1"
MODEL_ID = "NATIVE_SPPRC_ACCEPTANCE_V1"


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
) -> dict:
    root = Path(project_root).resolve()
    output = _root_path(root, output_dir)
    output.mkdir(parents=True, exist_ok=True)
    selected_instances = _group_instances_by_scale(root, instances)
    rows = []
    started = perf_counter()
    for scale in scales:
        profile = _profile_from_config(int(scale), config)
        backend_id = str(backend_override or profile.backend_id)
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
        row = {
            "scale": int(scale),
            "backend_id": backend_id,
            "profile": asdict(profile),
            "effective_memory_limit_gb": round(effective_memory_limit_gb(profile.memory_limit_gb), 6),
            "instance_count": len(scale_instances),
            "instances": [str(path) for path in scale_instances],
            "output_dir": str(scale_output),
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
            scale_output=scale_output,
            instances=scale_instances,
            resume=resume,
        )
        row["command"] = command
        if dry_run:
            row.update({"status": "DRY_RUN", "returncode": 0})
            rows.append(row)
            continue
        scale_output.mkdir(parents=True, exist_ok=True)
        environment = dict(os.environ)
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
            }
        )
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
        scale_summary = (b42_summary.get("by_scale") or {}).get(str(scale), {})
        exact_count = int(scale_summary.get("exact_count") or 0)
        row_count = int(scale_summary.get("row_count") or 0)
        redlines = b42_summary.get("redlines") or {}
        redlines_zero = bool(redlines) and all(int(value or 0) == 0 for value in redlines.values())
        exact_closed = bool(
            completed.returncode == 0
            and row_count == len(scale_instances)
            and exact_count == row_count
            and redlines_zero
        )
        row.update(
            {
                "status": (
                    "EXACT_CLOSED"
                    if exact_closed
                    else "FAIL_CLOSED"
                    if completed.returncode == 0
                    else "RUNNER_FAILED"
                ),
                "returncode": int(completed.returncode),
                "wall_time_sec": round(perf_counter() - scale_started, 6),
                "exact_count": exact_count,
                "fail_closed_count": int(scale_summary.get("fail_closed_count") or 0),
                "redlines_zero": redlines_zero,
                "b42_summary": b42_summary,
            }
        )
        rows.append(row)

    summary = {
        "schema_version": SCHEMA_VERSION,
        "model_id": MODEL_ID,
        "cold_start": True,
        "resume_enabled": bool(resume),
        "dry_run": bool(dry_run),
        "baseline_commit": _git_head(root),
        "config_hash": hashlib.sha256(
            json.dumps(config, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "engine_build_hashes": {
            backend_id: spprc_engine_build_hash(backend_id)
            for backend_id in sorted({row["backend_id"] for row in rows})
        },
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
    scale_output: Path,
    instances: tuple[Path, ...],
    resume: bool,
) -> list[str]:
    command = [
        sys.executable,
        str(root / "scripts" / "run_lunar_ice_b4_2_cold_exact.py"),
        "--output-dir",
        str(scale_output),
        "--scales",
        str(profile.scale),
        "--model-id",
        f"{MODEL_ID}_S{profile.scale}_{backend_id}",
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
        "--no-root-partition-proof",
        "--partition-feedback-rounds",
        "0",
        "--no-large-task-direct-worker",
        "--min-available-mem-gb",
        "1",
    ]
    command.append("--resume" if resume else "--no-resume")
    for path in instances:
        command.extend(("--instance", str(path)))
    return command


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
        "",
        "| scale | backend | instances | exact | redlines-zero | status | wall_sec |",
        "|---:|---|---:|---:|---|---|---:|",
    ]
    for row in summary["rows"]:
        lines.append(
            f"| {row['scale']} | {row['backend_id']} | {row['instance_count']} | "
            f"{row.get('exact_count', 0)} | {row.get('redlines_zero', False)} | "
            f"{row['status']} | {row.get('wall_time_sec', 0)} |"
        )
    lines.extend(
        [
            "",
            "`NO_INSTANCES_AVAILABLE` 表示当前 checkout 缺少对应 scale 数据，不是 exact closure。",
            "`FAIL_CLOSED` 表示命令本身完成但 exact closure gate 未通过。",
            "`RESOURCE_INSUFFICIENT` 在启动 solver 前 fail closed，不会降低搜索语义。",
            "任何 timeout、memory limit 或 runner failure 均不得提升为 certificate。",
            "",
        ]
    )
    return "\n".join(lines)
