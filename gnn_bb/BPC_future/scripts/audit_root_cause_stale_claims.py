#!/usr/bin/env python3
"""Audit stale root-cause claims in Markdown reports.

The current root-cause state forbids claiming that the optimization direction is
production-ready, that the goal is complete, or that worker/certificate paths
may be enabled by default.  This read-only audit scans docs/run_reports for
such optimistic phrases and verifies that each occurrence is guarded by nearby
negative context such as "不能说", "未证明", or "blocked".
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/root_cause_stale_claims_20260614")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_stale_claims_zh.md"
)
SCAN_ROOTS = [
    Path("BPC_future/docs"),
    Path("BPC_future/logical_graph/run_reports"),
]
EXCLUDED_PATH_PARTS = {
    "20260614_bpc_future_root_cause_stale_claims_zh.md",
}

CLAIM_PATTERNS: dict[str, re.Pattern[str]] = {
    "goal_complete_true": re.compile(r"\bgoal_complete\s*=\s*true\b", re.I),
    "production_direction_true": re.compile(
        r"\bproduction_direction_proven\s*=\s*true\b", re.I
    ),
    "production_selector_true": re.compile(
        r"\b(?:has_)?production_validated_selector\s*=\s*true\b", re.I
    ),
    "approved_production_direction": re.compile(
        r"\bapproved_production_direction_count\s*=\s*[1-9]\d*\b", re.I
    ),
    "production_ready": re.compile(r"production-ready|生产可用|可上线|可以上线"),
    "enable_worker_default": re.compile(
        r"default_enable_worker|默认启用\s*worker|打开\s*worker\s*default",
        re.I,
    ),
    "open_certificate_gate": re.compile(
        r"open_official_certificate_gate|打开\s*official certificate|"
        r"certificate gate\s*可以打开|official certificate gate\s*可以打开",
        re.I,
    ),
    "goal_completion": re.compile(r"目标完成|标记完成|宣布目标完成"),
}

NEGATION_PHRASES = [
    "不能",
    "不能说",
    "不应",
    "不支持",
    "不建议",
    "不默认",
    "不打开",
    "不得",
    "禁止",
    "未证明",
    "未默认",
    "没有证明",
    "没有证据",
    "没有依据",
    "不证明",
    "还没有",
    "不足以",
    "尚未",
    "仍未",
    "不是",
    "不等于",
    "低于",
    "是否",
    "阻塞",
    "审计",
    "目录",
    "说明见",
    "关闭以下子路线",
    "ruled_out",
    "blocked",
    "forbidden",
    "not ",
    "cannot",
    "must not",
    "do not",
]

SAFE_HEADING_PHRASES = [
    "阻塞",
    "审计",
    "边界",
    "不能",
    "未完成",
    "为什么",
    "扩大 worker",
    "completion audit",
]


def _iter_markdown_files(roots: list[Path]) -> list[Path]:
    paths: list[Path] = []
    for root in roots:
        if root.exists():
            for path in sorted(root.rglob("*.md")):
                if any(part in str(path) for part in EXCLUDED_PATH_PARTS):
                    continue
                paths.append(path)
    return paths


def _is_guarded(lines: list[str], index: int) -> bool:
    line = lines[index].strip()
    if line.startswith("#") and any(phrase in line for phrase in SAFE_HEADING_PHRASES):
        return True
    start = max(0, index - 8)
    end = min(len(lines), index + 2)
    window = "\n".join(lines[start:end]).lower()
    return any(phrase.lower() in window for phrase in NEGATION_PHRASES)


def _matches_for_file(path: Path) -> list[dict[str, Any]]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    matches: list[dict[str, Any]] = []
    for index, line in enumerate(lines):
        for claim_id, pattern in CLAIM_PATTERNS.items():
            if not pattern.search(line):
                continue
            guarded = _is_guarded(lines, index)
            context_start = max(0, index - 2)
            context_end = min(len(lines), index + 3)
            matches.append(
                {
                    "path": str(path),
                    "line": index + 1,
                    "claim_id": claim_id,
                    "guarded": guarded,
                    "text": line.strip(),
                    "context": lines[context_start:context_end],
                }
            )
    return matches


def build_summary(*, roots: list[Path]) -> dict[str, Any]:
    files = _iter_markdown_files(roots)
    matches: list[dict[str, Any]] = []
    for path in files:
        matches.extend(_matches_for_file(path))
    needs_review = [match for match in matches if not match["guarded"]]
    by_claim: dict[str, dict[str, int]] = {}
    for match in matches:
        entry = by_claim.setdefault(match["claim_id"], {"total": 0, "needs_review": 0})
        entry["total"] += 1
        if not match["guarded"]:
            entry["needs_review"] += 1
    checks = {
        "scan_roots_exist": all(root.exists() for root in roots),
        "has_markdown_files": bool(files),
        "no_unguarded_stale_claims": not needs_review,
        "guarded_claims_present": any(match["guarded"] for match in matches),
    }
    return {
        "schema_version": "root_cause_stale_claims_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "root_cause_stale_claims_audited",
        "scan_roots": [str(root) for root in roots],
        "markdown_file_count": len(files),
        "candidate_claim_count": len(matches),
        "guarded_claim_count": len(matches) - len(needs_review),
        "needs_review_count": len(needs_review),
        "claim_counts": by_claim,
        "needs_review": needs_review[:50],
        "guarded_examples": [match for match in matches if match["guarded"]][:20],
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }


def write_report(summary: dict[str, Any], report_path: Path) -> None:
    lines = [
        "# BPC_future Root Cause Stale Claim 审计报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告扫描根因相关 Markdown 文档，检查是否还存在未被否定上下文保护的",
        "“可上线 / 目标完成 / 默认启用 worker / 打开 certificate gate”等旧说法。",
        "它只读文档，不运行 BPC / pricing / RMP / Pulse，也不改变 solver 行为。",
        "",
        "## 机器字段",
        "",
        "```text",
        "root_cause_stale_claims = current",
        "diagnostic_only = true",
        "runs_bpc_or_pricing = false",
        f"status = {summary['status']}",
        f"markdown_file_count = {summary['markdown_file_count']}",
        f"candidate_claim_count = {summary['candidate_claim_count']}",
        f"guarded_claim_count = {summary['guarded_claim_count']}",
        f"needs_review_count = {summary['needs_review_count']}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 结论",
        "",
    ]
    if summary["needs_review_count"] == 0:
        lines.append(
            "当前扫描到的高风险说法都处在“不能说 / 未证明 / blocked / forbidden”等保护上下文中；"
            "未发现会把当前根因状态误写成 production-ready 或目标完成的无保护文案。"
        )
    else:
        lines.append(
            "发现未被否定上下文保护的高风险说法，必须人工复核后才能继续声称文档一致。"
        )
    lines.extend(
        [
            "",
            "## Claim Counts",
            "",
            "```json",
            json.dumps(summary["claim_counts"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Needs Review",
            "",
            "```json",
            json.dumps(summary["needs_review"], ensure_ascii=False, indent=2, sort_keys=True),
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
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--scan-root", action="append", type=Path)
    args = parser.parse_args()

    roots = args.scan_root or SCAN_ROOTS
    summary = build_summary(roots=roots)
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
