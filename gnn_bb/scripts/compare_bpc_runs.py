#!/usr/bin/env python3
"""Compare two clean-BPC result CSV files on proof/primal/pricing/RIM metrics."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any


FIELDS = [
    "status",
    "solving_time",
    "primal_bound",
    "dual_bound",
    "gap",
    "node_count",
    "pricing_calls",
    "exact_pricing_calls",
    "label_pops",
    "generated_labels",
    "restricted_master_integer_calls",
    "restricted_master_integer_rejected",
    "restricted_master_adaptive_skips",
    "restricted_master_adaptive_gap_skips",
    "restricted_master_adaptive_gap_forced_probes",
    "branch_testing_time",
    "pricing_tailing_certificate_slow",
    "pricing_tailing_negative_search_slow",
    "pricing_tailing_degenerate",
    "pricing_stabilization_attempts",
    "pricing_stabilization_true_negative_routes",
    "selective_pricing_exact_calls_avoided",
    "selective_pricing_exact_calls_required",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare two clean-BPC CSV outputs by instance.")
    parser.add_argument("--base", required=True, help="Baseline CSV path.")
    parser.add_argument("--candidate", required=True, help="Candidate CSV path.")
    args = parser.parse_args()

    base = _read_csv(Path(args.base))
    candidate = _read_csv(Path(args.candidate))
    instances = sorted(set(base) | set(candidate))
    headers = ["instance", "field", "base", "candidate", "delta"]
    widths = [len(item) for item in headers]
    rows: list[list[str]] = []
    for instance in instances:
        brow = base.get(instance, {})
        crow = candidate.get(instance, {})
        for field in FIELDS:
            bvalue = brow.get(field, "")
            cvalue = crow.get(field, "")
            delta = _delta(bvalue, cvalue)
            row = [instance, field, _fmt(bvalue), _fmt(cvalue), delta]
            widths = [max(width, len(cell)) for width, cell in zip(widths, row)]
            rows.append(row)
    print("  ".join(header.ljust(width) for header, width in zip(headers, widths)))
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print("  ".join(cell.ljust(width) for cell, width in zip(row, widths)))
    return 0


def _read_csv(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return {str(row.get("instance") or path.stem): row for row in csv.DictReader(handle)}


def _number(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"none", "nan"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _delta(base: Any, candidate: Any) -> str:
    bnum = _number(base)
    cnum = _number(candidate)
    if bnum is None or cnum is None:
        return ""
    return f"{cnum - bnum:.6g}"


def _fmt(value: Any) -> str:
    num = _number(value)
    if num is None:
        return "" if value is None else str(value)
    return f"{num:.6g}"


if __name__ == "__main__":
    raise SystemExit(main())
