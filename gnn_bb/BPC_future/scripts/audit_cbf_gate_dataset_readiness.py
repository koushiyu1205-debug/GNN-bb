#!/usr/bin/env python3
"""Audit readiness of flattened CBF gate transition datasets.

This script is diagnostic-only.  It reads ``cbf_gate_transitions.jsonl`` rows
and reports whether the data is broad enough for offline CBF/RMP-impact gate
calibration.  It does not run BPC, pricing, RMP, or model training.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/cbf_gate_dataset_readiness_20260614")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_cbf_gate_dataset_readiness_zh.md"
)


def _iter_jsonl_paths(paths: Iterable[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_file() and path.suffix == ".jsonl":
            files.append(path)
        elif path.is_dir():
            direct = path / "cbf_gate_transitions.jsonl"
            if direct.is_file():
                files.append(direct)
            files.extend(
                sorted(
                    candidate
                    for candidate in path.rglob("cbf_gate_transitions.jsonl")
                    if candidate.is_file()
                )
            )
    return sorted(dict.fromkeys(files))


def _read_rows(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            item = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append({"path": str(path), "line": line_number, "error": str(exc)})
            continue
        if isinstance(item, dict):
            row = dict(item)
            row["_source_dataset"] = str(path)
            rows.append(row)
    return rows, errors


def _as_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _row_no_effect(row: dict[str, Any]) -> bool:
    return (
        row.get("diagnostic_only") is True
        and row.get("certificate_capable") is False
        and row.get("official_bound_effect") is False
    )


def audit_readiness(
    paths: Iterable[Path],
    *,
    min_rows: int = 100,
    min_instances: int = 4,
    require_both_labels: bool = True,
    require_task20: bool = False,
) -> dict[str, Any]:
    files = _iter_jsonl_paths(paths)
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for path in files:
        path_rows, path_errors = _read_rows(path)
        rows.extend(path_rows)
        errors.extend(path_errors)

    row_count = len(rows)
    instances = sorted({str(row.get("instance", "")) for row in rows if str(row.get("instance", ""))})
    by_task = Counter(str(_as_int(row.get("task_count"))) for row in rows)
    by_instance_task = Counter(
        (
            str(row.get("instance", "")),
            str(_as_int(row.get("task_count"))),
        )
        for row in rows
    )
    cbf_feasible_count = sum(_as_int(row.get("label_cbf_feasible")) for row in rows)
    bad_mode_count = sum(_as_int(row.get("label_bad_mode_transition")) for row in rows)
    delta_nonpositive_count = sum(_as_int(row.get("label_delta_v_nonpositive")) for row in rows)
    no_effect_count = sum(1 for row in rows if _row_no_effect(row))
    both_labels_present = bool(cbf_feasible_count > 0 and cbf_feasible_count < row_count)
    checks = {
        "no_decode_errors": len(errors) == 0,
        "all_rows_no_certificate_effect": bool(row_count == 0 or no_effect_count == row_count),
        "row_count_meets_minimum": row_count >= int(min_rows),
        "instance_count_meets_minimum": len(instances) >= int(min_instances),
        "cbf_label_coverage": bool((not require_both_labels) or both_labels_present),
        "task20_coverage": bool((not require_task20) or by_task.get("20", 0) > 0),
    }
    training_ready = all(bool(value) for value in checks.values())
    return {
        "schema_version": "cbf_gate_dataset_readiness_v1",
        "status": "cbf_gate_dataset_training_ready" if training_ready else "cbf_gate_dataset_not_training_ready",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "input_file_count": len(files),
        "row_count": row_count,
        "unique_instance_count": len(instances),
        "instances": instances,
        "task_count_histogram": dict(sorted(by_task.items())),
        "instance_task_histogram": {
            f"{instance}|{task_count}": int(count)
            for (instance, task_count), count in sorted(by_instance_task.items())
        },
        "cbf_feasible_count": cbf_feasible_count,
        "cbf_infeasible_count": row_count - cbf_feasible_count,
        "bad_mode_transition_count": bad_mode_count,
        "delta_v_nonpositive_count": delta_nonpositive_count,
        "delta_v_positive_count": row_count - delta_nonpositive_count,
        "no_effect_row_count": no_effect_count,
        "decode_error_count": len(errors),
        "decode_errors": errors[:20],
        "min_rows": int(min_rows),
        "min_instances": int(min_instances),
        "require_both_labels": bool(require_both_labels),
        "require_task20": bool(require_task20),
        "checks": checks,
        "all_checks_pass": bool(len(errors) == 0 and (row_count == 0 or no_effect_count == row_count)),
        "training_ready": training_ready,
        "production_ready": False,
        "goal_complete": False,
    }


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# CBF Gate Dataset Readiness 审计报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告只审计已构建的 `cbf_gate_transitions.jsonl`，判断其是否具备",
        "离线 CBF/RMP-impact gate 训练或校准的最低覆盖。它不运行 BPC / pricing / RMP，",
        "也不训练模型。",
        "",
        "## 机器字段",
        "",
        "```text",
        "cbf_gate_dataset_readiness = current",
        f"status = {summary['status']}",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        f"training_ready = {str(summary['training_ready']).lower()}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        "```",
        "",
        "## 摘要",
        "",
        "```json",
        json.dumps(
            {
                "input_file_count": summary["input_file_count"],
                "row_count": summary["row_count"],
                "unique_instance_count": summary["unique_instance_count"],
                "task_count_histogram": summary["task_count_histogram"],
                "cbf_feasible_count": summary["cbf_feasible_count"],
                "cbf_infeasible_count": summary["cbf_infeasible_count"],
                "bad_mode_transition_count": summary["bad_mode_transition_count"],
                "decode_error_count": summary["decode_error_count"],
                "checks": summary["checks"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## 解释",
        "",
        "- `training_ready=false` 表示当前数据只能用于链路 smoke 或人工审计；",
        "- `all_checks_pass=true` 只表示数据行保持 no-certificate-effect，不代表样本足够；",
        "- production gate 仍需后续 holdout / calibration / no-regression A/B。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--min-rows", type=int, default=100)
    parser.add_argument("--min-instances", type=int, default=4)
    parser.add_argument("--allow-single-label", action="store_true")
    parser.add_argument("--require-task20", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    summary = audit_readiness(
        args.paths,
        min_rows=args.min_rows,
        min_instances=args.min_instances,
        require_both_labels=not bool(args.allow_single_label),
        require_task20=bool(args.require_task20),
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_report(args.report, summary)
    print(
        json.dumps(
            {
                "summary": str(summary_path),
                "report": str(args.report),
                "training_ready": summary["training_ready"],
                "all_checks_pass": summary["all_checks_pass"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
