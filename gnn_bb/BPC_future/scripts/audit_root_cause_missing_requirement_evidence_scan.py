#!/usr/bin/env python3
"""Scan result summaries for claims that missing root-cause requirements passed.

This diagnostic-only audit protects the active goal from being marked complete
because of a forgotten or stale result artifact.  It recursively scans
``BPC_future/results/**/summary.json`` for machine fields that would imply one
of the three blocking requirements is already satisfied.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_RESULTS_ROOT = Path("BPC_future/results")
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_missing_requirement_evidence_scan_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_missing_requirement_evidence_scan_zh.md"
)

TARGET_KEYS = [
    "goal_complete",
    "should_mark_goal_complete",
    "production_direction_proven",
    "has_full_5_10_production_ab_evidence",
    "has_production_validated_selector",
    "production_selector_validated",
    "approved_production_direction_count",
    "has_20_walltime_speedup_evidence",
]


def _is_scan_count_metadata_path(json_path: str) -> bool:
    """Ignore this audit's own count dictionaries when nested in ledgers."""
    return (
        ".target_key_seen_counts." in f".{json_path}."
        or ".target_key_positive_counts." in f".{json_path}."
    )


def _is_positive_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value > 0
    if isinstance(value, str):
        return value.strip().lower() in {"true", "yes", "passed", "complete"}
    return False


def _scan_object(path: Path, obj: Any, prefix: str = "") -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            child_path = f"{prefix}.{key}" if prefix else str(key)
            if key in TARGET_KEYS and not _is_scan_count_metadata_path(child_path):
                claims.append(
                    {
                        "path": str(path),
                        "json_path": child_path,
                        "key": key,
                        "value": value,
                        "positive": _is_positive_value(value),
                    }
                )
            if isinstance(value, (dict, list)):
                claims.extend(_scan_object(path, value, child_path))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            if isinstance(value, (dict, list)):
                claims.extend(_scan_object(path, value, f"{prefix}[{index}]"))
    return claims


def build_summary(*, results_root: Path, output_dir: Path) -> dict[str, Any]:
    summary_paths = sorted(results_root.rglob("summary.json"))
    output_summary = output_dir / "summary.json"
    claims: list[dict[str, Any]] = []
    unreadable: list[str] = []
    for path in summary_paths:
        if path == output_summary:
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            unreadable.append(str(path))
            continue
        claims.extend(_scan_object(path, data))

    positive_claims = [claim for claim in claims if claim["positive"]]
    seen_counts = {key: 0 for key in TARGET_KEYS}
    positive_counts = {key: 0 for key in TARGET_KEYS}
    for claim in claims:
        seen_counts[claim["key"]] += 1
        if claim["positive"]:
            positive_counts[claim["key"]] += 1

    checks = {
        "results_root_exists": results_root.exists(),
        "summary_files_present": bool(summary_paths),
        "no_unreadable_summaries": not unreadable,
        "target_fields_observed": any(seen_counts.values()),
        "no_positive_missing_requirement_claims": not positive_claims,
    }
    return {
        "schema_version": "root_cause_missing_requirement_evidence_scan_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "root_cause_missing_requirement_evidence_scan_audited",
        "results_root": str(results_root),
        "summary_file_count": len(summary_paths),
        "scanned_summary_file_count": len(summary_paths)
        - (1 if output_summary in summary_paths else 0),
        "target_key_seen_counts": seen_counts,
        "target_key_positive_counts": positive_counts,
        "candidate_claim_count": len(claims),
        "positive_claim_count": len(positive_claims),
        "positive_claims": positive_claims[:50],
        "unreadable_summaries": unreadable[:50],
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }


def write_report(summary: dict[str, Any], report_path: Path) -> None:
    lines = [
        "# BPC_future Missing Requirement Evidence Scan 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告扫描 `BPC_future/results/**/summary.json`，检查是否存在已经声称",
        "三项阻塞要求通过的机器字段。它只读 summary，不运行 BPC / pricing / RMP / Pulse，",
        "也不改变 solver 行为。",
        "",
        "## 机器字段",
        "",
        "```text",
        "root_cause_missing_requirement_evidence_scan = current",
        "diagnostic_only = true",
        "runs_bpc_or_pricing = false",
        f"status = {summary['status']}",
        f"summary_file_count = {summary['summary_file_count']}",
        f"scanned_summary_file_count = {summary['scanned_summary_file_count']}",
        f"candidate_claim_count = {summary['candidate_claim_count']}",
        f"positive_claim_count = {summary['positive_claim_count']}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 结论",
        "",
    ]
    if summary["positive_claim_count"] == 0:
        lines.append(
            "当前 results 机器摘要中没有任何字段声称 `goal_complete`、"
            "`production_direction_proven`、`production_validated_selector`、"
            "`5/10 full no-regression` 或 `20 walltime speedup` 已经通过。"
        )
    else:
        lines.append(
            "发现正向完成声明，必须人工复核后才能继续保持当前 missing requirement 结论。"
        )
    lines.extend(
        [
            "",
            "## Target Key Seen Counts",
            "",
            "```json",
            json.dumps(
                summary["target_key_seen_counts"],
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            "```",
            "",
            "## Target Key Positive Counts",
            "",
            "```json",
            json.dumps(
                summary["target_key_positive_counts"],
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            "```",
            "",
            "## Positive Claims",
            "",
            "```json",
            json.dumps(summary["positive_claims"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Checks",
            "",
            "```json",
            json.dumps(summary["checks"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    summary = build_summary(results_root=args.results_root, output_dir=args.output_dir)
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
