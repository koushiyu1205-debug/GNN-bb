#!/usr/bin/env python3
"""Audit the no-certificate-effect active-basis snapshot smoke.

This is a read-only diagnostic over an already generated smoke bundle.  It does
not run BPC, pricing, replay, workers, or certificates.  The purpose is to
verify that the full active-basis snapshot capture path can populate the
addition-before fields needed by the root-cause selector evidence chain.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


DEFAULT_SMOKE_ROOT = Path("BPC_future/results/root_cause_active_basis_snapshot_smoke_20260614")
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/root_cause_active_basis_snapshot_smoke_audit_20260614")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_active_basis_snapshot_smoke_zh.md"
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _nonempty(row: dict[str, str], field: str) -> bool:
    return row.get(field) not in {"", None}


def audit(smoke_root: Path) -> dict[str, Any]:
    log_dir = smoke_root / "logs"
    manifest_summary = smoke_root / "manifest" / "summary.json"
    replay_summary = smoke_root / "replay" / "summary.json"
    impact_summary = smoke_root / "impact" / "summary.json"
    candidate_rows_path = smoke_root / "impact" / "candidate_impact_rows.csv"

    log_paths = sorted(log_dir.glob("*.jsonl")) if log_dir.exists() else []
    capture_events: list[dict[str, Any]] = []
    for path in log_paths:
        capture_events.extend(
            row
            for row in _read_jsonl(path)
            if row.get("event") == "journey_counterfactual_replay_capture"
        )

    manifest = _read_json(manifest_summary) if manifest_summary.exists() else {}
    replay = _read_json(replay_summary) if replay_summary.exists() else {}
    impact = _read_json(impact_summary) if impact_summary.exists() else {}
    candidate_rows = _read_csv_rows(candidate_rows_path) if candidate_rows_path.exists() else []

    churn_nonempty_count = sum(
        1 for row in candidate_rows if _nonempty(row, "active_basis_churn_count_before")
    )
    degeneracy_nonempty_count = sum(
        1 for row in candidate_rows if _nonempty(row, "rmp_degeneracy_pressure_before")
    )
    source_counts: dict[str, int] = {}
    for row in candidate_rows:
        source = str(row.get("active_basis_churn_source_before", "") or "")
        source_counts[source] = source_counts.get(source, 0) + 1

    active_complete_capture_count = sum(
        1 for event in capture_events if event.get("active_basis_snapshot_complete") is True
    )
    active_payload_counts = [
        int(event.get("active_basis_payload_count") or 0)
        for event in capture_events
        if event.get("active_basis_snapshot_enabled") is True
    ]
    official_effect_count = sum(
        1
        for event in capture_events
        if event.get("official_bound_effect") is not False
        or event.get("certificate_capable") is not False
        or event.get("replay_no_certificate_effect") is not True
    )

    checks = {
        "smoke_root_exists": smoke_root.exists(),
        "has_log_file": bool(log_paths),
        "has_capture_events": bool(capture_events),
        "all_capture_events_no_certificate_effect": bool(capture_events)
        and official_effect_count == 0,
        "all_capture_events_have_complete_active_basis_snapshot": bool(capture_events)
        and active_complete_capture_count == len(capture_events),
        "active_basis_payload_nonempty": bool(active_payload_counts)
        and min(active_payload_counts) > 0,
        "manifest_passed": manifest.get("all_checks_pass") is True,
        "manifest_has_ready_cases": int(manifest.get("ready_case_count") or 0) > 0,
        "replay_passed": replay.get("all_checks_pass") is True,
        "impact_passed": impact.get("all_checks_pass") is True,
        "impact_has_candidate_rows": bool(candidate_rows),
        "active_basis_churn_populated_for_all_candidates": bool(candidate_rows)
        and churn_nonempty_count == len(candidate_rows),
        "rmp_degeneracy_pressure_populated_for_all_candidates": bool(candidate_rows)
        and degeneracy_nonempty_count == len(candidate_rows),
        "has_initial_snapshot_churn_source": source_counts.get("initial_active_basis_snapshot", 0) > 0,
        "has_full_snapshot_churn_source": source_counts.get(
            "full_active_basis_signature_symmetric_difference", 0
        )
        > 0,
        "replay_is_no_certificate_effect": bool(
            (replay.get("checks") or {}).get("all_replay_is_no_certificate_effect")
        ),
        "impact_replay_is_no_certificate_effect": bool(
            (impact.get("checks") or {}).get("replay_is_no_certificate_effect")
        ),
    }

    return {
        "schema_version": "active_basis_snapshot_smoke_audit_v1",
        "runs_bpc_or_pricing": False,
        "smoke_root": str(smoke_root),
        "log_paths": [str(path) for path in log_paths],
        "capture_event_count": len(capture_events),
        "active_complete_capture_count": active_complete_capture_count,
        "active_basis_payload_count_min": min(active_payload_counts) if active_payload_counts else 0,
        "active_basis_payload_count_max": max(active_payload_counts) if active_payload_counts else 0,
        "official_effect_count": official_effect_count,
        "manifest_ready_case_count": int(manifest.get("ready_case_count") or 0),
        "replay_case_count": int(replay.get("case_count") or 0),
        "impact_candidate_row_count": len(candidate_rows),
        "impact_high_impact_candidate_count": int(impact.get("high_impact_candidate_count") or 0),
        "impact_noop_candidate_count": int(impact.get("noop_candidate_count") or 0),
        "active_basis_churn_nonempty_count": churn_nonempty_count,
        "rmp_degeneracy_pressure_nonempty_count": degeneracy_nonempty_count,
        "active_basis_churn_source_counts": source_counts,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "The smoke proves that the default-off, no-certificate-effect capture path can "
            "populate full active-basis snapshot metrics in candidate impact rows.  It is "
            "not a production selector, no-regression, or 20-task speedup proof."
        ),
    }


def write_report(summary: dict[str, Any], report_path: Path) -> None:
    checks = summary["checks"]
    lines = [
        "# Active-basis Snapshot Smoke 审计报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目标",
        "",
        f"本报告只审计已生成的 no-certificate-effect smoke 产物 `{summary['smoke_root']}`，确认 full active-basis snapshot 采集链路能把 `active_basis_churn_count_before` 和 `rmp_degeneracy_pressure_before` 写入 candidate impact rows。",
        "",
        "它不运行 BPC / pricing / replay，不改变 worker、certificate 或 official lower bound。",
        "",
        "## 关键结果",
        "",
        "```text",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        f"capture_event_count = {summary['capture_event_count']}",
        f"active_complete_capture_count = {summary['active_complete_capture_count']}",
        f"active_basis_payload_count_min = {summary['active_basis_payload_count_min']}",
        f"manifest_ready_case_count = {summary['manifest_ready_case_count']}",
        f"replay_case_count = {summary['replay_case_count']}",
        f"impact_candidate_row_count = {summary['impact_candidate_row_count']}",
        f"active_basis_churn_nonempty_count = {summary['active_basis_churn_nonempty_count']}",
        f"rmp_degeneracy_pressure_nonempty_count = {summary['rmp_degeneracy_pressure_nonempty_count']}",
        f"official_effect_count = {summary['official_effect_count']}",
        "```",
        "",
        "## Churn Source",
        "",
        "```json",
        json.dumps(summary["active_basis_churn_source_counts"], indent=2, ensure_ascii=False),
        "```",
        "",
        "## Checks",
        "",
        "```json",
        json.dumps(checks, indent=2, ensure_ascii=False, sort_keys=True),
        "```",
        "",
        "## 解释",
        "",
        "本 smoke 解决的是证据链中的一个窄缺口：证明 active-basis snapshot schema 不只是单元测试可行，也能通过真实 driver 日志、manifest、replay 和 impact dataset 传递到 candidate rows。",
        "",
        "它没有证明 production selector，也没有证明 5/10 full no-regression 或 20-task wall-time speedup。下一步仍需采集更多 no-certificate-effect exact-context snapshot rows，并重新做 context / instance / dataset selector holdout。",
        "",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke-root", type=Path, default=DEFAULT_SMOKE_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary = audit(args.smoke_root)
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    write_report(summary, args.report)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
