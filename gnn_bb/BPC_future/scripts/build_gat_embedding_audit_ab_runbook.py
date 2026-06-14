#!/usr/bin/env python3
"""Build a pre-online GAT embedding audit A/B runbook.

This runbook is deliberately pre-production:

* 5/10 commands compare baseline vs capture-only runs to guard official-result
  no-regression before any online effect exists.
* 20-task commands collect sector-wave capture logs for GAT embedding
  kNN/OOD validation.
* No command enables a worker, certificate, or official-bound shortcut.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from BPC_future.scripts.audit_gat_embedding_knn_ood_external_validation import (
    DEFAULT_CHECKPOINT,
    DEFAULT_TRAIN_DATASET_DIR,
)
from BPC_future.scripts.build_cbf_family_capture_worklist import CAPTURE_OVERRIDES


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/gat_embedding_audit_ab_runbook_20260614")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_gat_embedding_audit_ab_runbook_zh.md"
)
PYTHON = "/home/kai/miniconda3/envs/ecole/bin/python"
DEFAULT_LOGICAL_GRAPH_ROOT = Path("BPC_future/logical_graph")

SCALE_CONFIG = {
    5: "BPC_future/configs/moon_trek_5_journey.yaml",
    10: "BPC_future/configs/moon_trek_10_journey.yaml",
    20: "BPC_future/configs/moon_trek_20_smoke.yaml",
}

NO_GNN_BASELINE_OVERRIDES = (
    "journey_learning_enabled=False",
    "journey_learning_required=False",
    "journey_learning_fail_hard=False",
    "journey_learning_force_light_profile_pricing=False",
    "journey_learning_prewarm_enabled=False",
    "journey_learning_pricing_enabled=False",
)


def _scale_root(logical_graph_root: Path, scale: int, *, family: str) -> Path:
    return Path(logical_graph_root) / f"tasks_{int(scale):03d}" / family


def _instance_ordinal(path: Path, scale: int) -> int | None:
    match = re.search(rf"_tasks{int(scale):03d}_(\d+)_seed", path.name)
    return int(match.group(1)) if match else None


def _region(path: Path) -> str:
    text = str(path).lower()
    if "tranquillitatis" in text:
        return "tranquillitatis"
    if "apollo" in text:
        return "apollo"
    return "unknown"


def _list_instances(
    scale: int,
    *,
    logical_graph_root: Path = DEFAULT_LOGICAL_GRAPH_ROOT,
    family: str = "sector-wave",
) -> list[dict[str, Any]]:
    root = _scale_root(Path(logical_graph_root), int(scale), family=family)
    rows: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*_logical_graph.json")):
        rows.append(
            {
                "instance": str(path),
                "task_count": int(scale),
                "family": family,
                "task_family": f"{int(scale)}|{family}",
                "region": _region(path),
                "ordinal": _instance_ordinal(path, int(scale)),
            }
        )
    return rows


def _select_instances(
    scale: int,
    *,
    logical_graph_root: Path = DEFAULT_LOGICAL_GRAPH_ROOT,
    family: str = "sector-wave",
    ordinals: tuple[int, ...] = (1,),
    max_instances: int = 2,
) -> list[dict[str, Any]]:
    available = _list_instances(
        int(scale),
        logical_graph_root=Path(logical_graph_root),
        family=family,
    )
    wanted = set(int(value) for value in ordinals)
    selected = [item for item in available if item.get("ordinal") in wanted]
    if not selected:
        selected = available
    region_order = {"apollo": 0, "tranquillitatis": 1, "unknown": 2}
    selected.sort(
        key=lambda item: (
            int(item.get("ordinal") or 10**9),
            region_order.get(str(item.get("region")), 9),
            str(item.get("instance")),
        )
    )
    return selected[: int(max_instances)]


def _batch_command(
    *,
    instances: list[dict[str, Any]],
    scale: int,
    profile: str,
    output_dir: Path,
    time_limit: float,
    max_workers: int,
    timeout_kill_after: str,
    capture_enabled: bool,
) -> str:
    run_dir = output_dir / f"task{int(scale):03d}_{profile}"
    parts = [
        "PYTHONDONTWRITEBYTECODE=1",
        "PYTHONPATH=.",
        PYTHON,
        "BPC_future/scripts/run_bpc_future_external_timeout_batch.py",
        "--config",
        SCALE_CONFIG[int(scale)],
        "--time-limit",
        f"{float(time_limit):.6f}",
        "--timeout-kill-after",
        str(timeout_kill_after),
        "--max-workers",
        str(int(max_workers)),
        "--results-csv",
        str(run_dir / "results.csv"),
        "--log-dir",
        str(run_dir / "logs"),
        "--solution-dir",
        str(run_dir / "solutions"),
        "--run-log-dir",
        str(run_dir / "run_logs"),
        "--quiet",
        "--instances",
    ]
    parts.extend(str(item["instance"]) for item in instances)
    for override in NO_GNN_BASELINE_OVERRIDES:
        parts.extend(["--set", override])
    if capture_enabled:
        for override in CAPTURE_OVERRIDES:
            parts.extend(["--set", override])
    return " ".join(parts)


def _validation_command(
    *,
    train_dataset_dir: Path,
    checkpoint: Path,
    capture_log_dir: Path,
    output_dir: Path,
    report: Path,
    device: str,
    knn_k: int,
    threshold: float,
    safe_radius_quantile: float,
    safe_radius_multiplier: float,
) -> str:
    validation_dir = output_dir / "task020_gat_embedding_capture_validation"
    parts = [
        "PYTHONDONTWRITEBYTECODE=1",
        "PYTHONPATH=.",
        PYTHON,
        "BPC_future/scripts/audit_gat_embedding_knn_ood_capture_validation.py",
        str(capture_log_dir),
        "--train-dataset-dir",
        str(train_dataset_dir),
        "--checkpoint",
        str(checkpoint),
        "--output-dir",
        str(validation_dir),
        "--report",
        str(report),
        "--device",
        str(device),
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


def _analysis_command(*, runbook_summary: Path, output_dir: Path, report: Path) -> str:
    return " ".join(
        [
            "PYTHONDONTWRITEBYTECODE=1",
            "PYTHONPATH=.",
            PYTHON,
            "BPC_future/scripts/audit_gat_embedding_audit_ab_results.py",
            "--runbook-summary",
            str(runbook_summary),
            "--output-dir",
            str(output_dir / "audit_ab_analysis"),
            "--report",
            str(report),
        ]
    )


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
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    logical_graph_root: Path = DEFAULT_LOGICAL_GRAPH_ROOT,
    train_dataset_dir: Path = DEFAULT_TRAIN_DATASET_DIR,
    checkpoint: Path = DEFAULT_CHECKPOINT,
    small_ordinals: tuple[int, ...] = (1,),
    twenty_ordinals: tuple[int, ...] = (1, 5),
    small_max_instances_per_scale: int = 2,
    twenty_max_instances: int = 4,
    small_time_limit: float = 60.0,
    twenty_time_limit: float = 200.0,
    max_workers: int = 1,
    timeout_kill_after: str = "30s",
    device: str = "cpu",
    knn_k: int = 3,
    threshold: float = 0.75,
    safe_radius_quantile: float = 1.0,
    safe_radius_multiplier: float = 1.0,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    small_instances = {
        scale: _select_instances(
            scale,
            logical_graph_root=Path(logical_graph_root),
            ordinals=small_ordinals,
            max_instances=small_max_instances_per_scale,
        )
        for scale in (5, 10)
    }
    twenty_instances = _select_instances(
        20,
        logical_graph_root=Path(logical_graph_root),
        ordinals=twenty_ordinals,
        max_instances=twenty_max_instances,
    )

    result_pairs: list[dict[str, Any]] = []
    commands: list[dict[str, str]] = []
    for scale in (5, 10, 20):
        instances = small_instances[scale] if scale in small_instances else twenty_instances
        time_limit = small_time_limit if scale in (5, 10) else twenty_time_limit
        for profile, capture_enabled in (("baseline", False), ("capture", True)):
            command = _batch_command(
                instances=instances,
                scale=scale,
                profile=profile,
                output_dir=output_dir,
                time_limit=float(time_limit),
                max_workers=int(max_workers),
                timeout_kill_after=str(timeout_kill_after),
                capture_enabled=bool(capture_enabled),
            )
            commands.append(
                {
                    "command_type": f"task{scale:03d}_{profile}",
                    "description": (
                        "Run baseline solver."
                        if not capture_enabled
                        else "Run solver with counterfactual replay capture enabled only."
                    ),
                    "command": command,
                }
            )
        result_pairs.append(
            {
                "task_count": int(scale),
                "baseline_csv": str(output_dir / f"task{scale:03d}_baseline" / "results.csv"),
                "capture_csv": str(output_dir / f"task{scale:03d}_capture" / "results.csv"),
                "instance_count": len(instances),
                "instances": instances,
            }
        )

    validation_report = output_dir / "task020_gat_embedding_capture_validation_zh.md"
    validation_summary = (
        output_dir
        / "task020_gat_embedding_capture_validation"
        / "summary.json"
    )
    validation_command = _validation_command(
        train_dataset_dir=train_dataset_dir,
        checkpoint=checkpoint,
        capture_log_dir=output_dir / "task020_capture" / "logs",
        output_dir=output_dir,
        report=validation_report,
        device=str(device),
        knn_k=int(knn_k),
        threshold=float(threshold),
        safe_radius_quantile=float(safe_radius_quantile),
        safe_radius_multiplier=float(safe_radius_multiplier),
    )
    commands.append(
        {
            "command_type": "task020_gat_embedding_capture_validation",
            "description": "Validate GAT embedding kNN/OOD safety shell on task-20 capture logs.",
            "command": validation_command,
        }
    )
    runbook_summary = output_dir / "summary.json"
    analysis_report = output_dir / "audit_ab_analysis_zh.md"
    commands.append(
        {
            "command_type": "audit_ab_result_analysis",
            "description": "Read result CSVs and validation summary after the previous commands finish.",
            "command": _analysis_command(
                runbook_summary=runbook_summary,
                output_dir=output_dir,
                report=analysis_report,
            ),
        }
    )

    all_instances = [item for group in result_pairs for item in group["instances"]]
    checks = {
        "diagnostic_only": True,
        "builder_runs_bpc_or_pricing_false": True,
        "all_selected_instances_exist": all(
            Path(str(item["instance"])).exists() for item in all_instances
        ),
        "has_5_and_10_no_regression_pairs": {5, 10}.issubset(
            {int(pair["task_count"]) for pair in result_pairs}
        ),
        "has_20_roi_capture_pair": any(int(pair["task_count"]) == 20 for pair in result_pairs),
        "capture_commands_enable_only_capture_overrides": all(
            all(override in item["command"] for override in CAPTURE_OVERRIDES)
            for item in commands
            if item["command_type"].endswith("_capture")
        ),
        "baseline_commands_do_not_enable_capture": all(
            not any(override in item["command"] for override in CAPTURE_OVERRIDES)
            for item in commands
            if item["command_type"].endswith("_baseline")
        ),
        "all_solver_commands_use_no_gnn_baseline_overrides": all(
            all(override in item["command"] for override in NO_GNN_BASELINE_OVERRIDES)
            for item in commands
            if item["command_type"].endswith(("_baseline", "_capture"))
        ),
        "commands_do_not_enable_worker_or_certificate": not any(
            _has_forbidden_active_knob(item["command"]) for item in commands
        ),
        "validation_uses_gat_embedding_candidate": (
            "audit_gat_embedding_knn_ood_capture_validation.py" in validation_command
            and str(checkpoint) in validation_command
            and "--knn-k 3" in validation_command
        ),
    }
    summary = {
        "schema_version": "gat_embedding_audit_ab_runbook_v1",
        "status": "gat_embedding_audit_ab_runbook_ready",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "active_worker_ready": False,
        "certificate_ready": False,
        "online_effect_enabled": False,
        "goal_complete": False,
        "train_dataset_dir": str(train_dataset_dir),
        "checkpoint": str(checkpoint),
        "result_pairs": result_pairs,
        "gat_validation_summary": str(validation_summary),
        "commands": commands,
        "candidate_policy": {
            "policy": "gat_embedding_knn_ood_delay_scheduler",
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
        "checks": checks,
        "baseline_overrides": list(NO_GNN_BASELINE_OVERRIDES),
        "all_checks_pass": all(bool(value) for value in checks.values()),
        "next_step": (
            "Run commands in order. The analysis can only clear the pre-online "
            "audit gate; actual 20-task wall-time ROI still requires later "
            "online opt-in integration."
        ),
    }
    runbook_summary.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(report, summary)
    return summary


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GAT Embedding Audit-Only A/B Runbook",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "生成生产化前的 GAT embedding 审计 A/B 命令。该 runbook 不运行 solver，",
        "不启用 worker，不产生 certificate，也不改变 official lower bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "gat_embedding_audit_ab_runbook = current",
        f"status = {summary['status']}",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"active_worker_ready = {str(summary['active_worker_ready']).lower()}",
        f"certificate_ready = {str(summary['certificate_ready']).lower()}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## Result Pairs",
        "",
        "```json",
        json.dumps(summary["result_pairs"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Proof Budget Contract",
        "",
        "```json",
        json.dumps(summary["proof_budget_contract"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Baseline Overrides",
        "",
        "```json",
        json.dumps(summary["baseline_overrides"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Commands",
        "",
    ]
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
            "- 5/10 pair 只验证 capture-only 是否保持官方结果不变；",
            "- 20 pair 只收集 GAT embedding validation 所需的真实日志；",
            "- 该 runbook 不能证明 wall-time ROI，因为还没有 online opt-in effect；",
            "- 任何 true-RC negative 都不能被 GAT/kNN/OOD 永久丢弃。",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--logical-graph-root", type=Path, default=DEFAULT_LOGICAL_GRAPH_ROOT)
    parser.add_argument("--train-dataset-dir", type=Path, default=DEFAULT_TRAIN_DATASET_DIR)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--small-ordinals", nargs="*", type=int, default=[1])
    parser.add_argument("--twenty-ordinals", nargs="*", type=int, default=[1, 5])
    parser.add_argument("--small-max-instances-per-scale", type=int, default=2)
    parser.add_argument("--twenty-max-instances", type=int, default=4)
    parser.add_argument("--small-time-limit", type=float, default=60.0)
    parser.add_argument("--twenty-time-limit", type=float, default=200.0)
    parser.add_argument("--max-workers", type=int, default=1)
    parser.add_argument("--timeout-kill-after", default="30s")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--knn-k", type=int, default=3)
    parser.add_argument("--threshold", type=float, default=0.75)
    parser.add_argument("--safe-radius-quantile", type=float, default=1.0)
    parser.add_argument("--safe-radius-multiplier", type=float, default=1.0)
    args = parser.parse_args(argv)
    summary = build_runbook(
        output_dir=args.output_dir,
        report=args.report,
        logical_graph_root=args.logical_graph_root,
        train_dataset_dir=args.train_dataset_dir,
        checkpoint=args.checkpoint,
        small_ordinals=tuple(args.small_ordinals),
        twenty_ordinals=tuple(args.twenty_ordinals),
        small_max_instances_per_scale=args.small_max_instances_per_scale,
        twenty_max_instances=args.twenty_max_instances,
        small_time_limit=args.small_time_limit,
        twenty_time_limit=args.twenty_time_limit,
        max_workers=args.max_workers,
        timeout_kill_after=args.timeout_kill_after,
        device=args.device,
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
                "command_count": len(summary["commands"]),
                "production_ready": summary["production_ready"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
