#!/usr/bin/env python3
"""Diagnose the current missing selector-holdout context.

This audit is diagnostic-only.  It reads existing selector holdout capture,
target002 probe, and trajectory-branch summaries.  It does not run BPC,
pricing, RMP, Pulse, or any calibration command.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_CAPTURE_AUDIT = Path(
    "BPC_future/results/root_cause_selector_holdout_collection_capture_audit_20260614/"
    "summary.json"
)
DEFAULT_TARGET002_PROBE_MATRIX = Path(
    "BPC_future/results/root_cause_selector_holdout_target002_probe_matrix_20260614/"
    "summary.json"
)
DEFAULT_TARGET002_TRAJECTORY_BRANCH = Path(
    "BPC_future/results/root_cause_selector_holdout_target002_trajectory_branch_20260614/"
    "summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_holdout_missing_context_diagnosis_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_holdout_missing_context_diagnosis_zh.md"
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _as_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def build_summary(
    *,
    capture_audit_path: Path,
    target002_probe_matrix_path: Path,
    target002_trajectory_branch_path: Path,
) -> dict[str, Any]:
    capture = _read_json(capture_audit_path)
    probe = _read_json(target002_probe_matrix_path)
    branch = _read_json(target002_trajectory_branch_path)

    missing_commands: list[dict[str, Any]] = []
    missing_hashes: set[str] = set()
    for command in capture.get("command_summaries", []):
        command_missing = sorted(
            set(command.get("missing_context_hashes", []))
            | set(command.get("missing_complete_context_hashes", []))
        )
        if not command_missing:
            continue
        missing_hashes.update(str(item) for item in command_missing)
        sample_contexts = sorted(
            {
                str(event.get("context_hash"))
                for event in command.get("sample_events", [])
                if event.get("context_hash")
            }
        )
        missing_commands.append(
            {
                "command_id": command.get("command_id"),
                "instance": command.get("instance"),
                "profile": command.get("profile"),
                "output_dir": command.get("output_dir"),
                "capture_event_count": command.get("capture_event_count"),
                "log_count": command.get("log_count"),
                "expected_context_hashes": command.get("expected_context_hashes", []),
                "missing_context_hashes": command_missing,
                "hit_context_hashes": command.get("hit_context_hashes", []),
                "sample_context_hashes": sample_contexts,
                "sample_context_hash_count": len(sample_contexts),
            }
        )

    target_context_hash = str(probe.get("target_context_hash") or "")
    target_missing = bool(target_context_hash and target_context_hash in missing_hashes)
    checks = {
        "capture_audit_not_ready_contract_observed": (
            capture.get("diagnostic_only") is True
            and capture.get("runs_bpc_or_pricing") is False
            and capture.get("ready_for_selector_holdout") is False
        ),
        "missing_context_exists": _as_int(capture.get("missing_expected_context_count"))
        > 0,
        "missing_command_identified": bool(missing_commands),
        "target002_missing_context_identified": target_missing,
        "target002_probe_matrix_passed": probe.get("all_checks_pass") is True,
        "target002_not_recovered_by_current_probes": _as_int(
            probe.get("target_recovered_probe_count")
        )
        == 0,
        "target002_trajectory_branch_passed": branch.get("all_checks_pass") is True,
        "same_active_hash_splits_context": _as_int(
            branch.get("same_active_event_count")
        )
        > 0
        and _as_int(branch.get("non_source_same_active_event_count")) > 0,
    }
    return {
        "schema_version": "root_cause_selector_holdout_missing_context_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "selector_holdout_missing_context_diagnosed",
        "source_capture_audit": str(capture_audit_path),
        "source_target002_probe_matrix": str(target002_probe_matrix_path),
        "source_target002_trajectory_branch": str(
            target002_trajectory_branch_path
        ),
        "ready_for_selector_holdout": capture.get("ready_for_selector_holdout"),
        "expected_context_hash_count": capture.get("expected_context_hash_count"),
        "expected_context_hit_count": capture.get("expected_context_hit_count"),
        "expected_context_complete_hit_count": capture.get(
            "expected_context_complete_hit_count"
        ),
        "missing_expected_context_count": capture.get(
            "missing_expected_context_count"
        ),
        "missing_expected_complete_context_count": capture.get(
            "missing_expected_complete_context_count"
        ),
        "missing_context_hashes": sorted(missing_hashes),
        "missing_command_count": len(missing_commands),
        "missing_commands": missing_commands,
        "target002_context_hash": target_context_hash,
        "target002_missing_context_identified": target_missing,
        "target002_target_recovered_probe_count": probe.get(
            "target_recovered_probe_count"
        ),
        "target002_reproduction_probe_count": probe.get("reproduction_probe_count"),
        "target002_source_target_hit_count": probe.get("source_target_hit_count"),
        "target002_same_active_event_count": branch.get("same_active_event_count"),
        "target002_non_source_same_active_event_count": branch.get(
            "non_source_same_active_event_count"
        ),
        "interpretation": (
            "当前 selector holdout 不是缺少 runbook，而是 target002 context 在当前 "
            "config-matched active-basis capture 中没有复现。probe matrix 显示当前"
            "重放 probe 对该 target 的 recovery 为 0；trajectory branch 显示同一 "
            "active hash 附近会按 pool / forbidden / returned-batch composition 分叉。"
        ),
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }


def write_report(summary: dict[str, Any], report_path: Path) -> None:
    lines = [
        "# Root Cause Selector Holdout Missing Context Diagnosis 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告解释 selector holdout 采集链当前为什么还不能进入 selector holdout。",
        "它只读 capture audit / target002 probe / trajectory branch summary，",
        "不运行 BPC / pricing / RMP / Pulse，也不改变 solver 行为。",
        "",
        "## 机器字段",
        "",
        "```text",
        "selector_holdout_missing_context_diagnosis = current",
        "diagnostic_only = true",
        "runs_bpc_or_pricing = false",
        f"status = {summary['status']}",
        f"ready_for_selector_holdout = {str(summary['ready_for_selector_holdout']).lower()}",
        f"expected_context_hash_count = {summary['expected_context_hash_count']}",
        f"expected_context_hit_count = {summary['expected_context_hit_count']}",
        f"missing_expected_context_count = {summary['missing_expected_context_count']}",
        f"target002_context_hash = {summary['target002_context_hash']}",
        f"target002_target_recovered_probe_count = {summary['target002_target_recovered_probe_count']}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 结论",
        "",
        summary["interpretation"],
        "",
        "因此下一步不是直接 production A/B，也不是默认开启 worker，而是先解决",
        "这个 missing context / context-trajectory 分叉问题，再重新做 addition-before",
        "selector holdout。",
        "",
        "## Missing Commands",
        "",
        "```json",
        json.dumps(
            summary["missing_commands"],
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
        "",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture-audit", type=Path, default=DEFAULT_CAPTURE_AUDIT)
    parser.add_argument(
        "--target002-probe-matrix",
        type=Path,
        default=DEFAULT_TARGET002_PROBE_MATRIX,
    )
    parser.add_argument(
        "--target002-trajectory-branch",
        type=Path,
        default=DEFAULT_TARGET002_TRAJECTORY_BRANCH,
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    summary = build_summary(
        capture_audit_path=args.capture_audit,
        target002_probe_matrix_path=args.target002_probe_matrix,
        target002_trajectory_branch_path=args.target002_trajectory_branch,
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
