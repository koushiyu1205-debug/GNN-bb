#!/usr/bin/env python3
"""Build a targeted capture worklist for CBF family-gate gaps.

The family-aware CBF audit tells us which residual families are unsafe or
under-sampled.  This helper turns that evidence into a concrete, no-certificate
effect capture worklist.  It does not run BPC/pricing/RMP; it only emits JSON,
CSV, and optional batch commands to run later.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

from BPC_future.scripts.audit_cbf_gate_family_policy import infer_family
from BPC_future.scripts.train_cbf_gate import load_rows


DEFAULT_DATASET = Path("BPC_future/results/cbf_gate_dataset_global_available_20260614/cbf_gate_transitions.jsonl")
DEFAULT_FAMILY_AUDIT = Path("BPC_future/results/cbf_gate_family_policy_audit_global_available_20260614/summary.json")
DEFAULT_TASKS_ROOT = Path("BPC_future/logical_graph/tasks_020")
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/cbf_family_capture_worklist_20260614")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_cbf_family_capture_worklist_zh.md"
)
PYTHON = "/home/kai/miniconda3/envs/ecole/bin/python"

CAPTURE_OVERRIDES = [
    "journey_counterfactual_replay_capture_enabled=true",
    "journey_counterfactual_replay_capture_active_basis_enabled=true",
    "journey_counterfactual_replay_capture_forbidden_signatures_enabled=true",
    "journey_counterfactual_replay_capture_log_empty=true",
    "journey_counterfactual_replay_capture_active_basis_max_rows=96",
    "journey_counterfactual_replay_capture_max_journeys=32",
    "journey_counterfactual_replay_capture_pool_max_journeys=256",
    "journey_counterfactual_replay_capture_forbidden_signature_max_count=256",
]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _as_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _dataset_instances(rows: list[dict[str, Any]]) -> dict[tuple[int, str], dict[str, int]]:
    counts: dict[tuple[int, str], dict[str, int]] = {}
    for row in rows:
        key = (_as_int(row.get("task_count")), infer_family(row))
        instance = str(row.get("instance", ""))
        if not instance:
            continue
        counts.setdefault(key, {})
        counts[key][instance] = counts[key].get(instance, 0) + 1
    return counts


def _instance_stem(path: Path) -> str:
    name = path.name
    return name.replace("_logical_graph.json", "").replace(".json", "")


def _region_priority(path: Path, preferred_region: str) -> int:
    text = str(path).lower()
    if preferred_region and preferred_region.lower() in text:
        return 0
    if "tranquillitatis" in text:
        return 1
    if "apollo" in text:
        return 2
    return 3


def _list_available_instances(tasks_root: Path, family: str) -> list[dict[str, Any]]:
    family_root = tasks_root / family
    if not family_root.exists():
        return []
    instances: list[dict[str, Any]] = []
    for path in sorted(family_root.rglob("*_logical_graph.json")):
        region = "tranquillitatis" if "tranquillitatis" in str(path).lower() else "apollo" if "apollo" in str(path).lower() else "unknown"
        instances.append(
            {
                "instance": str(path),
                "instance_stem": _instance_stem(path),
                "family": family,
                "region": region,
            }
        )
    return instances


def _family_priority(item: dict[str, Any]) -> int:
    status = str(item.get("status", ""))
    reason = str(item.get("reason", ""))
    if status == "family_gate_not_ready" and "holdout" in reason:
        return 100
    if status == "insufficient_family_rows":
        return 80
    if status == "insufficient_family_label_coverage":
        return 70
    return 10


def _preferred_region_for_family(item: dict[str, Any]) -> str:
    family = str(item.get("family", ""))
    if family == "greedy-anchor":
        return "tranquillitatis"
    return ""


def _select_instances(
    *,
    available: list[dict[str, Any]],
    existing_counts: dict[str, int],
    preferred_region: str,
    max_instances: int,
) -> list[dict[str, Any]]:
    scored: list[tuple[tuple[int, int, str], dict[str, Any]]] = []
    for item in available:
        stem = str(item["instance_stem"])
        already_rows = int(existing_counts.get(stem, 0))
        # Prefer unseen instances, then the family-specific region, then stable name.
        score = (
            1 if already_rows > 0 else 0,
            _region_priority(Path(str(item["instance"])), preferred_region),
            stem,
        )
        copied = dict(item)
        copied["existing_transition_rows"] = already_rows
        scored.append((score, copied))
    return [item for _score, item in sorted(scored)[: int(max_instances)]]


def _family_command(
    *,
    family: str,
    instances: list[dict[str, Any]],
    output_root: Path,
    time_limit: float,
    max_workers: int,
) -> str:
    if not instances:
        return ""
    result_dir = output_root / "captures" / family
    parts = [
        "PYTHONDONTWRITEBYTECODE=1",
        "PYTHONPATH=.",
        PYTHON,
        "BPC_future/scripts/run_bpc_future_external_timeout_batch.py",
        "--config BPC_future/configs/moon_trek_20_smoke.yaml",
        "--time-limit",
        f"{float(time_limit):.6f}",
        "--timeout-kill-after 30s",
        "--max-workers",
        str(int(max_workers)),
        "--results-csv",
        str(result_dir / "results.csv"),
        "--log-dir",
        str(result_dir / "logs"),
        "--solution-dir",
        str(result_dir / "solutions"),
        "--run-log-dir",
        str(result_dir / "run_logs"),
        "--quiet",
        "--instances",
    ]
    parts.extend(str(item["instance"]) for item in instances)
    for override in CAPTURE_OVERRIDES:
        parts.extend(["--set", override])
    return " ".join(parts)


def build_worklist(
    *,
    dataset_path: Path,
    family_audit_path: Path,
    tasks_root: Path,
    output_dir: Path,
    report: Path,
    min_family_rows: int = 30,
    max_instances_per_family: int = 4,
    expected_rows_per_capture: float = 3.0,
    time_limit: float = 90.0,
    max_workers: int = 1,
) -> dict[str, Any]:
    rows = load_rows(dataset_path) if dataset_path.exists() else []
    audit = _read_json(family_audit_path)
    existing = _dataset_instances(rows)
    work_items: list[dict[str, Any]] = []
    commands: list[dict[str, Any]] = []
    for item in audit.get("family_results", []):
        task_count = _as_int(item.get("task_count"))
        family = str(item.get("family", ""))
        if task_count < 20:
            continue
        status = str(item.get("status", ""))
        if status in {"family_gate_candidate_ready"}:
            continue
        if family in {"unknown", "moon_trek_tasks20"}:
            # These are legacy or unmapped buckets; do not create blind capture
            # commands until their generation family can be recovered.
            action = "recover_family_mapping_before_capture"
            selected: list[dict[str, Any]] = []
            command = ""
        else:
            family_rows = _as_int(item.get("row_count"))
            missing_rows = max(0, int(min_family_rows) - family_rows)
            if status == "family_gate_not_ready":
                # A safety failure needs neighborhood coverage even if row_count
                # already exceeds the minimum.
                missing_rows = max(missing_rows, int(math.ceil(2.0 * expected_rows_per_capture)))
            requested_instances = max(
                1,
                min(int(max_instances_per_family), int(math.ceil(missing_rows / max(1.0, expected_rows_per_capture)))),
            )
            available = _list_available_instances(tasks_root, family)
            key = (task_count, family)
            selected = _select_instances(
                available=available,
                existing_counts=existing.get(key, {}),
                preferred_region=_preferred_region_for_family(item),
                max_instances=requested_instances,
            )
            action = "capture_family_context_rows" if selected else "no_available_instances_for_family"
            command = _family_command(
                family=family,
                instances=selected,
                output_root=output_dir,
                time_limit=time_limit,
                max_workers=max_workers,
            )
        work_item = {
            "priority": _family_priority(item),
            "task_count": task_count,
            "family": family,
            "status": status,
            "reason": item.get("reason"),
            "row_count": item.get("row_count"),
            "label_counts": item.get("label_counts"),
            "fold_summary": item.get("fold_summary"),
            "recommended_action": action,
            "selected_instance_count": len(selected),
            "selected_instances": selected,
            "command": command,
        }
        work_items.append(work_item)
        if command:
            commands.append(
                {
                    "family": family,
                    "task_count": task_count,
                    "command": command,
                    "selected_instance_count": len(selected),
                }
            )

    work_items.sort(key=lambda value: (-int(value.get("priority", 0)), str(value.get("family", ""))))
    checks = {
        "dataset_exists": dataset_path.exists(),
        "family_audit_exists": family_audit_path.exists(),
        "tasks_root_exists": tasks_root.exists(),
        "diagnostic_only": True,
        "runs_bpc_or_pricing_false": True,
        "no_ready_family_is_scheduled": all(
            item.get("status") != "family_gate_candidate_ready" for item in work_items
        ),
        "small_scales_not_scheduled": all(_as_int(item.get("task_count")) >= 20 for item in work_items),
    }
    summary = {
        "schema_version": "cbf_family_capture_worklist_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "cbf_family_capture_worklist_ready",
        "dataset": str(dataset_path),
        "family_audit": str(family_audit_path),
        "tasks_root": str(tasks_root),
        "min_family_rows": int(min_family_rows),
        "max_instances_per_family": int(max_instances_per_family),
        "expected_rows_per_capture": float(expected_rows_per_capture),
        "time_limit": float(time_limit),
        "work_item_count": len(work_items),
        "command_count": len(commands),
        "work_items": work_items,
        "commands": commands,
        "checks": checks,
        "all_checks_pass": all(bool(value) for value in checks.values()),
        "production_ready": False,
        "goal_complete": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_csv(output_dir / "worklist.csv", work_items)
    _write_report(report, summary)
    return summary


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "priority",
        "task_count",
        "family",
        "status",
        "reason",
        "row_count",
        "label_counts",
        "recommended_action",
        "selected_instance_count",
        "selected_instances",
        "command",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    field: json.dumps(row.get(field), ensure_ascii=False, sort_keys=True)
                    if field in {"label_counts", "selected_instances"}
                    else row.get(field, "")
                    for field in fields
                }
            )


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# CBF Family Capture Worklist",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "把 family-aware CBF gate 审计中的缺口转成可执行 capture worklist。",
        "本脚本只读数据和实例目录，不运行 BPC / pricing / RMP，也不改变默认求解路径。",
        "",
        "## 机器字段",
        "",
        "```text",
        "cbf_family_capture_worklist = current",
        f"status = {summary['status']}",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"work_item_count = {summary['work_item_count']}",
        f"command_count = {summary['command_count']}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        "```",
        "",
        "## 摘要",
        "",
        "```json",
        json.dumps(
            {
                "work_item_count": summary["work_item_count"],
                "command_count": summary["command_count"],
                "work_items": [
                    {
                        "priority": item["priority"],
                        "task_count": item["task_count"],
                        "family": item["family"],
                        "status": item["status"],
                        "recommended_action": item["recommended_action"],
                        "selected_instance_count": item["selected_instance_count"],
                    }
                    for item in summary["work_items"]
                ],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## Commands",
        "",
    ]
    if not summary["commands"]:
        lines.append("当前没有可执行命令。")
    for command in summary["commands"]:
        lines.extend(
            [
                f"### {command['family']} / task_count={command['task_count']}",
                "",
                "```bash",
                command["command"],
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## 解释",
            "",
            "- 这些命令只用于后续 no-certificate-effect capture；",
            "- 小规模不会被安排采样，以保持 5/10 默认不退化；",
            "- 采样后必须重新 build CBF dataset、readiness、family-policy 审计；",
            "- worklist 不是 production gate，也不是 certificate。",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--family-audit", type=Path, default=DEFAULT_FAMILY_AUDIT)
    parser.add_argument("--tasks-root", type=Path, default=DEFAULT_TASKS_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--min-family-rows", type=int, default=30)
    parser.add_argument("--max-instances-per-family", type=int, default=4)
    parser.add_argument("--expected-rows-per-capture", type=float, default=3.0)
    parser.add_argument("--time-limit", type=float, default=90.0)
    parser.add_argument("--max-workers", type=int, default=1)
    args = parser.parse_args(argv)
    summary = build_worklist(
        dataset_path=args.dataset,
        family_audit_path=args.family_audit,
        tasks_root=args.tasks_root,
        output_dir=args.output_dir,
        report=args.report,
        min_family_rows=args.min_family_rows,
        max_instances_per_family=args.max_instances_per_family,
        expected_rows_per_capture=args.expected_rows_per_capture,
        time_limit=args.time_limit,
        max_workers=args.max_workers,
    )
    print(
        json.dumps(
            {
                "summary": str(args.output_dir / "summary.json"),
                "report": str(args.report),
                "all_checks_pass": summary["all_checks_pass"],
                "work_item_count": summary["work_item_count"],
                "command_count": summary["command_count"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
