#!/usr/bin/env python3
"""Run the corrected P0 model on the frozen 5/10/20/30 full-80 set.

Every instance is solved in a fresh Python/Native process.  The historical P0
V2 evidence is read only for longitudinal timing and objective comparisons; it
is never reused as a certificate because the service-timing mathematics has
changed.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import statistics
import sys
from time import perf_counter
from typing import Iterable, Mapping

import yaml


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
NATIVE_BUILD = ROOT / "build" / "native-spprc"
for path in (str(SRC), str(NATIVE_BUILD)):
    if path not in sys.path:
        sys.path.insert(0, path)

from freeze_live_sri_candidate import candidate_bundle_files
from run_live_sri_paired_promotion import (
    atomic_write_json,
    config_profile,
    discover_instances,
    effective_memory_limit_gb,
    instance_key_from_path,
    next_attempt_dir,
    read_run_result,
    run_monitored,
    sha256_file,
    stable_payload_hash,
)

from lunar_ice_bpc.domain.scenario import SERVICE_TIMING_POLICY_ID
from lunar_ice_bpc.exact.bpc.cuts.live_sri import LiveSriPolicy
from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import (
    spprc_engine_build_hash,
)
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data


SCHEMA_VERSION = "lunar_ice_bpc.p0_no_task_wait_full80_baseline.v1"
BASELINE_ID = "P0_NO_TASK_WAIT_BASELINE_V3_CANDIDATE"
FORMAL_SCALES = (5, 10, 20, 30)
EXPECTED_PER_SCALE = 20
ACCEPTANCE_RUNNER = ROOT / "scripts" / "run_lunar_ice_native_spprc_acceptance.py"
HISTORICAL_ROWS = (
    ROOT
    / "runs"
    / "frozen_native_live_sri_p0_optimized_baseline_v2_20260723"
    / "performance"
    / "full80_paired_rows_snapshot.json"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs" / "native_live_sri_p0_pilot_v1.yaml",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--scales",
        nargs="+",
        type=int,
        default=list(FORMAL_SCALES),
    )
    parser.add_argument("--instance", action="append", default=[])
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--heartbeat-interval-sec", type=float, default=30.0)
    parser.add_argument("--launcher-timeout-grace-sec", type=float, default=120.0)
    parser.add_argument("--monitor-memory-cap-gb", type=float, default=8.0)
    parser.add_argument("--min-available-memory-gb", type=float, default=1.0)
    parser.add_argument("--recover-completed-slots", action="store_true")
    parser.add_argument("--keep-going-on-correctness-failure", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config_path = args.config.resolve()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if str(config.get("live_sri_policy")) != "P0":
        raise SystemExit("baseline config must select live_sri_policy=P0")

    # Make the rebuilt extension importable in this process and every child.
    pythonpath = os.environ.get("PYTHONPATH")
    required_pythonpath = os.pathsep.join((str(SRC), str(NATIVE_BUILD)))
    os.environ["PYTHONPATH"] = (
        required_pythonpath
        if not pythonpath
        else os.pathsep.join((required_pythonpath, pythonpath))
    )
    import lunar_spprc_native

    selected = discover_instances(args.scales, args.instance, limit=args.limit)
    schedule = build_schedule(selected, output=output)
    formal_full80 = bool(
        not args.limit
        and tuple(int(value) for value in args.scales) == FORMAL_SCALES
        and all(len(selected.get(scale, ())) == EXPECTED_PER_SCALE for scale in FORMAL_SCALES)
    )
    bundle_rows = source_bundle_rows(config_path)
    source_bundle_hash = stable_payload_hash(bundle_rows)
    engine_hash = spprc_engine_build_hash("native_rcspp_inprocess")
    policy_hash = LiveSriPolicy.named("P0").policy_hash
    preflight = {
        "schema_version": f"{SCHEMA_VERSION}.preflight",
        "created_at_utc": utc_now(),
        "baseline_id": BASELINE_ID,
        "service_timing_policy_id": SERVICE_TIMING_POLICY_ID,
        "config": str(config_path),
        "config_sha256": sha256_file(config_path),
        "engine_hash": engine_hash,
        "native_build_info": dict(lunar_spprc_native.build_info()),
        "p0_policy_hash": policy_hash,
        "source_bundle_file_count": len(bundle_rows),
        "source_bundle_hash": source_bundle_hash,
        "source_bundle": bundle_rows,
        "selected_instance_count": len(schedule),
        "formal_full80": formal_full80,
        "strict_cold_start": True,
        "fresh_python_native_runtime_per_slot": True,
        "solver_resume": False,
    }
    atomic_write_json(output / "baseline_preflight.json", preflight)
    atomic_write_json(
        output / "baseline_schedule.json",
        {
            "schema_version": f"{SCHEMA_VERSION}.schedule",
            "created_at_utc": utc_now(),
            "slots": schedule,
        },
    )

    rows_path = output / "baseline_rows.json"
    rows: list[dict] = []
    if rows_path.exists():
        if not args.recover_completed_slots:
            raise SystemExit(
                "baseline_rows.json already exists; choose a new output directory "
                "or pass --recover-completed-slots"
            )
        rows = json.loads(rows_path.read_text(encoding="utf-8"))
    completed = recovered_rows(rows, schedule)
    historical = historical_p0_rows()
    stopped_reason = ""
    started = perf_counter()

    for spec in schedule:
        slot_id = str(spec["slot_id"])
        if slot_id in completed:
            continue
        if stable_payload_hash(source_bundle_rows(config_path)) != source_bundle_hash:
            stopped_reason = "SOURCE_BUNDLE_DRIFT"
            break

        row = dict(spec)
        row.update(
            {
                "baseline_id": BASELINE_ID,
                "service_timing_policy_id": SERVICE_TIMING_POLICY_ID,
                "config": str(config_path),
                "config_sha256": sha256_file(config_path),
                "expected_engine_hash": engine_hash,
                "expected_p0_policy_hash": policy_hash,
            }
        )
        if args.dry_run:
            row.update(
                {
                    "status": "DRY_RUN",
                    "returncode": 0,
                    "exact": False,
                    "correctness_pass": False,
                    "completed_at_utc": utc_now(),
                }
            )
        else:
            run_dir, attempt = next_attempt_dir(Path(spec["slot_dir"]))
            run_dir.mkdir(parents=True, exist_ok=False)
            row["run_dir"] = str(run_dir)
            row["attempt_number"] = attempt
            command = [
                sys.executable,
                str(ACCEPTANCE_RUNNER),
                "--config",
                str(config_path),
                "--scales",
                str(spec["scale"]),
                "--instance",
                str(spec["instance"]),
                "--output-dir",
                str(run_dir),
                "--no-resume",
            ]
            row["command"] = command
            profile = config_profile(config_path, int(spec["scale"]))
            monitor_limit = min(
                effective_memory_limit_gb(float(profile["memory_limit_gb"])),
                max(0.5, float(args.monitor_memory_cap_gb)),
            )
            run_started = perf_counter()
            monitor = run_monitored(
                command,
                cwd=ROOT,
                run_dir=run_dir,
                slot_id=slot_id,
                heartbeat_csv=output / "resource_heartbeat.csv",
                heartbeat_interval_sec=max(
                    1.0,
                    float(args.heartbeat_interval_sec),
                ),
                timeout_sec=float(profile["row_time_limit_sec"])
                + max(0.0, float(args.launcher_timeout_grace_sec)),
                effective_memory_limit_gb=monitor_limit,
                min_available_memory_gb=max(
                    0.0,
                    float(args.min_available_memory_gb),
                ),
                low_memory_consecutive_samples=2,
            )
            row.update(
                read_run_result(
                    run_dir,
                    scale=int(spec["scale"]),
                    returncode=int(monitor["returncode"]),
                )
            )
            row.update(monitor)
            row["launcher_wall_time_sec"] = round(
                perf_counter() - run_started,
                6,
            )
            tree = read_tree(run_dir, int(spec["scale"]))
            row["observed_instance_content_hash"] = str(
                tree.get("instance_content_hash") or ""
            )
            row["observed_service_timing_policy_id"] = str(
                tree.get("service_timing_policy_id") or ""
            )
            old = historical.get(
                (int(spec["scale"]), str(spec["instance_key"]))
            )
            row["historical_p0_v2_objective"] = (
                None if old is None else old.get("objective")
            )
            row["historical_p0_v2_sec"] = (
                None if old is None else old.get("cold_start_total_sec")
            )
            row["objective_delta_vs_historical_p0_v2"] = numeric_delta(
                row.get("objective"),
                row.get("historical_p0_v2_objective"),
            )
            row["time_ratio_vs_historical_p0_v2"] = numeric_ratio(
                row.get("cold_start_total_sec"),
                row.get("historical_p0_v2_sec"),
            )
            row["correctness_issues"] = correctness_issues(
                row,
                expected_engine_hash=engine_hash,
                expected_policy_hash=policy_hash,
            )
            row["correctness_pass"] = not row["correctness_issues"]
            row["completed_at_utc"] = utc_now()

        rows.append(row)
        completed[slot_id] = row
        write_rows(rows_path, output / "baseline_rows.csv", rows)
        atomic_write_json(
            output / "baseline_progress.json",
            {
                "schema_version": f"{SCHEMA_VERSION}.progress",
                "updated_at_utc": utc_now(),
                "expected_slot_count": len(schedule),
                "completed_slot_count": len(completed),
                "last_slot_id": slot_id,
                "last_status": row.get("status"),
                "last_exact": row.get("exact"),
                "last_correctness_pass": row.get("correctness_pass"),
                "solver_resume": False,
            },
        )
        if (
            not args.dry_run
            and not row.get("correctness_pass")
            and not args.keep_going_on_correctness_failure
        ):
            stopped_reason = f"CORRECTNESS_FAILURE:{slot_id}"
            break

    end_bundle_hash = stable_payload_hash(source_bundle_rows(config_path))
    if end_bundle_hash != source_bundle_hash and not stopped_reason:
        stopped_reason = "SOURCE_BUNDLE_DRIFT_AT_END"
    summary = summarize(
        rows,
        schedule=schedule,
        formal_full80=formal_full80,
        dry_run=bool(args.dry_run),
        stopped_reason=stopped_reason,
        source_bundle_hash=source_bundle_hash,
        source_bundle_hash_at_end=end_bundle_hash,
        engine_hash=engine_hash,
        config_path=config_path,
        wall_time_sec=perf_counter() - started,
    )
    atomic_write_json(output / "baseline_summary.json", summary)
    (output / "baseline_report_zh.md").write_text(
        render_report(summary),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["status"] in {"COMPLETE", "DRY_RUN"} else 1


def build_schedule(
    selected: Mapping[int, tuple[Path, ...]],
    *,
    output: Path,
) -> list[dict]:
    schedule: list[dict] = []
    for scale in sorted(selected):
        for path in selected[scale]:
            payload = json.loads(path.read_text(encoding="utf-8"))
            data = load_lunar_ice_data(payload)
            key = instance_key_from_path(path)
            schedule.append(
                {
                    "slot_id": f"s{int(scale):03d}_{key}",
                    "scale": int(scale),
                    "instance": str(path.resolve()),
                    "instance_key": key,
                    "instance_sha256": sha256_file(path),
                    "instance_content_hash": data.instance_content_hash,
                    "service_timing_policy_id": data.service_timing_policy_id,
                    "slot_dir": str(
                        output / "slots" / f"scale_{int(scale):03d}" / key
                    ),
                }
            )
    return schedule


def source_bundle_rows(config_path: Path) -> list[dict[str, str]]:
    paths = set(candidate_bundle_files())
    paths.add(Path(__file__).resolve())
    paths.add(config_path.resolve())
    return [
        {
            "path": str(path.relative_to(ROOT)),
            "sha256": sha256_file(path),
        }
        for path in sorted(paths, key=lambda value: str(value.relative_to(ROOT)))
    ]


def recovered_rows(
    rows: Iterable[dict],
    schedule: Iterable[dict],
) -> dict[str, dict]:
    expected = {str(row["slot_id"]): row for row in schedule}
    result: dict[str, dict] = {}
    for row in rows:
        slot_id = str(row.get("slot_id") or "")
        if slot_id not in expected:
            raise ValueError(f"unexpected recovered slot {slot_id!r}")
        if slot_id in result:
            raise ValueError(f"duplicate recovered slot {slot_id!r}")
        for key in (
            "scale",
            "instance_sha256",
            "instance_content_hash",
            "service_timing_policy_id",
        ):
            if row.get(key) != expected[slot_id].get(key):
                raise ValueError(
                    f"recovered slot binding mismatch {slot_id}:{key}"
                )
        result[slot_id] = row
    return result


def historical_p0_rows() -> dict[tuple[int, str], dict]:
    if not HISTORICAL_ROWS.is_file():
        return {}
    rows = json.loads(HISTORICAL_ROWS.read_text(encoding="utf-8"))
    return {
        (int(row["scale"]), str(row["instance_key"])): row
        for row in rows
        if str(row.get("mode")) == "live"
    }


def read_tree(run_dir: Path, scale: int) -> dict:
    paths = sorted(
        (run_dir / f"scale_{int(scale):03d}").glob(
            "**/tree_closure_001.json"
        )
    )
    if not paths:
        return {}
    return json.loads(paths[-1].read_text(encoding="utf-8"))


def correctness_issues(
    row: Mapping,
    *,
    expected_engine_hash: str,
    expected_policy_hash: str,
) -> list[str]:
    issues: list[str] = []
    checks = (
        ("returncode_nonzero", int(row.get("returncode") or 0) == 0),
        ("not_exact", bool(row.get("exact"))),
        ("redlines_nonzero", bool(row.get("redlines_zero"))),
        ("engine_binding_invalid", bool(row.get("engine_hash_valid"))),
        (
            "engine_hash_mismatch",
            str(row.get("engine_build_hash") or "")
            == str(expected_engine_hash),
        ),
        ("no_cheat_failed", bool(row.get("no_cheat_pass"))),
        (
            "p0_policy_name_mismatch",
            str(row.get("live_sri_policy_name") or "") == "P0",
        ),
        (
            "p0_policy_hash_mismatch",
            str(row.get("live_cut_policy_hash") or "")
            == str(expected_policy_hash),
        ),
        (
            "instance_content_hash_mismatch",
            str(row.get("observed_instance_content_hash") or "")
            == str(row.get("instance_content_hash") or ""),
        ),
        (
            "service_timing_policy_mismatch",
            str(row.get("observed_service_timing_policy_id") or "")
            == SERVICE_TIMING_POLICY_ID,
        ),
        (
            "same_run_checkpoint_resume_used",
            not bool(row.get("same_run_checkpoint_resume_used")),
        ),
        ("external_probe_used", not bool(row.get("external_probe_used"))),
        ("mature_pool_used", not bool(row.get("mature_pool_used"))),
        ("manual_columns_used", not bool(row.get("manual_columns_used"))),
        ("row_budget_exhausted", not bool(row.get("row_budget_exhausted"))),
        (
            "historical_objective_monotonicity_violation",
            objective_not_below_historical(row),
        ),
    )
    for issue, passed in checks:
        if not passed:
            issues.append(issue)
    return issues


def objective_not_below_historical(row: Mapping) -> bool:
    current = row.get("objective")
    historical = row.get("historical_p0_v2_objective")
    if current is None or historical is None:
        return True
    return float(current) + 5.0e-6 >= float(historical)


def summarize(
    rows: list[dict],
    *,
    schedule: list[dict],
    formal_full80: bool,
    dry_run: bool,
    stopped_reason: str,
    source_bundle_hash: str,
    source_bundle_hash_at_end: str,
    engine_hash: str,
    config_path: Path,
    wall_time_sec: float,
) -> dict:
    by_scale: dict[str, dict] = {}
    for scale in sorted({int(row["scale"]) for row in schedule}):
        scale_rows = [
            row for row in rows if int(row.get("scale") or 0) == scale
        ]
        times = [
            float(row["cold_start_total_sec"])
            for row in scale_rows
            if row.get("cold_start_total_sec") is not None
        ]
        ratios = [
            float(row["time_ratio_vs_historical_p0_v2"])
            for row in scale_rows
            if row.get("time_ratio_vs_historical_p0_v2") is not None
        ]
        objective_deltas = [
            float(row["objective_delta_vs_historical_p0_v2"])
            for row in scale_rows
            if row.get("objective_delta_vs_historical_p0_v2") is not None
        ]
        by_scale[str(scale)] = {
            "expected_count": sum(
                int(spec["scale"]) == scale for spec in schedule
            ),
            "completed_count": len(scale_rows),
            "exact_count": sum(bool(row.get("exact")) for row in scale_rows),
            "correctness_pass_count": sum(
                bool(row.get("correctness_pass")) for row in scale_rows
            ),
            "mean_sec": statistics.fmean(times) if times else None,
            "p50_sec": statistics.median(times) if times else None,
            "max_sec": max(times) if times else None,
            "mean_instance_time_ratio_vs_historical_p0_v2": (
                statistics.fmean(ratios) if ratios else None
            ),
            "p50_instance_time_ratio_vs_historical_p0_v2": (
                statistics.median(ratios) if ratios else None
            ),
            "objective_unchanged_count": sum(
                abs(value) <= 5.0e-6 for value in objective_deltas
            ),
            "objective_increased_count": sum(
                value > 5.0e-6 for value in objective_deltas
            ),
            "objective_decreased_count": sum(
                value < -5.0e-6 for value in objective_deltas
            ),
            "peak_process_tree_rss_gb": max(
                (
                    float(row.get("peak_process_tree_rss_gb") or 0.0)
                    for row in scale_rows
                ),
                default=0.0,
            ),
        }
    complete = bool(
        len(rows) == len(schedule)
        and all(bool(row.get("correctness_pass")) for row in rows)
        and source_bundle_hash == source_bundle_hash_at_end
        and not stopped_reason
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "baseline_id": BASELINE_ID,
        "status": "DRY_RUN" if dry_run else "COMPLETE" if complete else "INCOMPLETE",
        "created_at_utc": utc_now(),
        "service_timing_policy_id": SERVICE_TIMING_POLICY_ID,
        "historical_control_preserved": True,
        "historical_control_id": "FROZEN_NATIVE_LIVE_SRI_P0_OPTIMIZED_BASELINE_V2",
        "formal_full80": formal_full80,
        "strict_cold_start": True,
        "fresh_python_native_runtime_per_slot": True,
        "solver_resume": False,
        "expected_slot_count": len(schedule),
        "completed_slot_count": len(rows),
        "exact_count": sum(bool(row.get("exact")) for row in rows),
        "correctness_pass_count": sum(
            bool(row.get("correctness_pass")) for row in rows
        ),
        "stopped_reason": stopped_reason,
        "engine_hash": engine_hash,
        "config": str(config_path),
        "config_sha256": sha256_file(config_path),
        "source_bundle_hash": source_bundle_hash,
        "source_bundle_hash_at_end": source_bundle_hash_at_end,
        "source_bundle_stable": source_bundle_hash == source_bundle_hash_at_end,
        "scale_summary": by_scale,
        "wall_time_sec": round(float(wall_time_sec), 6),
        "new_baseline_freeze_authorized": bool(
            complete and formal_full80 and not dry_run
        ),
    }


def render_report(summary: Mapping) -> str:
    lines = [
        "# P0 禁止任务点等待：5/10/20/30 冷启动基准",
        "",
        f"- 状态：`{summary['status']}`",
        f"- 服务时序策略：`{summary['service_timing_policy_id']}`",
        f"- 完成 / 计划：{summary['completed_slot_count']} / {summary['expected_slot_count']}",
        f"- exact / correctness：{summary['exact_count']} / {summary['correctness_pass_count']}",
        f"- 旧 P0 V2 冻结证据保留：`{summary['historical_control_preserved']}`",
        f"- 新基准允许冻结：`{summary['new_baseline_freeze_authorized']}`",
        "",
        "| scale | 完成 | exact | mean s | p50 s | max s | mean ratio vs V2 | 目标不变/升高/降低 | peak RSS GiB |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for scale, row in summary["scale_summary"].items():
        lines.append(
            f"| {scale} | {row['completed_count']} | {row['exact_count']} | "
            f"{format_number(row['mean_sec'])} | {format_number(row['p50_sec'])} | "
            f"{format_number(row['max_sec'])} | "
            f"{format_number(row['mean_instance_time_ratio_vs_historical_p0_v2'])} | "
            f"{row['objective_unchanged_count']}/{row['objective_increased_count']}/"
            f"{row['objective_decreased_count']} | "
            f"{format_number(row['peak_process_tree_rss_gb'])} |"
        )
    lines.extend(
        [
            "",
            "目标值只能保持或升高：新模型删除了任务点等待可行性，未增加任何可行解。",
            "若出现目标降低、哈希漂移、非 P0 策略、resume、外部 pool 或证书红线，运行立即 fail closed。",
            "",
        ]
    )
    return "\n".join(lines)


def numeric_delta(left, right) -> float | None:
    if left is None or right is None:
        return None
    return float(left) - float(right)


def numeric_ratio(left, right) -> float | None:
    if left is None or right is None or float(right) <= 0.0:
        return None
    return float(left) / float(right)


def format_number(value) -> str:
    return "" if value is None else f"{float(value):.6f}"


def write_rows(json_path: Path, csv_path: Path, rows: list[dict]) -> None:
    atomic_write_json(json_path, rows)
    fields = [
        "slot_id",
        "scale",
        "instance_key",
        "status",
        "returncode",
        "cold_start_total_sec",
        "root_cg_sec",
        "tree_sec",
        "exact",
        "correctness_pass",
        "objective",
        "historical_p0_v2_objective",
        "objective_delta_vs_historical_p0_v2",
        "historical_p0_v2_sec",
        "time_ratio_vs_historical_p0_v2",
        "peak_process_tree_rss_gb",
        "launcher_termination_reason",
        "engine_build_hash",
        "instance_content_hash",
        "service_timing_policy_id",
        "run_dir",
    ]
    temporary = csv_path.with_suffix(csv_path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})
    os.replace(temporary, csv_path)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
