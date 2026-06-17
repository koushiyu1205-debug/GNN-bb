#!/usr/bin/env python3
"""Audit coverage-constrained GAT batch-impact threshold frontiers.

This script is offline/diagnostic-only.  It compares one or more existing
``GATBatchImpactModel`` checkpoints on their validation split, then asks a
deployment-facing question that the ordinary threshold frontier does not make
primary: is there a threshold surface that is both safety-constrained and still
covers the high-ROI families, especially the current 20-task sector-wave area?

It does not run BPC, pricing, RMP, workers, or certificate logic.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch

from BPC_future.learning.batch_impact_model import GATBatchImpactModel
from BPC_future.scripts.audit_gat_batch_impact_threshold_frontier import (
    _assert_contracts,
    _read_json,
    evaluate_threshold_frontier_records,
    records_for_split,
)
from BPC_future.scripts.train_gat_batch_impact import (
    _load_sample,
    _normalize_sample,
    _prediction_records,
)


DEFAULT_RUN_SPECS = (
    "v99:"
    "BPC_future/results/gat_batch_impact_training_v99_seed13_explicit_focused_combined_head_v75_20260617/checkpoint.pt:"
    "BPC_future/results/gat_batch_impact_training_v99_seed13_explicit_focused_combined_head_v75_20260617/metrics.json",
    "v102:"
    "BPC_future/results/gat_batch_impact_training_v102_seed13_safety_constrained_focused_combined_v75_20260617/checkpoint.pt:"
    "BPC_future/results/gat_batch_impact_training_v102_seed13_safety_constrained_focused_combined_v75_20260617/metrics.json",
    "v103:"
    "BPC_future/results/gat_batch_impact_training_v103_seed13_light_safety_focused_combined_v75_20260617/checkpoint.pt:"
    "BPC_future/results/gat_batch_impact_training_v103_seed13_light_safety_focused_combined_v75_20260617/metrics.json",
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/gat_batch_impact_coverage_constrained_frontier_v105_v99_v102_v103_20260617"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260617_bpc_future_gat_target_mode_stage3_v105_coverage_constrained_frontier_zh.md"
)


@dataclass(frozen=True)
class RunSpec:
    name: str
    checkpoint: Path
    training_summary: Path
    dataset_dir: Path | None = None


@dataclass(frozen=True)
class CoverageConstraints:
    max_false_safe_rate_union: float = 0.01
    max_false_high_priority_on_delay: float = 0.01
    min_safe_precision_ci_low: float = 0.85
    min_accepted_batch_count: int = 1
    max_accepted_bad_mode_count: int = 0
    min_family_accepted_high_roi_count: int = 1
    min_family_high_roi_capture_rate: float = 0.0
    required_high_roi_families: tuple[str, ...] = ("sector-wave",)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-spec",
        action="append",
        default=None,
        help=(
            "Run spec as name:checkpoint:training_summary[:dataset_dir]. "
            "May be repeated. Defaults to v99/v102/v103."
        ),
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--max-dynamic-thresholds", type=int, default=128)
    parser.add_argument("--top-k", type=int, default=20)
    parser.add_argument("--max-false-safe-rate-union", type=float, default=0.01)
    parser.add_argument("--max-false-high-priority-on-delay", type=float, default=0.01)
    parser.add_argument("--min-safe-precision-ci-low", type=float, default=0.85)
    parser.add_argument("--min-accepted-batch-count", type=int, default=1)
    parser.add_argument("--max-accepted-bad-mode-count", type=int, default=0)
    parser.add_argument("--min-family-accepted-high-roi-count", type=int, default=1)
    parser.add_argument("--min-family-high-roi-capture-rate", type=float, default=0.0)
    parser.add_argument(
        "--required-high-roi-family",
        action="append",
        default=None,
        help="Family with oracle high-ROI opportunity that must not have zero accepted high-ROI.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    constraints = CoverageConstraints(
        max_false_safe_rate_union=float(args.max_false_safe_rate_union),
        max_false_high_priority_on_delay=float(args.max_false_high_priority_on_delay),
        min_safe_precision_ci_low=float(args.min_safe_precision_ci_low),
        min_accepted_batch_count=max(1, int(args.min_accepted_batch_count)),
        max_accepted_bad_mode_count=max(0, int(args.max_accepted_bad_mode_count)),
        min_family_accepted_high_roi_count=max(0, int(args.min_family_accepted_high_roi_count)),
        min_family_high_roi_capture_rate=max(0.0, float(args.min_family_high_roi_capture_rate)),
        required_high_roi_families=tuple(
            str(item) for item in (args.required_high_roi_family or ["sector-wave"])
        ),
    )
    summary = audit_coverage_constrained_frontier(
        run_specs=[parse_run_spec(text) for text in (args.run_spec or DEFAULT_RUN_SPECS)],
        output_dir=args.output_dir,
        report=args.report,
        device=str(args.device),
        max_dynamic_thresholds=max(1, int(args.max_dynamic_thresholds)),
        top_k=max(1, int(args.top_k)),
        constraints=constraints,
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def parse_run_spec(text: str) -> RunSpec:
    parts = str(text).split(":")
    if len(parts) not in {3, 4}:
        raise ValueError(
            "run spec must be name:checkpoint:training_summary[:dataset_dir]"
        )
    dataset_dir = Path(parts[3]) if len(parts) == 4 and parts[3] else None
    return RunSpec(
        name=parts[0],
        checkpoint=Path(parts[1]),
        training_summary=Path(parts[2]),
        dataset_dir=dataset_dir,
    )


def audit_coverage_constrained_frontier(
    *,
    run_specs: list[RunSpec],
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    device: str = "cpu",
    max_dynamic_thresholds: int = 128,
    top_k: int = 20,
    constraints: CoverageConstraints = CoverageConstraints(),
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    run_summaries = [
        _audit_run(
            run_spec=run_spec,
            output_dir=output_dir,
            device=device,
            max_dynamic_thresholds=int(max_dynamic_thresholds),
            top_k=int(top_k),
            constraints=constraints,
        )
        for run_spec in run_specs
    ]
    coverage_gate_runs = [
        run["run_name"]
        for run in run_summaries
        if int(run["coverage_constrained_gate_pass_count"]) > 0
    ]
    coverage_constraint_runs = [
        run["run_name"]
        for run in run_summaries
        if int(run["coverage_constraint_pass_count"]) > 0
    ]
    aggregate_reject_counts = Counter(
        reason
        for run in run_summaries
        for reason, count in run["coverage_reject_reason_counts"].items()
        for _ in range(int(count))
    )
    summary = {
        "schema_version": "gat_batch_impact_coverage_constrained_frontier_v1",
        "status": "gat_batch_impact_coverage_constrained_frontier_audited",
        "output_dir": str(output_dir),
        "report": str(report),
        "run_count": len(run_summaries),
        "runs": run_summaries,
        "constraints": {
            "max_false_safe_rate_union": constraints.max_false_safe_rate_union,
            "max_false_high_priority_on_delay": constraints.max_false_high_priority_on_delay,
            "min_safe_precision_ci_low": constraints.min_safe_precision_ci_low,
            "min_accepted_batch_count": constraints.min_accepted_batch_count,
            "max_accepted_bad_mode_count": constraints.max_accepted_bad_mode_count,
            "min_family_accepted_high_roi_count": constraints.min_family_accepted_high_roi_count,
            "min_family_high_roi_capture_rate": constraints.min_family_high_roi_capture_rate,
            "required_high_roi_families": list(constraints.required_high_roi_families),
        },
        "coverage_constraint_pass_runs": coverage_constraint_runs,
        "coverage_constrained_gate_pass_runs": coverage_gate_runs,
        "coverage_constraint_pass_run_count": len(coverage_constraint_runs),
        "coverage_constrained_gate_pass_run_count": len(coverage_gate_runs),
        "aggregate_coverage_reject_reason_counts": dict(sorted(aggregate_reject_counts.items())),
        "stage3_completed": False,
        "stage4_candidate_ready": False,
        "recommended_next_step": _recommended_next_step(run_summaries),
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


def coverage_constraint_summary(
    row: dict[str, Any],
    *,
    constraints: CoverageConstraints = CoverageConstraints(),
) -> dict[str, Any]:
    reasons = coverage_reject_reasons(row, constraints=constraints)
    per_family = dict(row.get("family_holdout_per_family") or {})
    oracle_family_count = sum(
        1
        for metrics in per_family.values()
        if int(metrics.get("oracle_high_roi_count") or 0) > 0
    )
    accepted_high_roi_family_count = sum(
        1
        for metrics in per_family.values()
        if int(metrics.get("oracle_high_roi_count") or 0) > 0
        and int(metrics.get("accepted_high_roi_count") or 0)
        >= int(constraints.min_family_accepted_high_roi_count)
    )
    sector = per_family.get("sector-wave") or {}
    return {
        "coverage_constraint_pass": not reasons,
        "coverage_reject_reasons": reasons,
        "coverage_constrained_gate_pass": (
            not reasons and bool(row.get("threshold_local_gate_pass"))
        ),
        "oracle_high_roi_family_count": int(oracle_family_count),
        "accepted_high_roi_family_count": int(accepted_high_roi_family_count),
        "sector_wave_oracle_high_roi_count": int(sector.get("oracle_high_roi_count") or 0),
        "sector_wave_accepted_high_roi_count": int(sector.get("accepted_high_roi_count") or 0),
        "sector_wave_high_roi_capture_rate": sector.get("high_roi_capture_rate"),
    }


def coverage_reject_reasons(
    row: dict[str, Any],
    *,
    constraints: CoverageConstraints = CoverageConstraints(),
) -> list[str]:
    reasons: list[str] = []
    if float(row.get("false_safe_rate_union") or 0.0) > constraints.max_false_safe_rate_union:
        reasons.append("false_safe_rate_union_above_coverage_limit")
    if (
        float(row.get("false_high_priority_on_delay") or 0.0)
        > constraints.max_false_high_priority_on_delay
    ):
        reasons.append("false_high_priority_on_delay_above_coverage_limit")
    safe_ci = row.get("safe_precision_ci_low")
    if safe_ci is None or float(safe_ci) < constraints.min_safe_precision_ci_low:
        reasons.append("safe_precision_ci_low_below_coverage_limit")
    if int(row.get("accepted_batch_count") or 0) < constraints.min_accepted_batch_count:
        reasons.append("accepted_batch_count_below_coverage_limit")
    if int(row.get("accepted_bad_mode_count") or 0) > constraints.max_accepted_bad_mode_count:
        reasons.append("accepted_bad_mode_count_above_coverage_limit")

    per_family = row.get("family_holdout_per_family")
    if not isinstance(per_family, dict) or not per_family:
        reasons.append("family_holdout_per_family_missing")
        return reasons

    oracle_families = {
        str(family): dict(metrics)
        for family, metrics in per_family.items()
        if int(dict(metrics).get("oracle_high_roi_count") or 0) > 0
    }
    if not oracle_families:
        reasons.append("oracle_high_roi_family_missing")
    for family, metrics in sorted(oracle_families.items()):
        accepted_high_roi = int(metrics.get("accepted_high_roi_count") or 0)
        if accepted_high_roi < constraints.min_family_accepted_high_roi_count:
            reasons.append(f"family_high_roi_capture_count_below_limit:{family}")
        capture_rate = metrics.get("high_roi_capture_rate")
        if capture_rate is None or float(capture_rate) < constraints.min_family_high_roi_capture_rate:
            reasons.append(f"family_high_roi_capture_rate_below_limit:{family}")

    for family in constraints.required_high_roi_families:
        metrics = per_family.get(family)
        if not isinstance(metrics, dict):
            reasons.append(f"required_high_roi_family_missing:{family}")
            continue
        oracle_count = int(metrics.get("oracle_high_roi_count") or 0)
        accepted_high_roi = int(metrics.get("accepted_high_roi_count") or 0)
        if oracle_count > 0 and accepted_high_roi < constraints.min_family_accepted_high_roi_count:
            reasons.append(f"required_high_roi_family_zero_capture:{family}")
    return sorted(dict.fromkeys(reasons))


def _audit_run(
    *,
    run_spec: RunSpec,
    output_dir: Path,
    device: str,
    max_dynamic_thresholds: int,
    top_k: int,
    constraints: CoverageConstraints,
) -> dict[str, Any]:
    checkpoint_data = torch.load(run_spec.checkpoint, map_location="cpu", weights_only=False)
    training = _read_json(run_spec.training_summary)
    dataset_dir = run_spec.dataset_dir or Path(str(training.get("dataset_dir") or ""))
    if not str(dataset_dir):
        raise ValueError(f"{run_spec.name}: dataset_dir missing from run spec and training summary")
    manifest = _read_json(dataset_dir / "manifest.json")
    _assert_contracts(checkpoint_data, training, manifest)

    model = GATBatchImpactModel(**checkpoint_data["model_config"]).to(torch.device(device))
    model.load_state_dict(checkpoint_data["model_state_dict"])
    model.eval()
    samples = [
        _normalize_sample(_load_sample(dataset_dir / item["path"]), manifest)
        for item in manifest.get("samples", [])
    ]
    records = _prediction_records(model, samples, torch.device(device))
    record_items = [
        (
            str(
                getattr(sample, "batch_impact_instance_path", "")
                or getattr(sample, "batch_impact_instance", "")
            ),
            record,
        )
        for sample, record in zip(samples, records)
    ]
    split = training.get("split") or checkpoint_data.get("training_contract", {}).get("main_split") or {}
    train_records, validation_records = records_for_split(
        record_items,
        train_instances={str(instance) for instance in split.get("train_instances", [])},
        validation_instances={str(instance) for instance in split.get("validation_instances", [])},
    )
    if not train_records or not validation_records:
        raise ValueError(f"{run_spec.name}: training split does not match dataset")

    gate_config = dict(checkpoint_data.get("deployment_gate", {}).get("gate_config") or {})
    if not gate_config:
        raise ValueError(f"{run_spec.name}: checkpoint missing deployment gate config")
    frontier = evaluate_threshold_frontier_records(
        validation_records,
        gate_config=gate_config,
        max_dynamic_thresholds=int(max_dynamic_thresholds),
    )
    rows = [
        *frontier["global_rows"],
        *frontier["family_local_rows"],
        *frontier["family_delay_fallback_rows"],
    ]
    annotated_rows = [
        _annotated_coverage_row(row, constraints=constraints)
        for row in rows
    ]
    coverage_constraint_pass = [
        row for row in annotated_rows if bool(row["coverage_constraint_pass"])
    ]
    coverage_constrained_gate_pass = [
        row for row in annotated_rows if bool(row["coverage_constrained_gate_pass"])
    ]
    reject_counts = Counter(
        reason
        for row in annotated_rows
        for reason in row.get("coverage_reject_reasons", [])
    )
    top_rows = sorted(annotated_rows, key=_coverage_sort_key, reverse=True)[: int(top_k)]
    feasible_rows = sorted(
        coverage_constrained_gate_pass,
        key=_coverage_sort_key,
        reverse=True,
    )

    top_path = output_dir / f"{run_spec.name}_coverage_top_candidates.jsonl"
    feasible_path = output_dir / f"{run_spec.name}_coverage_constrained_gate_candidates.jsonl"
    top_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in top_rows)
        + ("\n" if top_rows else ""),
        encoding="utf-8",
    )
    feasible_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in feasible_rows)
        + ("\n" if feasible_rows else ""),
        encoding="utf-8",
    )

    best_coverage = top_rows[0] if top_rows else {}
    best_gate = feasible_rows[0] if feasible_rows else {}
    run_summary = {
        "run_name": run_spec.name,
        "checkpoint": str(run_spec.checkpoint),
        "training_summary": str(run_spec.training_summary),
        "dataset_dir": str(dataset_dir),
        "sample_count": int(manifest.get("sample_count") or 0),
        "candidate_count": int(manifest.get("candidate_count") or 0),
        "train_record_count": len(train_records),
        "validation_record_count": len(validation_records),
        "threshold_row_count": len(annotated_rows),
        "threshold_local_gate_pass_count": int(frontier["feasible_threshold_count"]),
        "checkpoint_gate_pass_count": int(frontier["checkpoint_feasible_threshold_count"]),
        "coverage_constraint_pass_count": len(coverage_constraint_pass),
        "coverage_constrained_gate_pass_count": len(coverage_constrained_gate_pass),
        "coverage_reject_reason_counts": dict(sorted(reject_counts.items())),
        "best_coverage_candidate": _candidate_snapshot(best_coverage),
        "best_coverage_constrained_gate_candidate": _candidate_snapshot(best_gate),
        "top_candidates_path": str(top_path),
        "coverage_constrained_gate_candidates_path": str(feasible_path),
        "training_selected_metrics": _candidate_snapshot(
            dict(training.get("validation_deployment_metrics") or {})
        ),
    }
    return run_summary


def _annotated_coverage_row(
    row: dict[str, Any],
    *,
    constraints: CoverageConstraints,
) -> dict[str, Any]:
    annotated = dict(row)
    annotated.update(coverage_constraint_summary(row, constraints=constraints))
    return annotated


def _coverage_sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        bool(row.get("coverage_constrained_gate_pass")),
        bool(row.get("coverage_constraint_pass")),
        -len(row.get("coverage_reject_reasons", [])),
        int(row.get("accepted_high_roi_family_count") or 0),
        _none_to_negative(row.get("family_holdout_min_high_roi_capture_rate")),
        _none_to_negative(row.get("safe_precision_ci_low")),
        _none_to_negative(row.get("accepted_batch_roi_ci_low")),
        int(row.get("sector_wave_accepted_high_roi_count") or 0),
        int(row.get("accepted_batch_count") or 0),
        _none_to_negative(row.get("accepted_batch_roi")),
        -float(row.get("false_safe_rate_union") or 0.0),
        -float(row.get("false_high_priority_on_delay") or 0.0),
    )


def _candidate_snapshot(row: dict[str, Any]) -> dict[str, Any]:
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
        "accepted_batch_rate",
        "accepted_bad_mode_count",
        "accepted_batch_roi",
        "accepted_batch_roi_ci_low",
        "safe_precision",
        "safe_precision_ci_low",
        "high_priority_precision",
        "high_priority_precision_ci_low",
        "false_high_priority_on_delay",
        "false_safe_rate_union",
        "family_holdout_min_accepted_roi",
        "family_holdout_min_accepted_high_roi_count",
        "family_holdout_min_high_roi_capture_rate",
        "family_holdout_missing_accepted_families",
        "family_holdout_missing_accepted_opportunity_families",
        "family_holdout_oracle_high_roi_families",
        "threshold_local_gate_pass",
        "threshold_local_reject_reasons",
        "coverage_constraint_pass",
        "coverage_constrained_gate_pass",
        "coverage_reject_reasons",
        "oracle_high_roi_family_count",
        "accepted_high_roi_family_count",
        "sector_wave_oracle_high_roi_count",
        "sector_wave_accepted_high_roi_count",
        "sector_wave_high_roi_capture_rate",
    )
    result = {key: row.get(key) for key in keys if key in row}
    per_family = row.get("family_holdout_per_family")
    if isinstance(per_family, dict):
        result["family_snapshot"] = {
            str(family): {
                "accepted_batch_count": metrics.get("accepted_batch_count"),
                "accepted_batch_roi": metrics.get("accepted_batch_roi"),
                "oracle_high_roi_count": metrics.get("oracle_high_roi_count"),
                "accepted_high_roi_count": metrics.get("accepted_high_roi_count"),
                "high_roi_capture_rate": metrics.get("high_roi_capture_rate"),
                "safe_precision": metrics.get("safe_precision"),
            }
            for family, metrics in sorted(per_family.items())
        }
    return result


def _recommended_next_step(run_summaries: list[dict[str, Any]]) -> str:
    if any(int(run["coverage_constrained_gate_pass_count"]) > 0 for run in run_summaries):
        return "inspect_coverage_constrained_gate_candidates_then_knn_ood_shadow_before_stage4"
    if any(int(run["coverage_constraint_pass_count"]) > 0 for run in run_summaries):
        return "repair_existing_threshold_gate_for_coverage_passing_rows"
    if any(
        "required_high_roi_family_zero_capture:sector-wave"
        in run.get("coverage_reject_reason_counts", {})
        or "family_high_roi_capture_count_below_limit:sector-wave"
        in run.get("coverage_reject_reason_counts", {})
        for run in run_summaries
    ):
        return "collect_or_train_sector_wave_context_local_high_roi_repair_before_more_global_sweeps"
    return "train_coverage_aware_family_context_head_or_collect_same_context_pairs"


def _none_to_negative(value: Any) -> float:
    if value is None:
        return -1.0
    return float(value)


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 2026-06-17 BPC_future GAT Target Mode Stage 3 v105 Coverage-constrained Frontier 报告",
        "",
        "## 结论",
        "",
        "本报告只做离线 Stage 3 frontier 审计，不运行 BPC、pricing、RMP、worker 或 certificate。",
        "目标是回答：现有 v99/v102/v103 logits 中是否存在同时满足 safety 和 high-ROI family coverage 的阈值面。",
        "",
        "```text",
        f"run_count = {summary['run_count']}",
        f"coverage_constraint_pass_run_count = {summary['coverage_constraint_pass_run_count']}",
        f"coverage_constrained_gate_pass_run_count = {summary['coverage_constrained_gate_pass_run_count']}",
        f"coverage_constraint_pass_runs = {summary['coverage_constraint_pass_runs']}",
        f"coverage_constrained_gate_pass_runs = {summary['coverage_constrained_gate_pass_runs']}",
        f"recommended_next_step = {summary['recommended_next_step']}",
        "stage3_completed = false",
        "stage4_candidate_ready = false",
        "selector_can_certificate = false",
        "```",
        "",
        "## Constraints",
        "",
        "```json",
        json.dumps(summary["constraints"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Run Comparison",
        "",
        "| run | threshold local pass | coverage pass | coverage+gate pass | best accepted | best safe CI | best ROI CI | best false-safe | sector accepted high-ROI | best coverage reject |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for run in summary["runs"]:
        best = run.get("best_coverage_candidate") or {}
        lines.append(
            "| {name} | {local} | {cov} | {gate} | {accepted} | {safe_ci} | {roi_ci} | {false_safe} | {sector} | {reasons} |".format(
                name=run["run_name"],
                local=run["threshold_local_gate_pass_count"],
                cov=run["coverage_constraint_pass_count"],
                gate=run["coverage_constrained_gate_pass_count"],
                accepted=best.get("accepted_batch_count"),
                safe_ci=_fmt(best.get("safe_precision_ci_low")),
                roi_ci=_fmt(best.get("accepted_batch_roi_ci_low")),
                false_safe=_fmt(best.get("false_safe_rate_union")),
                sector=best.get("sector_wave_accepted_high_roi_count"),
                reasons=best.get("coverage_reject_reasons"),
            )
        )
    lines.extend(
        [
            "",
            "## Best Candidate Snapshots",
            "",
        ]
    )
    for run in summary["runs"]:
        lines.extend(
            [
                f"### {run['run_name']}",
                "",
                "```json",
                json.dumps(
                    {
                        "best_coverage_candidate": run["best_coverage_candidate"],
                        "best_coverage_constrained_gate_candidate": run[
                            "best_coverage_constrained_gate_candidate"
                        ],
                        "coverage_reject_reason_counts": run["coverage_reject_reason_counts"],
                        "top_candidates_path": run["top_candidates_path"],
                        "coverage_constrained_gate_candidates_path": run[
                            "coverage_constrained_gate_candidates_path"
                        ],
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
            "`DELAY_QUEUE` 只能有限延迟 true-RC negative，不能永久丢弃。即使本审计找到可行 frontier，最终 certificate 仍只能由当前 branch/cut/dual 下的 exact pricing full no-negative closure 给出。",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _fmt(value: Any) -> str:
    if value is None:
        return "None"
    return f"{float(value):.4f}"


if __name__ == "__main__":
    raise SystemExit(main())
