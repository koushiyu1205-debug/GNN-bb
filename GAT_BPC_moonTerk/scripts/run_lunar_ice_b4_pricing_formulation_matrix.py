#!/usr/bin/env python3
"""Run B4D compact-pricing formulation variants from a saved staged probe."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.runners.b4_pricing_formulation_diagnostic import (  # noqa: E402
    EXPECTED_VARIANTS,
    b4_pricing_matrix_row_key,
    build_b4_pricing_formulation_report_from_rows,
    iter_b4_pricing_formulation_matrix_rows_from_probe,
    write_b4_pricing_formulation_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-probe-json", required=True)
    parser.add_argument("--output-dir", default="runs/b4_pricing_formulation_diagnostic")
    parser.add_argument("--variants", nargs="*", default=list(EXPECTED_VARIANTS))
    parser.add_argument("--history-round", type=int, default=-1)
    parser.add_argument("--negative-feasibility-time-limit-sec", type=float, default=600.0)
    parser.add_argument("--optimization-proof-time-limit-sec", type=float, default=900.0)
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--matrix-group", default="30-scale staged frontier formulation matrix")
    parser.add_argument("--rows-jsonl", default="matrix_run_rows.jsonl")
    parser.add_argument("--no-resume", dest="resume", action="store_false", default=True)
    args = parser.parse_args()

    output_dir = _resolve(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    rows_jsonl = _resolve(args.rows_jsonl) if Path(args.rows_jsonl).is_absolute() else output_dir / args.rows_jsonl
    rows = _load_rows_jsonl(rows_jsonl) if args.resume else []
    skip_keys = {b4_pricing_matrix_row_key(row) for row in rows}
    rows_csv = output_dir / "b4_pricing_rows.csv"
    summary_json = output_dir / "b4_pricing_summary.json"
    report_md = output_dir / "b4_pricing_report_zh.md"

    for row in iter_b4_pricing_formulation_matrix_rows_from_probe(
        _resolve(args.source_probe_json),
        variants=tuple(args.variants),
        history_round=int(args.history_round),
        negative_feasibility_time_limit_sec=float(args.negative_feasibility_time_limit_sec),
        optimization_proof_time_limit_sec=float(args.optimization_proof_time_limit_sec),
        threads=int(args.threads),
        matrix_group=str(args.matrix_group),
        skip_keys=skip_keys,
    ):
        rows.append(row)
        skip_keys.add(b4_pricing_matrix_row_key(row))
        _append_row_jsonl(rows_jsonl, row)
        write_b4_pricing_formulation_artifacts(
            build_b4_pricing_formulation_report_from_rows(rows),
            rows_csv=rows_csv,
            summary_json=summary_json,
            report_md=report_md,
        )

    write_b4_pricing_formulation_artifacts(
        build_b4_pricing_formulation_report_from_rows(rows),
        rows_csv=rows_csv,
        summary_json=summary_json,
        report_md=report_md,
    )
    print(f"B4 pricing formulation report written to {report_md}")
    return 0


def _resolve(path: str | Path) -> Path:
    raw = Path(path)
    return raw if raw.is_absolute() else ROOT / raw


def _load_rows_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        payload = json.loads(stripped)
        if not isinstance(payload, dict):
            raise ValueError(f"{path}:{lineno} does not contain a JSON object")
        rows.append(payload)
    return rows


def _append_row_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()


if __name__ == "__main__":
    raise SystemExit(main())
