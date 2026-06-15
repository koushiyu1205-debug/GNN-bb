#!/usr/bin/env python3
"""Build a pre-online same-run GAT impact audit A/B runbook.

The generated commands are intentionally conservative:

* 5/10/20 baseline commands keep the current mainline learning/GAT config;
* capture commands only add counterfactual replay capture logging;
* the GAT+kNN/OOD command is read-only and uses the same-run batch-impact
  checkpoint produced offline;
* no command enables workers, certificates, official-bound shortcuts, or
  permanent filtering of true-RC negative columns.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import shlex
from typing import Any

from BPC_future.scripts.build_cbf_family_capture_worklist import CAPTURE_OVERRIDES


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_20260615"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260615_bpc_future_gat_same_run_batch_impact_audit_ab_runbook_zh.md"
)
DEFAULT_LOGICAL_GRAPH_ROOT = Path("BPC_future/logical_graph")
DEFAULT_DATASET_DIR = Path("BPC_future/data/gat_same_run_batch_impact/v1")
DEFAULT_CHECKPOINT = Path(
    "BPC_future/results/gat_same_run_batch_impact_training_20260615/"
    "context_aware_same_run_batch_impact_gat.pt"
)
DEFAULT_TRAINING_SUMMARY = Path(
    "BPC_future/results/gat_same_run_batch_impact_training_20260615/summary.json"
)
PYTHON = "/home/kai/miniconda3/envs/ecole/bin/python"

SCALE_CONFIG = {
    5: "BPC_future/configs/moon_trek_5_journey.yaml",
    10: "BPC_future/configs/moon_trek_10_journey.yaml",
    20: "BPC_future/configs/moon_trek_20_smoke.yaml",
}


DEFAULT_FAMILIES = ("sector-wave",)


def _parse_csv_tuple(value: str | tuple[str, ...] | list[str] | None) -> tuple[str, ...]:
    if value is None:
        return DEFAULT_FAMILIES
    if isinstance(value, (tuple, list)):
        items = [str(item).strip() for item in value]
    else:
        items = [item.strip() for item in str(value).split(",")]
    return tuple(item for item in items if item)


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


def _family(path: Path, logical_graph_root: Path, scale: int) -> str:
    try:
        rel = path.relative_to(Path(logical_graph_root) / f"tasks_{int(scale):03d}")
    except ValueError:
        return "unknown"
    return str(rel.parts[0]) if rel.parts else "unknown"


def _list_instances(
    logical_graph_root: Path,
    scale: int,
    *,
    families: tuple[str, ...] = DEFAULT_FAMILIES,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    wanted = {str(family) for family in families}
    scale_root = Path(logical_graph_root) / f"tasks_{int(scale):03d}"
    for path in sorted(scale_root.glob("*/*/*_logical_graph.json")):
        family = _family(path, Path(logical_graph_root), int(scale))
        if wanted and family not in wanted:
            continue
        rows.append(
            {
                "instance": str(path),
                "task_count": int(scale),
                "family": family,
                "region": _region(path),
                "ordinal": _instance_ordinal(path, int(scale)),
            }
        )
    return rows


def _select_instances(
    *,
    logical_graph_root: Path,
    scale: int,
    ordinals: tuple[int, ...],
    max_instances: int,
    families: tuple[str, ...] = DEFAULT_FAMILIES,
) -> list[dict[str, Any]]:
    available = _list_instances(logical_graph_root, int(scale), families=tuple(families))
    wanted = {int(value) for value in ordinals}
    selected = [item for item in available if item.get("ordinal") in wanted]
    if not selected:
        selected = available
    region_order = {"apollo": 0, "tranquillitatis": 1, "unknown": 2}
    selected.sort(
        key=lambda item: (
            int(item.get("ordinal") or 10**9),
            str(item.get("family")),
            region_order.get(str(item.get("region")), 9),
            str(item.get("instance")),
        )
    )
    return selected[: int(max_instances)]


def _command(parts: list[str]) -> str:
    return shlex.join(parts)


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
    if capture_enabled:
        for override in CAPTURE_OVERRIDES:
            parts.extend(["--set", override])
    return _command(parts)


def _audit_command(
    *,
    dataset_dir: Path,
    checkpoint: Path,
    training_summary: Path,
    output_dir: Path,
    report: Path,
    device: str,
    knn_k: int,
    min_delay_recall: float,
    decision_scope: str,
) -> str:
    audit_dir = output_dir / "same_run_gat_knn_ood_audit"
    parts = [
        "PYTHONDONTWRITEBYTECODE=1",
        "PYTHONPATH=.",
        PYTHON,
        "BPC_future/scripts/audit_gat_same_run_batch_impact_knn_ood.py",
        "--dataset-dir",
        str(dataset_dir),
        "--checkpoint",
        str(checkpoint),
        "--training-summary",
        str(training_summary),
        "--output-dir",
        str(audit_dir),
        "--report",
        str(report),
        "--device",
        str(device),
        "--knn-k",
        str(int(knn_k)),
        "--max-neighbor-delay-fraction",
        "0.0",
        "--safe-radius-quantile",
        "1.0",
        "--safe-radius-multiplier",
        "1.0",
        "--min-validation-high-priority",
        "1",
        "--min-delay-recall",
        f"{float(min_delay_recall):.6f}",
        "--decision-scope",
        str(decision_scope),
    ]
    return _command(parts)


def _raw_dataset_command(
    *,
    result_pairs: list[dict[str, Any]],
    output_dir: Path,
    report: Path,
) -> str:
    dataset_dir = Path(output_dir) / "same_run_batch_impact_dataset"
    parts = [
        "PYTHONDONTWRITEBYTECODE=1",
        "PYTHONPATH=.",
        PYTHON,
        "BPC_future/scripts/build_gat_same_run_batch_impact_dataset.py",
        "--output-dir",
        str(dataset_dir),
        "--report",
        str(report),
    ]
    for pair in result_pairs:
        parts.extend(
            [
                "--log-root",
                str(Path(str(pair["capture_csv"])).parent / "logs"),
            ]
        )
    return _command(parts)


def _graph_dataset_command(
    *,
    input_jsonl: Path,
    dataset_dir: Path,
    report: Path,
) -> str:
    parts = [
        "PYTHONDONTWRITEBYTECODE=1",
        "PYTHONPATH=.",
        PYTHON,
        "BPC_future/scripts/build_gat_same_run_batch_impact_graph_dataset.py",
        "--input-jsonl",
        str(input_jsonl),
        "--output-dir",
        str(dataset_dir),
        "--report",
        str(report),
    ]
    return _command(parts)


def _candidate_extract_command(
    *,
    decision_records: Path,
    output_dir: Path,
    report: Path,
    max_candidates: int,
    delay_queue_only: bool = False,
) -> str:
    parts = [
        "PYTHONDONTWRITEBYTECODE=1",
        "PYTHONPATH=.",
        PYTHON,
        "BPC_future/scripts/build_gat_same_run_target_priority_candidates.py",
        "--decision-records",
        str(decision_records),
        "--output-dir",
        str(output_dir),
        "--report",
        str(report),
        "--max-candidates",
        str(int(max_candidates)),
    ]
    if delay_queue_only:
        parts.append("--delay-queue-only")
    return _command(parts)


def _has_forbidden_active_knob(command: str) -> bool:
    lowered = command.lower()
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
        "journey_sharded_pulse_hidden_negative_worker_enabled=true",
    ]
    return any(token in lowered for token in forbidden)


def _disables_mainline_learning(command: str) -> bool:
    lowered = command.lower()
    disabled_tokens = [
        "journey_learning_enabled=false",
        "journey_learning_required=false",
        "journey_learning_pricing_enabled=false",
        "journey_learning_prewarm_enabled=false",
    ]
    return any(token in lowered for token in disabled_tokens)


def build_runbook(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    logical_graph_root: Path = DEFAULT_LOGICAL_GRAPH_ROOT,
    dataset_dir: Path = DEFAULT_DATASET_DIR,
    checkpoint: Path = DEFAULT_CHECKPOINT,
    training_summary: Path = DEFAULT_TRAINING_SUMMARY,
    small_ordinals: tuple[int, ...] = (1,),
    twenty_ordinals: tuple[int, ...] = (1, 9),
    small_families: tuple[str, ...] = DEFAULT_FAMILIES,
    twenty_families: tuple[str, ...] = DEFAULT_FAMILIES,
    small_max_instances_per_scale: int = 2,
    twenty_max_instances: int = 4,
    small_time_limit: float = 60.0,
    twenty_time_limit: float = 200.0,
    max_workers: int = 1,
    timeout_kill_after: str = "30s",
    device: str = "cpu",
    knn_k: int = 3,
    min_delay_recall: float = 0.5,
    decision_scope: str = "validation",
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    selected_by_scale = {
        5: _select_instances(
            logical_graph_root=Path(logical_graph_root),
            scale=5,
            ordinals=tuple(int(value) for value in small_ordinals),
            max_instances=int(small_max_instances_per_scale),
            families=tuple(small_families),
        ),
        10: _select_instances(
            logical_graph_root=Path(logical_graph_root),
            scale=10,
            ordinals=tuple(int(value) for value in small_ordinals),
            max_instances=int(small_max_instances_per_scale),
            families=tuple(small_families),
        ),
        20: _select_instances(
            logical_graph_root=Path(logical_graph_root),
            scale=20,
            ordinals=tuple(int(value) for value in twenty_ordinals),
            max_instances=int(twenty_max_instances),
            families=tuple(twenty_families),
        ),
    }
    commands: list[dict[str, str]] = []
    result_pairs: list[dict[str, Any]] = []
    for scale in (5, 10, 20):
        time_limit = small_time_limit if scale in (5, 10) else twenty_time_limit
        for profile, capture_enabled in (("baseline", False), ("capture", True)):
            command = _batch_command(
                instances=selected_by_scale[scale],
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
                        "Run current mainline solver with existing learning/GAT config."
                        if not capture_enabled
                        else "Run current mainline solver with capture logging only."
                    ),
                    "command": command,
                }
            )
        result_pairs.append(
            {
                "task_count": int(scale),
                "baseline_csv": str(output_dir / f"task{scale:03d}_baseline" / "results.csv"),
                "capture_csv": str(output_dir / f"task{scale:03d}_capture" / "results.csv"),
                "instance_count": len(selected_by_scale[scale]),
                "instances": selected_by_scale[scale],
            }
        )

    audit_report = output_dir / "same_run_gat_knn_ood_audit_zh.md"
    audit_summary = output_dir / "same_run_gat_knn_ood_audit" / "summary.json"
    raw_dataset_dir = output_dir / "same_run_batch_impact_dataset"
    raw_dataset_report = output_dir / "same_run_batch_impact_dataset_zh.md"
    graph_dataset_report = output_dir / "same_run_batch_impact_graph_dataset_zh.md"
    decision_records = output_dir / "same_run_gat_knn_ood_audit" / "decision_records.jsonl"
    high_candidate_dir = output_dir / "target_priority_candidates"
    delay_candidate_dir = output_dir / "delay_queue_target_candidates"
    raw_dataset_build_command = _raw_dataset_command(
        result_pairs=result_pairs,
        output_dir=output_dir,
        report=raw_dataset_report,
    )
    graph_dataset_build_command = _graph_dataset_command(
        input_jsonl=raw_dataset_dir / "same_run_batch_impact_rows.jsonl",
        dataset_dir=Path(dataset_dir),
        report=graph_dataset_report,
    )
    audit_command = _audit_command(
        dataset_dir=Path(dataset_dir),
        checkpoint=Path(checkpoint),
        training_summary=Path(training_summary),
        output_dir=output_dir,
        report=audit_report,
        device=str(device),
        knn_k=int(knn_k),
        min_delay_recall=float(min_delay_recall),
        decision_scope=str(decision_scope),
    )
    commands.append(
        {
            "command_type": "same_run_batch_impact_rows_build",
            "description": "Build same-run raw ROI rows from capture logs after capture commands finish.",
            "command": raw_dataset_build_command,
        }
    )
    commands.append(
        {
            "command_type": "same_run_batch_impact_graph_dataset_build",
            "description": "Build graph samples for the same-run GAT checkpoint from raw ROI rows.",
            "command": graph_dataset_build_command,
        }
    )
    commands.append(
        {
            "command_type": "same_run_gat_knn_ood_offline_audit",
            "description": "Read offline same-run GAT checkpoint and validate kNN/OOD safety shell.",
            "command": audit_command,
        }
    )
    commands.append(
        {
            "command_type": "target_priority_candidate_extract",
            "description": "Extract HIGH_PRIORITY target-intervention candidates from audit decisions.",
            "command": _candidate_extract_command(
                decision_records=decision_records,
                output_dir=high_candidate_dir,
                report=output_dir / "target_priority_candidates_zh.md",
                max_candidates=12,
                delay_queue_only=False,
            ),
        }
    )
    commands.append(
        {
            "command_type": "delay_queue_candidate_extract",
            "description": "Extract DELAY_QUEUE target-intervention candidates for negative-label balance.",
            "command": _candidate_extract_command(
                decision_records=decision_records,
                output_dir=delay_candidate_dir,
                report=output_dir / "delay_queue_target_candidates_zh.md",
                max_candidates=12,
                delay_queue_only=True,
            ),
        }
    )

    all_instances = [item for values in selected_by_scale.values() for item in values]
    selected_families_by_scale = {
        str(scale): sorted({str(item.get("family")) for item in values})
        for scale, values in selected_by_scale.items()
    }
    selected_family_region_counts = {
        str(scale): {
            f"{item.get('family')}|{item.get('region')}": sum(
                1
                for other in values
                if other.get("family") == item.get("family")
                and other.get("region") == item.get("region")
            )
            for item in values
        }
        for scale, values in selected_by_scale.items()
    }
    checks = {
        "diagnostic_only": True,
        "builder_runs_bpc_or_pricing_false": True,
        "mainline_learning_kept": not any(
            _disables_mainline_learning(item["command"])
            for item in commands
            if item["command_type"].startswith("task")
        ),
        "all_selected_instances_exist": all(
            Path(str(item["instance"])).exists() for item in all_instances
        ),
        "has_5_and_10_no_regression_pairs": {5, 10}.issubset(
            {int(pair["task_count"]) for pair in result_pairs}
        ),
        "has_20_capture_pair": any(int(pair["task_count"]) == 20 for pair in result_pairs),
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
        "commands_do_not_enable_worker_or_certificate": not any(
            _has_forbidden_active_knob(item["command"]) for item in commands
        ),
        "audit_uses_same_run_checkpoint": (
            "audit_gat_same_run_batch_impact_knn_ood.py" in audit_command
            and str(checkpoint) in audit_command
            and str(training_summary) in audit_command
        ),
        "post_capture_pipeline_present": all(
            any(item["command_type"] == command_type for item in commands)
            for command_type in (
                "same_run_batch_impact_rows_build",
                "same_run_batch_impact_graph_dataset_build",
                "same_run_gat_knn_ood_offline_audit",
                "target_priority_candidate_extract",
                "delay_queue_candidate_extract",
            )
        ),
        "candidate_extract_uses_audit_decision_records": all(
            str(decision_records) in item["command"]
            for item in commands
            if item["command_type"].endswith("_candidate_extract")
        ),
        "memory_guard_single_worker": int(max_workers) == 1,
        "selected_twenty_families_available": set(str(family) for family in twenty_families).issubset(
            set(selected_families_by_scale.get("20", []))
        ),
    }
    summary = {
        "schema_version": "gat_same_run_batch_impact_audit_ab_runbook_v1",
        "status": "gat_same_run_batch_impact_audit_ab_runbook_ready",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "active_worker_ready": False,
        "certificate_ready": False,
        "online_effect_enabled": False,
        "default_enabled": False,
        "goal_complete": False,
        "dataset_dir": str(dataset_dir),
        "raw_dataset_dir": str(raw_dataset_dir),
        "checkpoint": str(checkpoint),
        "training_summary": str(training_summary),
        "gat_validation_summary": str(audit_summary),
        "audit_decision_scope": str(decision_scope),
        "decision_records": str(decision_records),
        "result_pairs": result_pairs,
        "selected_families_by_scale": selected_families_by_scale,
        "selected_family_region_counts": selected_family_region_counts,
        "requested_small_families": list(small_families),
        "requested_twenty_families": list(twenty_families),
        "commands": commands,
        "candidate_policy": {
            "policy": "same_run_gat_embedding_knn_ood_delay_scheduler",
            "safe_negative_decision": "HIGH_PRIORITY",
            "unsafe_negative_decision": "DELAY_QUEUE",
            "nonnegative_decision": "REJECT_NONNEGATIVE_ONLY",
            "negative_columns_must_remain_eventually_reachable": True,
            "permanent_negative_filter_allowed": False,
            "certificate_effect": False,
            "official_bound_effect": False,
            "active_worker_effect": False,
        },
        "productionization_standard": {
            "task5_10_no_regression_required": True,
            "task20_wall_time_roi_required": True,
            "default_enable_allowed": False,
            "certificate_effect_allowed": False,
            "negative_column_discard_allowed": False,
            "small_sample_training_requires_audit_only": True,
        },
        "checks": checks,
        "all_checks_pass": all(bool(value) for value in checks.values()),
        "next_step": (
            "Run task005/task010 baseline and capture pairs first.  If official "
            "results match, run task020 capture and the offline same-run GAT audit."
        ),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(Path(report), summary)
    return summary


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GAT Same-Run Batch Impact Audit-Only A/B Runbook",
        "",
        "日期：2026-06-15",
        "",
        "## 目的",
        "",
        "生成 same-run GAT+kNN/OOD 进入 online 前的 audit-only A/B 命令。",
        "该 runbook 本身不运行求解器；命令默认单 worker，保留当前 mainline",
        "learning/GAT 配置，只对 capture profile 打开日志。",
        "",
        "## 机器字段",
        "",
        "```text",
        "gat_same_run_batch_impact_audit_ab_runbook = current",
        f"status = {summary['status']}",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"active_worker_ready = {str(summary['active_worker_ready']).lower()}",
        f"certificate_ready = {str(summary['certificate_ready']).lower()}",
        f"default_enabled = {str(summary['default_enabled']).lower()}",
        f"audit_decision_scope = {summary['audit_decision_scope']}",
        f"requested_small_families = {summary['requested_small_families']}",
        f"requested_twenty_families = {summary['requested_twenty_families']}",
        f"selected_families_by_scale = {summary['selected_families_by_scale']}",
        f"selected_family_region_counts = {summary['selected_family_region_counts']}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## Candidate Policy",
        "",
        "```json",
        json.dumps(summary["candidate_policy"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Productionization Standard",
        "",
        "```json",
        json.dumps(summary["productionization_standard"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Result Pairs",
        "",
        "```json",
        json.dumps(summary["result_pairs"], ensure_ascii=False, indent=2, sort_keys=True),
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
            "- 5/10 baseline 与 capture 都保留当前 mainline GAT/learning；",
            "- capture-only 不允许改变 official result；",
            "- same-run GAT+kNN/OOD 只做离线审计，不接 worker、不接 certificate；",
            "- true-RC negative 只能 HIGH_PRIORITY 或 DELAY_QUEUE，不能永久丢弃；",
            "- 该 runbook 不能证明 wall-time ROI，真正 ROI 要等 online opt-in A/B。",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--logical-graph-root", type=Path, default=DEFAULT_LOGICAL_GRAPH_ROOT)
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--training-summary", type=Path, default=DEFAULT_TRAINING_SUMMARY)
    parser.add_argument("--small-ordinals", nargs="*", type=int, default=[1])
    parser.add_argument("--twenty-ordinals", nargs="*", type=int, default=[1, 9])
    parser.add_argument("--small-families", nargs="*", default=list(DEFAULT_FAMILIES))
    parser.add_argument("--twenty-families", nargs="*", default=list(DEFAULT_FAMILIES))
    parser.add_argument("--small-max-instances-per-scale", type=int, default=2)
    parser.add_argument("--twenty-max-instances", type=int, default=4)
    parser.add_argument("--small-time-limit", type=float, default=60.0)
    parser.add_argument("--twenty-time-limit", type=float, default=200.0)
    parser.add_argument("--max-workers", type=int, default=1)
    parser.add_argument("--timeout-kill-after", default="30s")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--knn-k", type=int, default=3)
    parser.add_argument("--min-delay-recall", type=float, default=0.5)
    parser.add_argument("--decision-scope", choices=("validation", "all"), default="validation")
    args = parser.parse_args(argv)
    summary = build_runbook(
        output_dir=args.output_dir,
        report=args.report,
        logical_graph_root=args.logical_graph_root,
        dataset_dir=args.dataset_dir,
        checkpoint=args.checkpoint,
        training_summary=args.training_summary,
        small_ordinals=tuple(args.small_ordinals),
        twenty_ordinals=tuple(args.twenty_ordinals),
        small_families=_parse_csv_tuple(args.small_families),
        twenty_families=_parse_csv_tuple(args.twenty_families),
        small_max_instances_per_scale=args.small_max_instances_per_scale,
        twenty_max_instances=args.twenty_max_instances,
        small_time_limit=args.small_time_limit,
        twenty_time_limit=args.twenty_time_limit,
        max_workers=args.max_workers,
        timeout_kill_after=args.timeout_kill_after,
        device=args.device,
        knn_k=args.knn_k,
        min_delay_recall=args.min_delay_recall,
        decision_scope=args.decision_scope,
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
