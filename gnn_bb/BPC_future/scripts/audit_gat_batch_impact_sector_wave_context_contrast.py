#!/usr/bin/env python3
"""Audit sector-wave same-context high-ROI vs low-ROI contrast pairs.

This script is offline/diagnostic-only. It consumes the v106 sector-wave
repair summary and its validation decision JSONL files, then builds
same-context positive/negative contrast pairs. The goal is to distinguish
near-threshold misses from structural rank reversals that require pairwise
training or representation repair. It does not run BPC, pricing, RMP, workers,
or certificate logic.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


DEFAULT_REPAIR_SUMMARY = Path(
    "BPC_future/results/gat_batch_impact_sector_wave_repair_v106_v105_frontier_20260617/summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/gat_batch_impact_sector_wave_context_contrast_v107_v106_20260617"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260617_bpc_future_gat_target_mode_stage3_v107_sector_wave_context_contrast_zh.md"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repair-summary", type=Path, default=DEFAULT_REPAIR_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--focus-family", default="sector-wave")
    parser.add_argument("--top-k", type=int, default=25)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = audit_sector_wave_context_contrast(
        repair_summary=Path(args.repair_summary),
        output_dir=Path(args.output_dir),
        report=Path(args.report),
        focus_family=str(args.focus_family),
        top_k=max(1, int(args.top_k)),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def audit_sector_wave_context_contrast(
    *,
    repair_summary: Path = DEFAULT_REPAIR_SUMMARY,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    focus_family: str = "sector-wave",
    top_k: int = 25,
) -> dict[str, Any]:
    repair = _read_json(Path(repair_summary))
    _assert_repair_contract(repair)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    run_summaries = []
    for run in repair.get("runs", []):
        run_name = str(run.get("run_name") or "")
        decisions_path = Path(str(run.get("validation_decisions_path") or ""))
        decisions = _read_jsonl(decisions_path)
        contrast_pairs = build_context_contrast_pairs(
            decisions,
            run_name=run_name,
            focus_family=focus_family,
        )
        context_rows = build_context_contrast_rows(contrast_pairs)
        pairs_path = output_dir / f"{run_name}_{focus_family}_context_contrast_pairs.jsonl"
        contexts_path = output_dir / f"{run_name}_{focus_family}_context_contrast_rows.jsonl"
        _write_jsonl(pairs_path, sorted(contrast_pairs, key=_pair_sort_key))
        _write_jsonl(contexts_path, sorted(context_rows, key=_context_sort_key))
        run_summaries.append(
            _summarize_run(
                run=run,
                pairs=contrast_pairs,
                context_rows=context_rows,
                pairs_path=pairs_path,
                contexts_path=contexts_path,
                top_k=top_k,
            )
        )

    aggregate = summarize_contrast_runs(run_summaries)
    summary = {
        "schema_version": "gat_batch_impact_sector_wave_context_contrast_v1",
        "status": "gat_batch_impact_sector_wave_context_contrast_audited",
        "repair_summary": str(repair_summary),
        "output_dir": str(output_dir),
        "report": str(report),
        "focus_family": str(focus_family),
        "run_count": len(run_summaries),
        "runs": run_summaries,
        "aggregate": aggregate,
        "recommended_next_step": recommend_next_step(aggregate),
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


def build_context_contrast_pairs(
    decisions: list[dict[str, Any]],
    *,
    run_name: str,
    focus_family: str = "sector-wave",
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in decisions:
        if str(item.get("family")) != str(focus_family):
            continue
        grouped[(str(item.get("context_hash") or ""), str(item.get("instance_path") or ""))].append(item)

    pairs: list[dict[str, Any]] = []
    for (context_hash, instance_path), items in sorted(grouped.items()):
        positive_items = [item for item in items if bool(item.get("is_high_roi_opportunity"))]
        negative_items = [item for item in items if bool(item.get("is_accepted_low_roi_or_bad"))]
        for positive in positive_items:
            for negative in negative_items:
                pairs.append(
                    build_contrast_pair(
                        positive=positive,
                        negative=negative,
                        run_name=run_name,
                        context_hash=context_hash,
                        instance_path=instance_path,
                    )
                )
    return pairs


def build_contrast_pair(
    *,
    positive: dict[str, Any],
    negative: dict[str, Any],
    run_name: str,
    context_hash: str,
    instance_path: str,
) -> dict[str, Any]:
    positive_roi = _float(positive.get("accepted_batch_roi_label"))
    negative_roi = _float(negative.get("accepted_batch_roi_label"))
    batch_gap = _score_gap(positive, negative, "batch_score")
    safe_gap = _score_gap(positive, negative, "max_safe_candidate_score")
    raw_gap = _score_gap(positive, negative, "max_raw_candidate_score")
    candidate_gap = _score_gap(positive, negative, "max_candidate_score")
    pair = {
        "run_name": str(run_name),
        "context_hash": str(context_hash),
        "instance_path": str(instance_path),
        "family": str(positive.get("family") or negative.get("family") or ""),
        "task_count": int(positive.get("task_count") or negative.get("task_count") or 0),
        "positive_was_missed": bool(positive.get("is_missed_high_roi_opportunity")),
        "positive_was_accepted": bool(positive.get("is_accepted_high_roi_opportunity")),
        "positive_roi": positive_roi,
        "negative_roi": negative_roi,
        "roi_gap": positive_roi - negative_roi,
        "positive_batch_score": _float(positive.get("batch_score")),
        "negative_batch_score": _float(negative.get("batch_score")),
        "batch_score_gap": batch_gap,
        "positive_candidate_score": _float(positive.get("max_candidate_score")),
        "negative_candidate_score": _float(negative.get("max_candidate_score")),
        "candidate_score_gap": candidate_gap,
        "positive_safe_candidate_score": _float(positive.get("max_safe_candidate_score")),
        "negative_safe_candidate_score": _float(negative.get("max_safe_candidate_score")),
        "safe_candidate_score_gap": safe_gap,
        "positive_raw_candidate_score": _float(positive.get("max_raw_candidate_score")),
        "negative_raw_candidate_score": _float(negative.get("max_raw_candidate_score")),
        "raw_candidate_score_gap": raw_gap,
        "positive_safe_candidate_margin": _float(positive.get("max_safe_candidate_score_margin")),
        "negative_safe_candidate_margin": _float(negative.get("max_safe_candidate_score_margin")),
        "positive_raw_candidate_margin": _float(positive.get("max_raw_candidate_score_margin")),
        "negative_raw_candidate_margin": _float(negative.get("max_raw_candidate_score_margin")),
        "positive_batch_margin": _float(positive.get("batch_score_margin")),
        "negative_batch_margin": _float(negative.get("batch_score_margin")),
        "positive_missed_reasons": list(positive.get("missed_reasons") or []),
        "positive_candidate_risk_adjusted_suppressed_count": int(
            positive.get("candidate_risk_adjusted_suppressed_count") or 0
        ),
        "positive_candidate_delay_gate_blocked_count": int(
            positive.get("candidate_delay_gate_blocked_count") or 0
        ),
        "negative_delay_candidate_label_count": int(negative.get("delay_candidate_label_count") or 0),
        "raw_rank_failure": raw_gap <= 0.0,
        "candidate_rank_failure": candidate_gap <= 0.0,
        "safe_rank_failure": safe_gap <= 0.0,
        "batch_rank_failure": batch_gap <= 0.0,
    }
    pair["repair_bucket"] = classify_contrast_pair(pair)
    return pair


def classify_contrast_pair(pair: dict[str, Any]) -> str:
    positive_missed = bool(pair.get("positive_was_missed"))
    raw_failure = bool(pair.get("raw_rank_failure"))
    safe_failure = bool(pair.get("safe_rank_failure"))
    batch_failure = bool(pair.get("batch_rank_failure"))
    risk_suppressed = int(pair.get("positive_candidate_risk_adjusted_suppressed_count") or 0) > 0
    delay_blocked = int(pair.get("positive_candidate_delay_gate_blocked_count") or 0) > 0
    positive_safe_margin = _float(pair.get("positive_safe_candidate_margin"))
    positive_raw_margin = _float(pair.get("positive_raw_candidate_margin"))

    if positive_missed and raw_failure and safe_failure:
        return "missed_high_roi_raw_and_safe_rank_reversal"
    if positive_missed and (not raw_failure) and safe_failure and risk_suppressed:
        return "missed_high_roi_risk_adjusted_rank_reversal"
    if positive_missed and positive_raw_margin >= 0.0 and positive_safe_margin < 0.0 and delay_blocked:
        return "missed_high_roi_delay_gate_blocks_raw_candidate"
    if positive_missed and positive_raw_margin >= 0.0 and positive_safe_margin < 0.0:
        return "missed_high_roi_risk_adjusted_below_threshold"
    if positive_missed and batch_failure:
        return "missed_high_roi_batch_head_rank_reversal"
    if positive_missed:
        return "missed_high_roi_threshold_or_unclassified"
    if raw_failure or safe_failure or batch_failure:
        return "accepted_high_roi_low_roi_suppression_pair"
    return "accepted_high_roi_correctly_ranked_but_low_roi_accepted"


def build_context_contrast_rows(pairs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for pair in pairs:
        grouped[
            (
                str(pair.get("run_name") or ""),
                str(pair.get("context_hash") or ""),
                str(pair.get("instance_path") or ""),
            )
        ].append(pair)

    rows = []
    for (run_name, context_hash, instance_path), items in sorted(grouped.items()):
        missed_pairs = [item for item in items if bool(item.get("positive_was_missed"))]
        rows.append(
            {
                "run_name": run_name,
                "context_hash": context_hash,
                "instance_path": instance_path,
                "task_count_counts": dict(
                    sorted(Counter(str(item.get("task_count") or 0) for item in items).items())
                ),
                "pair_count": len(items),
                "missed_high_roi_pair_count": len(missed_pairs),
                "accepted_high_roi_pair_count": len(items) - len(missed_pairs),
                "repair_bucket_counts": dict(
                    sorted(Counter(str(item.get("repair_bucket") or "") for item in items).items())
                ),
                "missed_raw_rank_failure_count": sum(
                    int(bool(item.get("raw_rank_failure"))) for item in missed_pairs
                ),
                "missed_safe_rank_failure_count": sum(
                    int(bool(item.get("safe_rank_failure"))) for item in missed_pairs
                ),
                "missed_batch_rank_failure_count": sum(
                    int(bool(item.get("batch_rank_failure"))) for item in missed_pairs
                ),
                "min_missed_raw_candidate_score_gap": _min_or_none(
                    _float(item.get("raw_candidate_score_gap")) for item in missed_pairs
                ),
                "min_missed_safe_candidate_score_gap": _min_or_none(
                    _float(item.get("safe_candidate_score_gap")) for item in missed_pairs
                ),
                "min_missed_batch_score_gap": _min_or_none(
                    _float(item.get("batch_score_gap")) for item in missed_pairs
                ),
                "max_positive_roi": _max_or_none(_float(item.get("positive_roi")) for item in items),
                "min_negative_roi": _min_or_none(_float(item.get("negative_roi")) for item in items),
                "recommended_repair": _context_repair(items),
            }
        )
    return rows


def summarize_contrast_runs(run_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    pair_count = sum(int(run.get("pair_count") or 0) for run in run_summaries)
    missed_pair_count = sum(int(run.get("missed_high_roi_pair_count") or 0) for run in run_summaries)
    raw_fail = sum(int(run.get("missed_raw_rank_failure_count") or 0) for run in run_summaries)
    safe_fail = sum(int(run.get("missed_safe_rank_failure_count") or 0) for run in run_summaries)
    batch_fail = sum(int(run.get("missed_batch_rank_failure_count") or 0) for run in run_summaries)
    buckets = Counter()
    for run in run_summaries:
        buckets.update({key: int(value) for key, value in run.get("repair_bucket_counts", {}).items()})
    return {
        "pair_count": pair_count,
        "missed_high_roi_pair_count": missed_pair_count,
        "accepted_high_roi_pair_count": sum(
            int(run.get("accepted_high_roi_pair_count") or 0) for run in run_summaries
        ),
        "missed_raw_rank_failure_count": raw_fail,
        "missed_safe_rank_failure_count": safe_fail,
        "missed_batch_rank_failure_count": batch_fail,
        "missed_raw_rank_failure_rate": raw_fail / float(missed_pair_count) if missed_pair_count else 0.0,
        "missed_safe_rank_failure_rate": safe_fail / float(missed_pair_count) if missed_pair_count else 0.0,
        "missed_batch_rank_failure_rate": batch_fail / float(missed_pair_count) if missed_pair_count else 0.0,
        "repair_bucket_counts": dict(sorted(buckets.items())),
    }


def recommend_next_step(aggregate: dict[str, Any]) -> str:
    buckets = dict(aggregate.get("repair_bucket_counts") or {})
    missed_pairs = int(aggregate.get("missed_high_roi_pair_count") or 0)
    raw_reversal = int(buckets.get("missed_high_roi_raw_and_safe_rank_reversal", 0))
    risk_reversal = int(buckets.get("missed_high_roi_risk_adjusted_rank_reversal", 0))
    delay_blocks = int(buckets.get("missed_high_roi_delay_gate_blocks_raw_candidate", 0))
    if missed_pairs and raw_reversal >= max(1, missed_pairs // 2):
        return "train_sector_wave_same_context_pairwise_ranking_with_trace_features"
    if risk_reversal or delay_blocks:
        return "calibrate_sector_wave_risk_adjusted_and_delay_heads"
    if missed_pairs:
        return "audit_sector_wave_threshold_near_misses_before_training"
    if int(aggregate.get("accepted_high_roi_pair_count") or 0):
        return "train_sector_wave_low_roi_acceptance_suppression_pairs"
    return "collect_more_sector_wave_same_context_contrast_pairs"


def _summarize_run(
    *,
    run: dict[str, Any],
    pairs: list[dict[str, Any]],
    context_rows: list[dict[str, Any]],
    pairs_path: Path,
    contexts_path: Path,
    top_k: int,
) -> dict[str, Any]:
    missed_pairs = [item for item in pairs if bool(item.get("positive_was_missed"))]
    buckets = Counter(str(item.get("repair_bucket") or "") for item in pairs)
    raw_fail = sum(int(bool(item.get("raw_rank_failure"))) for item in missed_pairs)
    safe_fail = sum(int(bool(item.get("safe_rank_failure"))) for item in missed_pairs)
    batch_fail = sum(int(bool(item.get("batch_rank_failure"))) for item in missed_pairs)
    return {
        "run_name": str(run.get("run_name") or ""),
        "pair_count": len(pairs),
        "context_count": len(context_rows),
        "missed_high_roi_pair_count": len(missed_pairs),
        "accepted_high_roi_pair_count": len(pairs) - len(missed_pairs),
        "missed_raw_rank_failure_count": raw_fail,
        "missed_safe_rank_failure_count": safe_fail,
        "missed_batch_rank_failure_count": batch_fail,
        "missed_raw_rank_failure_rate": raw_fail / float(len(missed_pairs)) if missed_pairs else 0.0,
        "missed_safe_rank_failure_rate": safe_fail / float(len(missed_pairs)) if missed_pairs else 0.0,
        "missed_batch_rank_failure_rate": batch_fail / float(len(missed_pairs)) if missed_pairs else 0.0,
        "repair_bucket_counts": dict(sorted(buckets.items())),
        "top_missed_rank_failures": sorted(missed_pairs, key=_pair_sort_key)[: int(top_k)],
        "top_context_rows": sorted(context_rows, key=_context_sort_key)[: int(top_k)],
        "context_contrast_pairs_path": str(pairs_path),
        "context_contrast_rows_path": str(contexts_path),
    }


def _context_repair(items: list[dict[str, Any]]) -> str:
    buckets = Counter(str(item.get("repair_bucket") or "") for item in items)
    if buckets.get("missed_high_roi_raw_and_safe_rank_reversal", 0):
        return "pairwise_ranking_or_representation_repair"
    if buckets.get("missed_high_roi_risk_adjusted_rank_reversal", 0):
        return "risk_adjusted_head_repair"
    if buckets.get("missed_high_roi_delay_gate_blocks_raw_candidate", 0):
        return "delay_gate_calibration_repair"
    if buckets.get("accepted_high_roi_low_roi_suppression_pair", 0):
        return "low_roi_acceptance_suppression"
    return "contrast_pair_monitor_only"


def _assert_repair_contract(summary: dict[str, Any]) -> None:
    if summary.get("schema_version") != "gat_batch_impact_sector_wave_repair_audit_v1":
        raise ValueError("sector-wave repair summary schema mismatch")
    if bool(summary.get("production_ready")):
        raise ValueError("repair summary must not be production_ready")
    if not bool(summary.get("diagnostic_only")):
        raise ValueError("repair summary must be diagnostic_only")
    if bool(summary.get("selector_can_certificate")):
        raise ValueError("repair summary must not be certificate-capable")


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    aggregate = summary["aggregate"]
    lines = [
        "# 2026-06-17 BPC_future GAT Target Mode Stage 3 v107 Sector-wave Context Contrast 报告",
        "",
        "## 结论",
        "",
        "本报告只做离线 Stage 3 诊断：读取 v106 sector-wave validation decisions，构造同 context high-ROI vs accepted low-ROI/bad contrast pairs，判断 high-ROI miss 是阈值近失还是模型排序结构性失败。",
        "",
        "```text",
        f"focus_family = {summary['focus_family']}",
        f"run_count = {summary['run_count']}",
        f"pair_count = {aggregate['pair_count']}",
        f"missed_high_roi_pair_count = {aggregate['missed_high_roi_pair_count']}",
        f"missed_raw_rank_failure_rate = {aggregate['missed_raw_rank_failure_rate']:.4f}",
        f"missed_safe_rank_failure_rate = {aggregate['missed_safe_rank_failure_rate']:.4f}",
        f"recommended_next_step = {summary['recommended_next_step']}",
        "stage3_completed = false",
        "stage4_candidate_ready = false",
        "selector_can_certificate = false",
        "```",
        "",
        "## Aggregate Buckets",
        "",
        "```json",
        json.dumps(aggregate["repair_bucket_counts"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Run Comparison",
        "",
        "| run | pairs | missed-pairs | raw rank fail | safe rank fail | batch rank fail | buckets |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for run in summary["runs"]:
        lines.append(
            "| {run} | {pairs} | {missed} | {raw} | {safe} | {batch} | {buckets} |".format(
                run=run["run_name"],
                pairs=run["pair_count"],
                missed=run["missed_high_roi_pair_count"],
                raw=run["missed_raw_rank_failure_count"],
                safe=run["missed_safe_rank_failure_count"],
                batch=run["missed_batch_rank_failure_count"],
                buckets=run["repair_bucket_counts"],
            )
        )
    lines.extend(["", "## Top Contrast Evidence", ""])
    for run in summary["runs"]:
        lines.extend(
            [
                f"### {run['run_name']}",
                "",
                "```json",
                json.dumps(
                    {
                        "top_missed_rank_failures": [
                            _pair_report_snapshot(item)
                            for item in run["top_missed_rank_failures"][:10]
                        ],
                        "top_context_rows": [
                            _context_report_snapshot(item)
                            for item in run["top_context_rows"][:10]
                        ],
                        "context_contrast_pairs_path": run["context_contrast_pairs_path"],
                        "context_contrast_rows_path": run["context_contrast_rows_path"],
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
            "## Interpretation",
            "",
            "- 如果 missed high-ROI 对 accepted low-ROI 的 `raw_candidate_score_gap <= 0`，说明不是阈值差一点，而是当前表示/排序已经把正样本排在负样本后面。",
            "- 如果 raw gap 为正但 safe gap 为负，优先修 risk-adjusted / delay head；如果 raw 和 safe 都反排，优先补 same-context pairwise ranking 与候选表示。",
            "- 这些 pair 只能进入 Stage 2/3 训练或诊断，不能作为 online HIGH_PRIORITY、pricing oracle 或 certificate 依据。",
            "",
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
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _pair_report_snapshot(item: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "context_hash",
        "task_count",
        "positive_roi",
        "negative_roi",
        "roi_gap",
        "batch_score_gap",
        "raw_candidate_score_gap",
        "safe_candidate_score_gap",
        "positive_safe_candidate_margin",
        "positive_raw_candidate_margin",
        "positive_missed_reasons",
        "repair_bucket",
    )
    return {key: item.get(key) for key in keys}


def _context_report_snapshot(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "context_hash": item.get("context_hash"),
        "instance": Path(str(item.get("instance_path") or "")).name,
        "pair_count": item.get("pair_count"),
        "missed_high_roi_pair_count": item.get("missed_high_roi_pair_count"),
        "missed_raw_rank_failure_count": item.get("missed_raw_rank_failure_count"),
        "missed_safe_rank_failure_count": item.get("missed_safe_rank_failure_count"),
        "min_missed_raw_candidate_score_gap": item.get("min_missed_raw_candidate_score_gap"),
        "min_missed_safe_candidate_score_gap": item.get("min_missed_safe_candidate_score_gap"),
        "repair_bucket_counts": item.get("repair_bucket_counts"),
        "recommended_repair": item.get("recommended_repair"),
    }


def _pair_sort_key(item: dict[str, Any]) -> tuple[Any, ...]:
    return (
        not bool(item.get("positive_was_missed")),
        not bool(item.get("raw_rank_failure")),
        _float(item.get("raw_candidate_score_gap")),
        _float(item.get("safe_candidate_score_gap")),
        -_float(item.get("roi_gap")),
        str(item.get("context_hash") or ""),
    )


def _context_sort_key(item: dict[str, Any]) -> tuple[Any, ...]:
    return (
        -int(item.get("missed_high_roi_pair_count") or 0),
        -int(item.get("missed_raw_rank_failure_count") or 0),
        _none_last(item.get("min_missed_raw_candidate_score_gap")),
        _none_last(item.get("min_missed_safe_candidate_score_gap")),
        str(item.get("context_hash") or ""),
    )


def _score_gap(positive: dict[str, Any], negative: dict[str, Any], key: str) -> float:
    return _float(positive.get(key)) - _float(negative.get(key))


def _float(value: Any) -> float:
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _min_or_none(values: Any) -> float | None:
    materialized = [float(value) for value in values]
    return min(materialized) if materialized else None


def _max_or_none(values: Any) -> float | None:
    materialized = [float(value) for value in values]
    return max(materialized) if materialized else None


def _none_last(value: Any) -> tuple[int, float]:
    if value is None:
        return (1, 0.0)
    return (0, _float(value))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped:
            rows.append(json.loads(stripped))
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows)
        + ("\n" if rows else ""),
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
