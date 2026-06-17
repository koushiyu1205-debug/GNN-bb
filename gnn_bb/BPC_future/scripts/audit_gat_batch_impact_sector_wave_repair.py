#!/usr/bin/env python3
"""Audit sector-wave high-ROI repair targets after coverage-frontier failure.

This script is offline/diagnostic-only.  It consumes the v105
coverage-constrained frontier summary, replays each run's best coverage
candidate on the validation split, and catalogs sector-wave high-ROI misses,
low-ROI accepts, and context-local repair priorities.  It does not run BPC,
pricing, RMP, workers, or certificate logic.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import sys
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch

from BPC_future.learning.batch_impact_model import GATBatchImpactModel
from BPC_future.scripts.audit_gat_batch_impact_opportunity_mining import (
    _attach_sample_metadata,
    classify_opportunity_record,
)
from BPC_future.scripts.audit_gat_batch_impact_threshold_frontier import (
    _assert_contracts,
    _read_json,
    records_for_split,
)
from BPC_future.scripts.train_gat_batch_impact import (
    _load_sample,
    _normalize_sample,
    _prediction_records,
)


DEFAULT_COVERAGE_SUMMARY = Path(
    "BPC_future/results/gat_batch_impact_coverage_constrained_frontier_v105_v99_v102_v103_20260617/summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/gat_batch_impact_sector_wave_repair_v106_v105_frontier_20260617"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260617_bpc_future_gat_target_mode_stage3_v106_sector_wave_repair_audit_zh.md"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coverage-summary", type=Path, default=DEFAULT_COVERAGE_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--focus-family", default="sector-wave")
    parser.add_argument("--top-contexts", type=int, default=20)
    parser.add_argument(
        "--run-name",
        action="append",
        default=None,
        help="Optional run name filter. May be repeated.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = audit_sector_wave_repair(
        coverage_summary=Path(args.coverage_summary),
        output_dir=Path(args.output_dir),
        report=Path(args.report),
        device=str(args.device),
        focus_family=str(args.focus_family),
        top_contexts=max(1, int(args.top_contexts)),
        run_names=set(str(name) for name in args.run_name) if args.run_name else None,
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def audit_sector_wave_repair(
    *,
    coverage_summary: Path = DEFAULT_COVERAGE_SUMMARY,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    device: str = "cpu",
    focus_family: str = "sector-wave",
    top_contexts: int = 20,
    run_names: set[str] | None = None,
) -> dict[str, Any]:
    coverage = _read_json(Path(coverage_summary))
    _assert_coverage_contract(coverage)
    selected_runs = [
        run
        for run in coverage.get("runs", [])
        if run_names is None or str(run.get("run_name")) in run_names
    ]
    if not selected_runs:
        raise ValueError("no runs selected from coverage summary")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    run_summaries = [
        _audit_run(
            run=run,
            output_dir=output_dir,
            device=device,
            focus_family=focus_family,
            top_contexts=top_contexts,
        )
        for run in selected_runs
    ]
    aggregate_context_counts = Counter(
        context["primary_repair_action"]
        for run in run_summaries
        for context in run.get("top_context_repair_rows", [])
    )
    summary = {
        "schema_version": "gat_batch_impact_sector_wave_repair_audit_v1",
        "status": "gat_batch_impact_sector_wave_repair_audited",
        "coverage_summary": str(coverage_summary),
        "output_dir": str(output_dir),
        "report": str(report),
        "focus_family": str(focus_family),
        "run_count": len(run_summaries),
        "runs": run_summaries,
        "aggregate_primary_repair_action_counts": dict(sorted(aggregate_context_counts.items())),
        "recommended_next_step": _recommended_next_step(run_summaries),
        "stage3_completed": False,
        "stage4_candidate_ready": False,
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "runs_rmp": False,
        "production_ready": False,
        "default_enabled": False,
        "official_bound_effect": False,
        "selector_is_pricing_oracle": False,
        "selector_can_certificate": False,
        "gate_can_permanently_discard_negative_columns": False,
        "all_checks_pass": True,
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(Path(report), summary)
    return summary


def build_context_repair_rows(
    decisions: list[dict[str, Any]],
    *,
    focus_family: str = "sector-wave",
) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in decisions:
        if str(item.get("family")) != str(focus_family):
            continue
        groups[(str(item.get("context_hash") or ""), str(item.get("instance_path") or ""))].append(item)

    rows = []
    for (context_hash, instance_path), items in sorted(groups.items()):
        high_roi = [item for item in items if bool(item.get("is_high_roi_opportunity"))]
        missed_high_roi = [
            item for item in items if bool(item.get("is_missed_high_roi_opportunity"))
        ]
        accepted_high_roi = [
            item for item in items if bool(item.get("is_accepted_high_roi_opportunity"))
        ]
        accepted_low_roi_or_bad = [
            item for item in items if bool(item.get("is_accepted_low_roi_or_bad"))
        ]
        reason_counts = Counter(
            str(reason)
            for item in missed_high_roi
            for reason in item.get("missed_reasons") or []
        )
        task_counts = Counter(str(item.get("task_count") or 0) for item in items)
        high_roi_count = len(high_roi)
        rows.append(
            {
                "context_hash": context_hash,
                "instance_path": instance_path,
                "family": str(focus_family),
                "task_count_counts": dict(sorted(task_counts.items())),
                "record_count": len(items),
                "high_roi_opportunity_count": high_roi_count,
                "accepted_high_roi_count": len(accepted_high_roi),
                "missed_high_roi_count": len(missed_high_roi),
                "accepted_low_roi_or_bad_count": len(accepted_low_roi_or_bad),
                "high_roi_capture_rate": (
                    len(accepted_high_roi) / float(high_roi_count)
                    if high_roi_count
                    else None
                ),
                "max_high_roi_label": _max_or_none(
                    float(item.get("accepted_batch_roi_label") or 0.0)
                    for item in high_roi
                ),
                "max_missed_high_roi_label": _max_or_none(
                    float(item.get("accepted_batch_roi_label") or 0.0)
                    for item in missed_high_roi
                ),
                "mean_missed_safe_candidate_margin": _mean_or_none(
                    float(item.get("max_safe_candidate_score_margin") or 0.0)
                    for item in missed_high_roi
                ),
                "mean_missed_batch_margin": _mean_or_none(
                    float(item.get("batch_score_margin") or 0.0)
                    for item in missed_high_roi
                ),
                "missed_reason_counts": dict(sorted(reason_counts.items())),
                "primary_repair_action": primary_repair_action(
                    missed_high_roi=missed_high_roi,
                    accepted_low_roi_or_bad=accepted_low_roi_or_bad,
                ),
                "top_missed_examples": sorted(
                    [
                        _decision_snapshot(item)
                        for item in missed_high_roi
                    ],
                    key=lambda item: float(item.get("accepted_batch_roi_label") or 0.0),
                    reverse=True,
                )[:5],
                "top_low_roi_or_bad_accepts": sorted(
                    [
                        _decision_snapshot(item)
                        for item in accepted_low_roi_or_bad
                    ],
                    key=lambda item: float(item.get("accepted_batch_roi_label") or 0.0),
                )[:5],
            }
        )
    return rows


def primary_repair_action(
    *,
    missed_high_roi: list[dict[str, Any]],
    accepted_low_roi_or_bad: list[dict[str, Any]],
) -> str:
    if missed_high_roi and accepted_low_roi_or_bad:
        return "same_context_high_roi_vs_low_roi_contrast"
    if any(
        "candidate_risk_adjusted_below_threshold" in (item.get("missed_reasons") or [])
        or "candidate_delay_risk_above_threshold" in (item.get("missed_reasons") or [])
        for item in missed_high_roi
    ):
        return "delay_risk_or_risk_adjusted_score_repair"
    if any("no_candidate_above_threshold" in (item.get("missed_reasons") or []) for item in missed_high_roi):
        return "candidate_score_repair"
    if any("batch_score_below_family_threshold" in (item.get("missed_reasons") or []) for item in missed_high_roi):
        return "batch_score_repair"
    if any(
        "family_delay_fallback" in (item.get("missed_reasons") or [])
        or "context_delay_fallback" in (item.get("missed_reasons") or [])
        for item in missed_high_roi
    ):
        return "fallback_rule_repair"
    if missed_high_roi:
        return "unclassified_high_roi_miss_repair"
    if accepted_low_roi_or_bad:
        return "low_roi_acceptance_suppression"
    return "no_sector_wave_repair_needed"


def _audit_run(
    *,
    run: dict[str, Any],
    output_dir: Path,
    device: str,
    focus_family: str,
    top_contexts: int,
) -> dict[str, Any]:
    selected_threshold = dict(run.get("best_coverage_candidate") or {})
    if not selected_threshold:
        raise ValueError(f"{run.get('run_name')}: missing best_coverage_candidate")
    checkpoint_path = Path(str(run["checkpoint"]))
    training_path = Path(str(run["training_summary"]))
    dataset_dir = Path(str(run["dataset_dir"]))
    checkpoint_data = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    training = _read_json(training_path)
    manifest = _read_json(dataset_dir / "manifest.json")
    _assert_contracts(checkpoint_data, training, manifest)
    gate_config = dict(checkpoint_data.get("deployment_gate", {}).get("gate_config") or {})
    if not gate_config:
        raise ValueError(f"{run.get('run_name')}: missing deployment gate config")

    model = GATBatchImpactModel(**checkpoint_data["model_config"]).to(torch.device(device))
    model.load_state_dict(checkpoint_data["model_state_dict"])
    model.eval()
    samples = [
        _normalize_sample(_load_sample(dataset_dir / item["path"]), manifest)
        for item in manifest.get("samples", [])
    ]
    prediction_records = _prediction_records(model, samples, torch.device(device))
    record_items = [
        (
            str(
                getattr(sample, "batch_impact_instance_path", "")
                or getattr(sample, "batch_impact_instance", "")
            ),
            _attach_sample_metadata(record, sample),
        )
        for sample, record in zip(samples, prediction_records)
    ]
    split = training.get("split") or checkpoint_data.get("training_contract", {}).get("main_split") or {}
    _, validation_records = records_for_split(
        record_items,
        train_instances={str(instance) for instance in split.get("train_instances", [])},
        validation_instances={str(instance) for instance in split.get("validation_instances", [])},
    )
    if not validation_records:
        raise ValueError(f"{run.get('run_name')}: validation split is empty")

    decisions = [
        classify_opportunity_record(
            record,
            batch_threshold=float(selected_threshold["batch_threshold"]),
            candidate_threshold=float(selected_threshold["candidate_threshold"]),
            candidate_delay_gate_enabled=bool(selected_threshold.get("candidate_delay_gate_enabled", False)),
            candidate_delay_risk_threshold=float(selected_threshold.get("candidate_delay_risk_threshold", 1.0)),
            candidate_admission_score_mode=str(
                selected_threshold.get("candidate_admission_score_mode", "high_priority")
                or "high_priority"
            ),
            candidate_delay_score_penalty=float(selected_threshold.get("candidate_delay_score_penalty", 0.0)),
            candidate_rescue_raw_score_threshold=float(
                selected_threshold.get("candidate_rescue_raw_score_threshold", 1.0)
            ),
            candidate_rescue_delay_risk_threshold=float(
                selected_threshold.get("candidate_rescue_delay_risk_threshold", 1.0)
            ),
            candidate_rescue_delay_score_penalty=float(
                selected_threshold.get("candidate_rescue_delay_score_penalty", 0.0)
            ),
            batch_thresholds_by_family=dict(selected_threshold.get("batch_thresholds_by_family") or {}),
            family_delay_fallback_families=list(
                selected_threshold.get("family_delay_fallback_families") or []
            ),
            context_delay_fallback_contexts=list(
                selected_threshold.get("context_delay_fallback_contexts") or []
            ),
            min_accepted_batch_roi=float(gate_config["min_accepted_batch_roi"]),
        )
        for record in validation_records
    ]
    family_decisions = [item for item in decisions if str(item.get("family")) == str(focus_family)]
    context_rows = build_context_repair_rows(decisions, focus_family=focus_family)
    top_context_rows = sorted(
        context_rows,
        key=lambda row: (
            int(row["missed_high_roi_count"]),
            float(row.get("max_missed_high_roi_label") or 0.0),
            int(row["accepted_low_roi_or_bad_count"]),
        ),
        reverse=True,
    )[: int(top_contexts)]
    missed = [item for item in family_decisions if bool(item.get("is_missed_high_roi_opportunity"))]
    accepted_high_roi = [
        item for item in family_decisions if bool(item.get("is_accepted_high_roi_opportunity"))
    ]
    accepted_low_roi_or_bad = [
        item for item in family_decisions if bool(item.get("is_accepted_low_roi_or_bad"))
    ]
    reason_counts = Counter(
        str(reason)
        for item in missed
        for reason in item.get("missed_reasons") or []
    )
    action_counts = Counter(str(row["primary_repair_action"]) for row in context_rows)

    run_name = str(run["run_name"])
    decisions_path = output_dir / f"{run_name}_{focus_family}_validation_decisions.jsonl"
    missed_path = output_dir / f"{run_name}_{focus_family}_missed_high_roi.jsonl"
    contexts_path = output_dir / f"{run_name}_{focus_family}_context_repair_rows.jsonl"
    _write_jsonl(decisions_path, family_decisions)
    _write_jsonl(missed_path, sorted(missed, key=_decision_sort_key))
    _write_jsonl(contexts_path, sorted(context_rows, key=_context_sort_key))

    high_roi_count = sum(int(bool(item.get("is_high_roi_opportunity"))) for item in family_decisions)
    run_summary = {
        "run_name": run_name,
        "checkpoint": str(checkpoint_path),
        "training_summary": str(training_path),
        "dataset_dir": str(dataset_dir),
        "focus_family": str(focus_family),
        "validation_record_count": len(validation_records),
        "family_record_count": len(family_decisions),
        "family_high_roi_opportunity_count": int(high_roi_count),
        "family_accepted_high_roi_count": len(accepted_high_roi),
        "family_missed_high_roi_count": len(missed),
        "family_accepted_low_roi_or_bad_count": len(accepted_low_roi_or_bad),
        "family_high_roi_capture_rate": (
            len(accepted_high_roi) / float(high_roi_count) if high_roi_count else None
        ),
        "missed_reason_counts": dict(sorted(reason_counts.items())),
        "primary_repair_action_counts": dict(sorted(action_counts.items())),
        "selected_threshold": _threshold_snapshot(selected_threshold),
        "coverage_frontier_best_reject_reasons": selected_threshold.get("coverage_reject_reasons", []),
        "context_repair_row_count": len(context_rows),
        "top_context_repair_rows": top_context_rows,
        "validation_decisions_path": str(decisions_path),
        "missed_high_roi_path": str(missed_path),
        "context_repair_rows_path": str(contexts_path),
    }
    return run_summary


def _decision_snapshot(item: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "context_hash",
        "instance_path",
        "task_count",
        "accepted",
        "is_high_roi_opportunity",
        "is_missed_high_roi_opportunity",
        "missed_reasons",
        "accepted_batch_roi_label",
        "batch_score",
        "family_batch_threshold",
        "batch_score_margin",
        "candidate_threshold",
        "candidate_admission_score_mode",
        "candidate_delay_score_penalty",
        "candidate_delay_gate_enabled",
        "candidate_delay_risk_threshold",
        "max_candidate_score",
        "max_candidate_score_margin",
        "max_raw_candidate_score",
        "max_raw_candidate_score_margin",
        "max_safe_candidate_score",
        "max_safe_candidate_score_margin",
        "max_delay_candidate_score",
        "candidate_delay_gate_blocked_count",
        "candidate_risk_adjusted_suppressed_count",
        "predicted_candidate_count",
        "predicted_safe_candidate_count",
        "predicted_delay_candidate_count",
        "delay_candidate_label_count",
        "true_high_priority_candidate_count",
    )
    return {key: item.get(key) for key in keys if key in item}


def _threshold_snapshot(row: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "threshold_scope",
        "threshold_mode",
        "batch_threshold",
        "candidate_threshold",
        "candidate_admission_score_mode",
        "candidate_delay_score_penalty",
        "candidate_delay_gate_enabled",
        "candidate_delay_risk_threshold",
        "accepted_batch_count",
        "accepted_batch_roi",
        "accepted_batch_roi_ci_low",
        "safe_precision_ci_low",
        "false_safe_rate_union",
        "sector_wave_accepted_high_roi_count",
        "sector_wave_oracle_high_roi_count",
        "threshold_local_gate_pass",
        "threshold_local_reject_reasons",
        "coverage_constraint_pass",
        "coverage_reject_reasons",
    )
    return {key: row.get(key) for key in keys if key in row}


def _recommended_next_step(run_summaries: list[dict[str, Any]]) -> str:
    action_counts = Counter(
        action
        for run in run_summaries
        for action, count in run.get("primary_repair_action_counts", {}).items()
        for _ in range(int(count))
    )
    if action_counts.get("same_context_high_roi_vs_low_roi_contrast", 0) > 0:
        return "collect_or_train_same_context_sector_wave_high_roi_vs_low_roi_contrast"
    if action_counts.get("delay_risk_or_risk_adjusted_score_repair", 0) > 0:
        return "repair_sector_wave_delay_risk_or_risk_adjusted_candidate_scores"
    if action_counts.get("candidate_score_repair", 0) > 0:
        return "repair_sector_wave_candidate_score_margins"
    return "collect_more_sector_wave_context_local_intervention_rows"


def _assert_coverage_contract(coverage: dict[str, Any]) -> None:
    if coverage.get("schema_version") != "gat_batch_impact_coverage_constrained_frontier_v1":
        raise ValueError("coverage summary schema mismatch")
    if bool(coverage.get("production_ready")):
        raise ValueError("coverage summary must not be production_ready")
    if not bool(coverage.get("diagnostic_only")):
        raise ValueError("coverage summary must be diagnostic_only")


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 2026-06-17 BPC_future GAT Target Mode Stage 3 v106 Sector-wave Repair Audit 报告",
        "",
        "## 结论",
        "",
        "本报告只做离线 Stage 3 诊断：读取 v105 coverage frontier，重放各 run 的 best coverage candidate，定位 sector-wave high-ROI miss 和 low-ROI accept 的 context-local 修复方向。",
        "",
        "```text",
        f"focus_family = {summary['focus_family']}",
        f"run_count = {summary['run_count']}",
        f"recommended_next_step = {summary['recommended_next_step']}",
        "stage3_completed = false",
        "stage4_candidate_ready = false",
        "selector_can_certificate = false",
        "```",
        "",
        "## Run Comparison",
        "",
        "| run | high-ROI | accepted high-ROI | missed high-ROI | low-ROI/bad accepts | capture | primary actions |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for run in summary["runs"]:
        capture = run.get("family_high_roi_capture_rate")
        lines.append(
            "| {run} | {high} | {accepted} | {missed} | {low} | {capture} | {actions} |".format(
                run=run["run_name"],
                high=run["family_high_roi_opportunity_count"],
                accepted=run["family_accepted_high_roi_count"],
                missed=run["family_missed_high_roi_count"],
                low=run["family_accepted_low_roi_or_bad_count"],
                capture="None" if capture is None else f"{float(capture):.4f}",
                actions=run["primary_repair_action_counts"],
            )
        )
    lines.extend(["", "## Top Contexts", ""])
    for run in summary["runs"]:
        lines.extend(
            [
                f"### {run['run_name']}",
                "",
                "```json",
                json.dumps(
                    {
                        "selected_threshold": run["selected_threshold"],
                        "missed_reason_counts": run["missed_reason_counts"],
                        "top_context_repair_rows": [
                            _context_report_snapshot(row)
                            for row in run["top_context_repair_rows"][:10]
                        ],
                        "context_repair_rows_path": run["context_repair_rows_path"],
                        "missed_high_roi_path": run["missed_high_roi_path"],
                    },
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                ),
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## Exactness Boundary",
            "",
            "```text",
            "diagnostic_only = true",
            "runs_bpc_or_pricing = false",
            "runs_rmp = false",
            "official_bound_effect = false",
            "selector_is_pricing_oracle = false",
            "selector_can_certificate = false",
            "gate_can_permanently_discard_negative_columns = false",
            "```",
            "",
            "这些 context 只能指导 Stage 2/3 数据采集和训练；不能作为 HIGH_PRIORITY admission、pricing oracle 或 certificate 依据。最终 certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows)
        + ("\n" if rows else ""),
        encoding="utf-8",
    )


def _context_report_snapshot(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "context_hash": row.get("context_hash"),
        "instance": Path(str(row.get("instance_path") or "")).name,
        "task_count_counts": row.get("task_count_counts"),
        "record_count": row.get("record_count"),
        "high_roi_opportunity_count": row.get("high_roi_opportunity_count"),
        "accepted_high_roi_count": row.get("accepted_high_roi_count"),
        "missed_high_roi_count": row.get("missed_high_roi_count"),
        "accepted_low_roi_or_bad_count": row.get("accepted_low_roi_or_bad_count"),
        "high_roi_capture_rate": row.get("high_roi_capture_rate"),
        "max_missed_high_roi_label": row.get("max_missed_high_roi_label"),
        "mean_missed_safe_candidate_margin": row.get("mean_missed_safe_candidate_margin"),
        "mean_missed_batch_margin": row.get("mean_missed_batch_margin"),
        "missed_reason_counts": row.get("missed_reason_counts"),
        "primary_repair_action": row.get("primary_repair_action"),
    }


def _decision_sort_key(item: dict[str, Any]) -> tuple[Any, ...]:
    return (
        -float(item.get("accepted_batch_roi_label") or 0.0),
        str(item.get("context_hash") or ""),
    )


def _context_sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        -int(row.get("missed_high_roi_count") or 0),
        -float(row.get("max_missed_high_roi_label") or 0.0),
        -int(row.get("accepted_low_roi_or_bad_count") or 0),
        str(row.get("context_hash") or ""),
    )


def _mean_or_none(values: Any) -> float | None:
    collected = list(values)
    return float(mean(collected)) if collected else None


def _max_or_none(values: Any) -> float | None:
    collected = list(values)
    return max(collected) if collected else None


if __name__ == "__main__":
    raise SystemExit(main())
