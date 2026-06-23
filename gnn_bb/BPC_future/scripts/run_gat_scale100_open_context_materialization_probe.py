#!/usr/bin/env python3
"""Run scale-100 open-context target-materialization probes.

This diagnostic helper automates the path that worked for the v107 scale-100
random-wave probe:

1. run a plain counterfactual capture on a scale-100 instance;
2. extract true-RC-negative returned journeys with materialization traces;
3. rerun the same instance with explicit opt-in open-context target
   materialization before the legacy final judge;
4. write a self-context runbook summary that
   build_gat_multibatch_worker_batch_impact_rows.py can consume.

The helper runs BPC through run_bpc_future.py, but it never changes solver
defaults and never enables certificate or official-bound effects.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from BPC_future.scripts.build_gat_same_run_target_priority_candidates import (  # noqa: E402
    _journey_sortie_traces,
    _true_reduced_cost,
)


DEFAULT_OUTPUT_DIR = Path(
    f"BPC_future/results/gat_target_mode_v107_stage4_biased_scale100_open_context_batch_probe_{date.today():%Y%m%d}"
)
PYTHON = "/home/kai/miniconda3/envs/ecole/bin/python"
DEFAULT_CONFIG = Path("BPC_future/configs/moon_trek_20_smoke.yaml")

CAPTURE_OVERRIDES = (
    "journey_counterfactual_replay_capture_enabled=True",
    "journey_counterfactual_replay_capture_active_basis_enabled=True",
    "journey_counterfactual_replay_capture_forbidden_signatures_enabled=True",
    "journey_counterfactual_replay_capture_log_empty=True",
    "journey_counterfactual_replay_capture_active_basis_max_rows=96",
    "journey_counterfactual_replay_capture_max_journeys=32",
    "journey_counterfactual_replay_capture_pool_max_journeys=256",
    "journey_counterfactual_replay_capture_forbidden_signature_max_count=256",
)

OPEN_CONTEXT_WORKER_OVERRIDES = (
    "journey_sharded_pulse_hidden_negative_worker_enabled=True",
    "journey_sharded_pulse_hidden_negative_worker_trigger=before_legacy_final_judge",
    "journey_sharded_pulse_hidden_negative_worker_log_skips=True",
    "journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=True",
    "journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=False",
    "journey_sharded_pulse_hidden_negative_worker_time_limit=0.250",
    "journey_sharded_pulse_hidden_negative_worker_max_recursions=0",
    "journey_sharded_pulse_hidden_negative_worker_archive_enabled=False",
    "journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=False",
    "journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=False",
    "journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=0",
    "journey_sharded_pulse_hidden_negative_worker_adaptive_sharding_enabled=False",
    "journey_sharded_pulse_hidden_negative_worker_refine_incomplete_first_task_shards=False",
    "journey_sharded_pulse_hidden_negative_worker_shard_scheduling_enabled=False",
    "journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled=False",
    "journey_sharded_pulse_hidden_negative_worker_impact_filter_mode=off",
    "journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=False",
    "journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=False",
    "journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=False",
    "journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True",
    "journey_sharded_pulse_hidden_negative_worker_target_path_diagnostics_enabled=False",
    "journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instance", type=Path, action="append", required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--capture-time-limit", type=float, default=80.0)
    parser.add_argument("--worker-time-limit", type=float, default=80.0)
    parser.add_argument("--timeout-seconds", type=float, default=150.0)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--skip-existing", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = run_probe(
        instances=[Path(path) for path in args.instance],
        output_dir=Path(args.output_dir),
        config=Path(args.config),
        capture_time_limit=float(args.capture_time_limit),
        worker_time_limit=float(args.worker_time_limit),
        timeout_seconds=float(args.timeout_seconds),
        batch_size=max(1, int(args.batch_size)),
        skip_existing=bool(args.skip_existing),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def run_probe(
    *,
    instances: list[Path],
    output_dir: Path,
    config: Path,
    capture_time_limit: float,
    worker_time_limit: float,
    timeout_seconds: float,
    batch_size: int,
    skip_existing: bool,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    candidate_runs: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    skipped: Counter[str] = Counter()

    for instance in instances:
        if not instance.exists():
            skipped["missing_instance"] += 1
            records.append({"instance": str(instance), "status": "skipped", "reason": "missing_instance"})
            continue
        run_name = _safe_name(instance.stem)
        capture_dir = output_dir / run_name / "capture"
        worker_dir = output_dir / run_name / "worker"
        capture_csv = capture_dir / "results.csv"
        worker_csv = worker_dir / "results.csv"

        if not (skip_existing and capture_csv.exists()):
            capture_cmd = _base_command(
                config=config,
                instance=instance,
                time_limit=capture_time_limit,
                results_csv=capture_csv,
                log_dir=capture_dir / "logs",
                solution_dir=capture_dir / "solutions",
                overrides=CAPTURE_OVERRIDES,
            )
            _write_json(capture_dir / "command.json", capture_cmd)
            capture_result = _run_command(capture_cmd, timeout_seconds=timeout_seconds)
        else:
            capture_result = {"status": "skipped_existing", "returncode": 0}

        capture_log = _single_jsonl(capture_dir / "logs")
        if capture_result["returncode"] != 0 or capture_log is None:
            skipped["capture_failed_or_missing_log"] += 1
            records.append(
                {
                    "instance": str(instance),
                    "status": "skipped",
                    "reason": "capture_failed_or_missing_log",
                    "capture_result": capture_result,
                }
            )
            continue

        selected = _select_materialization_payload(capture_log, batch_size=batch_size)
        if selected is None:
            skipped["no_negative_materialization_payload"] += 1
            records.append(
                {
                    "instance": str(instance),
                    "status": "skipped",
                    "reason": "no_negative_materialization_payload",
                    "capture_log": str(capture_log),
                    "capture_result": capture_result,
                }
            )
            continue

        worker_overrides = (
            *CAPTURE_OVERRIDES,
            *OPEN_CONTEXT_WORKER_OVERRIDES,
            f"journey_sharded_pulse_hidden_negative_worker_max_columns={int(batch_size)}",
            "journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence="
            + ",".join(str(task) for task in selected["flattened_sequence"]),
            "journey_sharded_pulse_hidden_negative_worker_target_materialization_journeys="
            + json.dumps(selected["materialization_journeys"], ensure_ascii=False, separators=(",", ":")),
        )
        worker_cmd = _base_command(
            config=config,
            instance=instance,
            time_limit=worker_time_limit,
            results_csv=worker_csv,
            log_dir=worker_dir / "logs",
            solution_dir=worker_dir / "solutions",
            overrides=worker_overrides,
        )
        _write_json(worker_dir / "command.json", worker_cmd)
        if not (skip_existing and worker_csv.exists()):
            worker_result = _run_command(worker_cmd, timeout_seconds=timeout_seconds)
        else:
            worker_result = {"status": "skipped_existing", "returncode": 0}

        worker_log = _single_jsonl(worker_dir / "logs")
        candidate = None
        if worker_result["returncode"] == 0 and worker_log is not None:
            candidate = _candidate_from_worker_log(
                instance=instance,
                worker_csv=worker_csv,
                worker_log=worker_log,
                selected=selected,
            )
        if candidate is None:
            skipped["worker_missing_materialized_context"] += 1
            records.append(
                {
                    "instance": str(instance),
                    "status": "skipped",
                    "reason": "worker_missing_materialized_context",
                    "capture_log": str(capture_log),
                    "worker_log": "" if worker_log is None else str(worker_log),
                    "capture_result": capture_result,
                    "worker_result": worker_result,
                }
            )
            continue
        candidate_runs.append(candidate)
        records.append(
            {
                "instance": str(instance),
                "status": "selected",
                "candidate_name": candidate["name"],
                "context_hash": candidate["expected_context_hash"],
                "family": candidate["instance_family"],
                "batch_size": len(candidate.get("target_sortie_traces") or []),
                "capture_log": str(capture_log),
                "worker_log": str(worker_log),
                "capture_result": capture_result,
                "worker_result": worker_result,
            }
        )

    runbook_summary = {
        "schema_version": "gat_target_priority_worker_ab_runbook_v1_self_context_probe",
        "status": "ready" if candidate_runs else "no_candidates",
        "worker_method": "target_materialization_fixed_open_context_batch_probe",
        "worker_batch_size": int(batch_size),
        "input_candidate_count": len(instances),
        "candidate_group_count": len(candidate_runs),
        "candidate_runs": candidate_runs,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "default_enabled": False,
        "certificate_ready": False,
        "official_bound_effect": False,
        "checks": {
            "self_context_probe": True,
            "no_certificate_effect": True,
            "official_bound_effect": False,
            "has_candidate_runs": bool(candidate_runs),
        },
        "all_checks_pass": bool(candidate_runs),
    }
    runbook_dir = output_dir / "self_context_worker_runbook"
    runbook_dir.mkdir(parents=True, exist_ok=True)
    _write_json(runbook_dir / "summary.json", runbook_summary)

    summary = {
        "schema_version": "gat_scale100_open_context_materialization_probe_execution_v1",
        "status": "built" if candidate_runs else "no_candidates",
        "output_dir": str(output_dir),
        "runbook_summary": str(runbook_dir / "summary.json"),
        "instance_count": len(instances),
        "candidate_count": len(candidate_runs),
        "records": records,
        "skipped_counts": dict(sorted(skipped.items())),
        "runs_bpc_or_pricing": True,
        "production_ready": False,
        "default_enabled": False,
        "certificate_ready": False,
        "official_bound_effect": False,
        "all_checks_pass": bool(candidate_runs),
    }
    _write_json(output_dir / "summary.json", summary)
    return summary


def _base_command(
    *,
    config: Path,
    instance: Path,
    time_limit: float,
    results_csv: Path,
    log_dir: Path,
    solution_dir: Path,
    overrides: tuple[str, ...],
) -> list[str]:
    results_csv.parent.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    solution_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        PYTHON,
        "BPC_future/scripts/run_bpc_future.py",
        "--config",
        str(config),
        "--instances",
        str(instance),
        "--time-limit",
        f"{float(time_limit):.6f}",
        "--results-csv",
        str(results_csv),
        "--log-dir",
        str(log_dir),
        "--solution-dir",
        str(solution_dir),
        "--quiet",
    ]
    for override in overrides:
        cmd.extend(["--set", override])
    return cmd


def _run_command(cmd: list[str], *, timeout_seconds: float) -> dict[str, Any]:
    env = dict(**__import__("os").environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = "."
    try:
        completed = subprocess.run(
            cmd,
            cwd=str(ROOT),
            env=env,
            text=True,
            capture_output=True,
            timeout=float(timeout_seconds),
        )
        return {
            "status": "success" if completed.returncode == 0 else "failed",
            "returncode": int(completed.returncode),
            "stdout_tail": completed.stdout[-2000:],
            "stderr_tail": completed.stderr[-2000:],
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "timeout",
            "returncode": 124,
            "stdout_tail": (exc.stdout or "")[-2000:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": (exc.stderr or "")[-2000:] if isinstance(exc.stderr, str) else "",
        }


def _single_jsonl(root: Path) -> Path | None:
    files = sorted(Path(root).glob("**/*.jsonl"))
    return files[0] if files else None


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            try:
                event = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict):
                rows.append(event)
    return rows


def _select_materialization_payload(path: Path, *, batch_size: int) -> dict[str, Any] | None:
    best: dict[str, Any] | None = None
    for event in _read_jsonl(path):
        if event.get("event") != "journey_counterfactual_replay_capture":
            continue
        candidates: list[dict[str, Any]] = []
        for journey in event.get("returned_journeys") or []:
            if not isinstance(journey, dict):
                continue
            true_rc = _true_reduced_cost(journey)
            if true_rc is None or float(true_rc) >= 0.0:
                continue
            traces = _journey_sortie_traces(journey)
            if not traces:
                continue
            candidates.append({"true_rc": float(true_rc), "traces": traces})
        if not candidates:
            continue
        candidates.sort(key=lambda item: item["true_rc"])
        selected = candidates[: int(batch_size)]
        flattened = [
            int(task)
            for item in selected
            for trace in item["traces"]
            for task in (trace.get("sequence") or [])
        ]
        if not flattened:
            continue
        score = (len(selected), -float(selected[0]["true_rc"]))
        item = {
            "score": score,
            "source_context_hash": str(event.get("context_hash") or ""),
            "source_cg_iter": int(event.get("cg_iter") or 0),
            "flattened_sequence": flattened,
            "target_priority_sequence": list(selected[0]["traces"][0].get("sequence") or []),
            "target_arc_option_sequence": list(selected[0]["traces"][0].get("arc_option_sequence") or []),
            "target_sortie_traces": [
                trace for selected_item in selected for trace in selected_item["traces"]
            ],
            "best_true_reduced_cost": float(selected[0]["true_rc"]),
            "materialization_journeys": [
                {"traces": selected_item["traces"]} for selected_item in selected
            ],
        }
        if best is None or item["score"] > best["score"]:
            best = item
    return best


def _candidate_from_worker_log(
    *,
    instance: Path,
    worker_csv: Path,
    worker_log: Path,
    selected: dict[str, Any],
) -> dict[str, Any] | None:
    events = _read_jsonl(worker_log)
    captures = {
        str(event.get("context_hash") or ""): event
        for event in events
        if event.get("event") == "journey_counterfactual_replay_capture"
    }
    workers = [
        event
        for event in events
        if event.get("event") == "journey_sharded_pulse_hidden_negative_worker"
        and not bool(event.get("pulse_worker_skipped"))
        and bool(event.get("pulse_worker_target_sequence_materialized"))
        and bool(event.get("pulse_worker_target_sequence_negative"))
        and int(event.get("pulse_worker_returned_journeys") or 0) > 0
    ]
    if not workers:
        return None
    workers.sort(key=lambda event: (int(event.get("cg_iter") or 0), int(event.get("node_id") or 0), int(event.get("depth") or 0)))
    worker = workers[0]
    context_hash = str(worker.get("pulse_worker_context_hash") or "")
    capture = captures.get(context_hash)
    if capture is None:
        return None
    family, region, task_count = _metadata_from_instance(instance)
    name = _safe_name(f"task{task_count}_{family}_open_context_batch{len(selected['materialization_journeys'])}_cg{int(capture.get('cg_iter') or 0):03d}_{context_hash}")
    return {
        "name": name,
        "baseline_command_type": "none_self_context_probe",
        "worker_command_type": name + "_worker",
        "worker_csv": str(worker_csv),
        "source_file": str(worker_log),
        "instance": str(instance),
        "instance_family": family,
        "family": family,
        "instance_region": region,
        "region": region,
        "instance_task_count": int(task_count),
        "task_count": int(task_count),
        "expected_context_hash": context_hash,
        "capture_cg_iter": int(capture.get("cg_iter") or 0),
        "capture_pricing_kind": str(capture.get("pricing_kind") or ""),
        "true_dual_hash": str(capture.get("true_dual_hash") or ""),
        "cut_hash": str(capture.get("cut_hash") or ""),
        "branch_hash": str(capture.get("branch_hash") or ""),
        "forbidden_signature_hash": str(capture.get("forbidden_signature_hash") or ""),
        "active_hash_before": str(capture.get("active_hash_before") or ""),
        "pool_signature_hash": str(capture.get("pool_signature_hash") or ""),
        "pool_task_set_hash": str(capture.get("pool_task_set_hash") or ""),
        "candidate_context_complete": True,
        "best_true_reduced_cost": float(worker.get("pulse_worker_best_rc") or selected["best_true_reduced_cost"]),
        "target_sequence": list(worker.get("pulse_worker_target_sequence") or selected["flattened_sequence"]),
        "target_priority_sequence": list(selected["target_priority_sequence"]),
        "target_arc_option_sequence": [],
        "target_sortie_traces": list(selected["target_sortie_traces"]),
    }


def _metadata_from_instance(instance: Path) -> tuple[str, str, int]:
    parts = set(instance.parts)
    family = "unknown"
    for candidate in ("sector-wave", "random-wave", "greedy-anchor"):
        if candidate in parts:
            family = candidate
            break
    region = "unknown"
    text = str(instance)
    if "tranquillitatis" in text:
        region = "tranquillitatis_balmer_like_20km"
    elif "apollo" in text:
        region = "apollo15_20km"
    task_count = 0
    for part in instance.parts:
        if part.startswith("tasks_"):
            digits = part.split("_", 1)[1]
            if digits.isdigit():
                task_count = int(digits)
                break
    return family, region, task_count or 100


def _safe_name(text: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in str(text))
    safe = "_".join(part for part in safe.split("_") if part)
    return safe[:180] or "probe"


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
