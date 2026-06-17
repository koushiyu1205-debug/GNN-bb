#!/usr/bin/env python3
"""Audit epoch-level constrained selector behavior for Stage 3 checkpoints.

This script is diagnostic-only. It reads a training metrics JSON and/or a saved
checkpoint, then checks whether any recorded epoch simultaneously has useful
coverage and low false-delay risk. It does not run BPC, pricing, RMP, workers,
or certificate logic.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import json
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from BPC_future.scripts.audit_gat_batch_impact_gate_shortfall import (
    additional_all_successes_for_wilson,
)


DEFAULT_CHECKPOINT = Path(
    "BPC_future/results/gat_batch_impact_training_v45_false_delay_contrast_v39_full_20260616/checkpoint.pt"
)
DEFAULT_TRAINING_SUMMARY = Path(
    "BPC_future/results/gat_batch_impact_training_v45_false_delay_contrast_v39_full_20260616/metrics.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/gat_batch_impact_epoch_selector_v47_v45_false_delay_contrast_20260616"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260616_bpc_future_gat_target_mode_stage3_v47_v45_epoch_selector_audit_zh.md"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--training-summary", type=Path, default=DEFAULT_TRAINING_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = audit_epoch_selector(
        checkpoint=Path(args.checkpoint),
        training_summary=Path(args.training_summary),
        output_dir=Path(args.output_dir),
        report=Path(args.report),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def audit_epoch_selector(
    *,
    checkpoint: Path | None = DEFAULT_CHECKPOINT,
    training_summary: Path | None = DEFAULT_TRAINING_SUMMARY,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
) -> dict[str, Any]:
    artifacts = _load_training_artifacts(
        checkpoint=Path(checkpoint) if checkpoint else None,
        training_summary=Path(training_summary) if training_summary else None,
    )
    history = [dict(row) for row in artifacts["history"]]
    if not history:
        raise ValueError("no epoch history found in training summary or checkpoint")
    gate_config = dict(artifacts["gate_config"])
    epoch_rows = [
        _audit_epoch_row(row, gate_config=gate_config)
        for row in history
    ]
    class_counts = Counter(row["epoch_signal_class"] for row in epoch_rows)
    false_delay_safe_rows = [row for row in epoch_rows if row["false_delay_safe"]]
    coverage_ready_rows = [row for row in epoch_rows if row["coverage_confidence_ready"]]
    constrained_rows = [
        row
        for row in epoch_rows
        if row["coverage_confidence_ready"] and row["false_delay_safe"]
    ]
    best_false_delay_safe = _best_epoch(false_delay_safe_rows)
    best_coverage_ready = _best_epoch(coverage_ready_rows)
    best_overall = _best_epoch(epoch_rows)
    primary = (
        "epoch_history_missing_full_stage3_ci_fields"
        if any(row["required_stage3_fields_missing"] for row in epoch_rows)
        else "epoch_level_constrained_window_found"
    )
    if not constrained_rows:
        primary = "no_epoch_satisfies_coverage_and_false_delay_constraints"
    summary = {
        "schema_version": "gat_batch_impact_epoch_selector_audit_v1",
        "status": "gat_batch_impact_epoch_selector_audited",
        "checkpoint": str(checkpoint) if checkpoint else None,
        "training_summary": str(training_summary) if training_summary else None,
        "output_dir": str(output_dir),
        "history_source": artifacts["history_source"],
        "gate_config": gate_config,
        "epoch_count": len(epoch_rows),
        "epoch_signal_class_counts": dict(sorted(class_counts.items())),
        "false_delay_safe_epoch_count": len(false_delay_safe_rows),
        "coverage_confidence_ready_epoch_count": len(coverage_ready_rows),
        "coverage_and_false_delay_safe_epoch_count": len(constrained_rows),
        "min_confidence_all_success_count": _min_confidence_all_success_count(gate_config),
        "best_false_delay_safe_epoch": best_false_delay_safe,
        "best_coverage_ready_epoch": best_coverage_ready,
        "best_overall_epoch": best_overall,
        "epoch_rows": epoch_rows,
        "diagnosis": {
            "primary": primary,
            "checkpoint_selection_is_primary_blocker": bool(constrained_rows),
            "safe_low_coverage_pattern": class_counts.get("false_delay_safe_but_low_coverage", 0) > 0,
            "coverage_unsafe_pattern": class_counts.get("coverage_ready_but_false_delay_unsafe", 0) > 0,
            "recommended_next_step": _recommended_next_step(
                constrained_rows=constrained_rows,
                class_counts=class_counts,
            ),
        },
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "default_enabled": False,
        "official_bound_effect": False,
        "selector_is_pricing_oracle": False,
        "selector_can_certificate": False,
        "gate_can_permanently_discard_negative_columns": False,
        "all_checks_pass": True,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "epoch_rows.jsonl").write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in epoch_rows)
        + "\n",
        encoding="utf-8",
    )
    _write_report(Path(report), summary)
    return summary


def _load_training_artifacts(
    *,
    checkpoint: Path | None,
    training_summary: Path | None,
) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    checkpoint_payload: dict[str, Any] = {}
    if training_summary is not None and training_summary.exists():
        summary = json.loads(training_summary.read_text(encoding="utf-8"))
    if checkpoint is not None and checkpoint.exists():
        checkpoint_payload = _load_checkpoint(checkpoint)
    summary_history = summary.get("history")
    if isinstance(summary_history, list) and summary_history:
        history = summary_history
        history_source = "training_summary"
    else:
        history = ((checkpoint_payload.get("training") or {}).get("history") or [])
        history_source = "checkpoint_training_history"
    gate_config = (
        ((checkpoint_payload.get("deployment_gate") or {}).get("gate_config") or {})
        or ((summary.get("threshold_search") or {}).get("gate_config") or {})
        or _gate_config_from_summary(summary)
    )
    return {
        "summary": summary,
        "checkpoint": checkpoint_payload,
        "history": history,
        "history_source": history_source,
        "gate_config": gate_config,
    }


def _load_checkpoint(path: Path) -> dict[str, Any]:
    try:
        import torch
    except Exception as exc:  # pragma: no cover - depends on optional torch install.
        raise RuntimeError("torch is required to read checkpoint history") from exc
    payload = torch.load(path, map_location="cpu")
    if not isinstance(payload, dict):
        raise ValueError(f"checkpoint is not a dict: {path}")
    return payload


def _gate_config_from_summary(summary: dict[str, Any]) -> dict[str, Any]:
    metrics = dict(summary.get("validation_deployment_metrics") or {})
    return {
        "min_high_priority_precision": 0.9,
        "min_high_priority_precision_ci_low": 0.9,
        "min_safe_precision": 0.9,
        "min_safe_precision_ci_low": 0.9,
        "confidence_z": 1.96,
        "max_false_high_priority_on_delay": 0.01,
        "max_false_safe_union_rate": 0.02,
        "min_accepted_batch_count": 1,
        "min_accepted_batch_roi": 0.65,
        "min_accepted_batch_roi_ci_low": 0.65,
        "candidate_admission_score_mode": metrics.get("candidate_admission_score_mode"),
        "candidate_delay_gate_enabled": metrics.get("candidate_delay_gate_enabled"),
    }


def _audit_epoch_row(row: dict[str, Any], *, gate_config: dict[str, Any]) -> dict[str, Any]:
    accepted_count = int(row.get("accepted_batch_count") or 0)
    false_delay = _float_or_none(row.get("false_high_priority_on_delay"))
    false_safe = _float_or_none(row.get("false_safe_rate_union"))
    hp_precision = _float_or_none(row.get("high_priority_precision"))
    safe_precision = _float_or_none(row.get("safe_precision"))
    roi = _float_or_none(row.get("accepted_batch_roi"))
    min_confidence_count = _min_confidence_all_success_count(gate_config)
    false_delay_safe = (
        false_delay is not None
        and false_delay <= float(gate_config.get("max_false_high_priority_on_delay", 0.01))
    )
    coverage_ready = accepted_count >= int(min_confidence_count)
    roi_point_pass = (
        roi is not None
        and roi >= float(gate_config.get("min_accepted_batch_roi", 0.65))
    )
    hp_precision_point_pass = (
        hp_precision is not None
        and hp_precision >= float(gate_config.get("min_high_priority_precision", 0.9))
    )
    safe_precision_point_pass = (
        safe_precision is not None
        and safe_precision >= float(gate_config.get("min_safe_precision", 0.9))
    )
    missing = [
        name
        for name in [
            "high_priority_precision_ci_low",
            "safe_precision_ci_low",
            "accepted_batch_roi_ci_low",
            "false_safe_rate_union",
            "accepted_batch_rate",
        ]
        if row.get(name) is None
    ]
    audited = dict(row)
    audited.update(
        {
            "false_delay_safe": bool(false_delay_safe),
            "false_safe_union_safe": (
                false_safe is not None
                and false_safe <= float(gate_config.get("max_false_safe_union_rate", 0.02))
            ),
            "coverage_confidence_ready": bool(coverage_ready),
            "min_confidence_all_success_count": int(min_confidence_count),
            "roi_point_pass": bool(roi_point_pass),
            "high_priority_precision_point_pass": bool(hp_precision_point_pass),
            "safe_precision_point_pass": bool(safe_precision_point_pass),
            "required_stage3_fields_missing": missing,
            "stage3_full_gate_auditable": not missing,
            "epoch_signal_class": _epoch_signal_class(
                false_delay_safe=bool(false_delay_safe),
                coverage_ready=bool(coverage_ready),
            ),
        }
    )
    return audited


def _min_confidence_all_success_count(gate_config: dict[str, Any]) -> int:
    target = gate_config.get("min_safe_precision_ci_low", 0.9)
    needed = additional_all_successes_for_wilson(
        0,
        0,
        target,
        z=float(gate_config.get("confidence_z", 1.96)),
        max_extra=100000,
    )
    if needed is None:
        return 0
    return int(needed)


def _epoch_signal_class(*, false_delay_safe: bool, coverage_ready: bool) -> str:
    if false_delay_safe and coverage_ready:
        return "coverage_ready_and_false_delay_safe"
    if false_delay_safe:
        return "false_delay_safe_but_low_coverage"
    if coverage_ready:
        return "coverage_ready_but_false_delay_unsafe"
    return "low_coverage_and_false_delay_unsafe"


def _best_epoch(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {}
    return dict(
        max(
            rows,
            key=lambda row: (
                float(row.get("accepted_batch_roi") or float("-inf")),
                int(row.get("accepted_batch_count") or 0),
                -float(row.get("validation_loss") or float("inf")),
            ),
        )
    )


def _recommended_next_step(
    *,
    constrained_rows: list[dict[str, Any]],
    class_counts: Counter[str],
) -> str:
    if constrained_rows:
        return "rerun_threshold_frontier_for_candidate_epoch_and_verify_full_stage3_gate"
    if class_counts.get("false_delay_safe_but_low_coverage", 0) and class_counts.get(
        "coverage_ready_but_false_delay_unsafe",
        0,
    ):
        return "not_a_checkpoint_selection_problem_collect_context_local_hard_negatives"
    if class_counts.get("false_delay_safe_but_low_coverage", 0):
        return "increase_safe_shell_coverage_without_relaxing_false_delay_gate"
    return "repair_false_delay_ranking_before_more_threshold_sweeps"


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GAT Batch Impact Epoch Selector 审计报告",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 结论",
        "",
        "本报告只审计训练 epoch history 中的 Stage 3 constrained selector 轨迹，",
        "不运行 BPC、pricing、RMP、worker 或 certificate。",
        "",
        "```text",
        f"epoch_count = {summary['epoch_count']}",
        f"history_source = {summary['history_source']}",
        f"min_confidence_all_success_count = {summary['min_confidence_all_success_count']}",
        f"false_delay_safe_epoch_count = {summary['false_delay_safe_epoch_count']}",
        f"coverage_confidence_ready_epoch_count = {summary['coverage_confidence_ready_epoch_count']}",
        "coverage_and_false_delay_safe_epoch_count = "
        f"{summary['coverage_and_false_delay_safe_epoch_count']}",
        f"epoch_signal_class_counts = {summary['epoch_signal_class_counts']}",
        f"primary = {summary['diagnosis']['primary']}",
        "checkpoint_selection_is_primary_blocker = "
        f"{str(summary['diagnosis']['checkpoint_selection_is_primary_blocker']).lower()}",
        f"recommended_next_step = {summary['diagnosis']['recommended_next_step']}",
        "production_ready = false",
        "selector_can_certificate = false",
        "```",
        "",
        "## Best Epochs",
        "",
        "```json",
        json.dumps(
            {
                "best_false_delay_safe_epoch": summary["best_false_delay_safe_epoch"],
                "best_coverage_ready_epoch": summary["best_coverage_ready_epoch"],
                "best_overall_epoch": summary["best_overall_epoch"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## Epoch Rows",
        "",
        "| epoch | class | accepted | ROI | false-delay | HP precision | safe precision | validation loss |",
        "|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary["epoch_rows"]:
        lines.append(
            "| {epoch} | {klass} | {accepted} | {roi} | {false_delay} | {hp} | {safe} | {vloss} |".format(
                epoch=row.get("epoch"),
                klass=row.get("epoch_signal_class"),
                accepted=row.get("accepted_batch_count"),
                roi=_fmt(row.get("accepted_batch_roi")),
                false_delay=_fmt(row.get("false_high_priority_on_delay")),
                hp=_fmt(row.get("high_priority_precision")),
                safe=_fmt(row.get("safe_precision")),
                vloss=_fmt(row.get("validation_loss")),
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- 若存在 `coverage_ready_and_false_delay_safe`，才说明 checkpoint selection 可能漏选了可行 epoch；",
            "- 若同时存在 `false_delay_safe_but_low_coverage` 和 `coverage_ready_but_false_delay_unsafe`，说明问题更像 coverage / false-delay tradeoff，而不是单纯 checkpoint selection；",
            "- 当前 epoch history 若缺少 CI / false-safe / family holdout 字段，不能直接证明 Stage 4 candidate，只能证明趋势。",
            "",
            "## Exactness Boundary",
            "",
            "- `diagnostic_only=true`；",
            "- `runs_bpc_or_pricing=false`；",
            "- `selector_is_pricing_oracle=false`；",
            "- `selector_can_certificate=false`；",
            "- `gate_can_permanently_discard_negative_columns=false`；",
            "- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _fmt(value: Any) -> str:
    if value is None:
        return "None"
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


if __name__ == "__main__":
    raise SystemExit(main())
