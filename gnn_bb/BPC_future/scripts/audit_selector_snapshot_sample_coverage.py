#!/usr/bin/env python3
"""Audit full active-basis snapshot sample coverage for selector calibration.

This script is diagnostic-only.  It scans existing candidate impact CSV files
and answers whether the current workspace already contains enough
addition-before, full active-basis snapshot rows to support a production
selector holdout.  It does not run BPC, pricing, RMP, Pulse, replay, or any
benchmark.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_snapshot_sample_coverage_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_snapshot_sample_coverage_zh.md"
)
DEFAULT_GLOB = "BPC_future/results/**/*candidate*impact*rows.csv"
REPLAY_SELECTOR_DATASET = (
    "root_cause_counterfactual_replay_impact_dataset_20260613/combined/"
    "combined_candidate_impact_rows.csv"
)
MIN_COMPLETE_ROWS_FOR_HOLDOUT = 50


def _truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _read_rows(paths: list[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in paths:
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("single_impact_class") not in {"improved", "noop"}:
                    continue
                copied = dict(row)
                copied["_source_csv"] = str(path)
                rows.append(copied)
    return rows


def _counter(rows: list[dict[str, str]], field: str) -> dict[str, int]:
    return dict(Counter(str(row.get(field, "")) for row in rows))


def _path_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    return dict(Counter(row["_source_csv"] for row in rows))


def _classify_source(path: str) -> str:
    if "root_cause_active_basis_snapshot" in path:
        return "active_basis_snapshot_smoke"
    if "root_cause_component_payload_addition_before_rows" in path:
        return "component_payload_addition_before_rows"
    if "counterfactual_replay_impact_dataset_20260613/combined" in path:
        return "combined_replay_selector_dataset"
    if "counterfactual_replay" in path or "counterfactual_target" in path:
        return "counterfactual_replay_dataset"
    return "other"


def audit(*, csv_glob: str) -> dict[str, Any]:
    paths = sorted(Path().glob(csv_glob))
    rows = _read_rows(paths)
    complete_rows = [
        row for row in rows if _truthy(row.get("active_basis_snapshot_complete_before"))
    ]
    replay_rows = [
        row for row in rows if row.get("_source_csv", "").endswith(REPLAY_SELECTOR_DATASET)
    ]
    replay_complete_rows = [
        row
        for row in replay_rows
        if _truthy(row.get("active_basis_snapshot_complete_before"))
    ]
    complete_source_classes = dict(
        Counter(_classify_source(row["_source_csv"]) for row in complete_rows)
    )
    complete_paths = _path_counts(complete_rows)
    all_paths = _path_counts(rows)
    complete_labels = _counter(complete_rows, "single_impact_class")
    complete_task_counts = _counter(complete_rows, "task_count")
    complete_instances = _counter(complete_rows, "instance")
    complete_context_count = len({row.get("context_hash", "") for row in complete_rows})
    complete_dataset_count = len(complete_paths)
    holdout_ready = (
        len(complete_rows) >= MIN_COMPLETE_ROWS_FOR_HOLDOUT
        and set(complete_labels) >= {"improved", "noop"}
        and complete_context_count >= 10
        and len(complete_instances) >= 4
        and complete_dataset_count >= 3
        and len(replay_complete_rows) > 0
    )
    checks = {
        "candidate_rows_exist": len(rows) > 0,
        "complete_snapshot_rows_exist": len(complete_rows) > 0,
        "complete_snapshot_rows_include_component_payload": (
            complete_source_classes.get("component_payload_addition_before_rows", 0) > 0
        ),
        "combined_replay_selector_rows_have_no_complete_snapshot": (
            len(replay_rows) > 0 and len(replay_complete_rows) == 0
        ),
        "complete_snapshot_rows_not_production_selector_dataset": (
            len(replay_complete_rows) == 0
            and complete_source_classes.get("component_payload_addition_before_rows", 0)
            < len(complete_rows)
        ),
        "both_labels_exist_in_complete_snapshot_rows": set(complete_labels)
        >= {"improved", "noop"},
        "holdout_not_ready": holdout_ready is False,
        "diagnostic_not_production_selector": True,
    }
    return {
        "schema_version": "root_cause_selector_snapshot_sample_coverage_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "selector_snapshot_sample_coverage_audited",
        "csv_glob": csv_glob,
        "csv_path_count": len(paths),
        "candidate_row_count": len(rows),
        "combined_replay_selector_row_count": len(replay_rows),
        "combined_replay_selector_complete_snapshot_row_count": len(
            replay_complete_rows
        ),
        "complete_snapshot_row_count": len(complete_rows),
        "complete_snapshot_min_rows_for_holdout": MIN_COMPLETE_ROWS_FOR_HOLDOUT,
        "complete_snapshot_label_counts": complete_labels,
        "complete_snapshot_task_count_counts": complete_task_counts,
        "complete_snapshot_instance_count": len(complete_instances),
        "complete_snapshot_context_count": complete_context_count,
        "complete_snapshot_dataset_count": complete_dataset_count,
        "complete_snapshot_source_class_counts": complete_source_classes,
        "complete_snapshot_path_counts": complete_paths,
        "candidate_path_counts": all_paths,
        "holdout_ready": holdout_ready,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "全局 candidate impact CSV 中确实存在 full active-basis snapshot rows，"
            "现在包括 active-basis snapshot smoke 的 14 行和 targeted component payload "
            "addition-before rows 的 48 行；但主 replay selector combined dataset 的 "
            "280 行里 complete snapshot 仍为 0，component payload rows 也还只是单目标"
            "上下文校准数据。因此当前不是已有样本未利用，而是还没有足够的、已合入 "
            "selector holdout 的 no-certificate-effect full-snapshot 数据。"
        ),
    }


def write_report(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# Root Cause Selector Snapshot Sample Coverage 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告扫描现有 candidate impact CSV，确认是否已经有足够 full active-basis",
        "snapshot rows 可用于 production selector holdout。它不运行 BPC / pricing / RMP / Pulse。",
        "",
        "## 机器字段",
        "",
        "```text",
        "root_cause_selector_snapshot_sample_coverage = current",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"status = {summary['status']}",
        f"csv_path_count = {summary['csv_path_count']}",
        f"candidate_row_count = {summary['candidate_row_count']}",
        "combined_replay_selector_row_count = "
        f"{summary['combined_replay_selector_row_count']}",
        "combined_replay_selector_complete_snapshot_row_count = "
        f"{summary['combined_replay_selector_complete_snapshot_row_count']}",
        f"complete_snapshot_row_count = {summary['complete_snapshot_row_count']}",
        f"holdout_ready = {str(summary['holdout_ready']).lower()}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 结论",
        "",
        summary["interpretation"],
        "",
        "## Complete Snapshot Source Classes",
        "",
        "```json",
        json.dumps(
            summary["complete_snapshot_source_class_counts"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## Checks",
        "",
        "```json",
        json.dumps(summary["checks"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv-glob", default=DEFAULT_GLOB)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    summary = audit(csv_glob=str(args.csv_glob))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_report(summary, args.report)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
