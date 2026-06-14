#!/usr/bin/env python3
"""Build a sector-wave-only kNN+OOD CBF audit smoke runbook.

This helper does not run BPC, pricing, workers, certificates, or the CBF
scheduler.  It emits two commands:

1. an opt-in capture command for 20-task sector-wave instances;
2. a read-only kNN+OOD capture-validation command for the produced JSONL logs.

The runbook is deliberately scoped to the first family that passed both
scale-level and family-level offline candidate checks: ``20|sector-wave``.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from BPC_future.scripts.build_cbf_family_capture_worklist import CAPTURE_OVERRIDES


DEFAULT_TRAIN_DATASET = Path(
    "BPC_future/results/cbf_trajectory_gate_dataset_global_h2_20260614/"
    "cbf_trajectory_gate_transitions.jsonl"
)
DEFAULT_TASKS_ROOT = Path("BPC_future/logical_graph/tasks_020/sector-wave")
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/cbf_knn_ood_sector_wave_smoke_runbook_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_cbf_knn_ood_sector_wave_smoke_runbook_zh.md"
)
PYTHON = "/home/kai/miniconda3/envs/ecole/bin/python"

DEFAULT_ORDINALS = (1, 5)


def _instance_stem(path: Path) -> str:
    return path.name.replace("_logical_graph.json", "").replace(".json", "")


def _instance_ordinal(path: Path) -> int | None:
    match = re.search(r"_tasks020_(\d+)_seed", path.name)
    return int(match.group(1)) if match else None


def _region(path: Path) -> str:
    text = str(path).lower()
    if "tranquillitatis" in text:
        return "tranquillitatis"
    if "apollo" in text:
        return "apollo"
    return "unknown"


def _list_sector_wave_instances(tasks_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(tasks_root.rglob("*_logical_graph.json")):
        rows.append(
            {
                "instance": str(path),
                "instance_stem": _instance_stem(path),
                "task_count": 20,
                "family": "sector-wave",
                "task_family": "20|sector-wave",
                "region": _region(path),
                "ordinal": _instance_ordinal(path),
            }
        )
    return rows


def _select_instances(
    *,
    tasks_root: Path,
    ordinals: tuple[int, ...],
    max_instances: int,
) -> list[dict[str, Any]]:
    available = _list_sector_wave_instances(tasks_root)
    wanted = set(int(value) for value in ordinals)
    preferred: list[dict[str, Any]] = [
        item for item in available if item.get("ordinal") in wanted
    ]
    if not preferred:
        preferred = available
    region_order = {"apollo": 0, "tranquillitatis": 1, "unknown": 2}
    preferred.sort(
        key=lambda item: (
            int(item.get("ordinal") or 10**9),
            region_order.get(str(item.get("region")), 9),
            str(item.get("instance")),
        )
    )
    return preferred[: int(max_instances)]


def _capture_command(
    *,
    instances: list[dict[str, Any]],
    output_dir: Path,
    time_limit: float,
    max_workers: int,
    timeout_kill_after: str,
) -> str:
    capture_dir = output_dir / "sector_wave_capture"
    parts = [
        "PYTHONDONTWRITEBYTECODE=1",
        "PYTHONPATH=.",
        PYTHON,
        "BPC_future/scripts/run_bpc_future_external_timeout_batch.py",
        "--config",
        "BPC_future/configs/moon_trek_20_smoke.yaml",
        "--time-limit",
        f"{float(time_limit):.6f}",
        "--timeout-kill-after",
        str(timeout_kill_after),
        "--max-workers",
        str(int(max_workers)),
        "--results-csv",
        str(capture_dir / "results.csv"),
        "--log-dir",
        str(capture_dir / "logs"),
        "--solution-dir",
        str(capture_dir / "solutions"),
        "--run-log-dir",
        str(capture_dir / "run_logs"),
        "--quiet",
        "--instances",
    ]
    parts.extend(str(item["instance"]) for item in instances)
    for override in CAPTURE_OVERRIDES:
        parts.extend(["--set", override])
    return " ".join(parts)


def _validation_command(
    *,
    train_dataset: Path,
    capture_log_dir: Path,
    output_dir: Path,
    report: Path,
    knn_k: int,
    threshold: float,
    safe_radius_quantile: float,
    safe_radius_multiplier: float,
) -> str:
    validation_dir = output_dir / "sector_wave_knn_ood_capture_validation"
    parts = [
        "PYTHONDONTWRITEBYTECODE=1",
        "PYTHONPATH=.",
        PYTHON,
        "BPC_future/scripts/audit_cbf_delay_queue_knn_ood_capture_validation.py",
        str(capture_log_dir),
        "--train-dataset",
        str(train_dataset),
        "--output-dir",
        str(validation_dir),
        "--report",
        str(report),
        "--knn-k",
        str(int(knn_k)),
        "--max-neighbor-unsafe-fraction",
        "0.0",
        "--min-high-priority-threshold",
        f"{float(threshold):.6f}",
        "--safe-radius-quantile",
        f"{float(safe_radius_quantile):.6f}",
        "--safe-radius-multiplier",
        f"{float(safe_radius_multiplier):.6f}",
    ]
    return " ".join(parts)


def _has_forbidden_active_knob(command: str) -> bool:
    forbidden = [
        "allow_certificate_effect=true",
        "certificate_enabled=true",
        "dummy_certificate=true",
        "worker_enabled=true",
        "active_worker_enabled=true",
        "journey_sharded_pulse_worker_enabled=true",
        "journey_pulse_hidden_negative_worker_enabled=true",
        "journey_final_judge_sharding_enabled=true",
        "journey_pulse_final_judge_enabled=true",
    ]
    return any(token in command for token in forbidden)


def build_runbook(
    *,
    tasks_root: Path = DEFAULT_TASKS_ROOT,
    train_dataset: Path = DEFAULT_TRAIN_DATASET,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    ordinals: tuple[int, ...] = DEFAULT_ORDINALS,
    max_instances: int = 4,
    time_limit: float = 90.0,
    max_workers: int = 1,
    timeout_kill_after: str = "30s",
    knn_k: int = 3,
    threshold: float = 0.8,
    safe_radius_quantile: float = 1.0,
    safe_radius_multiplier: float = 1.0,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    instances = _select_instances(
        tasks_root=tasks_root,
        ordinals=tuple(int(value) for value in ordinals),
        max_instances=int(max_instances),
    )
    capture_log_dir = output_dir / "sector_wave_capture" / "logs"
    validation_report = output_dir / "sector_wave_knn_ood_capture_validation_zh.md"
    capture_command = _capture_command(
        instances=instances,
        output_dir=output_dir,
        time_limit=float(time_limit),
        max_workers=int(max_workers),
        timeout_kill_after=str(timeout_kill_after),
    )
    validation_command = _validation_command(
        train_dataset=train_dataset,
        capture_log_dir=capture_log_dir,
        output_dir=output_dir,
        report=validation_report,
        knn_k=int(knn_k),
        threshold=float(threshold),
        safe_radius_quantile=float(safe_radius_quantile),
        safe_radius_multiplier=float(safe_radius_multiplier),
    )
    commands = [
        {
            "command_type": "sector_wave_capture",
            "description": "Run baseline solver with replay capture enabled only.",
            "command": capture_command,
        },
        {
            "command_type": "knn_ood_capture_validation",
            "description": "Read produced JSONL logs and validate the k=3 kNN+OOD scheduler.",
            "command": validation_command,
        },
    ]
    checks = {
        "diagnostic_only": True,
        "runs_bpc_or_pricing_false_for_builder": True,
        "all_selected_instances_exist": all(
            Path(str(item["instance"])).exists() for item in instances
        ),
        "all_selected_instances_are_task20_sector_wave": all(
            "/tasks_020/sector-wave/" in str(item["instance"]) for item in instances
        ),
        "has_apollo_and_tranquillitatis": {"apollo", "tranquillitatis"}.issubset(
            {str(item.get("region")) for item in instances}
        ),
        "capture_command_enables_capture": all(
            override in capture_command for override in CAPTURE_OVERRIDES
        ),
        "commands_do_not_enable_worker_or_certificate": not any(
            _has_forbidden_active_knob(item["command"]) for item in commands
        ),
        "validation_uses_k3_candidate": (
            "--knn-k 3" in validation_command
            and "--min-high-priority-threshold 0.800000" in validation_command
            and "--safe-radius-quantile 1.000000" in validation_command
            and "--safe-radius-multiplier 1.000000" in validation_command
        ),
    }
    summary = {
        "schema_version": "cbf_knn_ood_sector_wave_smoke_runbook_v1",
        "status": "cbf_knn_ood_sector_wave_smoke_runbook_ready",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "target_task_family": "20|sector-wave",
        "selected_instance_count": len(instances),
        "selected_instances": instances,
        "candidate_policy": {
            "policy": "knn_ood_delay_queue_scheduler",
            "knn_k": int(knn_k),
            "max_neighbor_unsafe_fraction": 0.0,
            "min_high_priority_threshold": float(threshold),
            "safe_radius_quantile": float(safe_radius_quantile),
            "safe_radius_multiplier": float(safe_radius_multiplier),
            "unsafe_action": "delay_not_reject",
            "certificate_effect": False,
            "official_bound_effect": False,
            "active_worker_effect": False,
        },
        "proof_budget_contract": {
            "delay_queue_can_extend_proof_budget": False,
            "delay_queue_runs_proof_sweep": False,
            "proof_stage_budget_effect": "none_existing_exact_deadlines_unchanged",
            "proof_stage_policy": "delay_queue_never_replaces_or_extends_exact_final_judge",
        },
        "train_dataset": str(train_dataset),
        "output_dir": str(output_dir),
        "commands": commands,
        "checks": checks,
        "all_checks_pass": all(bool(value) for value in checks.values()),
        "production_ready": False,
        "active_worker_ready": False,
        "certificate_ready": False,
        "goal_complete": False,
        "next_step": (
            "Run the capture command, then run the validation command. Only if "
            "validation has zero false positives and visible high-priority/RMP "
            "movement should a later opt-in active-worker A/B be considered."
        ),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(report, summary)
    return summary


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# CBF kNN+OOD Sector-Wave Audit-Only Smoke Runbook",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告只生成 `20|sector-wave` 的 opt-in audit-only smoke 命令。",
        "它本身不运行 BPC / pricing / RMP，不启用 worker，不产生 certificate，",
        "也不改变 official lower bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "cbf_knn_ood_sector_wave_smoke_runbook = current",
        f"status = {summary['status']}",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"target_task_family = {summary['target_task_family']}",
        f"selected_instance_count = {summary['selected_instance_count']}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"active_worker_ready = {str(summary['active_worker_ready']).lower()}",
        f"certificate_ready = {str(summary['certificate_ready']).lower()}",
        "```",
        "",
        "## Candidate",
        "",
        "```json",
        json.dumps(summary["candidate_policy"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Proof Budget Contract",
        "",
        "```json",
        json.dumps(summary["proof_budget_contract"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Selected Instances",
        "",
    ]
    for item in summary["selected_instances"]:
        lines.append(
            f"- `{item['region']}` ordinal={item['ordinal']}: `{item['instance']}`"
        )
    lines.extend(["", "## Commands", ""])
    for item in summary["commands"]:
        lines.extend(
            [
                f"### {item['command_type']}",
                "",
                item["description"],
                "",
                "```bash",
                item["command"],
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## 解释",
            "",
            "- 这是 sector-wave-only 的真实日志采集协议，不是 production 接入；",
            "- capture 命令只启用 counterfactual replay capture，不启用 Pulse worker 或 certificate；",
            "- validation 命令使用当前外部网格里有信号的 `k=3, threshold=0.8, q=1.0, m=1.0`；",
            "- 通过该 smoke 只能证明值得继续 A/B，不能证明可以默认启用；",
            "- 若 validation 仍全 delay，则候选还没有真实 ROI 证据；",
            "- 若出现 false positive，则该候选必须继续保持 delay / abstain。",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks-root", type=Path, default=DEFAULT_TASKS_ROOT)
    parser.add_argument("--train-dataset", type=Path, default=DEFAULT_TRAIN_DATASET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--ordinals", nargs="*", type=int, default=list(DEFAULT_ORDINALS))
    parser.add_argument("--max-instances", type=int, default=4)
    parser.add_argument("--time-limit", type=float, default=90.0)
    parser.add_argument("--max-workers", type=int, default=1)
    parser.add_argument("--timeout-kill-after", default="30s")
    parser.add_argument("--knn-k", type=int, default=3)
    parser.add_argument("--threshold", type=float, default=0.8)
    parser.add_argument("--safe-radius-quantile", type=float, default=1.0)
    parser.add_argument("--safe-radius-multiplier", type=float, default=1.0)
    args = parser.parse_args(argv)
    summary = build_runbook(
        tasks_root=args.tasks_root,
        train_dataset=args.train_dataset,
        output_dir=args.output_dir,
        report=args.report,
        ordinals=tuple(args.ordinals),
        max_instances=args.max_instances,
        time_limit=args.time_limit,
        max_workers=args.max_workers,
        timeout_kill_after=args.timeout_kill_after,
        knn_k=args.knn_k,
        threshold=args.threshold,
        safe_radius_quantile=args.safe_radius_quantile,
        safe_radius_multiplier=args.safe_radius_multiplier,
    )
    print(
        json.dumps(
            {
                "summary": str(args.output_dir / "summary.json"),
                "report": str(args.report),
                "all_checks_pass": summary["all_checks_pass"],
                "selected_instance_count": summary["selected_instance_count"],
                "production_ready": summary["production_ready"],
                "command_count": len(summary["commands"]),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
