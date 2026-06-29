#!/usr/bin/env python3
"""Convert paired branch child-probe rows into branch-action calibration rows.

The output intentionally reuses ``branch_counterfactual_delta_rows.jsonl`` so
the branch-action dataset builder can ingest proof-risk hard negatives.  These
rows are proxy evidence only: they are right-censored, production-disabled, and
cannot be used as official bounds, certificates, pruning rules, or full-replay
positives.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/journey_paired_probe_delta_rows_20260628"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260628_bpc_future_journey_paired_probe_delta_rows_zh.md"
)
ROW_FILENAME = "paired_probe_rows.jsonl"


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            yield payload


def _row_file(path: Path) -> Path:
    if path.is_dir():
        return path / ROW_FILENAME
    if path.name == "summary.json":
        return path.parent / ROW_FILENAME
    return path


def _load_rows(inputs: Iterable[Path]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    resolved: list[str] = []
    for path in inputs:
        row_path = _row_file(path)
        resolved.append(str(row_path))
        rows.extend(_iter_jsonl(row_path))
    return rows, resolved


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


def _int(value: Any, default: int = 0) -> int:
    if value in (None, ""):
        return int(default)
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _pair(value: Any) -> list[int] | None:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        return None
    try:
        left, right = int(value[0]), int(value[1])
    except (TypeError, ValueError):
        return None
    if left <= 0 or right <= 0 or left == right:
        return None
    return sorted([left, right])


def _loss_weight(row: dict[str, Any], *, max_weight: float) -> float:
    wall_gain = _float(row.get("paired_wall_time_gain"))
    gap_improvement = _float(row.get("paired_gap_improvement"))
    child_cpu = _float(row.get("child_proof_cpu"))
    cb_retry = _float(row.get("child_completion_bound_retry_count"))
    weight = 1.0
    if wall_gain < 0.0:
        weight += min(1.5, abs(wall_gain) / 30.0)
    if gap_improvement < 0.0:
        weight += min(1.5, abs(gap_improvement) * 500.0)
    if child_cpu >= 30.0:
        weight += 0.5
    if cb_retry >= 6.0:
        weight += 0.5
    return min(float(max_weight), max(0.5, float(weight)))


def _counterfactual_type(label_type: str) -> str | None:
    if label_type == "hard_negative_proxy":
        return "paired_probe_hard_negative_proxy"
    if label_type == "positive_proxy":
        return "paired_probe_positive_proxy"
    if label_type == "neutral_proxy":
        return "paired_probe_neutral_proxy"
    return None


def _convert_row(row: dict[str, Any], *, max_hard_negative_weight: float) -> dict[str, Any] | None:
    if str(row.get("pair_role") or "") != "alternative":
        return None
    label_type = str(row.get("paired_label_type") or "")
    converted_type = _counterfactual_type(label_type)
    if converted_type is None:
        return None
    baseline_pair = _pair(row.get("source_selected_pair"))
    alternative_pair = _pair(row.get("forced_pair"))
    if baseline_pair is None or alternative_pair is None:
        return None
    alternative_wall = _float(row.get("wall_time"), 600.0)
    wall_gain = _float(row.get("paired_wall_time_gain"), 0.0)
    baseline_wall = alternative_wall + wall_gain
    gap_improvement = row.get("paired_gap_improvement")
    hard_negative = converted_type == "paired_probe_hard_negative_proxy"
    positive_proxy = converted_type == "paired_probe_positive_proxy"
    hard_negative_weight = (
        _loss_weight(row, max_weight=max_hard_negative_weight) if hard_negative else 0.0
    )
    branch_labels = {
        "y_tail_improved": 1.0 if positive_proxy else 0.0,
        "y_completion_bound_tail": 1.0,
        "y_early_branch_continues": 0.0,
        "y_negative_chain_continues": 0.0,
        "y_active_touch": 0.0,
        "y_inactive_only": 0.0,
        "y_child_negative_pricing_events": _float(row.get("child_negative_pricing_event_count")),
        "y_child_exact_pricing_events": _float(row.get("child_exact_pricing_event_count")),
        "y_child_completion_bound_retries": _float(row.get("child_completion_bound_retry_count")),
        "y_child_early_branch_triggers": 0.0,
        "y_child_fathom_events": _float(row.get("child_fathomed_count")),
        "y_child_max_safe_bound_gain": 0.0,
        "y_child_max_corrected_bound_gain": 0.0,
    }
    labels = {
        "y_counterfactual_wall_improved": 1.0 if positive_proxy else 0.0,
        "y_counterfactual_regression": 0.0,
        "y_counterfactual_timeout_regression": 0.0,
        "y_counterfactual_no_effect_hard_negative": 1.0 if hard_negative else 0.0,
        "y_counterfactual_proxy_only": 1.0,
    }
    return {
        "schema_version": "journey_branch_counterfactual_delta_from_paired_probe_v1",
        "diagnostic_only": True,
        "proxy_only": True,
        "paired_probe_proxy": True,
        "production_ready": False,
        "runs_bpc_or_pricing": False,
        "official_bound_effect": False,
        "certificate_effect": False,
        "source_paired_probe_schema_version": row.get("schema_version"),
        "experiment": row.get("experiment"),
        "paired_baseline_experiment": row.get("paired_baseline_experiment"),
        "pair_group_id": row.get("pair_group_id"),
        "instance": row.get("instance"),
        "node_id": _int(row.get("source_node_id")),
        "depth": _int(row.get("source_depth")),
        "baseline_pair": baseline_pair,
        "alternative_pair": alternative_pair,
        "baseline_status": "BASELINE_CHILD_PROBE",
        "alternative_status": row.get("status"),
        "baseline_wall_time": round(float(baseline_wall), 6),
        "alternative_wall_time": round(float(alternative_wall), 6),
        "alternative_forced_pair_matched": True,
        "right_censored_counterfactual": True,
        "counterfactual_label_type": converted_type,
        "paired_label_type": label_type,
        "paired_wall_time_gain": wall_gain,
        "paired_completion_profile_gain": _float(row.get("paired_completion_profile_gain")),
        "paired_child_cb_retry_gain": _float(row.get("paired_child_cb_retry_gain")),
        "paired_status_rank_delta": _int(row.get("paired_status_rank_delta")),
        "paired_gap_improvement": gap_improvement,
        "gap": row.get("gap"),
        "gap_available": row.get("gap_available"),
        "child_proof_cpu": _float(row.get("child_proof_cpu"), 600.0),
        "child_time_to_certificate": _float(row.get("wall_time"), 600.0),
        "hard_negative_loss_weight": hard_negative_weight,
        "deltas": {
            "wall_time_delta": round(float(alternative_wall - baseline_wall), 6),
            "gap_delta": None if gap_improvement in (None, "") else -_float(gap_improvement),
            "child_completion_bound_retry_delta": -_float(row.get("paired_child_cb_retry_gain")),
            "child_proof_cpu": _float(row.get("child_proof_cpu")),
        },
        "labels": labels,
        "alternative_branch_labels": branch_labels,
        "alternative_raw_row": {
            "branch_time": 0.0,
            "candidate_count": 0,
            "eligible_count": 0,
            "branch_rank_in_top": 0,
            "branch_rank_in_priority_top": 0,
            "source_alt_routeopt_bkf_score": row.get("source_alt_routeopt_bkf_score"),
            "source_alt_routeopt_bkf_reason": row.get("source_alt_routeopt_bkf_reason"),
            "source_alt_routeopt_bkf_stage": row.get("source_alt_routeopt_bkf_stage"),
            "source_alt_routeopt_bkf_dynamic_k": row.get("source_alt_routeopt_bkf_dynamic_k"),
            "source_alt_routeopt_bkf_stage_rank": row.get("source_alt_routeopt_bkf_stage_rank"),
            "source_alt_routeopt_bkf_filtered_count": row.get("source_alt_routeopt_bkf_filtered_count"),
            "phased_testing_stage": row.get("phased_testing_stage"),
            "phased_testing_decision": row.get("phased_testing_decision"),
            "phased_testing_reason": row.get("phased_testing_reason"),
            "phased_testing_elimination_reason": row.get("phased_testing_elimination_reason"),
            "phased_testing_phase0_passed": row.get("phased_testing_phase0_passed"),
            "phased_testing_phase1_lp_complete": row.get("phased_testing_phase1_lp_complete"),
            "phased_testing_phase2_heuristic_complete": row.get("phased_testing_phase2_heuristic_complete"),
            "phase1_min_child_lp_gain": row.get("phase1_min_child_lp_gain"),
            "phase1_child_lp_gain_product": row.get("phase1_child_lp_gain_product"),
            "phase1_child_width_balance": row.get("phase1_child_width_balance"),
            "phase1_wall_time": row.get("phase1_wall_time"),
            "phase1_dynamic_k_probe_count": row.get("phase1_dynamic_k_probe_count"),
            "phase2_negative_child_count": row.get("phase2_negative_child_count"),
            "phase2_negative_journey_count": row.get("phase2_negative_journey_count"),
            "phase2_best_reduced_cost": row.get("phase2_best_reduced_cost"),
            "phase2_worst_negative_severity": row.get("phase2_worst_negative_severity"),
            "phase2_wall_time": row.get("phase2_wall_time"),
            "phase2_dynamic_k_probe_count": row.get("phase2_dynamic_k_probe_count"),
        },
    }


def build_delta_rows(
    inputs: list[Path],
    output_dir: Path,
    report: Path,
    *,
    include_neutral: bool = False,
    max_hard_negative_weight: float = 4.0,
) -> dict[str, Any]:
    rows, resolved = _load_rows(inputs)
    converted: list[dict[str, Any]] = []
    skipped: Counter[str] = Counter()
    input_label_counts: Counter[str] = Counter()
    output_label_counts: Counter[str] = Counter()
    instance_counts: Counter[str] = Counter()
    for row in rows:
        if str(row.get("pair_role") or "") == "alternative":
            input_label_counts[str(row.get("paired_label_type") or "")] += 1
        converted_row = _convert_row(row, max_hard_negative_weight=max_hard_negative_weight)
        if converted_row is None:
            skipped["not_convertible"] += 1
            continue
        if (
            converted_row.get("counterfactual_label_type") == "paired_probe_neutral_proxy"
            and not bool(include_neutral)
        ):
            skipped["neutral_proxy_excluded"] += 1
            continue
        converted.append(converted_row)
        output_label_counts[str(converted_row.get("counterfactual_label_type") or "")] += 1
        instance_counts[str(converted_row.get("instance") or "")] += 1

    output_dir.mkdir(parents=True, exist_ok=True)
    rows_path = output_dir / "branch_counterfactual_delta_rows.jsonl"
    rows_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in converted),
        encoding="utf-8",
    )
    summary = {
        "schema_version": "journey_paired_probe_delta_rows_summary_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "official_bound_effect": False,
        "certificate_effect": False,
        "production_ready": False,
        "proxy_only": True,
        "input_paths": [str(path) for path in inputs],
        "resolved_row_files": resolved,
        "output_dir": str(output_dir),
        "rows_path": str(rows_path),
        "input_row_count": len(rows),
        "output_row_count": len(converted),
        "include_neutral": bool(include_neutral),
        "max_hard_negative_weight": float(max_hard_negative_weight),
        "input_paired_label_counts": dict(sorted(input_label_counts.items())),
        "output_counterfactual_label_counts": dict(sorted(output_label_counts.items())),
        "skipped_counts": dict(sorted(skipped.items())),
        "instance_count": len([key for key in instance_counts if key]),
        "instance_counts": dict(sorted(instance_counts.items())),
        "exactness_contract": {
            "proxy_only": True,
            "scheduler_only": True,
            "pricing_oracle": False,
            "branching_oracle": False,
            "certificate_source": False,
            "official_bound_effect": False,
            "can_prune_branch_candidates": False,
            "can_promote_proxy_positive_to_full_replay_positive": False,
        },
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(report, summary, converted)
    return summary


def _write_report(report: Path, summary: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Journey Paired-Probe Delta Rows",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 目的",
        "",
        "把 paired child-probe 的 proof-risk evidence 转成 branch-action 数据集可读取的 calibration rows。输出是 proxy-only，不能当完整求解反事实标签。",
        "",
        "## 机器字段",
        "",
        "```text",
        f"input_row_count = {summary['input_row_count']}",
        f"output_row_count = {summary['output_row_count']}",
        f"input_paired_label_counts = {summary['input_paired_label_counts']}",
        f"output_counterfactual_label_counts = {summary['output_counterfactual_label_counts']}",
        f"skipped_counts = {summary['skipped_counts']}",
        f"rows_path = {summary['rows_path']}",
        "production_ready = false",
        "official_bound_effect = false",
        "certificate_effect = false",
        "```",
        "",
        "## 输出样本",
        "",
    ]
    for row in rows[:20]:
        lines.append(
            "- "
            f"{Path(str(row.get('instance') or '')).name} "
            f"d={row.get('depth')} pair={row.get('alternative_pair')} "
            f"type={row.get('counterfactual_label_type')} "
            f"wall_gain={float(row.get('paired_wall_time_gain') or 0.0):.3f} "
            f"gap_improvement={row.get('paired_gap_improvement')} "
            f"weight={float(row.get('hard_negative_loss_weight') or 0.0):.3f}"
        )
    lines.extend(
        [
            "",
            "## 边界",
            "",
            "这些 row 的 `right_censored_counterfactual=True`，只用于 proof-risk / hard-negative calibration。任何 positive proxy 都不能直接升级为 full-replay positive；后续仍需完整 replay 或 exact pricing closure 验证。",
        ]
    )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, action="append", required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--include-neutral", action="store_true")
    parser.add_argument("--max-hard-negative-weight", type=float, default=4.0)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    summary = build_delta_rows(
        list(args.input),
        args.output_dir,
        args.report,
        include_neutral=bool(args.include_neutral),
        max_hard_negative_weight=float(args.max_hard_negative_weight),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
