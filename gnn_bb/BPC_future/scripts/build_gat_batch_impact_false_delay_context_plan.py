#!/usr/bin/env python3
"""Build context-local hard-negative sampling plans from false-delay catalogs.

This script is offline and read-only with respect to BPC.  It converts the
v41-style false HIGH_PRIORITY-on-delay context catalog into context-priority
rows, then reuses the guarded multi-batch intervention planner to select
materialized true-RC negative targets for explicit opt-in worker probes.
"""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import sys
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from BPC_future.scripts.build_gat_batch_impact_multibatch_intervention_plan import (
    build_intervention_plan,
)


DEFAULT_FALSE_POSITIVE_SUMMARY = Path(
    "BPC_future/results/"
    "gat_batch_impact_false_positive_catalog_v39_neighbor_roi_b6d808_20260616/"
    "summary.json"
)
DEFAULT_CONTEXT_SUMMARY_JSONL = Path(
    "BPC_future/results/"
    "gat_batch_impact_false_positive_catalog_v39_neighbor_roi_b6d808_20260616/"
    "context_false_positive_summary.jsonl"
)
DEFAULT_DATASET_DIR = Path(
    "BPC_future/data/gat_batch_impact/"
    "v39_mixed_v23_plus_neighbor_roi_b6d808_ab_roi_20260616"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/"
    "gat_batch_impact_false_delay_context_plan_v48_v39_20260616"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260616_bpc_future_gat_target_mode_stage3_v48_v39_false_delay_context_plan_zh.md"
)
DEFAULT_INCLUDE_TASK_COUNTS = (20,)
DEFAULT_INCLUDE_FAMILIES = ("sector-wave",)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            text = line.strip()
            if text:
                rows.append(json.loads(text))
    return rows


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _float_value(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _int_value(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _task_counts(row: dict[str, Any]) -> list[int]:
    raw_counts = row.get("task_counts")
    if isinstance(raw_counts, list):
        counts = [_int_value(value) for value in raw_counts]
    else:
        counts = [_int_value(row.get("task_count"))]
    return sorted({count for count in counts if count > 0})


def _first_task_count(row: dict[str, Any]) -> int:
    counts = _task_counts(row)
    return counts[0] if counts else _int_value(row.get("task_count"))


def _candidate_signature_count(row: dict[str, Any]) -> int:
    signatures = row.get("candidate_signature_ids")
    if isinstance(signatures, list):
        return len(signatures)
    return _int_value(row.get("candidate_signature_count"))


def _priority_score(row: dict[str, Any]) -> float:
    false_count = _int_value(row.get("false_high_priority_on_delay_count"))
    signature_count = _candidate_signature_count(row)
    batch_count = _int_value(row.get("batch_record_count"))
    accepted_count = _int_value(row.get("accepted_batch_count"))
    return float(false_count * 1000 + signature_count * 10 + batch_count + accepted_count)


def build_false_delay_context_priority_rows(
    context_rows: Iterable[dict[str, Any]],
    *,
    include_task_counts: Iterable[int] | None = DEFAULT_INCLUDE_TASK_COUNTS,
    include_families: Iterable[str] | None = DEFAULT_INCLUDE_FAMILIES,
) -> list[dict[str, Any]]:
    """Convert false-delay context summaries into intervention priority rows."""

    allowed_task_counts = (
        None if include_task_counts is None else {int(value) for value in include_task_counts}
    )
    allowed_families = (
        None
        if include_families is None
        else {str(value).strip() for value in include_families if str(value).strip()}
    )
    rows: list[dict[str, Any]] = []
    for row in context_rows:
        context_hash = str(row.get("context_hash") or "").strip()
        family = str(row.get("family") or "").strip()
        task_count = _first_task_count(row)
        false_count = _int_value(row.get("false_high_priority_on_delay_count"))
        if not context_hash or false_count <= 0:
            continue
        if allowed_task_counts is not None and task_count not in allowed_task_counts:
            continue
        if allowed_families is not None and family not in allowed_families:
            continue
        signature_count = _candidate_signature_count(row)
        rows.append(
            {
                "schema_version": "gat_batch_impact_false_delay_context_priority_v1",
                "context_hash": context_hash,
                "family": family,
                "task_count": task_count,
                "priority_score": _priority_score(row),
                "primary_action": "collect_same_context_false_delay_hard_negative_contrast",
                "primary_blocker": "context_local_false_delay_ranking",
                "accepted_batch_roi_label": _float_value(
                    row.get("max_accepted_batch_roi_label")
                ),
                "candidate_count": false_count,
                "false_high_priority_on_delay_count": false_count,
                "candidate_signature_count": signature_count,
                "batch_record_count": _int_value(row.get("batch_record_count")),
                "accepted_batch_count": _int_value(row.get("accepted_batch_count")),
                "source_instances": list(row.get("instances") or []),
                "task_counts": _task_counts(row),
                "max_delay_risk_score": _float_value(row.get("max_delay_risk_score")),
                "median_delay_risk_score": _float_value(row.get("median_delay_risk_score")),
                "median_raw_high_priority_score": _float_value(
                    row.get("median_raw_high_priority_score")
                ),
                "context_false_delay_false_high_priority_on_delay_count": false_count,
                "context_false_delay_candidate_signature_count": signature_count,
                "context_false_delay_batch_record_count": _int_value(
                    row.get("batch_record_count")
                ),
                "context_false_delay_accepted_batch_count": _int_value(
                    row.get("accepted_batch_count")
                ),
                "context_false_delay_max_delay_risk_score": _float_value(
                    row.get("max_delay_risk_score")
                ),
                "context_false_delay_median_delay_risk_score": _float_value(
                    row.get("median_delay_risk_score")
                ),
                "context_false_delay_median_raw_high_priority_score": _float_value(
                    row.get("median_raw_high_priority_score")
                ),
                "is_high_roi_opportunity": False,
                "is_missed_high_roi_opportunity": False,
                "is_false_delay_context": True,
                "training_label_allowed_before_worker_reachability": False,
                "requires_worker_target_causal_match": True,
                "diagnostic_only": True,
                "runs_bpc_or_pricing": False,
                "production_ready": False,
                "default_enabled": False,
                "certificate_effect": False,
                "official_bound_effect": False,
                "selector_can_certificate": False,
                "gate_can_permanently_discard_negative_columns": False,
            }
        )
    rows.sort(
        key=lambda item: (
            _float_value(item.get("priority_score")),
            _int_value(item.get("candidate_signature_count")),
            str(item.get("context_hash") or ""),
        ),
        reverse=True,
    )
    return rows


def build_false_delay_context_plan(
    *,
    false_positive_summary: Path = DEFAULT_FALSE_POSITIVE_SUMMARY,
    context_summary_jsonl: Path = DEFAULT_CONTEXT_SUMMARY_JSONL,
    dataset_dir: Path = DEFAULT_DATASET_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    max_contexts: int = 5,
    targets_per_context: int = 3,
    min_negative_targets_per_context: int = 2,
    include_task_counts: Iterable[int] | None = DEFAULT_INCLUDE_TASK_COUNTS,
    include_families: Iterable[str] | None = DEFAULT_INCLUDE_FAMILIES,
) -> dict[str, Any]:
    false_summary = _read_json(Path(false_positive_summary))
    context_rows = _read_jsonl(Path(context_summary_jsonl))
    priority_rows = build_false_delay_context_priority_rows(
        context_rows,
        include_task_counts=include_task_counts,
        include_families=include_families,
    )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    priority_path = output_dir / "false_delay_context_priority.jsonl"
    _write_jsonl(priority_path, priority_rows)

    intervention_output_dir = output_dir / "multibatch_intervention_plan"
    intervention_report = output_dir / "multibatch_intervention_plan.md"
    intervention = build_intervention_plan(
        dataset_dir=Path(dataset_dir),
        opportunity_jsonl_paths=[],
        context_priority_jsonl_paths=[priority_path],
        output_dir=intervention_output_dir,
        report=intervention_report,
        max_contexts=max(0, int(max_contexts)),
        targets_per_context=max(1, int(targets_per_context)),
        min_negative_targets_per_context=max(1, int(min_negative_targets_per_context)),
        include_task_counts=include_task_counts,
        include_families=include_families,
        require_opportunity_context=True,
    )

    top_contexts = priority_rows[: max(0, int(max_contexts))]
    checks = {
        "diagnostic_only": True,
        "source_catalog_diagnostic_only": bool(false_summary.get("diagnostic_only", True)),
        "source_catalog_does_not_run_bpc_or_pricing": not bool(
            false_summary.get("runs_bpc_or_pricing", False)
        ),
        "priority_rows_have_false_delay_contexts": bool(priority_rows)
        and all(_int_value(row.get("false_high_priority_on_delay_count")) > 0 for row in priority_rows),
        "intervention_does_not_run_bpc_or_pricing": not bool(
            intervention.get("runs_bpc_or_pricing", True)
        ),
        "intervention_has_candidates": _int_value(intervention.get("candidate_count")) > 0,
        "intervention_checks_pass": bool(intervention.get("all_checks_pass")),
        "no_certificate_effect": not bool(intervention.get("official_bound_effect", True))
        and not bool(intervention.get("certificate_ready", True)),
    }
    summary = {
        "schema_version": "gat_batch_impact_false_delay_context_plan_v1",
        "status": "ready" if all(bool(value) for value in checks.values()) else "needs_more_capture",
        "date": date.today().isoformat(),
        "false_positive_summary": str(false_positive_summary),
        "context_summary_jsonl": str(context_summary_jsonl),
        "dataset_dir": str(dataset_dir),
        "output_dir": str(output_dir),
        "priority_jsonl": str(priority_path),
        "context_summary_row_count": len(context_rows),
        "context_priority_row_count": len(priority_rows),
        "top_contexts": top_contexts,
        "false_positive_catalog_counts": {
            "false_high_priority_on_delay_count": _int_value(
                false_summary.get("false_high_priority_on_delay_count")
            ),
            "context_false_positive_count": _int_value(
                false_summary.get("context_false_positive_count")
            ),
            "false_high_priority_on_delay": _float_value(
                false_summary.get("false_high_priority_on_delay")
            ),
            "family_task_counts": dict(false_summary.get("family_task_counts") or {}),
            "candidate_threshold_zero": bool(false_summary.get("candidate_threshold_zero")),
            "primary_diagnosis": str(
                (false_summary.get("diagnosis") or {}).get("primary") or ""
            ),
        },
        "intervention_output_dir": str(intervention_output_dir),
        "intervention_report": str(intervention_report),
        "intervention_status": str(intervention.get("status") or ""),
        "intervention_planned_context_count": _int_value(
            intervention.get("planned_context_count")
        ),
        "intervention_selected_context_count": _int_value(
            intervention.get("selected_context_count")
        ),
        "intervention_pairwise_context_target_count": _int_value(
            intervention.get("pairwise_context_target_count")
        ),
        "intervention_candidate_count": _int_value(intervention.get("candidate_count")),
        "intervention_skipped_counts": dict(intervention.get("skipped_counts") or {}),
        "runbook_command": str(intervention.get("runbook_command") or ""),
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "default_enabled": False,
        "certificate_ready": False,
        "official_bound_effect": False,
        "selector_is_pricing_oracle": False,
        "selector_can_certificate": False,
        "gate_can_permanently_discard_negative_columns": False,
        "training_label_allowed_before_worker_reachability": False,
        "checks": checks,
        "all_checks_pass": all(bool(value) for value in checks.values()),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(Path(report), summary)
    return summary


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    counts = summary["false_positive_catalog_counts"]
    lines = [
        "# GAT Target Mode Stage 3 v48 v39 False-delay Context Plan 报告",
        "",
        f"日期：{summary['date']}",
        "",
        "## 结论",
        "",
        "本报告把 v41 false-positive catalog 转成同一 RMP context 的 hard-negative",
        "采样计划。它只生成 context-priority 行和 guarded worker runbook 输入，不运行",
        "BPC、pricing、RMP、worker 或 certificate。",
        "",
        "跨版本结论和 v46 一致：v23 证明 coverage 能上去但 false-delay 爆，v24/v28",
        "证明 false-delay 能压住但 coverage / CI 不够，v39/v45 证明两者合并后误放行",
        "复发，v47 又排除了简单 checkpoint selection。下一步应补",
        "`sector-wave|20` context-local false-delay hard negative，而不是继续普通阈值 sweep。",
        "",
        "## 机器字段",
        "",
        "```text",
        f"status = {summary['status']}",
        f"context_priority_row_count = {summary['context_priority_row_count']}",
        f"intervention_selected_context_count = {summary['intervention_selected_context_count']}",
        f"intervention_pairwise_context_target_count = {summary['intervention_pairwise_context_target_count']}",
        f"intervention_candidate_count = {summary['intervention_candidate_count']}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"default_enabled = {str(summary['default_enabled']).lower()}",
        f"certificate_ready = {str(summary['certificate_ready']).lower()}",
        f"official_bound_effect = {str(summary['official_bound_effect']).lower()}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## v41 输入诊断",
        "",
        "```json",
        json.dumps(counts, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Top Context Priority",
        "",
        "| context | family | task | false-delay FP | signatures | batch records | priority | action |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in summary.get("top_contexts") or []:
        lines.append(
            "| {context_hash} | {family} | {task_count} | {false_count} | {signature_count} | {batch_count} | {priority:.1f} | {action} |".format(
                context_hash=str(row.get("context_hash") or ""),
                family=str(row.get("family") or ""),
                task_count=_int_value(row.get("task_count")),
                false_count=_int_value(row.get("false_high_priority_on_delay_count")),
                signature_count=_int_value(row.get("candidate_signature_count")),
                batch_count=_int_value(row.get("batch_record_count")),
                priority=_float_value(row.get("priority_score")),
                action=str(row.get("primary_action") or ""),
            )
        )
    lines.extend(
        [
            "",
            "## Intervention Plan 摘要",
            "",
            "```json",
            json.dumps(
                {
                    "status": summary["intervention_status"],
                    "selected_context_count": summary["intervention_selected_context_count"],
                    "pairwise_context_target_count": summary[
                        "intervention_pairwise_context_target_count"
                    ],
                    "candidate_count": summary["intervention_candidate_count"],
                    "skipped_counts": summary["intervention_skipped_counts"],
                    "checks": summary["checks"],
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            "```",
            "",
            "## 下一步命令",
            "",
            "该命令只生成 worker A/B runbook；实际 worker 运行仍需显式 opt-in：",
            "",
            "```bash",
            summary["runbook_command"],
            "```",
            "",
            "## 边界",
            "",
            "- 本计划只服务 Stage 3 采样和训练诊断，不是 Stage 4 production gate；",
            "- 选出的候选必须是 materialized true-RC negative，但不能直接成为训练标签；",
            "- worker 跑完前必须验证 expected context reachability 与 target causal match；",
            "- 低 ROI 或拖尾 true-RC negative 只能作为 DELAY_QUEUE / hard-negative 证据，不能永久丢弃；",
            "- 最终 OPTIMAL / no-negative certificate 仍只能来自当前 branch/cut/dual 下 exact pricing exhaustive closure。",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_optional_ints(values: list[int] | None) -> tuple[int, ...] | None:
    if values is None:
        return DEFAULT_INCLUDE_TASK_COUNTS
    return tuple(int(value) for value in values) if values else None


def _parse_optional_strings(values: list[str] | None) -> tuple[str, ...] | None:
    if values is None:
        return DEFAULT_INCLUDE_FAMILIES
    parsed = tuple(str(value).strip() for value in values if str(value).strip())
    return parsed if parsed else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--false-positive-summary", type=Path, default=DEFAULT_FALSE_POSITIVE_SUMMARY)
    parser.add_argument("--context-summary-jsonl", type=Path, default=DEFAULT_CONTEXT_SUMMARY_JSONL)
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--max-contexts", type=int, default=5)
    parser.add_argument("--targets-per-context", type=int, default=3)
    parser.add_argument("--min-negative-targets-per-context", type=int, default=2)
    parser.add_argument("--include-task-counts", nargs="*", type=int, default=None)
    parser.add_argument("--include-families", nargs="*", default=None)
    args = parser.parse_args(argv)
    summary = build_false_delay_context_plan(
        false_positive_summary=args.false_positive_summary,
        context_summary_jsonl=args.context_summary_jsonl,
        dataset_dir=args.dataset_dir,
        output_dir=args.output_dir,
        report=args.report,
        max_contexts=max(0, int(args.max_contexts)),
        targets_per_context=max(1, int(args.targets_per_context)),
        min_negative_targets_per_context=max(1, int(args.min_negative_targets_per_context)),
        include_task_counts=_parse_optional_ints(args.include_task_counts),
        include_families=_parse_optional_strings(args.include_families),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
