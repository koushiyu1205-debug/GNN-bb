#!/usr/bin/env python3
"""Compare target002 source context components with same-active events.

This diagnostic is read-only.  It explains why the target002 context hash is
not recovered by comparing the historical source target event against all
available non-source events that share the same active hash.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_TRAJECTORY_BRANCH = Path(
    "BPC_future/results/root_cause_selector_holdout_target002_trajectory_branch_20260614/"
    "summary.json"
)
DEFAULT_MISSING_CONTEXT = Path(
    "BPC_future/results/root_cause_selector_holdout_missing_context_diagnosis_20260614/"
    "summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_holdout_target002_component_drift_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_holdout_target002_component_drift_zh.md"
)

COMPONENT_FIELDS = [
    "pool_signature_hash",
    "forbidden_signature_hash",
    "pool_task_set_hash",
    "pool_journey_count",
    "rmp_objective_before",
    "pricing_state",
    "pricing_best_reduced_cost",
]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _task_sets(event: dict[str, Any]) -> set[tuple[int, ...]]:
    returned = event.get("returned", {}) or {}
    sets = returned.get("task_set_set", []) or []
    return {tuple(int(item) for item in task_set) for task_set in sets}


def _as_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def build_summary(
    *, trajectory_branch_path: Path, missing_context_path: Path
) -> dict[str, Any]:
    branch = _read_json(trajectory_branch_path)
    missing = _read_json(missing_context_path)
    source = dict(branch.get("source_target_event") or {})
    events = [dict(event) for event in branch.get("non_source_same_active_events", [])]
    source_sets = _task_sets(source)

    field_same_counts: dict[str, int] = {}
    field_diff_counts: dict[str, int] = {}
    for field in COMPONENT_FIELDS:
        counter = Counter(event.get(field) == source.get(field) for event in events)
        field_same_counts[field] = int(counter[True])
        field_diff_counts[field] = int(counter[False])

    group_counts = Counter(str(event.get("group_id", "")) for event in events)
    exact_returned_same_count = 0
    config_matched_exact_returned_same_count = 0
    event_comparisons: list[dict[str, Any]] = []
    for event in events:
        event_sets = _task_sets(event)
        exact_returned_same = event_sets == source_sets
        if exact_returned_same:
            exact_returned_same_count += 1
        if (
            event.get("group_id") == "config_matched_active_basis_capture"
            and exact_returned_same
        ):
            config_matched_exact_returned_same_count += 1
        event_comparisons.append(
            {
                "group_id": event.get("group_id"),
                "repeat": event.get("repeat"),
                "cg_iter": event.get("cg_iter"),
                "context_hash": event.get("context_hash"),
                "same_context_hash": event.get("context_hash")
                == source.get("context_hash"),
                "same_pool_signature_hash": event.get("pool_signature_hash")
                == source.get("pool_signature_hash"),
                "same_forbidden_signature_hash": event.get(
                    "forbidden_signature_hash"
                )
                == source.get("forbidden_signature_hash"),
                "same_pool_task_set_hash": event.get("pool_task_set_hash")
                == source.get("pool_task_set_hash"),
                "same_pool_journey_count": event.get("pool_journey_count")
                == source.get("pool_journey_count"),
                "same_rmp_objective_before": event.get("rmp_objective_before")
                == source.get("rmp_objective_before"),
                "same_pricing_state": event.get("pricing_state")
                == source.get("pricing_state"),
                "same_pricing_best_reduced_cost": event.get(
                    "pricing_best_reduced_cost"
                )
                == source.get("pricing_best_reduced_cost"),
                "same_returned_task_sets": exact_returned_same,
                "returned_journey_count": (event.get("returned", {}) or {}).get(
                    "returned_journey_count"
                ),
                "missing_source_task_sets": [
                    list(task_set) for task_set in sorted(source_sets - event_sets)
                ],
                "extra_task_sets": [
                    list(task_set) for task_set in sorted(event_sets - source_sets)
                ],
            }
        )

    checks = {
        "trajectory_branch_passed": branch.get("all_checks_pass") is True,
        "missing_context_diagnosis_passed": missing.get("all_checks_pass") is True,
        "source_target_event_exists": bool(source),
        "non_source_same_active_events_exist": bool(events),
        "target_context_hash_matches_missing_context": (
            source.get("context_hash")
            == "3f914a0d2b97fd27"
            == missing.get("target002_context_hash")
        ),
        "target_context_not_recovered": _as_int(
            missing.get("target002_target_recovered_probe_count")
        )
        == 0,
        "no_non_source_same_context_hash": all(
            event.get("context_hash") != source.get("context_hash")
            for event in events
        ),
        "no_non_source_same_pool_signature_hash": field_same_counts.get(
            "pool_signature_hash"
        )
        == 0,
        "no_non_source_same_forbidden_signature_hash": field_same_counts.get(
            "forbidden_signature_hash"
        )
        == 0,
        "config_matched_does_not_recover_returned_task_sets": (
            config_matched_exact_returned_same_count == 0
        ),
    }
    return {
        "schema_version": "root_cause_target002_component_drift_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "selector_holdout_target002_component_drift_diagnosed",
        "source_trajectory_branch": str(trajectory_branch_path),
        "source_missing_context": str(missing_context_path),
        "target_context_hash": source.get("context_hash"),
        "target_active_hash": source.get("active_hash_before"),
        "source_components": {
            field: source.get(field) for field in ["context_hash", "active_hash_before", *COMPONENT_FIELDS]
        },
        "source_returned_task_sets": [list(task_set) for task_set in sorted(source_sets)],
        "non_source_same_active_event_count": len(events),
        "non_source_group_counts": dict(sorted(group_counts.items())),
        "field_same_counts": field_same_counts,
        "field_diff_counts": field_diff_counts,
        "exact_returned_task_sets_same_count": exact_returned_same_count,
        "config_matched_exact_returned_task_sets_same_count": (
            config_matched_exact_returned_same_count
        ),
        "event_comparisons": event_comparisons,
        "interpretation": (
            "target002 source context is not recovered because same-active events "
            "drift in pool signature, forbidden signature, RMP objective, and/or "
            "returned-batch composition.  Active hash alone is therefore not a "
            "sufficient selector or replay key."
        ),
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }


def write_report(summary: dict[str, Any], report_path: Path) -> None:
    lines = [
        "# Root Cause target002 Component Drift 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告比较 target002 historical source context 与同 active hash 的非 source",
        "事件，定位 target context 不能复现的具体组成差异。它只读已有 summary，",
        "不运行 BPC / pricing / RMP / Pulse，也不改变 solver 行为。",
        "",
        "## 机器字段",
        "",
        "```text",
        "selector_holdout_target002_component_drift = current",
        "diagnostic_only = true",
        "runs_bpc_or_pricing = false",
        f"status = {summary['status']}",
        f"target_context_hash = {summary['target_context_hash']}",
        f"target_active_hash = {summary['target_active_hash']}",
        f"non_source_same_active_event_count = {summary['non_source_same_active_event_count']}",
        f"pool_signature_hash_same_count = {summary['field_same_counts']['pool_signature_hash']}",
        f"forbidden_signature_hash_same_count = {summary['field_same_counts']['forbidden_signature_hash']}",
        f"config_matched_exact_returned_task_sets_same_count = {summary['config_matched_exact_returned_task_sets_same_count']}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 结论",
        "",
        "同一个 active hash 下，非 source 事件没有一个同时复现 source 的",
        "`pool_signature_hash` 或 `forbidden_signature_hash`；config-matched",
        "active-basis capture 也没有复现 source 的 returned task-set batch。",
        "因此 target002 缺失不是简单 active-basis snapshot 字段缺失，而是",
        "pool / forbidden / returned-batch composition 分叉。",
        "",
        summary["interpretation"],
        "",
        "## Source Components",
        "",
        "```json",
        json.dumps(summary["source_components"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Field Same Counts",
        "",
        "```json",
        json.dumps(summary["field_same_counts"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Event Comparisons",
        "",
        "```json",
        json.dumps(summary["event_comparisons"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Checks",
        "",
        "```json",
        json.dumps(summary["checks"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--trajectory-branch", type=Path, default=DEFAULT_TRAJECTORY_BRANCH
    )
    parser.add_argument("--missing-context", type=Path, default=DEFAULT_MISSING_CONTEXT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    summary = build_summary(
        trajectory_branch_path=args.trajectory_branch,
        missing_context_path=args.missing_context,
    )
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
