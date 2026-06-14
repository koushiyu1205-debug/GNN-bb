#!/usr/bin/env python3
"""Audit component-payload addition-before candidate rows.

This diagnostic checks the offline chain:

capture JSONL -> ready-only replay manifest -> local RMP replay -> candidate rows

It does not run BPC, pricing, Pulse, branch-and-bound, or certificate logic.
The existing replay artifact may contain local RMP treatment labels, but the
feature coverage checked here is restricted to addition-before payload fields.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


DEFAULT_ROOT = Path(
    "BPC_future/results/root_cause_component_payload_addition_before_rows_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_component_payload_addition_before_rows_zh.md"
)
REQUIRED_ADDITION_BEFORE_FIELDS = (
    "active_basis_snapshot_complete_before",
    "pool_candidate_task_set_max_jaccard",
    "pool_candidate_task_freq_sum",
    "candidate_signature_in_pool",
    "candidate_forbidden_signature",
    "forbidden_signature_count_before",
    "forbidden_signature_payload_count_before",
    "forbidden_signature_payload_complete_before",
    "explicit_forbidden_signature_list_available",
    "returned_batch_size",
    "returned_batch_new_task_set_count",
    "returned_batch_forbidden_signature_count",
    "returned_candidate_true_rc_rank",
    "returned_batch_true_rc_gap_from_best",
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict, set)):
        return bool(value)
    return True


def build_summary(root: Path) -> dict[str, Any]:
    manifest = _read_json(root / "manifest_ready" / "summary.json")
    replay = _read_json(root / "replay_ready" / "summary.json")
    impact = _read_json(root / "impact" / "summary.json")
    candidate_rows_path = root / "impact" / "candidate_impact_rows.csv"
    rows = _read_csv(candidate_rows_path)
    field_nonempty_counts = {
        field: sum(1 for row in rows if _nonempty(row.get(field)))
        for field in REQUIRED_ADDITION_BEFORE_FIELDS
    }
    field_complete = {
        field: count == len(rows) and len(rows) > 0
        for field, count in field_nonempty_counts.items()
    }
    explicit_forbidden_true_count = sum(
        1
        for row in rows
        if str(row.get("explicit_forbidden_signature_list_available", "")).lower()
        == "true"
    )
    forbidden_complete_true_count = sum(
        1
        for row in rows
        if str(row.get("forbidden_signature_payload_complete_before", "")).lower()
        == "true"
    )
    checks = {
        "manifest_ready_only": manifest.get("ready_only") is True,
        "manifest_all_checks_pass": manifest.get("all_checks_pass") is True,
        "manifest_has_ready_cases": int(manifest.get("ready_case_count") or 0) > 0,
        "replay_all_checks_pass": replay.get("all_checks_pass") is True,
        "replay_no_certificate_effect": (
            replay.get("checks", {}).get("all_replay_is_no_certificate_effect") is True
        ),
        "impact_all_checks_pass": impact.get("all_checks_pass") is True,
        "candidate_rows_present": len(rows) > 0,
        "all_required_addition_before_fields_complete": all(field_complete.values()),
        "explicit_forbidden_payload_observed": explicit_forbidden_true_count == len(rows)
        and len(rows) > 0,
        "forbidden_payload_complete": forbidden_complete_true_count == len(rows)
        and len(rows) > 0,
        "diagnostic_not_production_selector": True,
    }
    return {
        "schema_version": "component_payload_addition_before_rows_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "runs_local_rmp_replay": True,
        "status": "component_payload_addition_before_rows_audited",
        "root": str(root),
        "manifest_summary": str(root / "manifest_ready" / "summary.json"),
        "replay_summary": str(root / "replay_ready" / "summary.json"),
        "impact_summary": str(root / "impact" / "summary.json"),
        "candidate_rows_csv": str(candidate_rows_path),
        "raw_capture_case_count": manifest.get("raw_case_count"),
        "ready_case_count": manifest.get("ready_case_count"),
        "candidate_row_count": len(rows),
        "high_impact_candidate_count": impact.get("high_impact_candidate_count"),
        "noop_candidate_count": impact.get("noop_candidate_count"),
        "field_nonempty_counts": field_nonempty_counts,
        "field_complete": field_complete,
        "explicit_forbidden_true_count": explicit_forbidden_true_count,
        "forbidden_complete_true_count": forbidden_complete_true_count,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "The targeted component capture can now be converted into "
            "addition-before candidate rows with active-basis, pool, returned-batch, "
            "and explicit forbidden-signature payload fields. This is calibration "
            "evidence only: it is not a production selector, BPC speedup proof, "
            "or certificate effect."
        ),
    }


def write_report(summary: dict[str, Any], report_path: Path) -> None:
    lines = [
        "# Root Cause Component Payload Addition-Before Rows 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告检查 target002 component payload 是否已经能转成可做 selector",
        "holdout 的 addition-before candidate rows。它只审计离线 manifest /",
        "local RMP replay / impact CSV，不运行 BPC、pricing、Pulse 或 certificate。",
        "",
        "## 机器字段",
        "",
        "```text",
        "component_payload_addition_before_rows = current",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"runs_local_rmp_replay = {str(summary['runs_local_rmp_replay']).lower()}",
        f"status = {summary['status']}",
        f"raw_capture_case_count = {summary['raw_capture_case_count']}",
        f"ready_case_count = {summary['ready_case_count']}",
        f"candidate_row_count = {summary['candidate_row_count']}",
        f"high_impact_candidate_count = {summary['high_impact_candidate_count']}",
        f"noop_candidate_count = {summary['noop_candidate_count']}",
        f"explicit_forbidden_true_count = {summary['explicit_forbidden_true_count']}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 字段覆盖",
        "",
        "```json",
        json.dumps(
            {
                "field_nonempty_counts": summary["field_nonempty_counts"],
                "field_complete": summary["field_complete"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## 解释",
        "",
        summary["interpretation"],
        "",
        "## 检查项",
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
    parser.add_argument("--root", default=str(DEFAULT_ROOT))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()
    root = Path(args.root)
    summary = build_summary(root)
    (root / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_report(summary, Path(args.report))
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
