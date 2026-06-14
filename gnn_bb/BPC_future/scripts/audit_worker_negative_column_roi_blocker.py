#!/usr/bin/env python3
"""Audit whether worker-added negative columns were sufficient for ROI.

This diagnostic-only helper reads existing Phase 7O / 8Q calibration summaries
and produces a compact machine-checkable explanation for why "Pulse can add
true-RC negative columns" is not yet a production optimization direction.

It does not run BPC, pricing, RMP, Pulse, workers, certificates, or benchmarks.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_PHASE7O_EXPANDED = Path(
    "BPC_future/results/sharded_pulse_phase7o_worker_roi_ab_expanded_20260612/"
    "summary.json"
)
DEFAULT_PHASE8Q_VALIDATION = Path(
    "BPC_future/results/sharded_pulse_phase8q_passed_source_roi_validation_smoke_20260613/"
    "summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_worker_negative_column_roi_blocker_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_worker_negative_column_roi_blocker_zh.md"
)


def _read_rows(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise TypeError(f"{path} must contain a JSON list")
    return [row for row in data if isinstance(row, dict)]


def _as_int(value: Any) -> int:
    try:
        if value in ("", None):
            return 0
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _as_float(value: Any) -> float | None:
    try:
        if value in ("", None):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _is_true(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def _scale_of(row: dict[str, Any]) -> str:
    value = row.get("scale")
    if value in ("", None):
        value = row.get("tasks")
    return str(value)


def _profile_of(row: dict[str, Any]) -> str:
    return str(row.get("profile", ""))


def _is_baseline(row: dict[str, Any]) -> bool:
    return _profile_of(row) == "baseline"


def _row_added_journeys(row: dict[str, Any]) -> int:
    return _as_int(row.get("pulse_worker_added_journeys"))


def _aggregate_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    nonbaseline = [row for row in rows if not _is_baseline(row)]
    worker_added = [row for row in rows if _row_added_journeys(row) > 0]
    triggered = [row for row in rows if _is_true(row.get("worker_triggered"))]
    improved = [row for row in rows if row.get("improvement_class") == "improved"]
    worsened = [row for row in rows if row.get("improvement_class") == "worsened"]
    time_limit = [row for row in rows if str(row.get("status") or row.get("official_status")) == "TIME_LIMIT"]
    critical = [
        row
        for row in rows
        if _is_true(row.get("critical_disagreement"))
        or _as_int(row.get("critical_disagreement_count")) > 0
    ]

    by_scale: dict[str, dict[str, Any]] = {}
    for scale in sorted({_scale_of(row) for row in rows}):
        scale_rows = [row for row in rows if _scale_of(row) == scale]
        scale_nonbaseline = [row for row in scale_rows if not _is_baseline(row)]
        by_scale[scale] = {
            "row_count": len(scale_rows),
            "baseline_rows": len(scale_rows) - len(scale_nonbaseline),
            "nonbaseline_rows": len(scale_nonbaseline),
            "improvement_class_counts": dict(
                Counter(str(row.get("improvement_class", "")) for row in scale_rows)
            ),
            "worker_triggered_rows": sum(
                1 for row in scale_rows if _is_true(row.get("worker_triggered"))
            ),
            "worker_added_rows": sum(
                1 for row in scale_rows if _row_added_journeys(row) > 0
            ),
            "worker_added_journeys": sum(_row_added_journeys(row) for row in scale_rows),
            "worker_added_new_task_sets": sum(
                _as_int(row.get("pulse_worker_added_new_task_set_count"))
                for row in scale_rows
            ),
            "worker_added_support_changing": sum(
                _as_int(row.get("pulse_worker_added_support_changing_count"))
                for row in scale_rows
            ),
            "nonbaseline_worsened_rows": sum(
                1 for row in scale_nonbaseline if row.get("improvement_class") == "worsened"
            ),
            "nonbaseline_improved_rows": sum(
                1 for row in scale_nonbaseline if row.get("improvement_class") == "improved"
            ),
            "time_limit_rows": sum(
                1
                for row in scale_rows
                if str(row.get("status") or row.get("official_status")) == "TIME_LIMIT"
            ),
        }

    objective_deltas = [
        _as_float(row.get("pulse_worker_next_rmp_objective_delta"))
        for row in worker_added
    ]
    objective_deltas = [value for value in objective_deltas if value is not None]
    dual_deltas = [
        _as_float(row.get("pulse_worker_next_dual_l1_delta"))
        for row in worker_added
    ]
    dual_deltas = [value for value in dual_deltas if value is not None]

    return {
        "row_count": len(rows),
        "baseline_rows": len(rows) - len(nonbaseline),
        "nonbaseline_rows": len(nonbaseline),
        "time_limit_rows": len(time_limit),
        "critical_disagreement_rows": len(critical),
        "worker_triggered_rows": len(triggered),
        "worker_added_rows": len(worker_added),
        "worker_added_journeys": sum(_row_added_journeys(row) for row in rows),
        "worker_added_new_task_sets": sum(
            _as_int(row.get("pulse_worker_added_new_task_set_count")) for row in rows
        ),
        "worker_added_support_changing": sum(
            _as_int(row.get("pulse_worker_added_support_changing_count"))
            for row in rows
        ),
        "worker_added_replacement_journeys": sum(
            _as_int(row.get("pulse_worker_added_replacement_journeys"))
            for row in rows
        ),
        "improvement_class_counts": dict(
            Counter(str(row.get("improvement_class", "")) for row in rows)
        ),
        "nonbaseline_improved_rows": sum(
            1 for row in nonbaseline if row.get("improvement_class") == "improved"
        ),
        "nonbaseline_worsened_rows": len(worsened),
        "objective_delta_rows": len(objective_deltas),
        "objective_delta_min": min(objective_deltas) if objective_deltas else None,
        "objective_delta_max": max(objective_deltas) if objective_deltas else None,
        "dual_l1_delta_rows": len(dual_deltas),
        "dual_l1_delta_max": max(dual_deltas) if dual_deltas else None,
        "by_scale": by_scale,
    }


def _worker_added_samples(rows: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    for row in rows:
        if _row_added_journeys(row) <= 0:
            continue
        samples.append(
            {
                "instance": row.get("instance"),
                "scale": _scale_of(row),
                "profile": row.get("profile"),
                "improvement_class": row.get("improvement_class"),
                "status": row.get("status") or row.get("official_status"),
                "worker_added_journeys": _row_added_journeys(row),
                "worker_added_new_task_sets": _as_int(
                    row.get("pulse_worker_added_new_task_set_count")
                ),
                "worker_added_support_changing": _as_int(
                    row.get("pulse_worker_added_support_changing_count")
                ),
                "next_rmp_objective_delta": _as_float(
                    row.get("pulse_worker_next_rmp_objective_delta")
                ),
                "next_dual_l1_delta": _as_float(
                    row.get("pulse_worker_next_dual_l1_delta")
                ),
            }
        )
        if len(samples) >= limit:
            break
    return samples


def build_summary(*, phase7o_path: Path, phase8q_path: Path) -> dict[str, Any]:
    phase7o_rows = _read_rows(phase7o_path)
    phase8q_rows = _read_rows(phase8q_path)
    phase7o = _aggregate_rows(phase7o_rows)
    phase8q = _aggregate_rows(phase8q_rows)

    phase8q_worker_added_rows = [
        row for row in phase8q_rows if _row_added_journeys(row) > 0
    ]
    phase8q_worker_added_improved = [
        row for row in phase8q_worker_added_rows if row.get("improvement_class") == "improved"
    ]
    phase8q_improved_without_worker = [
        row
        for row in phase8q_rows
        if row.get("improvement_class") == "improved"
        and _row_added_journeys(row) == 0
    ]

    checks = {
        "phase7o_rows_present": len(phase7o_rows) == 108,
        "phase8q_rows_present": len(phase8q_rows) == 35,
        "no_critical_disagreement": (
            phase7o["critical_disagreement_rows"] == 0
            and phase8q["critical_disagreement_rows"] == 0
        ),
        "worker_added_true_negative_columns_exist": (
            phase7o["worker_added_journeys"] > 0
            and phase8q["worker_added_journeys"] > 0
        ),
        "worker_added_new_task_sets_exist": (
            phase7o["worker_added_new_task_sets"] > 0
            and phase8q["worker_added_new_task_sets"] > 0
        ),
        "worker_added_support_changing_exists": (
            phase7o["worker_added_support_changing"] > 0
            and phase8q["worker_added_support_changing"] > 0
        ),
        "phase7o_all_nonbaseline_worsened": (
            phase7o["nonbaseline_rows"] > 0
            and phase7o["nonbaseline_worsened_rows"] == phase7o["nonbaseline_rows"]
        ),
        "phase7o_5_task_no_regression_not_met": (
            phase7o["by_scale"].get("5", {}).get("nonbaseline_worsened_rows", 0)
            == phase7o["by_scale"].get("5", {}).get("nonbaseline_rows", -1)
        ),
        "phase7o_10_task_no_regression_not_met": (
            phase7o["by_scale"].get("10", {}).get("nonbaseline_worsened_rows", 0)
            == phase7o["by_scale"].get("10", {}).get("nonbaseline_rows", -1)
        ),
        "phase7o_20_task_speedup_not_met": (
            phase7o["by_scale"].get("20", {}).get("nonbaseline_improved_rows", -1)
            == 0
            and phase7o["by_scale"].get("20", {}).get("worker_added_journeys", 0)
            > 0
        ),
        "phase8q_worker_added_rows_not_improved": (
            len(phase8q_worker_added_rows) > 0
            and len(phase8q_worker_added_improved) == 0
        ),
        "phase8q_improved_row_is_not_worker_added": (
            len(phase8q_improved_without_worker) >= 1
            and len(phase8q_worker_added_improved) == 0
        ),
        "all_rows_time_limit": (
            phase7o["time_limit_rows"] == phase7o["row_count"]
            and phase8q["time_limit_rows"] == phase8q["row_count"]
        ),
    }

    all_checks_pass = all(checks.values())
    status = (
        "worker_negative_columns_not_sufficient_for_roi"
        if all_checks_pass
        else "worker_negative_column_roi_audit_needs_review"
    )

    return {
        "schema_version": "worker_negative_column_roi_blocker_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": status,
        "all_checks_pass": all_checks_pass,
        "phase7o_source": str(phase7o_path),
        "phase8q_source": str(phase8q_path),
        "phase7o_expanded": phase7o,
        "phase8q_validation": phase8q,
        "phase7o_worker_added_samples": _worker_added_samples(phase7o_rows),
        "phase8q_worker_added_samples": _worker_added_samples(phase8q_rows),
        "phase8q_improved_without_worker_added_count": len(
            phase8q_improved_without_worker
        ),
        "interpretation": (
            "Worker paths can add true-RC negative columns, including new task sets "
            "and support-changing replacements, without critical disagreement.  "
            "However, Phase 7O non-baseline rows all worsened and Phase 8Q worker-added "
            "rows did not produce improved rows.  Therefore negative-column discovery "
            "is not sufficient; the unresolved blocker is returned-batch impact and "
            "low-overhead addition-before selection."
        ),
        "checks": checks,
    }


def _fmt_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)


def write_report(summary: dict[str, Any], path: Path) -> None:
    p7 = summary["phase7o_expanded"]
    p8 = summary["phase8q_validation"]
    lines = [
        "# Worker Negative Column ROI Blocker 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告只读已有 Phase 7O / 8Q summary，回答一个窄问题：",
        "worker 已经能加入 true-RC negative columns，为什么仍不能证明 5/10 不退化与 20 加速？",
        "它不运行 BPC / pricing / RMP / Pulse，也不改变 worker 或 certificate 行为。",
        "",
        "## 结论",
        "",
        "负列发现能力已经不是充分条件。Phase 7O expanded 中 worker 加入了列，"
        "包括 new task-set 和 support-changing replacement，但所有 non-baseline rows 都 worsened；"
        "Phase 8Q 中 worker-added rows 也没有成为 improved rows。当前阻塞点是 returned-batch impact "
        "与低开销 addition-before selector，而不是继续扩大 worker 或只追求更负 RC。",
        "",
        "```text",
        "worker_negative_column_roi_blocker = current",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"status = {summary['status']}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## Phase 7O Expanded 证据",
        "",
        "```json",
        _fmt_json(
            {
                "row_count": p7["row_count"],
                "nonbaseline_rows": p7["nonbaseline_rows"],
                "nonbaseline_worsened_rows": p7["nonbaseline_worsened_rows"],
                "worker_triggered_rows": p7["worker_triggered_rows"],
                "worker_added_journeys": p7["worker_added_journeys"],
                "worker_added_new_task_sets": p7["worker_added_new_task_sets"],
                "worker_added_support_changing": p7["worker_added_support_changing"],
                "critical_disagreement_rows": p7["critical_disagreement_rows"],
                "by_scale": p7["by_scale"],
            }
        ),
        "```",
        "",
        "解释：5-task、10-task、20-task 都存在 non-baseline worsening；20-task 即使有 "
        "worker-added journeys，也没有形成 wall-time / status 改善证据。",
        "",
        "## Phase 8Q Validation 证据",
        "",
        "```json",
        _fmt_json(
            {
                "row_count": p8["row_count"],
                "worker_triggered_rows": p8["worker_triggered_rows"],
                "worker_added_journeys": p8["worker_added_journeys"],
                "worker_added_new_task_sets": p8["worker_added_new_task_sets"],
                "worker_added_support_changing": p8["worker_added_support_changing"],
                "improvement_class_counts": p8["improvement_class_counts"],
                "critical_disagreement_rows": p8["critical_disagreement_rows"],
                "worker_added_rows": p8["worker_added_rows"],
                "phase8q_improved_without_worker_added_count": summary[
                    "phase8q_improved_without_worker_added_count"
                ],
            }
        ),
        "```",
        "",
        "解释：8Q 中确有 worker-added columns，但 improved row 不是 worker-added row。"
        "passed-source 可重复加列仍没有证明 tail ROI。",
        "",
        "## Worker-added Samples",
        "",
        "### Phase 7O",
        "",
        "```json",
        _fmt_json(summary["phase7o_worker_added_samples"]),
        "```",
        "",
        "### Phase 8Q",
        "",
        "```json",
        _fmt_json(summary["phase8q_worker_added_samples"]),
        "```",
        "",
        "## 对根因判断的影响",
        "",
        "- 不能再把“Pulse 找不到负列”当成主因；",
        "- 不能把“找到更多 true-RC negative columns”当成充分优化方向；",
        "- 5/10 仍然要求默认完全避开固定开销，而不是只靠 worker min-task gate；",
        "- 20 的下一步必须先证明 returned-batch selector 能改变 RMP/tail trajectory；",
        "- 在 selector 通过 context / instance / dataset holdout 前，不能进入 production A/B 或 certificate gate。",
        "",
        "## 检查项",
        "",
        "```json",
        _fmt_json(summary["checks"]),
        "```",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit worker negative-column ROI blocker evidence."
    )
    parser.add_argument("--phase7o", type=Path, default=DEFAULT_PHASE7O_EXPANDED)
    parser.add_argument("--phase8q", type=Path, default=DEFAULT_PHASE8Q_VALIDATION)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = build_summary(phase7o_path=args.phase7o, phase8q_path=args.phase8q)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_report(summary, args.report)
    print(json.dumps({"all_checks_pass": summary["all_checks_pass"], "status": summary["status"]}))


if __name__ == "__main__":
    main()
