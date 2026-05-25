#!/usr/bin/env python3
"""中文摘要：汇总 clean BPC JSONL/CSV 日志，输出 hardness summary。"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bpc.perf_stats import HARDNESS_HELP, analyze_logs  # noqa: E402


CSV_FIELDS = [
    "instance",
    "status",
    "hardness_tags",
    "primal_bound",
    "dual_bound",
    "diagnostic_dual_bound",
    "gap",
    "diagnostic_gap",
    "root_relaxation",
    "initial_incumbent",
    "root_gap",
    "time_to_first_incumbent",
    "time_to_best_incumbent",
    "rmp_solves",
    "pricing_calls",
    "exact_pricing_calls",
    "label_pops",
    "generated_labels",
    "best_reduced_cost",
    "added_routes",
    "certified_pricing_calls",
    "restricted_master_rejected",
    "restricted_master_pair_conflict_cuts",
    "restricted_master_route_set_packing_cuts",
    "restricted_master_schedule_capacity_cuts",
    "restricted_master_no_good_cuts",
    "branch_candidate_count",
    "branch_lp_testing",
    "branch_heuristic_testing",
    "branch_testing_time",
    "open_nodes_remaining",
    "timeout_pending_node_certified",
    "official_bound_available",
    "source",
]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze clean BPC JSONL/CSV logs and classify instance hardness.",
        epilog=HARDNESS_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("paths", nargs="+", help="JSONL/CSV paths or glob patterns.")
    parser.add_argument("--csv", dest="csv_path", help="Write summary CSV to this path.")
    parser.add_argument("--json", dest="json_path", help="Write full summary JSON to this path.")
    parser.add_argument("--pretty", action="store_true", help="Print a compact table to stdout.")
    args = parser.parse_args()

    paths = _expand_paths(args.paths)
    if not paths:
        parser.error("no input logs matched")

    summaries = analyze_logs(paths)
    if args.csv_path:
        _write_csv(Path(args.csv_path), summaries)
    if args.json_path:
        Path(args.json_path).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_path).write_text(json.dumps(summaries, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    if args.pretty or (not args.csv_path and not args.json_path):
        _print_pretty(summaries)
    return 0


def _expand_paths(patterns: list[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        matches = glob.glob(pattern)
        if matches:
            paths.extend(Path(match) for match in matches)
        else:
            paths.append(Path(pattern))
    return [path for path in paths if path.exists()]


def _write_csv(path: Path, summaries: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for summary in summaries:
            row = {field: _cell(summary.get(field)) for field in CSV_FIELDS}
            row["hardness_tags"] = "|".join(summary.get("hardness_tags") or [])
            writer.writerow(row)


def _print_pretty(summaries: list[dict[str, Any]]) -> None:
    rows = []
    for summary in summaries:
        rows.append(
            [
                str(summary.get("instance")),
                str(summary.get("status")),
                ",".join(summary.get("hardness_tags") or []),
                _fmt(summary.get("root_relaxation")),
                _fmt(summary.get("primal_bound")),
                _fmt(summary.get("dual_bound")),
                _fmt(summary.get("diagnostic_gap")),
                str(summary.get("label_pops") or 0),
                str(summary.get("open_nodes_remaining") or 0),
                str(summary.get("timeout_pending_node_certified")),
            ]
        )
    headers = ["instance", "status", "tags", "root_lb", "primal", "dual", "diag_gap", "labels", "open", "pending_cert"]
    widths = [len(header) for header in headers]
    for row in rows:
        widths = [max(width, len(cell)) for width, cell in zip(widths, row)]
    print("  ".join(header.ljust(width) for header, width in zip(headers, widths)))
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print("  ".join(cell.ljust(width) for cell, width in zip(row, widths)))


def _cell(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return value


def _fmt(value: Any) -> str:
    if value is None:
        return ""
    try:
        return f"{float(value):.6g}"
    except (TypeError, ValueError):
        return str(value)


if __name__ == "__main__":
    raise SystemExit(main())

