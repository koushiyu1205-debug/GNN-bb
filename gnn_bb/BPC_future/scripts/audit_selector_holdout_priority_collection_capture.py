#!/usr/bin/env python3
"""Audit priority selector holdout active-basis capture outputs.

This is the fixed entrypoint for the priority collection runbook.  It reuses
the generic collection-capture audit logic but points at the priority runbook
and priority capture-output paths.  It only reads JSONL/summary files; it does
not run BPC, pricing, RMP, Pulse, workers, or certificates.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from BPC_future.scripts.audit_selector_holdout_collection_capture import (
    audit_capture,
    write_report as write_generic_report,
)


DEFAULT_RUNBOOK = Path(
    "BPC_future/results/"
    "root_cause_selector_holdout_priority_collection_runbook_20260614/"
    "summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/"
    "root_cause_selector_holdout_priority_collection_capture_audit_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_holdout_priority_collection_capture_audit_zh.md"
)


def write_report(summary: dict[str, object], path: Path) -> None:
    write_generic_report(summary, path)
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "# Root Cause Selector Holdout Collection Capture Audit 报告",
        "# Root Cause Selector Holdout Priority Collection Capture Audit 报告",
    )
    text = text.replace(
        "root_cause_selector_holdout_collection_capture_audit = current",
        "root_cause_selector_holdout_priority_collection_capture_audit = current",
    )
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runbook", default=str(DEFAULT_RUNBOOK))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    summary = audit_capture(runbook_path=Path(args.runbook))
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
