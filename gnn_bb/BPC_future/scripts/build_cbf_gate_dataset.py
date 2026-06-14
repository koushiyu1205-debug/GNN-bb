#!/usr/bin/env python3
"""Build a diagnostic CBF/RMP-impact gate dataset from replay capture logs.

The builder is read-only with respect to solver state.  It calls the
``audit_cbf_mode_transition`` reconstruction, validates that every capture is
diagnostic/no-certificate-effect, and writes flattened transition rows for
offline CBF gate modeling.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from BPC_future.scripts.audit_cbf_mode_transition import audit


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/cbf_gate_dataset_20260614")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_cbf_gate_dataset_zh.md"
)


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        result = float(value)
        if math.isnan(result) or math.isinf(result):
            return default
        return result
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _round(value: Any, ndigits: int = 9) -> float:
    return round(_as_float(value), ndigits)


def _entropy(counter: Counter[Any]) -> float:
    total = sum(int(value) for value in counter.values())
    if total <= 0:
        return 0.0
    entropy = 0.0
    for value in counter.values():
        p = float(value) / float(total)
        if p > 0.0:
            entropy -= p * math.log(p)
    return entropy


def _task_set_sizes(task_sets: Iterable[Any]) -> list[int]:
    sizes: list[int] = []
    for task_set in task_sets:
        if isinstance(task_set, (list, tuple, set)):
            sizes.append(len(set(task_set)))
    return sizes


def _action_features(transition: dict[str, Any]) -> dict[str, Any]:
    action_task_sets = transition.get("action_task_sets", [])
    if not isinstance(action_task_sets, list):
        action_task_sets = []
    task_set_tuples = [
        tuple(sorted(int(task) for task in task_set))
        for task_set in action_task_sets
        if isinstance(task_set, (list, tuple, set))
    ]
    action_pairs = transition.get("action_first_second", [])
    if not isinstance(action_pairs, list):
        action_pairs = []
    first_counter: Counter[str] = Counter()
    second_counter: Counter[str] = Counter()
    for pair in action_pairs:
        if not isinstance(pair, (list, tuple)) or len(pair) < 2:
            continue
        first = str(pair[0])
        second = str(pair[1])
        first_counter[first] += 1
        second_counter[f"{first}->{second}"] += 1
    sizes = _task_set_sizes(task_set_tuples)
    returned = _as_int(transition.get("action_returned_count"), len(task_set_tuples))
    negative = _as_int(transition.get("action_negative_count"), 0)
    return {
        "action_returned_count": returned,
        "action_negative_count": negative,
        "action_negative_ratio": _round(0.0 if returned <= 0 else negative / returned),
        "action_unique_task_set_count": len(set(task_set_tuples)),
        "action_duplicate_task_set_count": max(0, len(task_set_tuples) - len(set(task_set_tuples))),
        "action_avg_task_set_size": _round(0.0 if not sizes else sum(sizes) / len(sizes)),
        "action_max_task_set_size": max(sizes) if sizes else 0,
        "action_first_task_entropy": _round(_entropy(first_counter)),
        "action_second_action_entropy": _round(_entropy(second_counter)),
    }


def _component(prefix: str, transition: dict[str, Any], name: str) -> float:
    components = transition.get(f"{prefix}_components", {})
    if not isinstance(components, dict):
        return 0.0
    return _round(components.get(name))


def _mode_value(prefix: str, transition: dict[str, Any], name: str) -> float:
    mode = transition.get(f"{prefix}_mode", {})
    if not isinstance(mode, dict):
        return 0.0
    return _round(mode.get(name))


def flatten_transition(transition: dict[str, Any]) -> dict[str, Any]:
    """Return one stable tabular row for a reconstructed CBF transition."""

    row: dict[str, Any] = {
        "schema_version": "cbf_gate_dataset_row_v1",
        "diagnostic_only": True,
        "certificate_capable": False,
        "official_bound_effect": False,
        "source_file": str(transition.get("source_file", "")),
        "instance": str(transition.get("instance", "")),
        "task_count": _as_int(transition.get("task_count")),
        "node_id": _as_int(transition.get("node_id")),
        "depth": _as_int(transition.get("depth")),
        "cg_iter": _as_int(transition.get("cg_iter")),
        "next_cg_iter": _as_int(transition.get("next_cg_iter")),
        "context_hash": str(transition.get("context_hash", "")),
        "next_context_hash": str(transition.get("next_context_hash", "")),
        "state_t_z_hash": str(transition.get("state_t_z_hash", "")),
        "state_next_z_hash": str(transition.get("state_next_z_hash", "")),
        "mode_switched": int(bool(transition.get("mode_switched", False))),
        "active_hash_switched": int(bool(transition.get("active_hash_switched", False))),
        "v_t": _round(transition.get("v_t")),
        "v_next": _round(transition.get("v_next")),
        "delta_v": _round(transition.get("delta_v")),
        "h_t": _round(transition.get("h_t")),
        "h_next": _round(transition.get("h_next")),
        "barrier_slack": _round(transition.get("barrier_slack")),
        "label_cbf_feasible": int(bool(transition.get("cbf_feasible_observed", False))),
        "label_bad_mode_transition": int(bool(transition.get("bad_mode_transition", False))),
        "label_delta_v_nonpositive": int(_as_float(transition.get("delta_v")) <= 0.0),
    }
    row.update(_action_features(transition))
    for name in (
        "dual_l1_delta",
        "basis_turnover",
        "residual_mode_entropy",
        "hidden_negative_count",
        "final_judge_retry_count",
        "replacement_ratio",
        "objective_progress",
        "support_changing_progress",
    ):
        row[f"state_t_{name}"] = _component("v_t", transition, name)
        row[f"state_next_{name}"] = _component("v_next", transition, name)
        row[f"delta_{name}"] = _round(row[f"state_next_{name}"] - row[f"state_t_{name}"])
    for name in (
        "mode_entropy",
        "observed_journey_count",
        "returned_journey_count",
        "negative_count",
        "best_true_rc",
        "replacement_ratio",
        "support_changing_ratio",
    ):
        row[f"state_t_mode_{name}"] = _mode_value("state_t", transition, name)
        row[f"state_next_mode_{name}"] = _mode_value("state_next", transition, name)
        row[f"delta_mode_{name}"] = _round(row[f"state_next_mode_{name}"] - row[f"state_t_mode_{name}"])
    return row


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + ("\n" if rows else ""),
        encoding="utf-8",
    )


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


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# CBF Gate Dataset 构建报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "把 `journey_counterfactual_replay_capture` 日志重建出的 transition",
        "压平成 CBF/RMP-impact gate 可训练表。该脚本只读日志，不运行 BPC / pricing，",
        "也不改变 solver、certificate 或 official lower bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "cbf_gate_dataset = current",
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
                "transition_count": summary["transition_count"],
                "row_count": summary["row_count"],
                "cbf_feasible_count": summary["cbf_feasible_count"],
                "cbf_infeasible_count": summary["cbf_infeasible_count"],
                "bad_mode_transition_count": summary["bad_mode_transition_count"],
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
        "- `label_cbf_feasible` 是当前 Lyapunov surrogate 下的观测标签，不是数学证明；",
        "- `label_bad_mode_transition` 表示 mode switch 且 `V_next > V_t`；",
        "- 数据只可用于 offline calibration / holdout，不可作为 pricing oracle 或 certificate；",
        "- 当前 `training_ready` 只有在有足够覆盖且正负标签同时存在时才会变为 true。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_dataset(
    paths: Iterable[Path],
    *,
    output_dir: Path,
    report: Path,
    alpha: float = 0.25,
    v_crit: float = 1.0,
    min_rows_for_training: int = 100,
) -> dict[str, Any]:
    audit_summary = audit(paths, alpha=alpha, v_crit=v_crit)
    rows = [flatten_transition(item) for item in audit_summary.get("transitions", [])]
    output_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = output_dir / "cbf_gate_transitions.jsonl"
    csv_path = output_dir / "cbf_gate_transitions.csv"
    _write_jsonl(jsonl_path, rows)
    _write_csv(csv_path, rows)

    cbf_feasible_count = sum(int(row["label_cbf_feasible"]) for row in rows)
    bad_mode_count = sum(int(row["label_bad_mode_transition"]) for row in rows)
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
        "row_count_matches_transitions": len(rows) == int(audit_summary.get("transition_count", 0)),
    }
    training_ready = bool(
        len(rows) >= int(min_rows_for_training)
        and cbf_feasible_count > 0
        and cbf_feasible_count < len(rows)
        and bool(audit_summary.get("all_checks_pass", False))
    )
    summary = {
        "schema_version": "cbf_gate_dataset_v1",
        "status": "cbf_gate_dataset_built" if rows else "cbf_gate_dataset_empty",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "input_file_count": int(audit_summary.get("input_file_count", 0)),
        "capture_event_count": int(audit_summary.get("capture_event_count", 0)),
        "transition_count": int(audit_summary.get("transition_count", 0)),
        "row_count": len(rows),
        "cbf_feasible_count": cbf_feasible_count,
        "cbf_infeasible_count": len(rows) - cbf_feasible_count,
        "bad_mode_transition_count": bad_mode_count,
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
    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_report(report, summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="JSONL files or directories to scan.")
    parser.add_argument("--alpha", type=float, default=0.25)
    parser.add_argument("--v-crit", type=float, default=1.0)
    parser.add_argument("--min-rows-for-training", type=int, default=100)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    summary = build_dataset(
        args.paths,
        output_dir=args.output_dir,
        report=args.report,
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
                "all_checks_pass": summary["all_checks_pass"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
