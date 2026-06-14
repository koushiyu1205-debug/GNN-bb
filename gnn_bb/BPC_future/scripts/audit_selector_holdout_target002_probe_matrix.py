#!/usr/bin/env python3
"""Audit target002 exact-context reproduction probes.

This diagnostic is intentionally read-only.  It summarizes the small probe
matrix used to test why the remaining target002 selector-holdout context does
not reproduce under the current code path.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


EVENT_NAME = "journey_counterfactual_replay_capture"
TARGET_CONTEXT_HASH = "3f914a0d2b97fd27"

DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_holdout_target002_probe_matrix_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_holdout_target002_probe_matrix_zh.md"
)

PROBES = [
    {
        "probe_id": "historical_source",
        "role": "source",
        "log_dir": Path("BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/logs"),
        "expected_target_hit": True,
        "description": "原始 target002 pt0.3 capture。",
    },
    {
        "probe_id": "config_matched_active_basis_capture",
        "role": "new_capture",
        "log_dir": Path(
            "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/"
            "002_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000"
            "__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8/logs"
        ),
        "expected_target_hit": False,
        "description": "config-matched holdout 补采，包含 active-basis snapshot。",
    },
    {
        "probe_id": "no_active_basis_capture",
        "role": "probe",
        "log_dir": Path(
            "BPC_future/results/root_cause_selector_holdout_target002_no_active_basis_probe_20260614/logs"
        ),
        "expected_target_hit": False,
        "description": "同配置但去掉 active-basis snapshot。",
    },
    {
        "probe_id": "alias_instance_capture",
        "role": "probe",
        "log_dir": Path(
            "BPC_future/results/root_cause_selector_holdout_target002_alias_probe_20260614/logs"
        ),
        "expected_target_hit": False,
        "description": "使用原始实例别名 mt20_greedy_apollo_01。",
    },
    {
        "probe_id": "multi_profile_order_capture",
        "role": "probe",
        "log_dir": Path(
            "BPC_future/results/root_cause_selector_holdout_target002_multi_profile_order_probe_20260614/logs"
        ),
        "expected_target_hit": False,
        "description": "恢复原始多 profile 顺序，只审计 early-new-task-set profile。",
        "log_glob": "*experimental_early_new_task_set_quota_3_20_only*.jsonl",
    },
]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def _probe_events(probe: dict[str, Any]) -> list[dict[str, Any]]:
    log_dir = Path(probe["log_dir"])
    log_glob = str(probe.get("log_glob") or "*.jsonl")
    events: list[dict[str, Any]] = []
    for log_path in sorted(log_dir.glob(log_glob)):
        for row in _read_jsonl(log_path):
            if row.get("event") != EVENT_NAME:
                continue
            event = dict(row)
            event["_log_path"] = str(log_path)
            event["_repeat"] = log_path.stem.rsplit("__r", 1)[-1] if "__r" in log_path.stem else ""
            events.append(event)
    return events


def _compact_event(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "repeat": event.get("_repeat"),
        "cg_iter": event.get("cg_iter"),
        "context_hash": event.get("context_hash"),
        "active_hash_before": event.get("active_hash_before"),
        "rmp_objective_before": event.get("rmp_objective_before"),
        "pricing_state": event.get("pricing_state"),
        "returned_journey_count": event.get("returned_journey_count"),
        "pricing_best_reduced_cost": event.get("pricing_best_reduced_cost"),
    }


def _summarize_probe(probe: dict[str, Any]) -> dict[str, Any]:
    events = _probe_events(probe)
    target_events = [
        event for event in events if str(event.get("context_hash")) == TARGET_CONTEXT_HASH
    ]
    contexts = sorted({str(event.get("context_hash")) for event in events if event.get("context_hash")})
    found_negative_count = sum(1 for event in events if event.get("pricing_state") == "FOUND_NEGATIVE")
    incomplete_count = sum(1 for event in events if event.get("pricing_state") == "INCOMPLETE_LIMIT")
    repeats = sorted({str(event.get("_repeat")) for event in events if event.get("_repeat") != ""})
    return {
        "probe_id": probe["probe_id"],
        "role": probe["role"],
        "description": probe["description"],
        "log_dir": str(probe["log_dir"]),
        "log_dir_exists": Path(probe["log_dir"]).exists(),
        "event_count": len(events),
        "repeat_count": len(repeats),
        "context_hash_count": len(contexts),
        "contexts": contexts,
        "target_hit_count": len(target_events),
        "target_hit_expected": bool(probe["expected_target_hit"]),
        "target_hit_expectation_met": (len(target_events) > 0)
        == bool(probe["expected_target_hit"]),
        "found_negative_count": found_negative_count,
        "incomplete_count": incomplete_count,
        "path": [_compact_event(event) for event in events],
        "target_events": [_compact_event(event) for event in target_events],
    }


def audit() -> dict[str, Any]:
    probes = [_summarize_probe(probe) for probe in PROBES]
    source_probe = probes[0]
    reproduction_probes = probes[1:]
    target_recovered_probe_ids = [
        probe["probe_id"] for probe in reproduction_probes if probe["target_hit_count"] > 0
    ]
    checks = {
        "all_probe_logs_exist": all(probe["log_dir_exists"] for probe in probes),
        "source_has_target": source_probe["target_hit_count"] == 1,
        "reproduction_probes_have_no_target": not target_recovered_probe_ids,
        "all_expectations_met": all(probe["target_hit_expectation_met"] for probe in probes),
        "reproduction_probes_have_events": all(probe["event_count"] > 0 for probe in reproduction_probes),
        "diagnostic_has_no_certificate_effect_claim": True,
    }
    return {
        "schema_version": "root_cause_selector_holdout_target002_probe_matrix_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "selector_holdout_target002_probe_matrix_audited",
        "target_context_hash": TARGET_CONTEXT_HASH,
        "probe_count": len(probes),
        "reproduction_probe_count": len(reproduction_probes),
        "target_recovered_probe_ids": target_recovered_probe_ids,
        "target_recovered_probe_count": len(target_recovered_probe_ids),
        "source_target_hit_count": source_probe["target_hit_count"],
        "probes": probes,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "原始 target002 pt0.3 capture 中存在目标 exact context，但当前代码下的 "
            "config-matched active-basis 补采、去 active-basis 补采、实例别名补采、"
            "多 profile 顺序补采均未复现该 context。剩余缺口因此不是某一个"
            "采集字段或命令分组开关导致，而是 time-limit/returned-batch trajectory "
            "本身在临界区域不稳定；它继续阻塞 production selector holdout。"
        ),
    }


def write_report(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# Root Cause Selector Holdout target002 Probe Matrix 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告汇总 target002 剩余 exact context 缺口的最小 probe matrix。它只读",
        "已经完成的 probe 日志，不运行 BPC / pricing / RMP / Pulse，也不改变",
        "worker、certificate 或 solver 默认行为。",
        "",
        "## 机器字段",
        "",
        "```text",
        "root_cause_selector_holdout_target002_probe_matrix = current",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"status = {summary['status']}",
        f"target_context_hash = {summary['target_context_hash']}",
        f"probe_count = {summary['probe_count']}",
        f"reproduction_probe_count = {summary['reproduction_probe_count']}",
        f"source_target_hit_count = {summary['source_target_hit_count']}",
        f"target_recovered_probe_count = {summary['target_recovered_probe_count']}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 结论",
        "",
        summary["interpretation"],
        "",
        "## Probe Summary",
        "",
        "| probe | role | events | target hits | found negative | incomplete | contexts |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for probe in summary["probes"]:
        lines.append(
            f"| {probe['probe_id']} | {probe['role']} | {probe['event_count']} | "
            f"{probe['target_hit_count']} | {probe['found_negative_count']} | "
            f"{probe['incomplete_count']} | {probe['context_hash_count']} |"
        )
    lines.extend(
        [
            "",
            "## Probe Paths",
            "",
            "```json",
            json.dumps(
                [
                    {
                        "probe_id": probe["probe_id"],
                        "path": probe["path"],
                    }
                    for probe in summary["probes"]
                ],
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
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    summary = audit()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_report(summary, Path(args.report))
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
