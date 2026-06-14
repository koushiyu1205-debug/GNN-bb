#!/usr/bin/env python3
"""Build trajectory-level CBF/RMP-impact rows from replay capture logs.

The one-step CBF gate estimates immediate impact of an observed column batch.
This helper keeps the same no-certificate-effect boundary, but labels each
observed action by its multi-step trajectory impact ``Delta V_{t->t+H}``.
It is read-only with respect to solver state: it does not run BPC, pricing,
RMP, workers, or certificates.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from BPC_future.scripts.audit_cbf_mode_transition import audit
from BPC_future.scripts.build_cbf_gate_dataset import _as_float, _as_int, _round, flatten_transition


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/cbf_trajectory_gate_dataset_20260614")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_cbf_trajectory_gate_dataset_zh.md"
)


def _transition_key(item: dict[str, Any]) -> tuple[str, str, int, int]:
    return (
        str(item.get("source_file", "")),
        str(item.get("instance", "")),
        _as_int(item.get("node_id")),
        _as_int(item.get("depth")),
    )


def _transition_order(item: dict[str, Any]) -> tuple[int, int]:
    return (_as_int(item.get("cg_iter")), _as_int(item.get("next_cg_iter")))


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows)
    path.write_text(text + ("\n" if text else ""), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def flatten_trajectory_transition(
    transition: dict[str, Any],
    horizon_end: dict[str, Any],
    *,
    horizon_steps: int,
    alpha: float,
    v_crit: float,
) -> dict[str, Any]:
    """Return one trajectory-level row for the action at ``transition``."""

    row = flatten_transition(transition)
    horizon_v_next = _as_float(horizon_end.get("v_next"))
    horizon_h_next = float(v_crit) - horizon_v_next
    h_t = _as_float(row.get("h_t"))
    horizon_barrier_slack = horizon_h_next - h_t + float(alpha) * h_t
    horizon_delta_v = horizon_v_next - _as_float(row.get("v_t"))
    horizon_mode_switched = bool(row.get("state_t_z_hash") != str(horizon_end.get("state_next_z_hash", "")))
    horizon_active_hash_switched = bool(
        str(transition.get("active_hash_before", "")) != str(horizon_end.get("active_hash_next", ""))
    )
    row.update(
        {
            "schema_version": "cbf_trajectory_gate_dataset_row_v1",
            "horizon_steps": int(horizon_steps),
            "horizon_next_cg_iter": _as_int(horizon_end.get("next_cg_iter")),
            "horizon_next_context_hash": str(horizon_end.get("next_context_hash", "")),
            "horizon_state_next_z_hash": str(horizon_end.get("state_next_z_hash", "")),
            "horizon_mode_switched": int(horizon_mode_switched),
            "horizon_active_hash_switched": int(horizon_active_hash_switched),
            "horizon_v_next": _round(horizon_v_next),
            "horizon_h_next": _round(horizon_h_next),
            "horizon_delta_v": _round(horizon_delta_v),
            "horizon_barrier_slack": _round(horizon_barrier_slack),
            "label_horizon_cbf_feasible": int(horizon_barrier_slack >= -1.0e-9),
            "label_horizon_delta_v_nonpositive": int(horizon_delta_v <= 0.0),
            "label_horizon_bad_mode_transition": int(horizon_mode_switched and horizon_delta_v > 0.0),
        }
    )
    return row


def _trajectory_rows(
    transitions: list[dict[str, Any]],
    *,
    horizon_steps: int,
    alpha: float,
    v_crit: float,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, int, int], list[dict[str, Any]]] = defaultdict(list)
    for item in transitions:
        grouped[_transition_key(item)].append(item)
    rows: list[dict[str, Any]] = []
    for items in grouped.values():
        ordered = sorted(items, key=_transition_order)
        for idx, transition in enumerate(ordered):
            end_idx = idx + int(horizon_steps) - 1
            if end_idx >= len(ordered):
                continue
            rows.append(
                flatten_trajectory_transition(
                    transition,
                    ordered[end_idx],
                    horizon_steps=int(horizon_steps),
                    alpha=float(alpha),
                    v_crit=float(v_crit),
                )
            )
    return rows


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# CBF Trajectory Gate Dataset 构建报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "把 one-step `state_t, action_t, state_{t+1}` transition 扩展为",
        "`state_t, action_t, state_{t+H}` 轨迹标签。该脚本只读已有 capture 日志，",
        "不运行 BPC / pricing / RMP，不改变 worker、certificate 或 official lower bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "cbf_trajectory_gate_dataset = current",
        f"horizon_steps = {summary['horizon_steps']}",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"status = {summary['status']}",
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
                "capture_event_count": summary["capture_event_count"],
                "one_step_transition_count": summary["one_step_transition_count"],
                "row_count": summary["row_count"],
                "horizon_cbf_feasible_count": summary["horizon_cbf_feasible_count"],
                "horizon_cbf_infeasible_count": summary["horizon_cbf_infeasible_count"],
                "horizon_bad_mode_transition_count": summary["horizon_bad_mode_transition_count"],
                "task_count_histogram": summary["task_count_histogram"],
                "jsonl_path": summary["jsonl_path"],
                "csv_path": summary["csv_path"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## 解释",
        "",
        "- `label_horizon_cbf_feasible` 评估的是观测 column batch 在 horizon 末端的 CBF slack；",
        "- 它把目标从 one-step immediate impact 推向 trajectory Lyapunov control，但仍只是观测标签；",
        "- 数据只可用于 offline calibration / holdout，不能作为 pricing oracle 或 certificate；",
        "- 训练时必须排除 `state_next_*`、`delta_*`、`horizon_*` 和所有 label 字段。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_trajectory_dataset(
    paths: Iterable[Path],
    *,
    output_dir: Path,
    report: Path,
    horizon_steps: int = 2,
    alpha: float = 0.25,
    v_crit: float = 1.0,
    min_rows_for_training: int = 100,
) -> dict[str, Any]:
    if int(horizon_steps) < 1:
        raise ValueError("horizon_steps must be >= 1")
    audit_summary = audit(paths, alpha=alpha, v_crit=v_crit)
    transitions = list(audit_summary.get("transitions", []))
    rows = (
        _trajectory_rows(
            transitions,
            horizon_steps=int(horizon_steps),
            alpha=float(alpha),
            v_crit=float(v_crit),
        )
        if bool(audit_summary.get("all_checks_pass", False))
        else []
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = output_dir / "cbf_trajectory_gate_transitions.jsonl"
    csv_path = output_dir / "cbf_trajectory_gate_transitions.csv"
    _write_jsonl(jsonl_path, rows)
    _write_csv(csv_path, rows)

    feasible_count = sum(int(row["label_horizon_cbf_feasible"]) for row in rows)
    bad_mode_count = sum(int(row["label_horizon_bad_mode_transition"]) for row in rows)
    by_task_count = Counter(str(row["task_count"]) for row in rows)
    checks = {
        "audit_checks_pass": bool(audit_summary.get("all_checks_pass", False)),
        "diagnostic_only": True,
        "runs_bpc_or_pricing_false": True,
        "all_rows_no_certificate_effect": all(
            bool(row["diagnostic_only"])
            and not bool(row["certificate_capable"])
            and not bool(row["official_bound_effect"])
            for row in rows
        ),
        "rows_require_full_horizon": all(int(row["horizon_steps"]) == int(horizon_steps) for row in rows),
    }
    training_ready = bool(
        len(rows) >= int(min_rows_for_training)
        and feasible_count > 0
        and feasible_count < len(rows)
        and bool(audit_summary.get("all_checks_pass", False))
    )
    summary = {
        "schema_version": "cbf_trajectory_gate_dataset_v1",
        "status": "cbf_trajectory_gate_dataset_built" if rows else "cbf_trajectory_gate_dataset_empty",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "input_file_count": int(audit_summary.get("input_file_count", 0)),
        "capture_event_count": int(audit_summary.get("capture_event_count", 0)),
        "one_step_transition_count": int(audit_summary.get("transition_count", 0)),
        "row_count": len(rows),
        "horizon_steps": int(horizon_steps),
        "horizon_cbf_feasible_count": feasible_count,
        "horizon_cbf_infeasible_count": len(rows) - feasible_count,
        "horizon_bad_mode_transition_count": bad_mode_count,
        "task_count_histogram": dict(sorted(by_task_count.items())),
        "jsonl_path": str(jsonl_path),
        "csv_path": str(csv_path),
        "alpha": float(alpha),
        "v_crit": float(v_crit),
        "min_rows_for_training": int(min_rows_for_training),
        "training_ready": training_ready,
        "production_ready": False,
        "goal_complete": False,
        "checks": checks,
        "all_checks_pass": all(bool(value) for value in checks.values()),
        "row_samples": rows[:5],
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(report, summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="JSONL files or directories to scan.")
    parser.add_argument("--horizon-steps", type=int, default=2)
    parser.add_argument("--alpha", type=float, default=0.25)
    parser.add_argument("--v-crit", type=float, default=1.0)
    parser.add_argument("--min-rows-for-training", type=int, default=100)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    summary = build_trajectory_dataset(
        args.paths,
        output_dir=args.output_dir,
        report=args.report,
        horizon_steps=args.horizon_steps,
        alpha=args.alpha,
        v_crit=args.v_crit,
        min_rows_for_training=args.min_rows_for_training,
    )
    print(
        json.dumps(
            {
                "summary": str(args.output_dir / "summary.json"),
                "report": str(args.report),
                "row_count": summary["row_count"],
                "horizon_steps": summary["horizon_steps"],
                "all_checks_pass": summary["all_checks_pass"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
