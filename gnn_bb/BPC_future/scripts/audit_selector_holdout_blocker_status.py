"""Audit why selector holdout is still blocked.

This diagnostic-only script reads existing root-cause summaries.  It does not
run BPC, pricing, RMP, Pulse, workers, certificates, or benchmarks.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_GAP_MATRIX = Path(
    "BPC_future/results/root_cause_selector_holdout_gap_matrix_20260614/"
    "summary.json"
)
DEFAULT_COLLECTION_CAPTURE_AUDIT = Path(
    "BPC_future/results/root_cause_selector_holdout_collection_capture_audit_20260614/"
    "summary.json"
)
DEFAULT_PRIORITY_CAPTURE_AUDIT = Path(
    "BPC_future/results/"
    "root_cause_selector_holdout_priority_collection_capture_audit_20260614/"
    "summary.json"
)
DEFAULT_PRODUCTION_GATE = Path(
    "BPC_future/results/root_cause_production_ab_entry_gate_catalog_20260614/"
    "summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_holdout_blocker_status_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_holdout_blocker_status_zh.md"
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _label_count(section: dict[str, Any], label: str) -> int:
    counts = section.get("label_counts")
    if not isinstance(counts, dict):
        counts = section.get("complete_snapshot_label_counts")
    if not isinstance(counts, dict):
        counts = section.get("complete_snapshot_and_explicit_forbidden_label_counts")
    return int(counts.get(label, 0)) if isinstance(counts, dict) else 0


def _capture_metrics(summary: dict[str, Any]) -> dict[str, Any]:
    expected = int(summary.get("expected_context_hash_count", 0) or 0)
    hit = int(summary.get("expected_context_hit_count", 0) or 0)
    complete_hit = int(summary.get("expected_context_complete_hit_count", 0) or 0)
    missing = int(summary.get("missing_expected_context_count", 0) or 0)
    missing_complete = int(summary.get("missing_expected_complete_context_count", 0) or 0)
    return {
        "all_checks_pass": summary.get("all_checks_pass") is True,
        "ready_for_selector_holdout": summary.get("ready_for_selector_holdout") is True,
        "command_count": int(summary.get("command_count", 0) or 0),
        "capture_event_count": int(summary.get("capture_event_count", 0) or 0),
        "expected_context_hash_count": expected,
        "expected_context_hit_count": hit,
        "expected_context_complete_hit_count": complete_hit,
        "missing_expected_context_count": missing,
        "missing_expected_complete_context_count": missing_complete,
        "active_basis_bad_count": int(summary.get("active_basis_bad_count", 0) or 0),
        "no_certificate_bad_count": int(summary.get("no_certificate_bad_count", 0) or 0),
    }


def build_summary(
    *,
    gap_matrix_path: Path,
    collection_capture_audit_path: Path,
    priority_capture_audit_path: Path,
    production_gate_path: Path,
) -> dict[str, Any]:
    gap = _read_json(gap_matrix_path)
    collection = _read_json(collection_capture_audit_path)
    priority = _read_json(priority_capture_audit_path)
    production = _read_json(production_gate_path)

    base = gap.get("source_summaries", {}).get("base_replay_selector", {})
    complete_snapshot = gap.get("complete_snapshot_total", {})
    complete_snapshot_mix = gap.get("complete_snapshot_context_label_mix", {})
    complete_explicit = gap.get("complete_explicit_forbidden_total", {})
    complete_explicit_mix = gap.get(
        "complete_explicit_forbidden_context_label_mix", {}
    )
    selector_ready_proxy = gap.get("selector_ready_proxy_total", {})
    gap_items = list(gap.get("gap_items", []))

    collection_metrics = _capture_metrics(collection)
    priority_metrics = _capture_metrics(priority)
    raw_entry_blockers = production.get("entry_gate_blockers", [])
    entry_blockers = [
        str(item.get("blocker_id", ""))
        if isinstance(item, dict)
        else str(item)
        for item in raw_entry_blockers
        if item
    ]
    if not entry_blockers:
        entry_blockers = [
            str(item.get("blocker_id", ""))
            for item in production.get("blockers", [])
            if item.get("blocker_id")
        ]

    complete_snapshot_noops = _label_count(complete_snapshot, "noop")
    complete_snapshot_improved = _label_count(complete_snapshot, "improved")
    complete_explicit_noops = _label_count(complete_explicit, "noop")
    complete_explicit_improved = _label_count(complete_explicit, "improved")

    checks = {
        "gap_matrix_passed": gap.get("all_checks_pass") is True,
        "gap_matrix_has_blocking_items": any(
            item.get("status") == "blocking" for item in gap_items
        ),
        "collection_capture_audit_passed": collection_metrics["all_checks_pass"],
        "priority_capture_audit_passed": priority_metrics["all_checks_pass"],
        "captures_have_no_certificate_effect": (
            collection_metrics["no_certificate_bad_count"] == 0
            and priority_metrics["no_certificate_bad_count"] == 0
        ),
        "captures_have_complete_active_basis_payload": (
            collection_metrics["active_basis_bad_count"] == 0
            and priority_metrics["active_basis_bad_count"] == 0
        ),
        "collection_not_ready_for_selector_holdout": (
            collection_metrics["ready_for_selector_holdout"] is False
            and collection_metrics["missing_expected_context_count"] > 0
        ),
        "priority_not_ready_for_selector_holdout": (
            priority_metrics["ready_for_selector_holdout"] is False
            and priority_metrics["missing_expected_context_count"] > 0
        ),
        "base_rows_lack_full_snapshot": (
            int(base.get("row_count", 0) or 0) > 0
            and int(base.get("complete_snapshot_row_count", 0) or 0) == 0
        ),
        "complete_snapshot_label_mix_too_sparse": (
            int(complete_snapshot.get("complete_snapshot_row_count", 0) or 0) > 0
            and complete_snapshot_noops <= 3
            and int(complete_snapshot_mix.get("mixed_label_context_count", 0) or 0)
            == 0
        ),
        "complete_explicit_forbidden_positive_only": (
            int(
                complete_explicit.get(
                    "complete_snapshot_and_explicit_forbidden_row_count", 0
                )
                or 0
            )
            > 0
            and complete_explicit_improved > 0
            and complete_explicit_noops == 0
            and int(complete_explicit_mix.get("mixed_label_context_count", 0) or 0)
            == 0
        ),
        "production_ab_gate_blocked": (
            production.get("all_checks_pass") is True
            and set(
                [
                    "selector_not_validated",
                    "five_ten_full_no_regression_missing",
                    "twenty_speedup_missing",
                ]
            ).issubset(set(entry_blockers))
        ),
    }
    all_checks_pass = all(checks.values())

    return {
        "schema_version": "selector_holdout_blocker_status_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "selector_holdout_blocked_by_snapshot_label_mix",
        "all_checks_pass": all_checks_pass,
        "checks": checks,
        "source_paths": {
            "gap_matrix": str(gap_matrix_path),
            "collection_capture_audit": str(collection_capture_audit_path),
            "priority_capture_audit": str(priority_capture_audit_path),
            "production_gate": str(production_gate_path),
        },
        "capture_status": {
            "collection": collection_metrics,
            "priority": priority_metrics,
        },
        "snapshot_label_mix": {
            "base_selector_rows": {
                "row_count": int(base.get("row_count", 0) or 0),
                "complete_snapshot_row_count": int(
                    base.get("complete_snapshot_row_count", 0) or 0
                ),
                "label_counts": base.get("label_counts", {}),
            },
            "complete_snapshot": {
                "row_count": int(
                    complete_snapshot.get("complete_snapshot_row_count", 0) or 0
                ),
                "label_counts": complete_snapshot.get(
                    "complete_snapshot_label_counts", {}
                ),
                "context_mix": complete_snapshot_mix,
            },
            "complete_explicit_forbidden": {
                "row_count": int(
                    complete_explicit.get(
                        "complete_snapshot_and_explicit_forbidden_row_count", 0
                    )
                    or 0
                ),
                "label_counts": complete_explicit.get(
                    "complete_snapshot_and_explicit_forbidden_label_counts", {}
                ),
                "context_mix": complete_explicit_mix,
            },
            "selector_ready_proxy": {
                "row_count": int(selector_ready_proxy.get("row_count", 0) or 0),
                "label_counts": selector_ready_proxy.get("label_counts", {}),
                "context_count": selector_ready_proxy.get("context_count"),
            },
        },
        "blocking_gap_ids": [
            str(item.get("gap_id", ""))
            for item in gap_items
            if item.get("status") == "blocking"
        ],
        "production_entry_blockers": entry_blockers,
        "interpretation": (
            "Capture commands and active-basis payload checks pass, but selector "
            "production validation remains blocked because the full-snapshot data "
            "lacks mixed positive/noop contexts and explicit forbidden rows are "
            "positive-only. Calibration-only data collection can continue."
        ),
        "required_next_evidence": [
            "Collect no-certificate-effect full-snapshot rows for noop/false-positive contexts.",
            "Collect explicit forbidden/pool payloads that include both improved and noop rows.",
            "Do not enter production BPC A/B until selector passes context/instance/dataset holdouts.",
        ],
    }


def write_report(summary: dict[str, Any], report_path: Path) -> None:
    collection = summary["capture_status"]["collection"]
    priority = summary["capture_status"]["priority"]
    mix = summary["snapshot_label_mix"]
    lines = [
        "# Selector Holdout Blocker Status 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 结论",
        "",
        "当前不是没有采集入口，也不是采集命令不安全；阻塞点是 production selector validation 所需的 full-snapshot 标签覆盖仍不够。",
        "",
        "```text",
        f"status = {summary['status']}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "runs_bpc_or_pricing = false",
        "diagnostic_only = true",
        "```",
        "",
        "## 已确认安全的部分",
        "",
        f"- 普通 collection capture：`command_count={collection['command_count']}`，`capture_event_count={collection['capture_event_count']}`，`no_certificate_bad_count={collection['no_certificate_bad_count']}`，`active_basis_bad_count={collection['active_basis_bad_count']}`；",
        f"- priority capture：`command_count={priority['command_count']}`，`capture_event_count={priority['capture_event_count']}`，`no_certificate_bad_count={priority['no_certificate_bad_count']}`，`active_basis_bad_count={priority['active_basis_bad_count']}`；",
        "- 两类 capture 都没有 certificate / official bound effect；",
        "- 两类 capture 的 active-basis payload 检查通过。",
        "",
        "## 仍然阻塞的部分",
        "",
        f"- 普通 collection expected contexts：`{collection['expected_context_hit_count']}/{collection['expected_context_hash_count']}` hit，`missing_expected_context_count={collection['missing_expected_context_count']}`；",
        f"- priority expected contexts：`{priority['expected_context_hit_count']}/{priority['expected_context_hash_count']}` hit，`missing_expected_context_count={priority['missing_expected_context_count']}`；",
        f"- base selector rows：`row_count={mix['base_selector_rows']['row_count']}`，但 `complete_snapshot_row_count={mix['base_selector_rows']['complete_snapshot_row_count']}`；",
        f"- complete snapshot rows：`row_count={mix['complete_snapshot']['row_count']}`，`label_counts={mix['complete_snapshot']['label_counts']}`，即 `59 improved / 3 noop`，且 mixed-label context 为 `0`；",
        f"- complete explicit forbidden rows：`row_count={mix['complete_explicit_forbidden']['row_count']}`，`label_counts={mix['complete_explicit_forbidden']['label_counts']}`，即 `48 improved / 0 noop`，仍是 positive-only；",
        "",
        "## 对根因判断的影响",
        "",
        "这进一步收紧了当前根因：我们已经能安全采集 active-basis / pool / forbidden payload，但 production selector 仍缺负例/混合 context 的 full-snapshot 覆盖。",
        "",
        "因此下一步可以继续做 calibration-only 数据补齐，但不能直接进入 production BPC A/B，也不能把现有 selector、Pulse worker 或 return policy 当成主线优化。",
        "",
        "production selector validation 与 production BPC A/B 仍被阻塞。需要先补齐：",
        "",
        "1. no-certificate-effect full-snapshot 的 noop / false-positive contexts；",
        "2. explicit forbidden / pool payload 下同时包含 improved 和 noop 的 rows；",
        "3. context / instance / dataset holdout 全部通过后的 selector。",
        "",
        "在这些证据之前，当前目标仍保持 active，不能宣称 5/10 no-regression 与 20-task wall-time speedup 已被证明。",
        "",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gap-matrix", type=Path, default=DEFAULT_GAP_MATRIX)
    parser.add_argument(
        "--collection-capture-audit",
        type=Path,
        default=DEFAULT_COLLECTION_CAPTURE_AUDIT,
    )
    parser.add_argument(
        "--priority-capture-audit",
        type=Path,
        default=DEFAULT_PRIORITY_CAPTURE_AUDIT,
    )
    parser.add_argument("--production-gate", type=Path, default=DEFAULT_PRODUCTION_GATE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    summary = build_summary(
        gap_matrix_path=args.gap_matrix,
        collection_capture_audit_path=args.collection_capture_audit,
        priority_capture_audit_path=args.priority_capture_audit,
        production_gate_path=args.production_gate,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.output_dir / "summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    write_report(summary, args.report)
    print(json.dumps(summary, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
