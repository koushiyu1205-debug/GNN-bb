#!/usr/bin/env python3
"""Run B3 branch-and-price tree ablation matrix."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.runners.b3_branch_tree_ablation import (  # noqa: E402
    run_b3_branch_tree_ablation_matrix,
    write_b3_branch_tree_ablation_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="data/manifests/lunar_ice_sp50_real_benchmark_manifest.json")
    parser.add_argument("--rows-csv", default="runs/b3_branch_tree_ablation/b3_branch_tree_rows.csv")
    parser.add_argument("--summary-json", default="runs/b3_branch_tree_ablation/b3_branch_tree_summary.json")
    parser.add_argument("--report-md", default="runs/b3_branch_tree_ablation/b3_branch_tree_report_zh.md")
    parser.add_argument("--scale5-limit", type=int, default=20)
    parser.add_argument("--scale10-limit", type=int, default=5)
    parser.add_argument(
        "--scale20-probe-limit",
        type=int,
        default=5,
        help="Selected 20-scale direct20 diagnostic probe count. Use 0 to skip heavy probe rows.",
    )
    parser.add_argument("--fail-closed-max-direct-tasks", type=int, default=10)
    parser.add_argument("--b2-max-rounds", type=int, default=8)
    parser.add_argument("--b3-max-rounds-per-node", type=int, default=16)
    parser.add_argument("--max-tree-nodes", type=int, default=31)
    parser.add_argument("--max-branch-depth", type=int, default=4)
    parser.add_argument("--row-time-limit", type=float, default=60.0)
    args = parser.parse_args()

    report = run_b3_branch_tree_ablation_matrix(
        manifest_path=args.manifest,
        project_root=ROOT,
        scale5_limit=args.scale5_limit,
        scale10_limit=args.scale10_limit,
        scale20_probe_limit=args.scale20_probe_limit,
        fail_closed_max_direct_tasks=args.fail_closed_max_direct_tasks,
        b2_max_rounds=args.b2_max_rounds,
        b3_max_rounds_per_node=args.b3_max_rounds_per_node,
        max_tree_nodes=args.max_tree_nodes,
        max_branch_depth=args.max_branch_depth,
        row_time_limit_sec=args.row_time_limit,
    )
    write_b3_branch_tree_ablation_artifacts(
        report,
        rows_csv=ROOT / args.rows_csv,
        summary_json=ROOT / args.summary_json,
        report_md=ROOT / args.report_md,
    )
    print(
        "ran {row_count} B3 branch-tree ablation rows; redlines={redlines}; accepted={accepted}; report={report}".format(
            row_count=report["row_count"],
            redlines=report["redlines"],
            accepted=report["acceptance"]["b3b_seeded_branch_price_tree_accepted"],
            report=args.report_md,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
