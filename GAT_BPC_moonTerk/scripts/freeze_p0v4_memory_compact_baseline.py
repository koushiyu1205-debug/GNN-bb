#!/usr/bin/env python3
"""Freeze the P0 V4 memory-compact experiment baseline.

This freeze intentionally accepts a bounded validation scope: scale30 full20
must be exact and safe, while scale50/001 is preserved as a known 3600-second
incomplete boundary.  It never represents that boundary as six-scale
promotion evidence.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import math
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import tarfile


ROOT = Path(__file__).resolve().parents[1]
FREEZE_ID = "FROZEN_NATIVE_LIVE_SRI_P0_MEMORY_COMPACT_BASELINE_V4"
HISTORICAL_CONTROL_ID = "FROZEN_NATIVE_LIVE_SRI_P0_NO_TASK_WAIT_BASELINE_V3"
DEFAULT_OUTPUT = (
    ROOT / "runs" / "frozen_native_live_sri_p0_memory_compact_baseline_v4_20260729"
)
DEFAULT_BUILD = ROOT / "build" / "native-spprc-memory-opt-v2"
DEFAULT_CONFIG = ROOT / "configs" / "native_live_sri_p0v3_memory_compact_candidate_v3.yaml"
DEFAULT_SCALE30 = (
    ROOT / "runs" / "p0v3_memory_compact_candidate_20260729" / "scale30_full20_v3"
)
DEFAULT_SCALE50 = (
    ROOT
    / "runs"
    / "p0v3_memory_compact_candidate_20260729"
    / "scale50_instance001_v5_batch128_fast_selector"
)
DEFAULT_CONTROL = ROOT / "runs" / "p0v3_six_scale_full120_baseline_20260727"
OLD_SOURCE_SNAPSHOT = (
    ROOT
    / "runs"
    / "frozen_native_live_sri_p0_no_task_wait_baseline_v3_20260725"
    / "candidate_preflight_snapshot.json"
)
VERIFY_SOURCE = ROOT / "scripts" / "verify_p0v4_memory_compact_freeze.py"
EXTRA_SOURCE_PATHS = (
    "configs/native_live_sri_p0v3_memory_compact_candidate_v3.yaml",
    "docs/P0V3_MEMORY_COMPACT_SCALE30_50_STATUS_20260729_ZH.md",
    "scripts/freeze_p0v4_memory_compact_baseline.py",
    "scripts/verify_p0v4_memory_compact_freeze.py",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--native-build", type=Path, default=DEFAULT_BUILD)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--scale30-run", type=Path, default=DEFAULT_SCALE30)
    parser.add_argument("--scale50-run", type=Path, default=DEFAULT_SCALE50)
    parser.add_argument("--control-run", type=Path, default=DEFAULT_CONTROL)
    args = parser.parse_args()

    output = args.output_dir.resolve()
    if output.exists() and any(output.iterdir()):
        raise SystemExit(f"refusing to overwrite nonempty freeze: {output}")
    build = args.native_build.resolve()
    config = args.config.resolve()
    scale30 = args.scale30_run.resolve()
    scale50 = args.scale50_run.resolve()
    control = args.control_run.resolve()
    module = build / "install" / _native_module_name(build / "install")
    required = (
        config,
        module,
        scale30 / "native_spprc_acceptance_summary.json",
        scale30 / "scale_030" / "b4_2_cold_exact_rows.csv",
        scale50 / "native_spprc_acceptance_summary.json",
        scale50 / "scale_050" / "b4_2_cold_exact_rows.csv",
        OLD_SOURCE_SNAPSHOT,
        VERIFY_SOURCE,
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise SystemExit("required freeze inputs missing: " + ",".join(missing))

    validation = _validation_summary(scale30=scale30, scale50=scale50, control=control)
    issues = _freeze_issues(validation)
    if issues:
        raise SystemExit("P0 V4 freeze refused: " + ",".join(issues))

    output.mkdir(parents=True, exist_ok=False)
    tests_dir = output / "tests"
    tests_dir.mkdir()
    test_results = _run_tests(build=build, output=tests_dir)
    _write_json(tests_dir / "test_results.json", test_results)
    if not test_results["all_passed"]:
        raise SystemExit("P0 V4 freeze refused: tests failed")

    native_dir = output / "native"
    native_dir.mkdir()
    frozen_native = native_dir / module.name
    shutil.copy2(module, frozen_native)
    frozen_config = output / "frozen_config.yaml"
    shutil.copy2(config, frozen_config)
    frozen_verify = output / "verify_freeze.py"
    shutil.copy2(VERIFY_SOURCE, frozen_verify)

    evidence_dir = output / "evidence"
    evidence_dir.mkdir()
    evidence_sources = {
        "scale30_acceptance_summary.json": (
            scale30 / "native_spprc_acceptance_summary.json"
        ),
        "scale30_acceptance_report_zh.md": (
            scale30 / "native_spprc_acceptance_report_zh.md"
        ),
        "scale30_b42_summary.json": (
            scale30 / "scale_030" / "b4_2_cold_exact_summary.json"
        ),
        "scale30_rows.csv": (
            scale30 / "scale_030" / "b4_2_cold_exact_rows.csv"
        ),
        "scale30_report_zh.md": (
            scale30 / "scale_030" / "b4_2_cold_exact_full_report_zh.md"
        ),
        "scale50_acceptance_summary.json": (
            scale50 / "native_spprc_acceptance_summary.json"
        ),
        "scale50_acceptance_report_zh.md": (
            scale50 / "native_spprc_acceptance_report_zh.md"
        ),
        "scale50_b42_summary.json": (
            scale50 / "scale_050" / "b4_2_cold_exact_summary.json"
        ),
        "scale50_rows.csv": (
            scale50 / "scale_050" / "b4_2_cold_exact_rows.csv"
        ),
        "scale50_report_zh.md": (
            scale50 / "scale_050" / "b4_2_cold_exact_full_report_zh.md"
        ),
        "scale50_probe_report_zh.md": (
            scale50
            / "scale_050"
            / "pools"
            / "scale_050"
            / "instance_001"
            / "stage_001"
            / "probe_report_zh.md"
        ),
    }
    for name, source in evidence_sources.items():
        if not source.is_file():
            raise SystemExit(f"required evidence missing: {source}")
        shutil.copy2(source, evidence_dir / name)
    validation_path = evidence_dir / "validation_summary.json"
    _write_json(validation_path, validation)

    source_rows = _source_bundle_rows()
    source_manifest = output / "source_bundle_manifest.json"
    source_payload = {
        "schema_version": "lunar_ice_bpc.source_bundle.v1",
        "freeze_id": FREEZE_ID,
        "file_count": len(source_rows),
        "files": source_rows,
        "bundle_hash": _stable_payload_hash(source_rows),
    }
    _write_json(source_manifest, source_payload)
    source_archive = output / "source_bundle.tar.gz"
    _write_source_archive(source_archive, source_rows)

    sys.path.insert(0, str(build / "install"))
    import lunar_spprc_native  # type: ignore

    artifacts = {}
    artifact_paths = (
        frozen_config,
        frozen_native,
        frozen_verify,
        tests_dir / "test_results.json",
        validation_path,
        source_manifest,
        source_archive,
        *(evidence_dir / name for name in evidence_sources),
    )
    for path in artifact_paths:
        artifacts[str(path.relative_to(ROOT))] = _artifact(path)

    scale30_acceptance = _read_json(
        scale30 / "native_spprc_acceptance_summary.json"
    )
    scale50_acceptance = _read_json(
        scale50 / "native_spprc_acceptance_summary.json"
    )
    manifest = {
        "schema_version": "lunar_ice_bpc.baseline_freeze_manifest.v4",
        "freeze_id": FREEZE_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "role": "active_experiment_baseline_and_gat_foundation",
        "historical_control_id": HISTORICAL_CONTROL_ID,
        "production_default_policy": "no_cut",
        "production_default_switch_authorized": False,
        "repository_head_at_freeze": _git_commit(),
        "worktree_clean_at_freeze": _worktree_clean(),
        "binding_mode": "frozen_binary_config_and_content_addressed_source_archive",
        "algorithm": {
            "model_id": "NATIVE_LIVE_SRI_P0_MEMORY_COMPACT_V4",
            "source_config_model_id": _config_model_id(config),
            "family": "exact_native_branch_price_and_cut",
            "cut_policy": "P0 root-only SRI-3 divisor-2",
            "service_timing_policy_id": "no_task_wait_base_departure_shift_v1",
            "branching": "Ryan-Foster same/different task-pair branching",
            "tree_max_rounds_unchanged": 16,
            "native_label_state_bytes": int(
                lunar_spprc_native.build_info()["label_state_bytes"]
            ),
            "native_journey_value_bytes": int(
                lunar_spprc_native.build_info()["journey_value_bytes"]
            ),
            "host_recycle_large_scale_only": True,
            "guidance_enabled": False,
            "exactness_contract": (
                "All official RC, bounds, pruning, no-negative and tree "
                "certificates require current true-dual exhaustive pricing."
            ),
        },
        "native_build_info": dict(lunar_spprc_native.build_info()),
        "engine_hashes": {
            "native_rcspp_inprocess": (
                scale30_acceptance["rows"][0]["engine_build_hash_at_start"]
            ),
            "native_rcspp_host": (
                scale50_acceptance["rows"][0]["engine_build_hash_at_start"]
            ),
        },
        "validation_scope": {
            "scale30_full20": "EXACT_CLOSED",
            "scale50_instance001_3600sec": "BPC_INCOMPLETE_PRICING",
            "scale5_v4_binary": "NOT_RERUN",
            "scale10_v4_binary": "NOT_RERUN",
            "scale20_v4_binary": "NOT_RERUN",
            "scale50_full": "NOT_RUN_BY_USER_DIRECTION",
            "scale100": "NOT_RUN",
            "six_scale_promotion_complete": False,
            "known_boundary_preserved": True,
        },
        "performance": validation,
        "artifacts": artifacts,
        "source_bundle_hash": source_payload["bundle_hash"],
        "source_bundle_archive_sha256": _sha256_file(source_archive),
        "verification": {
            "command": (
                "/home/kai/miniconda3/bin/python "
                "runs/frozen_native_live_sri_p0_memory_compact_baseline_v4_"
                "20260729/verify_freeze.py"
            ),
            "expected_valid": True,
        },
        "historical_control_preserved": True,
        "formal_full120_complete": False,
        "new_baseline_freeze_authorized_by_user": True,
    }
    _write_json(output / "baseline_freeze_manifest.json", manifest)
    _write_readme(output / "README_ZH.md", validation)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _native_module_name(directory: Path) -> str:
    modules = sorted(directory.glob("lunar_spprc_native*.so"))
    if len(modules) != 1:
        raise SystemExit(
            f"isolated native install must contain one module: {directory}"
        )
    return modules[0].name


def _validation_summary(*, scale30: Path, scale50: Path, control: Path) -> dict:
    candidate_rows = _read_csv_rows(
        scale30 / "scale_030" / "b4_2_cold_exact_rows.csv"
    )
    control_rows = {}
    for index in range(1, 21):
        key = f"instance_{index:03d}"
        path = (
            control
            / "slots"
            / "scale_030"
            / key
            / "attempt_01"
            / "scale_030"
            / "b4_2_cold_exact_rows.csv"
        )
        rows = _read_csv_rows(path)
        if len(rows) != 1:
            raise SystemExit(f"invalid control row count: {path}")
        control_rows[key] = rows[0]
    candidate = {row["instance_key"]: row for row in candidate_rows}
    keys = sorted(candidate)
    candidate_times = [float(candidate[key]["cold_start_total_sec"]) for key in keys]
    control_times = [
        float(control_rows[key]["cold_start_total_sec"]) for key in keys
    ]
    ratios = [
        candidate_time / control_time
        for candidate_time, control_time in zip(candidate_times, control_times)
    ]
    objective_deltas = []
    hash_mismatch_count = 0
    for key in keys:
        candidate_tree = _read_json(Path(candidate[key]["tree_result_json"]))
        control_tree = _read_json(Path(control_rows[key]["tree_result_json"]))
        objective_deltas.append(
            abs(
                float(candidate_tree["incumbent_objective"])
                - float(control_tree["incumbent_objective"])
            )
        )
        hash_mismatch_count += int(
            candidate_tree["instance_content_hash"]
            != control_tree["instance_content_hash"]
        )
    scale50_summary = _read_json(
        scale50 / "native_spprc_acceptance_summary.json"
    )
    scale50_row = scale50_summary["rows"][0]
    scale50_b42 = scale50_row["b42_summary"]
    return {
        "schema_version": "lunar_ice_bpc.p0v4_validation_summary.v1",
        "historical_control_id": HISTORICAL_CONTROL_ID,
        "scale30": {
            "row_count": len(keys),
            "exact_count": sum(
                row["algorithm_status"] == "BPC_OPTIMAL"
                and row["exact_certificate"] == "True"
                for row in candidate.values()
            ),
            "incomplete_count": sum(
                row["algorithm_status"] != "BPC_OPTIMAL"
                for row in candidate.values()
            ),
            "redline_count": sum(
                row["certificate_leak"] != "0"
                or row["manual_rc_fail"] != "0"
                or row["pricing_rc_fail"] != "0"
                for row in candidate.values()
            ),
            "candidate_total_sec": sum(candidate_times),
            "control_total_sec": sum(control_times),
            "candidate_mean_sec": statistics.mean(candidate_times),
            "control_mean_sec": statistics.mean(control_times),
            "candidate_p50_sec": statistics.median(candidate_times),
            "control_p50_sec": statistics.median(control_times),
            "candidate_max_sec": max(candidate_times),
            "control_max_sec": max(control_times),
            "mean_ratio": statistics.mean(candidate_times)
            / statistics.mean(control_times),
            "paired_geometric_mean_ratio": math.exp(
                statistics.mean(math.log(ratio) for ratio in ratios)
            ),
            "paired_median_ratio": statistics.median(ratios),
            "improved_count": sum(ratio < 1.0 for ratio in ratios),
            "regressed_count": sum(ratio > 1.0 for ratio in ratios),
            "max_objective_delta": max(objective_deltas),
            "objective_tolerance": 1.1e-6,
            "instance_content_hash_mismatch_count": hash_mismatch_count,
        },
        "scale50_instance001": {
            "status": scale50_row["status"],
            "exact_count": scale50_row["exact_count"],
            "fail_closed_count": scale50_row["fail_closed_count"],
            "solver_wall_sec": scale50_row["profile_gate"][
                "mean_cold_start_total_sec"
            ],
            "effective_memory_limit_gb": scale50_row[
                "effective_memory_limit_gb"
            ],
            "redlines_zero": scale50_row["redlines_zero"],
            "root_added_column_count": scale50_b42["harvest_telemetry"][
                "root_pool_post_final_judge_harvest_added_to_master_count"
            ],
            "full_scale50_run_complete": False,
            "exact_root_closure": False,
        },
        "freeze_scope": {
            "scale30_full20_required": True,
            "scale50_singleton_boundary_preserved": True,
            "scale50_full_run_requested": False,
            "six_scale_promotion_claimed": False,
        },
    }


def _freeze_issues(validation: dict) -> list[str]:
    scale30 = validation["scale30"]
    scale50 = validation["scale50_instance001"]
    issues = []
    if scale30["row_count"] != 20 or scale30["exact_count"] != 20:
        issues.append("scale30_not_20_of_20_exact")
    if scale30["incomplete_count"] != 0 or scale30["redline_count"] != 0:
        issues.append("scale30_safety_gate_failed")
    if scale30["instance_content_hash_mismatch_count"] != 0:
        issues.append("scale30_instance_hash_mismatch")
    if scale30["max_objective_delta"] > scale30["objective_tolerance"]:
        issues.append("scale30_objective_mismatch")
    if scale30["mean_ratio"] > 1.0:
        issues.append("scale30_mean_regression")
    if scale30["paired_geometric_mean_ratio"] > 1.0:
        issues.append("scale30_geomean_regression")
    if scale50["status"] != "FAIL_CLOSED" or scale50["redlines_zero"] is not True:
        issues.append("scale50_boundary_not_fail_closed_safe")
    if scale50["exact_count"] != 0 or scale50["exact_root_closure"] is not False:
        issues.append("scale50_boundary_misrepresented")
    return issues


def _run_tests(*, build: Path, output: Path) -> dict:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join(
        (str(build / "install"), str(ROOT / "src"))
    )
    commands = (
        (
            "ctest",
            ["ctest", "--test-dir", str(build), "--output-on-failure"],
        ),
        (
            "pytest",
            [
                str(Path(sys.executable)),
                "-m",
                "pytest",
                "-q",
                "tests/native/test_native_spprc_backend.py",
                "tests/test_lunar_ice_labeling_pricer.py",
            ],
        ),
    )
    rows = []
    for name, command in commands:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )
        (output / f"{name}_stdout.txt").write_text(
            completed.stdout, encoding="utf-8"
        )
        (output / f"{name}_stderr.txt").write_text(
            completed.stderr, encoding="utf-8"
        )
        rows.append(
            {
                "name": name,
                "command": command,
                "returncode": completed.returncode,
                "stdout_sha256": _sha256_file(output / f"{name}_stdout.txt"),
                "stderr_sha256": _sha256_file(output / f"{name}_stderr.txt"),
            }
        )
    return {
        "schema_version": "lunar_ice_bpc.freeze_test_results.v1",
        "all_passed": all(row["returncode"] == 0 for row in rows),
        "tests": rows,
    }


def _source_bundle_rows() -> list[dict]:
    old = _read_json(OLD_SOURCE_SNAPSHOT)
    paths = {str(row["path"]) for row in old["source_bundle"]}
    paths.update(EXTRA_SOURCE_PATHS)
    rows = []
    for relative in sorted(paths):
        path = ROOT / relative
        if not path.is_file():
            raise SystemExit(f"source bundle file missing: {relative}")
        rows.append(
            {
                "path": relative,
                "sha256": _sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
        )
    return rows


def _write_source_archive(path: Path, rows: list[dict]) -> None:
    with path.open("wb") as raw:
        import gzip

        with gzip.GzipFile(
            filename="source_bundle.tar",
            mode="wb",
            fileobj=raw,
            mtime=0,
        ) as gz:
            with tarfile.open(fileobj=gz, mode="w") as archive:
                for row in rows:
                    source = ROOT / row["path"]
                    info = archive.gettarinfo(str(source), arcname=row["path"])
                    info.uid = 0
                    info.gid = 0
                    info.uname = ""
                    info.gname = ""
                    info.mtime = 0
                    with source.open("rb") as handle:
                        archive.addfile(info, handle)


def _write_readme(path: Path, validation: dict) -> None:
    scale30 = validation["scale30"]
    text = f"""# P0 V4 memory-compact 冻结基准

