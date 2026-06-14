#!/usr/bin/env python3
"""Add online history features to H=2 CBF trajectory rows.

The input rows are already offline H=2 trajectory labels.  This helper appends
``history_prev_*`` fields derived only from earlier rows in the same
``source_file / instance / node / depth`` trajectory.  These fields represent
state that would be known before the current candidate batch is admitted.

No BPC/pricing/RMP run is triggered, no columns are generated, and no
certificate or official lower bound is produced.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from BPC_future.scripts.audit_cbf_trajectory_gate_policy import (
    _label_counts,
    trajectory_gate_feature_names,
)
from BPC_future.scripts.train_cbf_gate import _is_no_effect_row, load_rows


DEFAULT_INPUT = Path(
    "BPC_future/results/cbf_trajectory_gate_dataset_global_all_h2_20260614/"
    "cbf_trajectory_gate_transitions.jsonl"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/cbf_trajectory_history_dataset_global_all_h2_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_cbf_trajectory_history_dataset_global_all_h2_zh.md"
)


PREVIOUS_ONLINE_FIELDS = {
    "active_hash_switched": "history_prev_active_hash_switched",
    "barrier_slack": "history_prev_barrier_slack",
    "delta_basis_turnover": "history_prev_delta_basis_turnover",
    "delta_dual_l1_delta": "history_prev_delta_dual_l1_delta",
    "delta_final_judge_retry_count": "history_prev_delta_final_judge_retry_count",
    "delta_hidden_negative_count": "history_prev_delta_hidden_negative_count",
    "delta_mode_best_true_rc": "history_prev_delta_mode_best_true_rc",
    "delta_mode_mode_entropy": "history_prev_delta_mode_mode_entropy",
    "delta_mode_negative_count": "history_prev_delta_mode_negative_count",
    "delta_mode_replacement_ratio": "history_prev_delta_mode_replacement_ratio",
    "delta_mode_support_changing_ratio": "history_prev_delta_mode_support_changing_ratio",
    "delta_objective_progress": "history_prev_delta_objective_progress",
    "delta_replacement_ratio": "history_prev_delta_replacement_ratio",
    "delta_residual_mode_entropy": "history_prev_delta_residual_mode_entropy",
    "delta_support_changing_progress": "history_prev_delta_support_changing_progress",
    "delta_v": "history_prev_delta_v",
    "label_bad_mode_transition": "history_prev_label_bad_mode_transition",
    "label_cbf_feasible": "history_prev_label_cbf_feasible",
    "label_delta_v_nonpositive": "history_prev_label_delta_v_nonpositive",
    "mode_switched": "history_prev_mode_switched",
}
PREVIOUS_ACTION_FIELDS = {
    "action_returned_count": "history_prev_action_returned_count",
    "action_negative_count": "history_prev_action_negative_count",
    "action_unique_task_set_count": "history_prev_action_unique_task_set_count",
    "action_duplicate_task_set_count": "history_prev_action_duplicate_task_set_count",
    "action_avg_task_set_size": "history_prev_action_avg_task_set_size",
    "action_first_task_entropy": "history_prev_action_first_task_entropy",
    "action_second_action_entropy": "history_prev_action_second_action_entropy",
}


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _group_key(row: dict[str, Any]) -> tuple[str, str, int, int]:
    return (
        str(row.get("source_file", "")),
        str(row.get("instance", "")),
        _safe_int(row.get("node_id")),
        _safe_int(row.get("depth")),
    )


def _order_key(row: dict[str, Any]) -> tuple[int, int, str]:
    return (
        _safe_int(row.get("cg_iter")),
        _safe_int(row.get("next_cg_iter")),
        str(row.get("context_hash", "")),
    )


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows)
    path.write_text(text + ("\n" if text else ""), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _with_previous_history(row: dict[str, Any], previous: dict[str, Any] | None) -> dict[str, Any]:
    enriched = dict(row)
    enriched["schema_version"] = "cbf_trajectory_history_dataset_row_v1"
    enriched["history_prev_available"] = 1 if previous is not None else 0
    enriched["history_prev_cg_gap"] = (
        _safe_int(row.get("cg_iter")) - _safe_int(previous.get("cg_iter"))
        if previous is not None
        else 0
    )
    for target in [*PREVIOUS_ONLINE_FIELDS.values(), *PREVIOUS_ACTION_FIELDS.values()]:
        enriched[target] = 0.0
    if previous is None:
        return enriched
    for source, target in PREVIOUS_ONLINE_FIELDS.items():
        enriched[target] = _safe_float(previous.get(source))
    for source, target in PREVIOUS_ACTION_FIELDS.items():
        enriched[target] = _safe_float(previous.get(source))
    return enriched


def build_history_dataset(
    input_path: Path,
    *,
    output_dir: Path,
    report: Path,
) -> dict[str, Any]:
    rows = load_rows(input_path)
    grouped: dict[tuple[str, str, int, int], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[_group_key(row)].append(row)
    enriched_rows: list[dict[str, Any]] = []
    for items in grouped.values():
        ordered = sorted(items, key=_order_key)
        previous: dict[str, Any] | None = None
        for row in ordered:
            enriched_rows.append(_with_previous_history(row, previous))
            previous = row
    enriched_rows.sort(key=lambda row: (str(row.get("source_file", "")), str(row.get("instance", "")), _order_key(row)))

    output_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = output_dir / "cbf_trajectory_history_transitions.jsonl"
    csv_path = output_dir / "cbf_trajectory_history_transitions.csv"
    _write_jsonl(jsonl_path, enriched_rows)
    _write_csv(csv_path, enriched_rows)

    no_effect_count = sum(1 for row in enriched_rows if _is_no_effect_row(row))
    feature_names = trajectory_gate_feature_names(enriched_rows)
    history_feature_names = [name for name in feature_names if name.startswith("history_")]
    checks = {
        "row_count_preserved": len(enriched_rows) == len(rows),
        "all_rows_no_certificate_effect": bool(enriched_rows and no_effect_count == len(enriched_rows)),
        "history_features_online_only": all(
            not name.startswith("history_prev_horizon_")
            and not name.startswith("history_prev_state_next_")
            for name in history_feature_names
        ),
        "history_features_are_train_visible": bool(history_feature_names),
    }
    summary = {
        "schema_version": "cbf_trajectory_history_dataset_v1",
        "status": "cbf_trajectory_history_dataset_built",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "input_path": str(input_path),
        "row_count": len(enriched_rows),
        "label_counts": _label_counts(enriched_rows),
        "task_count_histogram": dict(Counter(str(row.get("task_count")) for row in enriched_rows)),
        "feature_count": len(feature_names),
        "history_feature_count": len(history_feature_names),
        "history_feature_names": history_feature_names,
        "jsonl_path": str(jsonl_path),
        "csv_path": str(csv_path),
        "training_ready": bool(enriched_rows),
        "production_ready": False,
        "official_bound_effect": False,
        "checks": checks,
        "all_checks_pass": all(bool(value) for value in checks.values()),
        "goal_complete": False,
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(report, summary)
    return summary


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# CBF Trajectory History Dataset 构建报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "给 H=2 trajectory rows 添加只来自过去 transition 的 `history_prev_*`",
        "在线历史特征。该脚本只读已有 dataset，不运行 BPC / pricing / RMP，",
        "不生成列，不产生 certificate 或 official lower bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "cbf_trajectory_history_dataset = current",
        f"status = {summary['status']}",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"row_count = {summary['row_count']}",
        f"history_feature_count = {summary['history_feature_count']}",
        f"training_ready = {str(summary['training_ready']).lower()}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 摘要",
        "",
        "```json",
        json.dumps(
            {
                "row_count": summary["row_count"],
                "label_counts": summary["label_counts"],
                "task_count_histogram": summary["task_count_histogram"],
                "feature_count": summary["feature_count"],
                "history_feature_count": summary["history_feature_count"],
                "jsonl_path": summary["jsonl_path"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## 解释",
        "",
        "- `history_prev_*` 只来自同一 trajectory 中更早的 one-step transition；",
        "- 不加入当前 row 的 `horizon_*`、`state_next_*` 或 `delta_*` 未来字段；",
        "- 该数据集只能用于 offline holdout / feature-gap 诊断，不能直接接 production。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    summary = build_history_dataset(
        args.input,
        output_dir=args.output_dir,
        report=args.report,
    )
    print(
        json.dumps(
            {
                "summary": str(args.output_dir / "summary.json"),
                "jsonl": summary["jsonl_path"],
                "report": str(args.report),
                "all_checks_pass": summary["all_checks_pass"],
                "row_count": summary["row_count"],
                "history_feature_count": summary["history_feature_count"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
