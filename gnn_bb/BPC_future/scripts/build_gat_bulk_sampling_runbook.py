#!/usr/bin/env python3
"""Build a memory-safe bulk GAT sampling runbook.

This script does not run BPC, pricing, workers, or certificates.  It emits a
runbook for collecting many same-run batch-impact labels cheaply:

* task-5/10 baseline+capture sentinel pairs protect no-regression checks;
* task-20 bulk waves are capture-only, because same-run labels only need
  capture logs and the next RMP state from the same run;
* offline graph build, GAT training, kNN/OOD audit, and candidate extraction
  commands are appended after the capture waves.

The generated plan is explicitly diagnostic/audit-only.  GAT output is a
trajectory-impact scheduler signal, not a pricing oracle or certificate source.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
from typing import Any, Iterable

from BPC_future.scripts.build_gat_same_run_batch_impact_audit_ab_runbook import (
    CAPTURE_OVERRIDES,
    DEFAULT_LOGICAL_GRAPH_ROOT,
    PYTHON,
    _audit_command,
    _candidate_extract_command,
    _graph_dataset_command,
    _list_instances,
    _raw_dataset_command,
)


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/gat_bulk_sampling_runbook_20260615")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260615_bpc_future_gat_bulk_sampling_runbook_zh.md"
)
BULK_SCALE_CONFIG = {
    5: "BPC_future/configs/moon_trek_5_journey.yaml",
    10: "BPC_future/configs/moon_trek_10_journey.yaml",
    20: "BPC_future/configs/moon_trek_20_smoke.yaml",
    30: "BPC_future/configs/moon_trek_20_smoke.yaml",
    50: "BPC_future/configs/moon_trek_20_smoke.yaml",
    100: "BPC_future/configs/moon_trek_20_smoke.yaml",
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--logical-graph-root", type=Path, default=DEFAULT_LOGICAL_GRAPH_ROOT)
    parser.add_argument("--existing-row-jsonl", type=Path, action="append", default=[])
    parser.add_argument("--families", nargs="*", default=["random-wave", "greedy-anchor", "sector-wave"])
    parser.add_argument("--bulk-scales", nargs="*", type=int, default=[20])
    parser.add_argument("--twenty-ordinals", nargs="*", type=int, default=list(range(1, 11)))
    parser.add_argument("--small-ordinals", nargs="*", type=int, default=[1])
    parser.add_argument("--target-total-samples", type=int, default=300)
    parser.add_argument("--target-positive-samples", type=int, default=100)
    parser.add_argument("--expected-rows-per-instance", type=float, default=7.0)
    parser.add_argument("--expected-positive-per-instance", type=float, default=2.5)
    parser.add_argument("--max-new-instances", type=int, default=24)
    parser.add_argument("--instances-per-wave", type=int, default=4)
    parser.add_argument("--small-time-limit", type=float, default=60.0)
    parser.add_argument("--twenty-time-limit", type=float, default=200.0)
    parser.add_argument("--max-workers", type=int, default=1)
    parser.add_argument("--timeout-kill-after", default="30s")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--knn-k", type=int, default=3)
    parser.add_argument("--min-delay-recall", type=float, default=0.5)
    parser.add_argument("--decision-scope", choices=("validation", "all"), default="all")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    summary = build_bulk_sampling_runbook(
        output_dir=args.output_dir,
        report=args.report,
        logical_graph_root=args.logical_graph_root,
        existing_row_jsonl=tuple(args.existing_row_jsonl or ()),
        families=tuple(args.families),
        bulk_scales=tuple(args.bulk_scales),
        twenty_ordinals=tuple(args.twenty_ordinals),
        small_ordinals=tuple(args.small_ordinals),
        target_total_samples=int(args.target_total_samples),
        target_positive_samples=int(args.target_positive_samples),
        expected_rows_per_instance=float(args.expected_rows_per_instance),
        expected_positive_per_instance=float(args.expected_positive_per_instance),
        max_new_instances=int(args.max_new_instances),
        instances_per_wave=int(args.instances_per_wave),
        small_time_limit=float(args.small_time_limit),
        twenty_time_limit=float(args.twenty_time_limit),
        max_workers=int(args.max_workers),
        timeout_kill_after=str(args.timeout_kill_after),
        device=str(args.device),
        epochs=int(args.epochs),
        knn_k=int(args.knn_k),
        min_delay_recall=float(args.min_delay_recall),
        decision_scope=str(args.decision_scope),
    )
    print(
        json.dumps(
            {
                "summary": str(Path(args.output_dir) / "summary.json"),
                "report": str(args.report),
                "command_count": len(summary["commands"]),
                "selected_new_instance_count": summary["selected_new_instance_count"],
                "estimated_total_after": summary["estimated_total_after"],
                "estimated_positive_after": summary["estimated_positive_after"],
                "all_checks_pass": summary["all_checks_pass"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if summary["all_checks_pass"] else 1


def build_bulk_sampling_runbook(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    logical_graph_root: Path = DEFAULT_LOGICAL_GRAPH_ROOT,
    existing_row_jsonl: Iterable[Path] = tuple(),
    families: tuple[str, ...] = ("random-wave", "greedy-anchor", "sector-wave"),
    bulk_scales: tuple[int, ...] = (20,),
    twenty_ordinals: tuple[int, ...] = tuple(range(1, 11)),
    small_ordinals: tuple[int, ...] = (1,),
    target_total_samples: int = 300,
    target_positive_samples: int = 100,
    expected_rows_per_instance: float = 7.0,
    expected_positive_per_instance: float = 2.5,
    max_new_instances: int = 24,
    instances_per_wave: int = 4,
    small_time_limit: float = 60.0,
    twenty_time_limit: float = 200.0,
    max_workers: int = 1,
    timeout_kill_after: str = "30s",
    device: str = "cpu",
    epochs: int = 30,
    knn_k: int = 3,
    min_delay_recall: float = 0.5,
    decision_scope: str = "all",
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    existing_rows = _read_existing_rows(tuple(Path(path) for path in existing_row_jsonl))
    existing_counts = _existing_counts(existing_rows)
    sampled_instances = {
        str(row.get("instance_path") or row.get("instance") or "")
        for row in existing_rows
        if str(row.get("instance_path") or row.get("instance") or "")
    }
    total_gap = max(0, int(target_total_samples) - int(existing_counts["row_count"]))
    positive_gap = max(0, int(target_positive_samples) - int(existing_counts["positive_count"]))
    needed_by_total = _ceil_div(total_gap, max(float(expected_rows_per_instance), 1.0e-9))
    needed_by_positive = _ceil_div(
        positive_gap, max(float(expected_positive_per_instance), 1.0e-9)
    )
    needed_instances = min(
        int(max_new_instances),
        max(0, int(max(needed_by_total, needed_by_positive))),
    )
    selected_bulk = _select_bulk_instances(
        logical_graph_root=Path(logical_graph_root),
        scales=tuple(int(value) for value in bulk_scales),
        families=tuple(str(family) for family in families),
        ordinals=tuple(int(value) for value in twenty_ordinals),
        sampled_instances=sampled_instances,
        limit=needed_instances,
        existing_rows=existing_rows,
    )
    waves = _chunk(selected_bulk, max(1, int(instances_per_wave)))
    selected_small = {
        scale: _select_small_sentinel(
            logical_graph_root=Path(logical_graph_root),
            scale=scale,
            ordinals=tuple(int(value) for value in small_ordinals),
        )
        for scale in (5, 10)
    }

    commands: list[dict[str, Any]] = []
    result_pairs: list[dict[str, Any]] = []
    for scale in (5, 10):
        for profile, capture_enabled in (("baseline", False), ("capture", True)):
            commands.append(
                {
                    "command_type": f"task{scale:03d}_{profile}_sentinel",
                    "description": (
                        "5/10 no-regression sentinel with current mainline config."
                        if not capture_enabled
                        else "5/10 capture sentinel; capture logging only, no online effect."
                    ),
                    "command": _bulk_batch_command(
                        instances=selected_small[scale],
                        scale=scale,
                        profile=f"{profile}_sentinel",
                        output_dir=output_dir,
                        time_limit=float(small_time_limit),
                        max_workers=int(max_workers),
                        timeout_kill_after=str(timeout_kill_after),
                        capture_enabled=bool(capture_enabled),
                    ),
                }
            )
        result_pairs.append(
            {
                "task_count": int(scale),
                "baseline_csv": str(output_dir / f"task{scale:03d}_baseline_sentinel" / "results.csv"),
                "capture_csv": str(output_dir / f"task{scale:03d}_capture_sentinel" / "results.csv"),
                "instances": selected_small[scale],
                "instance_count": len(selected_small[scale]),
                "sentinel_only": True,
            }
        )

    bulk_capture_pairs: list[dict[str, Any]] = []
    for wave_idx, wave in enumerate(waves, start=1):
        wave_scales = sorted({int(item["task_count"]) for item in wave})
        wave_scale_label = "_".join(f"{scale:03d}" for scale in wave_scales)
        profile = f"bulk_capture_wave{wave_idx:02d}"
        command = _bulk_batch_command(
            instances=wave,
            scale=wave_scales[0],
            profile=profile,
            output_dir=output_dir,
            time_limit=float(twenty_time_limit),
            max_workers=int(max_workers),
            timeout_kill_after=str(timeout_kill_after),
            capture_enabled=True,
        )
        commands.append(
            {
                "command_type": f"task{wave_scale_label}_{profile}",
                "description": (
                    "Bulk same-run label capture only.  No baseline pair, "
                    "worker, certificate, or official-bound effect."
                ),
                "command": command,
            }
        )
        bulk_capture_pairs.append(
            {
                "task_count": int(wave_scales[0]),
                "task_counts": wave_scales,
                "capture_csv": str(output_dir / f"task{int(wave_scales[0]):03d}_{profile}" / "results.csv"),
                "instances": wave,
                "instance_count": len(wave),
                "bulk_capture_only": True,
                "wave": wave_idx,
            }
        )

    raw_dataset_dir = output_dir / "same_run_batch_impact_dataset"
    graph_dataset_dir = output_dir / "graph_dataset"
    training_dir = output_dir / "same_run_batch_impact_training"
    checkpoint = training_dir / "context_aware_bulk_sampling_gat.pt"
    training_summary = training_dir / "summary.json"
    audit_dir = output_dir / "same_run_gat_knn_ood_audit"
    decision_records = audit_dir / "decision_records.jsonl"
    dataset_pairs = [
        {"capture_csv": str(output_dir / f"task{scale:03d}_capture_sentinel" / "results.csv")}
        for scale in (5, 10)
    ] + bulk_capture_pairs
    commands.extend(
        [
            {
                "command_type": "same_run_batch_impact_rows_build",
                "description": "Build same-run raw training rows from all capture log roots.",
                "command": _raw_dataset_command(
                    result_pairs=dataset_pairs,
                    output_dir=output_dir,
                    report=output_dir / "same_run_batch_impact_dataset_zh.md",
                ),
            },
            {
                "command_type": "same_run_batch_impact_graph_dataset_build",
                "description": "Build local graph dataset; do not overwrite global dataset.",
                "command": _graph_dataset_command(
                    input_jsonl=raw_dataset_dir / "same_run_batch_impact_rows.jsonl",
                    dataset_dir=graph_dataset_dir,
                    report=output_dir / "same_run_batch_impact_graph_dataset_zh.md",
                ),
            },
            {
                "command_type": "same_run_gat_train_offline",
                "description": (
                    "Train audit-only ContextAwareColumnSelector on the local bulk dataset. "
                    "This checkpoint remains non-production until safety audits pass."
                ),
                "command": _train_command(
                    dataset_dir=graph_dataset_dir,
                    checkpoint=checkpoint,
                    metrics=training_summary,
                    device=device,
                    epochs=int(epochs),
                ),
            },
            {
                "command_type": "same_run_gat_knn_ood_offline_audit",
                "description": "Audit the local checkpoint with kNN/OOD safety shell.",
                "command": _audit_command(
                    dataset_dir=graph_dataset_dir,
                    checkpoint=checkpoint,
                    training_summary=training_summary,
                    output_dir=output_dir,
                    report=output_dir / "same_run_gat_knn_ood_audit_zh.md",
                    device=device,
                    knn_k=int(knn_k),
                    min_delay_recall=float(min_delay_recall),
                    decision_scope=str(decision_scope),
                ),
            },
            {
                "command_type": "target_priority_candidate_extract",
                "description": "Extract HIGH_PRIORITY candidates for later small top-K worker A/B.",
                "command": _candidate_extract_command(
                    decision_records=decision_records,
                    output_dir=output_dir / "target_priority_candidates",
                    report=output_dir / "target_priority_candidates_zh.md",
                    max_candidates=24,
                    delay_queue_only=False,
                ),
            },
            {
                "command_type": "delay_queue_candidate_extract",
                "description": "Extract DELAY_QUEUE candidates for boundary/negative balance sampling.",
                "command": _candidate_extract_command(
                    decision_records=decision_records,
                    output_dir=output_dir / "delay_queue_target_candidates",
                    report=output_dir / "delay_queue_target_candidates_zh.md",
                    max_candidates=24,
                    delay_queue_only=True,
                ),
            },
        ]
    )

    estimated_new_rows = int(round(len(selected_bulk) * float(expected_rows_per_instance)))
    estimated_new_positive = int(
        round(len(selected_bulk) * float(expected_positive_per_instance))
    )
    checks = {
        "diagnostic_only": True,
        "runs_bpc_or_pricing_false": True,
        "no_certificate_effect": True,
        "no_official_bound_effect": True,
        "active_worker_effect_false": True,
        "default_enabled_false": True,
        "memory_guard_parallel_workers_bounded": 1 <= int(max_workers) <= 4,
        "has_small_no_regression_sentinels": all(selected_small.values()),
        "bulk_is_capture_only": all(
            "_bulk_capture_wave" in item["command_type"]
            and all(override in item["command"] for override in CAPTURE_OVERRIDES)
            for item in commands
            if "_bulk_capture_wave" in item["command_type"]
        ),
        "no_bulk_baseline_commands": not any(
            "_baseline" in item["command_type"]
            for item in commands
            if "_bulk_capture_wave" in item["command_type"]
        ),
        "selected_instances_not_previously_sampled": all(
            str(item["instance"]) not in sampled_instances for item in selected_bulk
        ),
        "post_capture_pipeline_present": all(
            any(item["command_type"] == command_type for item in commands)
            for command_type in (
                "same_run_batch_impact_rows_build",
                "same_run_batch_impact_graph_dataset_build",
                "same_run_gat_train_offline",
                "same_run_gat_knn_ood_offline_audit",
                "target_priority_candidate_extract",
                "delay_queue_candidate_extract",
            )
        ),
    }
    summary = {
        "schema_version": "gat_bulk_sampling_runbook_v1",
        "status": "gat_bulk_sampling_runbook_ready",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "active_worker_ready": False,
        "certificate_ready": False,
        "official_bound_effect": False,
        "default_enabled": False,
        "goal_complete": False,
        "target_total_samples": int(target_total_samples),
        "target_positive_samples": int(target_positive_samples),
        "existing_row_count": int(existing_counts["row_count"]),
        "existing_positive_count": int(existing_counts["positive_count"]),
        "existing_negative_count": int(existing_counts["negative_count"]),
        "total_gap_before": int(total_gap),
        "positive_gap_before": int(positive_gap),
        "expected_rows_per_instance": float(expected_rows_per_instance),
        "expected_positive_per_instance": float(expected_positive_per_instance),
        "selected_new_instance_count": len(selected_bulk),
        "selected_wave_count": len(waves),
        "estimated_new_rows": int(estimated_new_rows),
        "estimated_new_positive": int(estimated_new_positive),
        "estimated_total_after": int(existing_counts["row_count"]) + estimated_new_rows,
        "estimated_positive_after": int(existing_counts["positive_count"]) + estimated_new_positive,
        "families": list(families),
        "bulk_scales": [int(value) for value in bulk_scales],
        "twenty_ordinals": [int(value) for value in twenty_ordinals],
        "selected_bulk_instances": selected_bulk,
        "selected_twenty_instances": selected_bulk,
        "selected_small_sentinels": selected_small,
        "existing_label_counts_by_family_region": existing_counts["by_family_region"],
        "bulk_sampling_policy": {
            "cheap_sampling": "multi_scale_capture_only",
            "expensive_worker_ab": "top_k_after_gat_knn_ood_only",
            "max_workers": int(max_workers),
            "memory_guard": "bounded_parallel_capture_workers_le_4",
            "gat_role": "embedding_and_trajectory_impact_representation",
            "knn_ood_role": "safety_shell",
            "high_priority": "priority_only_not_certificate",
            "delay_queue": "delayed_negative_not_discarded",
            "permanent_negative_filter_allowed": False,
        },
        "commands": commands,
        "checks": checks,
        "all_checks_pass": all(bool(value) for value in checks.values()),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(Path(report), summary)
    return summary


def _ceil_div(numerator: int, denominator: float) -> int:
    if numerator <= 0:
        return 0
    return int(math.ceil(float(numerator) / float(denominator)))


def _read_existing_rows(paths: tuple[Path, ...]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(path)
        with path.open(encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                text = line.strip()
                if text:
                    rows.append(json.loads(text))
    return rows


def _existing_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    positive = 0
    by_family_region: dict[str, dict[str, int]] = {}
    for row in rows:
        if _row_is_positive(row):
            positive += 1
        family, region = _family_region_from_row(row)
        key = f"{family}|{region}"
        cell = by_family_region.setdefault(
            key, {"row_count": 0, "positive_count": 0, "negative_count": 0}
        )
        cell["row_count"] += 1
        if _row_is_positive(row):
            cell["positive_count"] += 1
        else:
            cell["negative_count"] += 1
    return {
        "row_count": len(rows),
        "positive_count": positive,
        "negative_count": len(rows) - positive,
        "by_family_region": dict(sorted(by_family_region.items())),
    }


def _row_is_positive(row: dict[str, Any]) -> bool:
    for key in ("label_positive_trajectory_roi", "label_worker_roi_positive"):
        if row.get(key) is not None:
            return bool(int(row.get(key) or 0))
    roi_class = str(row.get("roi_class") or "")
    if roi_class.startswith("positive_"):
        return True
    if row.get("label_objective_improved") is not None:
        return bool(int(row.get("label_objective_improved") or 0))
    return False


def _family_region_from_row(row: dict[str, Any]) -> tuple[str, str]:
    text = str(row.get("instance_path") or row.get("instance") or "")
    parts = Path(text).parts
    for idx, part in enumerate(parts):
        if part.startswith("tasks_") and idx + 2 < len(parts):
            return str(parts[idx + 1]), str(parts[idx + 2])
    return "unknown", str(row.get("instance_region") or "unknown")


def _select_small_sentinel(
    *, logical_graph_root: Path, scale: int, ordinals: tuple[int, ...]
) -> list[dict[str, Any]]:
    available = _list_instances(
        Path(logical_graph_root),
        int(scale),
        families=("random-wave", "greedy-anchor", "sector-wave"),
    )
    wanted = {int(value) for value in ordinals}
    selected = [item for item in available if item.get("ordinal") in wanted]
    selected.sort(key=lambda item: (str(item.get("region")), str(item.get("family"))))
    # One Apollo-like and one Tranq-like sentinel is enough for capture no-regression.
    result: list[dict[str, Any]] = []
    seen_region: set[str] = set()
    for item in selected or available:
        region = str(item.get("region"))
        if region in seen_region:
            continue
        result.append(item)
        seen_region.add(region)
        if len(result) >= 2:
            break
    return result


def _select_bulk_instances(
    *,
    logical_graph_root: Path,
    scales: tuple[int, ...],
    families: tuple[str, ...],
    ordinals: tuple[int, ...],
    sampled_instances: set[str],
    limit: int,
    existing_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if limit <= 0:
        return []
    available: list[dict[str, Any]] = []
    for scale in scales:
        for item in _list_instances(Path(logical_graph_root), int(scale), families=tuple(families)):
            enriched = dict(item)
            enriched["task_count"] = int(scale)
            available.append(enriched)
    wanted_ordinals = {int(value) for value in ordinals}
    candidates = [
        item
        for item in available
        if item.get("ordinal") in wanted_ordinals
        and str(item.get("instance")) not in sampled_instances
    ]
    cell_counts = _existing_counts(existing_rows)["by_family_region"]

    def score(item: dict[str, Any]) -> tuple[Any, ...]:
        cell = f"{item.get('family')}|{item.get('region')}"
        stats = cell_counts.get(cell, {})
        positive = int(stats.get("positive_count", 0))
        rows = int(stats.get("row_count", 0))
        family_priority = {"random-wave": 0, "greedy-anchor": 1, "sector-wave": 2}
        region_priority = {
            "apollo15_20km": 0,
            "tranquillitatis_balmer_like_20km": 1,
        }
        return (
            positive,
            rows,
            int(item.get("task_count") or 10**9),
            family_priority.get(str(item.get("family")), 9),
            int(item.get("ordinal") or 10**9),
            region_priority.get(str(item.get("region")), 9),
            str(item.get("instance")),
        )

    candidates.sort(key=score)
    by_scale: dict[int, list[dict[str, Any]]] = {}
    for item in candidates:
        by_scale.setdefault(int(item.get("task_count") or 0), []).append(item)
    selected: list[dict[str, Any]] = []
    scale_order = sorted(by_scale)
    while len(selected) < int(limit) and any(by_scale.values()):
        for scale in scale_order:
            if len(selected) >= int(limit):
                break
            bucket = by_scale.get(scale) or []
            if bucket:
                selected.append(bucket.pop(0))
    return selected


def _chunk(items: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [items[index : index + size] for index in range(0, len(items), int(size))]


def _train_command(
    *,
    dataset_dir: Path,
    checkpoint: Path,
    metrics: Path,
    device: str,
    epochs: int,
) -> str:
    parts = [
        "PYTHONDONTWRITEBYTECODE=1",
        "PYTHONPATH=.",
        PYTHON,
        "BPC_future/scripts/train_gnn_column_selector.py",
        "--dataset-dir",
        str(dataset_dir),
        "--checkpoint-out",
        str(checkpoint),
        "--metrics-out",
        str(metrics),
        "--device",
        str(device),
        "--epochs",
        str(int(epochs)),
    ]
    import shlex

    return shlex.join(parts)


def _bulk_batch_command(
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
    import shlex

    if int(scale) not in BULK_SCALE_CONFIG:
        raise ValueError(f"unsupported bulk sampling scale: {scale}")
    run_dir = output_dir / f"task{int(scale):03d}_{profile}"
    parts = [
        "PYTHONDONTWRITEBYTECODE=1",
        "PYTHONPATH=.",
        PYTHON,
        "BPC_future/scripts/run_bpc_future_external_timeout_batch.py",
        "--config",
        BULK_SCALE_CONFIG[int(scale)],
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
    return shlex.join(parts)


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GAT Bulk Sampling Runbook 报告",
        "",
        "日期：2026-06-15",
        "",
        "## 目的",
        "",
        "把慢的单候选 worker A/B 改成批量采样流程：20/30/50/100 只做",
        "capture-only 批量采集 same-run batch-impact 标签，5/10 只保留",
        "baseline/capture sentinel 来证明 no-regression。后续 GAT 训练、kNN/OOD",
        "审计和候选抽取都在离线命令中完成。",
        "",
        "## 机器字段",
        "",
        "```text",
        "gat_bulk_sampling_runbook = current",
        f"status = {summary['status']}",
        f"target_total_samples = {summary['target_total_samples']}",
        f"target_positive_samples = {summary['target_positive_samples']}",
        f"existing_row_count = {summary['existing_row_count']}",
        f"existing_positive_count = {summary['existing_positive_count']}",
        f"selected_new_instance_count = {summary['selected_new_instance_count']}",
        f"selected_wave_count = {summary['selected_wave_count']}",
        f"estimated_total_after = {summary['estimated_total_after']}",
        f"estimated_positive_after = {summary['estimated_positive_after']}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"certificate_ready = {str(summary['certificate_ready']).lower()}",
        f"default_enabled = {str(summary['default_enabled']).lower()}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## Bulk Sampling Policy",
        "",
        "```json",
        json.dumps(summary["bulk_sampling_policy"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Selected Bulk Instances",
        "",
        "```json",
        json.dumps(summary["selected_bulk_instances"], ensure_ascii=False, indent=2, sort_keys=True),
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
            "## 结论",
            "",
            "- 该 runbook 只生成批量采样命令，本身不运行求解器；",
            "- 20/30/50/100 采样使用 capture-only，减少无标签成本；",
            "- 5/10 只做 sentinel，不把小快实例混入大规模 ROI 目标；",
            "- GAT/kNN/OOD 只做优先级与延迟队列，不能证书，不能丢弃 true-RC negative；",
            "- 真正接 worker 前仍需 top-K target worker A/B 和 5/10 no-regression。",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