- freeze ID: `{FREEZE_ID}`
- 历史 control: `{HISTORICAL_CONTROL_ID}`
- scale30: 20/20 exact，mean ratio `{scale30['mean_ratio']:.6f}`，
  paired geometric mean ratio `{scale30['paired_geometric_mean_ratio']:.6f}`
- scale50/001: 3600 秒 `BPC_INCOMPLETE_PRICING`，安全 fail closed
- scale50 全量：按用户指示未运行
- scale5/10/20 V4 二进制：未重新跑正式全量
- scale100：未运行
- production 默认：`no_cut`，未切换

本目录冻结的是新的实验基准，不是六规模 promotion 证明。未来实验必须同时报告
上述未验证边界，不得把 scale50 的安全 timeout 写成 exact closure。
"""
    path.write_text(text, encoding="utf-8")


def _artifact(path: Path) -> dict:
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": _sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def _read_csv_rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stable_payload_hash(payload: object) -> str:
    encoded = json.dumps(
        payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _git_commit() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return completed.stdout.strip()


def _worktree_clean() -> bool:
    completed = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return not completed.stdout.strip()


def _config_model_id(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("model_id:"):
            return line.split(":", 1)[1].strip().strip("\"'")
    raise SystemExit("config model_id missing")


if __name__ == "__main__":
    raise SystemExit(main())
