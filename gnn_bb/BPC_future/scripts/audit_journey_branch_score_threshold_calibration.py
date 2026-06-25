#!/usr/bin/env python3
"""Calibrate branch-score admission thresholds from completed A/B audits.

The audit is diagnostic-only. It reads finished branch-score A/B rows and
summarizes which score thresholds would have admitted only improving contexts.
It does not run BPC, pricing, RMP, or produce official bounds/certificates.
"""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_branch_score_threshold_calibration_20260624")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260624_bpc_future_journey_branch_score_threshold_calibration_zh.md"
)


def _float(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return float(default)
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float(default)
    if parsed != parsed:
        return float(default)
    return float(parsed)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if path.is_dir():
        path = path / "branch_score_ab_rows.jsonl"
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _branch_score(row: dict[str, Any]) -> float | None:
    optin = row.get("optin")
    if not isinstance(optin, dict):
        return None
    if optin.get("branch_score") is None:
        return None
    return _float(optin.get("branch_score"), default=float("nan"))


def _wall_delta(row: dict[str, Any]) -> float:
    deltas = row.get("deltas")
    if not isinstance(deltas, dict):
        return 0.0
    return _float(deltas.get("wall_time"), 0.0)


def _wall(row: dict[str, Any], key: str) -> float:
    payload = row.get(key)
    if not isinstance(payload, dict):
        return 0.0
    return _float(payload.get("wall_time"), 0.0)


def _status(row: dict[str, Any], key: str) -> str:
    payload = row.get(key)
    if not isinstance(payload, dict):
        return ""
    return str(payload.get("status") or "")


def _threshold_rows(
    rows: Iterable[dict[str, Any]],
    *,
    thresholds: Iterable[float],
    target_wall: float,
) -> list[dict[str, Any]]:
    materialized = list(rows)
    output: list[dict[str, Any]] = []
    for threshold in thresholds:
        admitted = [
            row
            for row in materialized
            if _branch_score(row) is not None and float(_branch_score(row) or 0.0) > float(threshold)
        ]
        wall_improved = [row for row in admitted if _wall_delta(row) < 0.0]
        wall_regressed = [row for row in admitted if _wall_delta(row) > 0.0]
        baseline_over_target = [row for row in admitted if _wall(row, "baseline") > float(target_wall)]
        optin_within_target = [row for row in admitted if _wall(row, "optin") <= float(target_wall)]
        crossed_into_target = [
            row
            for row in admitted
            if _wall(row, "baseline") > float(target_wall) and _wall(row, "optin") <= float(target_wall)
        ]
        both_optimal = [
            row
            for row in admitted
            if _status(row, "baseline") == "OPTIMAL" and _status(row, "optin") == "OPTIMAL"
        ]
        output.append(
            {
                "schema_version": "journey_branch_score_threshold_row_v1",
                "threshold": float(threshold),
                "admitted_count": len(admitted),
                "both_optimal_count": len(both_optimal),
                "baseline_over_target_count": len(baseline_over_target),
                "optin_within_target_count": len(optin_within_target),
                "crossed_into_target_count": len(crossed_into_target),
                "wall_improved_count": len(wall_improved),
                "wall_regressed_count": len(wall_regressed),
                "wall_delta_sum": round(sum(_wall_delta(row) for row in admitted), 6),
                "min_admitted_score": None
                if not admitted
                else round(min(float(_branch_score(row) or 0.0) for row in admitted), 9),
                "max_rejected_score": None
                if len(admitted) == len(materialized)
                else round(
                    max(
                        (
                            float(_branch_score(row) or 0.0)
                            for row in materialized
                            if _branch_score(row) is not None
                            and float(_branch_score(row) or 0.0) <= float(threshold)
                        ),
                        default=float("nan"),
                    ),
                    9,
                ),
            }
        )
    return output


def _choose_recommended_threshold(rows: list[dict[str, Any]]) -> float | None:
    candidates = [
        row
        for row in rows
        if int(row.get("admitted_count") or 0) > 0
        and int(row.get("wall_regressed_count") or 0) == 0
        and int(row.get("wall_improved_count") or 0) == int(row.get("admitted_count") or 0)
    ]
    if not candidates:
        return None
    candidates.sort(
        key=lambda row: (
            -int(row.get("crossed_into_target_count") or 0),
            -int(row.get("admitted_count") or 0),
            -float(row.get("threshold") or 0.0),
        )
    )
    return float(candidates[0]["threshold"])


def build_threshold_calibration(
    *,
    inputs: list[Path],
    output_dir: Path,
    report: Path,
    thresholds: list[float] | None = None,
    target_wall: float = 200.0,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for path in inputs:
        rows.extend(_read_jsonl(path))
    if thresholds is None:
        thresholds = [0.0, 0.25, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
    threshold_rows = _threshold_rows(rows, thresholds=thresholds, target_wall=target_wall)
    recommended = _choose_recommended_threshold(threshold_rows)
    summary = {
        "schema_version": "journey_branch_score_threshold_calibration_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "official_bound_effect": False,
        "certificate_effect": False,
        "production_ready": False,
        "input_paths": [str(path) for path in inputs],
        "output_dir": str(output_dir),
        "target_wall": float(target_wall),
        "raw_ab_row_count": len(rows),
        "threshold_count": len(threshold_rows),
        "recommended_min_score": recommended,
        "threshold_rows": threshold_rows,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "threshold_calibration_rows.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in threshold_rows),
        encoding="utf-8",
    )
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(report, summary)
    return summary


def _write_report(report: Path, summary: dict[str, Any]) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Journey Branch Score Threshold Calibration",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 目的",
        "",
        "用已完成 branch-score A/B 审计校准 score-horizon admission 阈值。该脚本只读结果，不运行 BPC / pricing / RMP，不产生 official bound 或 certificate。",
        "",
        "## 机器字段",
        "",
        "```text",
        f"raw_ab_row_count = {summary['raw_ab_row_count']}",
        f"target_wall = {summary['target_wall']}",
        f"recommended_min_score = {summary['recommended_min_score']}",
        "official_bound_effect = false",
        "certificate_effect = false",
        "```",
        "",
        "## Thresholds",
        "",
    ]
    for row in summary["threshold_rows"]:
        lines.append(
            "- "
            f"threshold>{row['threshold']}: admitted={row['admitted_count']}, "
            f"improved={row['wall_improved_count']}, regressed={row['wall_regressed_count']}, "
            f"crossed_200={row['crossed_into_target_count']}, "
            f"wall_delta_sum={row['wall_delta_sum']}"
        )
    lines.extend(["", "## 边界", ""])
    lines.append(
        "推荐阈值只用于 score-horizon 调度 admission；它不改变 exact pricing、official bound 或 node certificate。样本量仍小，不能作为 production GAT 泛化门槛。"
    )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", action="append", required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--threshold", type=float, action="append", default=None)
    parser.add_argument("--target-wall", type=float, default=200.0)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    build_threshold_calibration(
        inputs=[Path(path) for path in args.input],
        output_dir=args.output_dir,
        report=args.report,
        thresholds=args.threshold,
        target_wall=args.target_wall,
    )


if __name__ == "__main__":
    main()
