#!/usr/bin/env python3
"""Audit accepted bad-mode rows in GAT batch-impact decision records.

This script is diagnostic-only. It reads already-produced Stage 3 decision
records and checks the deployment-facing hard gate:
``accepted_bad_mode_count <= max_accepted_bad_mode_count``.
It does not run BPC, pricing, RMP, workers, or certificate logic.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import json
from pathlib import Path
from typing import Any


DEFAULT_DECISION_RECORDS = Path(
    "BPC_future/results/gat_batch_impact_knn_ood_audit_v12_coverage_aware_scale_20260616/"
    "decision_records.jsonl"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/gat_accepted_bad_mode_gate_v12_scale_20260616"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260616_bpc_future_gat_target_mode_stage3_v12_accepted_bad_mode_gate_audit_zh.md"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decision-records", type=Path, default=DEFAULT_DECISION_RECORDS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--max-accepted-bad-mode-count", type=int, default=0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = audit_accepted_bad_mode_gate(
        decision_records=Path(args.decision_records),
        output_dir=Path(args.output_dir),
        report=Path(args.report),
        max_accepted_bad_mode_count=max(0, int(args.max_accepted_bad_mode_count)),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def audit_accepted_bad_mode_gate(
    *,
    decision_records: Path = DEFAULT_DECISION_RECORDS,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    max_accepted_bad_mode_count: int = 0,
) -> dict[str, Any]:
    records = _read_jsonl(Path(decision_records))
    total = len(records)
    accepted = [record for record in records if _is_high_priority_decision(record)]
    bad_mode = [record for record in records if _is_bad_mode(record)]
    accepted_bad = [record for record in accepted if _is_bad_mode(record)]
    accepted_good = [record for record in accepted if not _is_bad_mode(record)]
    gate_pass = len(accepted_bad) <= int(max_accepted_bad_mode_count)

    by_split = _count_by(records, "decision_split")
    accepted_bad_by_split = _count_by(accepted_bad, "decision_split")
    accepted_bad_by_family = _count_by(accepted_bad, "instance_family")
    accepted_bad_by_scope = _count_by(accepted_bad, "threshold_scope")
    accepted_bad_examples = [_record_sample(record) for record in accepted_bad[:10]]

    summary = {
        "schema_version": "gat_accepted_bad_mode_gate_audit_v1",
        "status": "accepted_bad_mode_gate_audited",
        "decision_records": str(decision_records),
        "output_dir": str(output_dir),
        "report": str(report),
        "decision_record_count": int(total),
        "high_priority_decision_count": int(len(accepted)),
        "bad_mode_record_count": int(len(bad_mode)),
        "accepted_bad_mode_count": int(len(accepted_bad)),
        "accepted_good_mode_count": int(len(accepted_good)),
        "max_accepted_bad_mode_count": int(max_accepted_bad_mode_count),
        "accepted_bad_mode_gate_pass": bool(gate_pass),
        "accepted_bad_mode_by_split": dict(sorted(accepted_bad_by_split.items())),
        "accepted_bad_mode_by_family": dict(sorted(accepted_bad_by_family.items())),
        "accepted_bad_mode_by_threshold_scope": dict(sorted(accepted_bad_by_scope.items())),
        "decision_records_by_split": dict(sorted(by_split.items())),
        "accepted_bad_mode_examples": accepted_bad_examples,
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "default_enabled": False,
        "selector_is_pricing_oracle": False,
        "selector_can_certificate": False,
        "official_bound_effect": False,
        "gate_can_permanently_discard_negative_columns": False,
        "all_checks_pass": bool(gate_pass),
    }
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(Path(report), summary)
    return summary


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            payload = json.loads(text)
            if not isinstance(payload, dict):
                raise ValueError(f"decision record is not an object: {path}")
            rows.append(payload)
    return rows


def _is_high_priority_decision(record: dict[str, Any]) -> bool:
    if str(record.get("decision_name") or "").upper() == "HIGH_PRIORITY":
        return True
    if str(record.get("decision") or "") == "1":
        return True
    return False


def _is_bad_mode(record: dict[str, Any]) -> bool:
    return int(record.get("bad_mode_switch") or record.get("label_bad_mode_switch") or 0) == 1


def _count_by(records: list[dict[str, Any]], field: str) -> Counter[str]:
    return Counter(str(record.get(field) or "unknown") for record in records)


def _record_sample(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "row_index": record.get("row_index"),
        "decision_split": record.get("decision_split"),
        "instance": record.get("instance"),
        "instance_family": record.get("instance_family"),
        "instance_task_count": record.get("instance_task_count"),
        "context_hash": record.get("context_hash"),
        "decision_name": record.get("decision_name"),
        "decision_reason": record.get("decision_reason"),
        "accepted_batch_roi_label": record.get("accepted_batch_roi_label"),
        "batch_score": record.get("batch_score"),
        "batch_threshold": record.get("batch_threshold"),
        "candidate_predicted_high_priority_count": record.get(
            "candidate_predicted_high_priority_count"
        ),
        "candidate_false_high_priority_on_delay_count": record.get(
            "candidate_false_high_priority_on_delay_count"
        ),
    }


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# BPC_future GAT Accepted Bad-mode Gate Audit 报告",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 结论",
        "",
        "本报告只读 Stage 3 decision records，检查 HIGH_PRIORITY decision 中是否包含",
        "bad-mode batch。它不运行 BPC / pricing / RMP，不改变 admission，也不产生 certificate。",
        "",
        "```text",
        f"decision_record_count = {summary['decision_record_count']}",
        f"high_priority_decision_count = {summary['high_priority_decision_count']}",
        f"bad_mode_record_count = {summary['bad_mode_record_count']}",
        f"accepted_bad_mode_count = {summary['accepted_bad_mode_count']}",
        f"max_accepted_bad_mode_count = {summary['max_accepted_bad_mode_count']}",
        f"accepted_bad_mode_gate_pass = {str(summary['accepted_bad_mode_gate_pass']).lower()}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 判定",
        "",
        "训练 gate 的默认硬约束是 `accepted_bad_mode_count = 0`。如果这里失败，",
        "对应 checkpoint / safe-source 只能保留为 diagnostic，不能升级为 Stage 4 candidate。",
        "",
        "## Exactness Boundary",
        "",
        "```text",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"selector_is_pricing_oracle = {str(summary['selector_is_pricing_oracle']).lower()}",
        f"selector_can_certificate = {str(summary['selector_can_certificate']).lower()}",
        f"official_bound_effect = {str(summary['official_bound_effect']).lower()}",
        f"gate_can_permanently_discard_negative_columns = {str(summary['gate_can_permanently_discard_negative_columns']).lower()}",
        "```",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
