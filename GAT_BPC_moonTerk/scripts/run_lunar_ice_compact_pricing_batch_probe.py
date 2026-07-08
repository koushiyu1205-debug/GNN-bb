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

from lunar_ice_bpc.exact.bpc.solver.root_node_solver import solve_b1_root_node_baseline  # noqa: E402
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
    args = parser.parse_args()

    instance_path = _resolve(args.instance)
    output_dir = _resolve(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    data = load_lunar_ice_data(json.loads(instance_path.read_text(encoding="utf-8")))
    resume_payload = _load_resume_payload(args.resume_probe)
    initial_columns = _resume_initial_columns(data, resume_payload)
    started = perf_counter()
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
            "env_compact_negative_batch_target": os.environ.get("LUNAR_ICE_COMPACT_NEGATIVE_BATCH_TARGET", ""),
            "env_compact_negative_search_cap_sec": os.environ.get("LUNAR_ICE_COMPACT_NEGATIVE_SEARCH_CAP_SEC", ""),
            "env_compact_negative_no_good_scope": os.environ.get("LUNAR_ICE_COMPACT_NEGATIVE_NO_GOOD_SCOPE", ""),
            "resume_probe": "" if not resume_payload else str(_resolve(args.resume_probe)),
            "resume_initial_column_count": len(initial_columns) if initial_columns is not None else 0,
            "write_active_columns": bool(args.write_active_columns or initial_columns),
        },
        "elapsed_sec": round(elapsed, 6),
        "algorithm_status": result.get("algorithm_status"),
        "certificate_scope": result.get("certificate_scope"),
        "pricing_state": result.get("pricing_state"),
        "pricing_round_count": result.get("pricing_round_count"),
        "added_column_count": result.get("added_column_count"),
        "final_judge_call_count": result.get("final_judge_call_count"),
        "final_judge_found_negative_count": result.get("final_judge_found_negative_count"),
        "final_judge_incomplete_count": result.get("final_judge_incomplete_count"),
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
        f"- pricing_round_count: `{payload['pricing_round_count']}`",
        f"- added_column_count: `{payload['added_column_count']}`",
        f"- final_judge_call_count: `{payload['final_judge_call_count']}`",
        f"- final_judge phase: `{final_judge.get('compact_pricing_phase')}`",
        f"- final_judge negative_column_count: `{final_judge.get('negative_column_count')}`",
        f"- compact batch found count: `{final_judge.get('compact_negative_batch_found_count')}`",
        f"- compact batch search calls: `{final_judge.get('compact_negative_batch_search_call_count')}`",
        f"- compact no-good scope: `{final_judge.get('compact_negative_no_good_scope')}`",
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
