#!/usr/bin/env python3
"""Merge B4.1 partition proof probes without rerunning solved regions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lunar_ice_bpc.runners.b4_1_true_dual_proof_tail import (  # noqa: E402
    _first_int,
    _partition_best_rows_by_region,
    _partition_probe_summary,
    write_b4_1_required_task_set_partition_probe,
)


def _canonical_task_set(row: object) -> tuple[str, ...]:
    if not isinstance(row, (list, tuple, set)):
        return tuple()
    return tuple(sorted(str(item) for item in row))


def _total_task_count(payloads: list[dict], rows: list[dict]) -> int:
    for row in rows:
        value = _first_int(row.get("task_count"))
        if value is not None and value > 0:
            return int(value)
    for payload in payloads:
        summary = payload.get("summary")
        if isinstance(summary, dict):
            value = _first_int(summary.get("residual_task_count_region_expected_count"))
            if value is not None and value > 0:
                return int(value)
    for payload in payloads:
        diagnostic = payload.get("taskset_diagnostic")
        if isinstance(diagnostic, dict):
            frequency = diagnostic.get("task_frequency")
            if isinstance(frequency, dict) and frequency:
                return len(frequency)
    return 0


def merge_partition_probes(paths: list[Path]) -> dict:
    payloads = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    if not payloads:
        raise ValueError("at least one partition probe is required")
    rows: list[dict] = []
    task_sets: set[tuple[str, ...]] = set()
    for payload in payloads:
        for row in payload.get("target_task_sets") or []:
            task_set = _canonical_task_set(row)
            if task_set:
                task_sets.add(task_set)
        rows.extend(item for item in (payload.get("rows") or []) if isinstance(item, dict))
    if not rows:
        raise ValueError("input probes did not contain any region rows")
    best_rows = list(_partition_best_rows_by_region(rows).values())
    first = payloads[0]
    first_summary = first.get("summary") if isinstance(first.get("summary"), dict) else {}
    negative_eps = float(first_summary.get("negative_eps") or 1.0e-6)
    total_task_count = _total_task_count(payloads, best_rows)
    sorted_task_sets = sorted(task_sets)
    summary = _partition_probe_summary(
        best_rows,
        task_sets=sorted_task_sets,
        negative_eps=negative_eps,
        total_task_count=total_task_count,
    )
    return {
        "schema_version": "lunar_ice_bpc.b4_1_required_task_set_partition_probe_merged.v1",
        "source_probe_json": first.get("source_probe_json") or "",
        "merged_from_probe_jsons": [str(path) for path in paths],
        "instance_id": first.get("instance_id") or "",
        "diagnostic_only": True,
        "official_certificate_allowed": False,
        "can_claim_certificate": False,
        "target_task_sets": [list(row) for row in sorted_task_sets],
        "target_task_set_count": len(sorted_task_sets),
        "rows": best_rows,
        "row_count": len(best_rows),
        "raw_input_row_count": len(rows),
        "taskset_diagnostic": first.get("taskset_diagnostic") or {},
        "summary": summary,
        "redlines": {
            "certificate_claim_count": sum(1 for row in best_rows if row.get("can_claim_certificate") is True),
            "official_certificate_claim_count": sum(
                1 for row in best_rows if row.get("official_certificate_allowed") is True
            ),
            "full_space_certificate_claim_count": int(summary.get("can_claim_certificate") is True),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("probe_json", nargs="+")
    args = parser.parse_args(argv)
    output_dir = Path(args.output_dir)
    report = merge_partition_probes([Path(item) for item in args.probe_json])
    write_b4_1_required_task_set_partition_probe(
        report,
        summary_json=output_dir / "required_task_set_partition_probe.json",
        report_md=output_dir / "partition_probe_report_zh.md",
    )
    print(
        "Merged",
        len(args.probe_json),
        "B4.1 partition probe(s) into",
        output_dir / "required_task_set_partition_probe.json",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
