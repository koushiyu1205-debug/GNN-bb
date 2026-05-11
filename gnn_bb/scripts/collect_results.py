#!/usr/bin/env python3
"""中文摘要：本脚本汇总一个或多个实验 CSV，生成统一的 per-instance 结果表。"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="汇总 baseline/BP/ML 实验结果 CSV。")
    parser.add_argument("--inputs", nargs="+", default=["results/scip_baseline.csv"])
    parser.add_argument("--output", default="results/per_instance_results.csv")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = []
    fieldnames = set()
    for input_path_text in args.inputs:
        input_path = Path(input_path_text)
        solver_name = input_path.stem
        if not input_path.exists():
            continue
        with input_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                row = dict(row)
                row.setdefault("solver", solver_name)
                rows.append(row)
                fieldnames.update(row.keys())

    ordered_fields = ["solver", "instance", *sorted(field for field in fieldnames if field not in {"solver", "instance"})]
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=ordered_fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"汇总结果已写入：{output_path}")


if __name__ == "__main__":
    main()

