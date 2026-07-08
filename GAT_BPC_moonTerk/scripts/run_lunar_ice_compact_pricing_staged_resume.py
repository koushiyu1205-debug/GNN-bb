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


def _stage_row(stage_index: int, probe_path: Path, probe: dict, *, stage_config: dict | None = None) -> dict:
    history = list(probe.get("history") or [])
    best_rc_values = [
        row.get("best_reduced_cost")
        for row in history
        if isinstance(row.get("best_reduced_cost"), (int, float))
    ]
    config = dict(stage_config or {})
    return {
        "stage_index": int(stage_index),
        "probe_path": str(probe_path),
        "stage_time_limit_sec": config.get("stage_time_limit_sec"),
        "max_rounds_per_stage": config.get("max_rounds_per_stage"),
        "batch_target": config.get("batch_target"),
        "negative_search_cap_sec": config.get("negative_search_cap_sec"),
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
        "best_negative_reduced_cost": min(best_rc_values) if best_rc_values else None,
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
        "",
        "| stage | batch | round cap | resume cols | active cols | added | rounds | state | scope | best RC | elapsed s |",
        "|---:|---:|---:|---:|---:|---:|---:|---|---|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| "
            f"{row.get('stage_index')} | "
            f"{row.get('batch_target', '')} | "
            f"{row.get('max_rounds_per_stage', '')} | "
            f"{row.get('resume_initial_column_count')} | "
            f"{row.get('active_column_count')} | "
            f"{row.get('added_column_count')} | "
            f"{row.get('pricing_round_count')} | "
            f"{row.get('pricing_state')} | "
            f"{row.get('certificate_scope')} | "
            f"{row.get('best_negative_reduced_cost')} | "
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
        "latest_active_column_count": latest.get("active_column_count"),
        "latest_added_column_count": latest.get("added_column_count"),
    }


if __name__ == "__main__":
    raise SystemExit(main())
