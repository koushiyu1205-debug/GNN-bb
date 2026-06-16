#!/usr/bin/env python3
"""Audit fixed cross-checkpoint batch-impact admission selectors.

This script is offline/diagnostic-only. It consumes opportunity-mining outputs
from multiple GAT batch-impact checkpoints, joins their validation records, and
evaluates fixed selector combinations such as v18 coverage with v19/v20
low-ROI suppression. It does not run BPC, pricing, RMP, workers, or certificate
logic.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import sys
from statistics import mean, stdev
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


DEFAULT_SOURCES = [
    (
        "v18",
        Path(
            "BPC_future/results/"
            "gat_batch_impact_opportunity_mining_v18_train_split_next3_hard_negative_20260616/"
            "summary.json"
        ),
    ),
    (
        "v19",
        Path(
            "BPC_future/results/"
            "gat_batch_impact_opportunity_mining_v19_candidate_pairwise_margin_20260616/"
            "summary.json"
        ),
    ),
    (
        "v20",
        Path(
            "BPC_future/results/"
            "gat_batch_impact_opportunity_mining_v20_candidate_pairwise_margin025_20260616/"
            "summary.json"
        ),
    ),
]
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/"
    "gat_batch_impact_cross_checkpoint_selector_v18_v19_v20_20260616"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260616_bpc_future_gat_batch_impact_cross_checkpoint_selector_v18_v19_v20_zh.md"
)


DecisionFn = Callable[[dict[str, dict[str, Any]]], list[str]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        action="append",
        default=[],
        help="Source in label=opportunity_summary.json form. May be repeated.",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--top-k", type=int, default=25)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sources = _parse_sources(args.source) if args.source else list(DEFAULT_SOURCES)
    summary = audit_cross_checkpoint_selector(
        sources=sources,
        output_dir=Path(args.output_dir),
        report=Path(args.report),
        top_k=max(1, int(args.top_k)),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def audit_cross_checkpoint_selector(
    *,
    sources: list[tuple[str, Path]] = DEFAULT_SOURCES,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    top_k: int = 25,
) -> dict[str, Any]:
    if len(sources) < 2:
        raise ValueError("at least two sources are required")
    source_summaries, source_records = _load_sources(sources)
    labels = [label for label, _ in sources]
    joined_rows = _join_records(source_records)
    base_label = labels[0]
    gate_config = dict(source_summaries[base_label].get("gate_config") or {})
    rules = _selector_rules(labels)
    metrics = [
        _evaluate_rule(
            name=name,
            joined_rows=joined_rows,
            decision_fn=decision_fn,
            base_label=base_label,
            gate_config=gate_config,
        )
        for name, decision_fn in rules
    ]
    metrics = sorted(metrics, key=_rule_sort_key)
    output_dir.mkdir(parents=True, exist_ok=True)
    rule_metrics_path = output_dir / "rule_metrics.jsonl"
    selected_records_path = output_dir / "selected_records.jsonl"
    _write_jsonl(rule_metrics_path, metrics)
    _write_jsonl(
        selected_records_path,
        _selected_record_rows(joined_rows, metrics, top_k=max(1, int(top_k))),
    )
    feasible = [item for item in metrics if item["passes_gate"]]
    best_gate = feasible[0] if feasible else None
    best_diagnostic = metrics[0] if metrics else None
    summary = {
        "schema_version": "gat_batch_impact_cross_checkpoint_selector_v1",
        "status": "gat_batch_impact_cross_checkpoint_selector_audited",
        "sources": {label: str(path) for label, path in sources},
        "source_validation_record_counts": {
            label: len(records) for label, records in source_records.items()
        },
        "output_dir": str(output_dir),
        "rule_metrics_path": str(rule_metrics_path),
        "selected_records_path": str(selected_records_path),
        "report": str(report),
        "validation_record_count": len(joined_rows),
        "base_label": base_label,
        "gate_config": gate_config,
        "minimum_all_success_count_for_safe_precision_ci": _min_all_successes_for_wilson(
            gate_config.get("min_safe_precision_ci_low"),
            z=float(gate_config.get("confidence_z", 1.96)),
        ),
        "rule_count": len(metrics),
        "feasible_rule_count": len(feasible),
        "best_gate_rule": best_gate,
        "best_diagnostic_rule": best_diagnostic,
        "recommended_next_step": _recommended_next_step(
            metrics,
            gate_config=gate_config,
            base_label=base_label,
        ),
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
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(Path(report), summary, metrics)
    return summary


def _parse_sources(items: list[str]) -> list[tuple[str, Path]]:
    sources: list[tuple[str, Path]] = []
    seen: set[str] = set()
    for item in items:
        if "=" not in item:
            raise ValueError(f"source must be label=path, got: {item}")
        label, raw_path = item.split("=", 1)
        label = label.strip()
        if not label:
            raise ValueError("source label must be non-empty")
        if label in seen:
            raise ValueError(f"duplicate source label: {label}")
        seen.add(label)
        sources.append((label, Path(raw_path)))
    return sources


def _load_sources(
    sources: list[tuple[str, Path]]
) -> tuple[dict[str, dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    summaries: dict[str, dict[str, Any]] = {}
    records: dict[str, list[dict[str, Any]]] = {}
    for label, summary_path in sources:
        summary = _read_json(Path(summary_path))
        _assert_opportunity_contract(summary, label=label)
        validation_path = Path(str(summary.get("validation_opportunities_path") or ""))
        rows = _read_jsonl(validation_path)
        if not rows:
            raise ValueError(f"{label} validation_opportunities is empty")
        summaries[label] = summary
        records[label] = rows
    return summaries, records


def _join_records(
    source_records: dict[str, list[dict[str, Any]]]
) -> list[dict[str, dict[str, Any]]]:
    labels = list(source_records)
    first = labels[0]
    base_keys = [_record_key(record) for record in source_records[first]]
    joined: list[dict[str, dict[str, Any]]] = []
    for index, key in enumerate(base_keys):
        item: dict[str, dict[str, Any]] = {first: source_records[first][index]}
        for label in labels[1:]:
            records = source_records[label]
            if index >= len(records):
                raise ValueError(f"{label} has fewer records than {first}")
            other_key = _record_key(records[index])
            if other_key != key:
                raise ValueError(
                    f"validation record key mismatch at index {index}: "
                    f"{first}={key}, {label}={other_key}"
                )
            item[label] = records[index]
        joined.append(item)
    for label in labels[1:]:
        if len(source_records[label]) != len(source_records[first]):
            raise ValueError(f"{label} record count differs from {first}")
    return joined


def _record_key(record: dict[str, Any]) -> tuple[Any, ...]:
    return (
        str(record.get("instance_path") or ""),
        str(record.get("context_hash") or ""),
        str(record.get("family") or ""),
        int(record.get("task_count") or 0),
        str(record.get("region") or ""),
        round(float(record.get("accepted_batch_roi_label") or 0.0), 12),
    )


def _selector_rules(labels: list[str]) -> list[tuple[str, DecisionFn]]:
    rules: list[tuple[str, DecisionFn]] = []
    for label in labels:
        rules.append(
            (
                f"{label}_selected",
                lambda row, source_label=label: [source_label]
                if bool(row[source_label].get("accepted"))
                else [],
            )
        )
    for left_index, left in enumerate(labels):
        for right in labels[left_index + 1 :]:
            rules.append(
                (
                    f"{left}_and_{right}",
                    lambda row, a=left, b=right: [a, b]
                    if bool(row[a].get("accepted")) and bool(row[b].get("accepted"))
                    else [],
                )
            )
            rules.append(
                (
                    f"{left}_or_{right}",
                    lambda row, a=left, b=right: [
                        label for label in (a, b) if bool(row[label].get("accepted"))
                    ],
                )
            )
    if {"v18", "v19"}.issubset(set(labels)):
        rules.append(
            (
                "v18_no_greedy_anchor",
                lambda row: ["v18"]
                if bool(row["v18"].get("accepted"))
                and str(row["v18"].get("family")) != "greedy-anchor"
                else [],
            )
        )
        rules.append(
            (
                "v18_sector_only",
                lambda row: ["v18"]
                if bool(row["v18"].get("accepted"))
                and str(row["v18"].get("family")) == "sector-wave"
                else [],
            )
        )
        rules.append(
            (
                "v18_sector_plus_v19_random",
                _v18_sector_plus_v19_random,
            )
        )
    if {"v18", "v19", "v20"}.issubset(set(labels)):
        rules.append(
            (
                "v18_and_v19_or_v20",
                lambda row: [
                    label
                    for label in ("v18", "v19", "v20")
                    if bool(row[label].get("accepted"))
                ]
                if bool(row["v18"].get("accepted"))
                and (bool(row["v19"].get("accepted")) or bool(row["v20"].get("accepted")))
                else [],
            )
        )
        rules.append(("v20_plus_v18_sector", _v20_plus_v18_sector))
        rules.append(("v19_or_v20_plus_v18_sector", _v19_or_v20_plus_v18_sector))
    return rules


def _v18_sector_plus_v19_random(row: dict[str, dict[str, Any]]) -> list[str]:
    family = str(row["v18"].get("family") or "")
    if family == "sector-wave" and bool(row["v18"].get("accepted")):
        return ["v18"]
    if family == "random-wave" and bool(row["v19"].get("accepted")):
        return ["v19"]
    return []


def _v20_plus_v18_sector(row: dict[str, dict[str, Any]]) -> list[str]:
    family = str(row["v18"].get("family") or "")
    selected: list[str] = []
    if bool(row["v20"].get("accepted")):
        selected.append("v20")
    if family == "sector-wave" and bool(row["v18"].get("accepted")):
        selected.append("v18")
    return selected


def _v19_or_v20_plus_v18_sector(row: dict[str, dict[str, Any]]) -> list[str]:
    family = str(row["v18"].get("family") or "")
    selected = [label for label in ("v19", "v20") if bool(row[label].get("accepted"))]
    if family == "sector-wave" and bool(row["v18"].get("accepted")):
        selected.append("v18")
    return selected


def _evaluate_rule(
    *,
    name: str,
    joined_rows: list[dict[str, dict[str, Any]]],
    decision_fn: DecisionFn,
    base_label: str,
    gate_config: dict[str, Any],
) -> dict[str, Any]:
    z = float(gate_config.get("confidence_z", 1.96))
    min_roi = float(gate_config.get("min_accepted_batch_roi", 0.65))
    selected_rows: list[tuple[dict[str, dict[str, Any]], list[str]]] = []
    for row in joined_rows:
        selected_sources = sorted(set(decision_fn(row)))
        if selected_sources:
            selected_rows.append((row, selected_sources))
    accepted = [row[base_label] for row, _ in selected_rows]
    roi_values = [float(record.get("accepted_batch_roi_label") or 0.0) for record in accepted]
    false_safe_count = sum(
        int(_selected_sources_have_predicted_delay(row, selected_sources))
        for row, selected_sources in selected_rows
    )
    accepted_count = len(accepted)
    accepted_high_roi = sum(int(float(row.get("accepted_batch_roi_label") or 0.0) >= min_roi) for row in accepted)
    accepted_low_roi_or_bad = sum(
        int(
            float(row.get("accepted_batch_roi_label") or 0.0) < min_roi
            or bool(row.get("bad_mode_switch"))
        )
        for row in accepted
    )
    total_high_roi = sum(
        int(float(row[base_label].get("accepted_batch_roi_label") or 0.0) >= min_roi)
        for row in joined_rows
    )
    safe_count = accepted_count - false_safe_count
    safe_precision = safe_count / float(accepted_count) if accepted_count else 0.0
    false_safe_rate = false_safe_count / float(accepted_count) if accepted_count else 0.0
    family_counts = Counter(str(row.get("family") or "unknown") for row in accepted)
    family_roi = _family_roi_summary(accepted)
    source_counts = Counter(
        source for _, selected_sources in selected_rows for source in selected_sources
    )
    metrics = {
        "rule": name,
        "accepted_batch_count": accepted_count,
        "accepted_batch_rate": accepted_count / float(len(joined_rows)) if joined_rows else 0.0,
        "accepted_batch_roi": mean(roi_values) if roi_values else 0.0,
        "accepted_batch_roi_ci_low": _mean_ci_low(roi_values, z=z),
        "accepted_high_roi_opportunities": accepted_high_roi,
        "missed_high_roi_opportunities": max(0, total_high_roi - accepted_high_roi),
        "accepted_high_roi_capture_rate": (
            accepted_high_roi / float(total_high_roi) if total_high_roi else 0.0
        ),
        "accepted_low_roi_or_bad": accepted_low_roi_or_bad,
        "false_safe_union_count": false_safe_count,
        "false_safe_rate_union": false_safe_rate,
        "safe_precision": safe_precision,
        "safe_precision_ci_low": _wilson_ci_low(safe_count, accepted_count, z=z),
        "family_counts": dict(sorted(family_counts.items())),
        "family_accepted_roi": family_roi,
        "family_holdout_min_accepted_roi": (
            min(family_roi.values()) if family_roi else None
        ),
        "source_accept_counts": dict(sorted(source_counts.items())),
    }
    reject_reasons = _reject_reasons(metrics, gate_config)
    metrics["reject_reasons"] = reject_reasons
    metrics["passes_gate"] = not reject_reasons
    metrics["diagnostic_score"] = _diagnostic_score(metrics)
    return metrics


def _selected_sources_have_predicted_delay(
    row: dict[str, dict[str, Any]],
    selected_sources: list[str],
) -> bool:
    return any(
        int(row[source].get("predicted_delay_candidate_count") or 0) > 0
        for source in selected_sources
    )


def _family_roi_summary(accepted: list[dict[str, Any]]) -> dict[str, float]:
    grouped: dict[str, list[float]] = {}
    for record in accepted:
        family = str(record.get("family") or "unknown")
        grouped.setdefault(family, []).append(float(record.get("accepted_batch_roi_label") or 0.0))
    return {
        family: float(mean(values))
        for family, values in sorted(grouped.items())
        if values
    }


def _reject_reasons(metrics: dict[str, Any], gate_config: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    min_safe_ci = gate_config.get("min_safe_precision_ci_low")
    if min_safe_ci is not None:
        safe_ci = metrics.get("safe_precision_ci_low")
        if safe_ci is None or float(safe_ci) < float(min_safe_ci):
            reasons.append("safe_precision_ci_low_below_threshold_or_not_measurable")
    min_roi = gate_config.get("min_accepted_batch_roi")
    if min_roi is not None and float(metrics["accepted_batch_roi"]) < float(min_roi):
        reasons.append("accepted_batch_roi_below_threshold")
    min_roi_ci = gate_config.get("min_accepted_batch_roi_ci_low")
    if min_roi_ci is not None:
        roi_ci = metrics.get("accepted_batch_roi_ci_low")
        if roi_ci is None or float(roi_ci) < float(min_roi_ci):
            reasons.append("accepted_batch_roi_ci_low_below_threshold_or_not_measurable")
    max_false_safe = gate_config.get("max_false_safe_union_rate")
    if max_false_safe is not None and float(metrics["false_safe_rate_union"]) > float(max_false_safe):
        reasons.append("false_safe_union_rate_above_threshold")
    min_family_roi = gate_config.get("min_family_holdout_accepted_roi")
    if min_family_roi is not None:
        family_min = metrics.get("family_holdout_min_accepted_roi")
        if family_min is None:
            reasons.append("family_holdout_accepted_roi_missing")
        elif float(family_min) < float(min_family_roi):
            reasons.append("family_holdout_accepted_roi_below_threshold")
    min_accepted_count = _min_all_successes_for_wilson(
        gate_config.get("min_safe_precision_ci_low"),
        z=float(gate_config.get("confidence_z", 1.96)),
    )
    if min_accepted_count is not None and int(metrics["accepted_batch_count"]) < int(min_accepted_count):
        reasons.append("accepted_all_success_count_below_safe_precision_ci_requirement")
    return reasons


def _diagnostic_score(metrics: dict[str, Any]) -> tuple[float, float, float, float]:
    return (
        float(metrics.get("accepted_batch_roi_ci_low") or -1.0),
        float(metrics.get("accepted_batch_roi") or 0.0),
        -float(metrics.get("accepted_low_roi_or_bad") or 0.0),
        float(metrics.get("accepted_batch_count") or 0.0),
    )


def _rule_sort_key(metrics: dict[str, Any]) -> tuple[Any, ...]:
    return (
        not bool(metrics.get("passes_gate")),
        -float(metrics.get("accepted_batch_roi_ci_low") or -1.0),
        -float(metrics.get("accepted_batch_roi") or 0.0),
        int(metrics.get("accepted_low_roi_or_bad") or 0),
        -int(metrics.get("accepted_batch_count") or 0),
        str(metrics.get("rule") or ""),
    )


def _selected_record_rows(
    joined_rows: list[dict[str, dict[str, Any]]],
    metrics: list[dict[str, Any]],
    *,
    top_k: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for metric in metrics[:top_k]:
        rows.append(
            {
                "rule": metric["rule"],
                "accepted_batch_count": metric["accepted_batch_count"],
                "accepted_batch_roi": metric["accepted_batch_roi"],
                "accepted_batch_roi_ci_low": metric["accepted_batch_roi_ci_low"],
                "safe_precision_ci_low": metric["safe_precision_ci_low"],
                "accepted_low_roi_or_bad": metric["accepted_low_roi_or_bad"],
                "reject_reasons": metric["reject_reasons"],
            }
        )
    return rows


def _recommended_next_step(
    metrics: list[dict[str, Any]],
    *,
    gate_config: dict[str, Any],
    base_label: str,
) -> dict[str, Any]:
    required_count = _min_all_successes_for_wilson(
        gate_config.get("min_safe_precision_ci_low"),
        z=float(gate_config.get("confidence_z", 1.96)),
    )
    feasible = [item for item in metrics if bool(item.get("passes_gate"))]
    if feasible:
        return {
            "primary": "run_knn_ood_and_holdout_audit_for_best_cross_checkpoint_selector",
            "best_rule": feasible[0]["rule"],
            "base_label": base_label,
        }
    coverage_candidates = [
        item
        for item in metrics
        if required_count is not None
        and int(item.get("accepted_batch_count") or 0) < int(required_count)
        and float(item.get("accepted_batch_roi") or 0.0)
        >= float(gate_config.get("min_accepted_batch_roi", 0.65))
    ]
    best_coverage = coverage_candidates[0] if coverage_candidates else (metrics[0] if metrics else {})
    missing = (
        max(0, int(required_count or 0) - int(best_coverage.get("accepted_batch_count") or 0))
        if best_coverage
        else None
    )
    return {
        "primary": "collect_reachability_valid_same_context_contrast_before_more_threshold_tuning",
        "best_diagnostic_rule": best_coverage.get("rule"),
        "best_diagnostic_accepted_count": best_coverage.get("accepted_batch_count"),
        "minimum_all_success_count_for_safe_precision_ci": required_count,
        "additional_all_success_accepts_needed": missing,
        "reason": "fixed_hybrid_selectors_reduce_low_roi_but_do_not_restore_confidence_coverage",
    }


def _assert_opportunity_contract(summary: dict[str, Any], *, label: str) -> None:
    if summary.get("schema_version") != "gat_batch_impact_opportunity_mining_v1":
        raise ValueError(f"{label} opportunity summary schema mismatch")
    if bool(summary.get("production_ready")):
        raise ValueError(f"{label} opportunity summary must not be production_ready")
    if bool(summary.get("runs_bpc_or_pricing")):
        raise ValueError(f"{label} opportunity summary must not run BPC or pricing")
    if bool(summary.get("selector_can_certificate")):
        raise ValueError(f"{label} opportunity summary must not be certificate-capable")


def _wilson_ci_low(successes: int, total: int, *, z: float = 1.96) -> float | None:
    if total <= 0:
        return None
    p_hat = successes / float(total)
    denom = 1.0 + (z * z) / float(total)
    center = p_hat + (z * z) / (2.0 * total)
    spread = z * math.sqrt((p_hat * (1.0 - p_hat) + (z * z) / (4.0 * total)) / total)
    return max(0.0, (center - spread) / denom)


def _mean_ci_low(values: list[float], *, z: float = 1.96) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return float(values[0])
    return float(mean(values) - z * stdev(values) / math.sqrt(len(values)))


def _min_all_successes_for_wilson(target: Any, *, z: float) -> int | None:
    if target is None:
        return None
    target_value = float(target)
    for count in range(1, 10000):
        low = _wilson_ci_low(count, count, z=z)
        if low is not None and low >= target_value:
            return count
    return None


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows)
        + ("\n" if rows else ""),
        encoding="utf-8",
    )


def _write_report(
    path: Path,
    summary: dict[str, Any],
    metrics: list[dict[str, Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    best = summary.get("best_diagnostic_rule") or {}
    recommended = summary["recommended_next_step"]
    reject_counts = Counter(
        reason
        for item in metrics
        for reason in item.get("reject_reasons", [])
    )
    table_rows = [
        "| rule | accepted | roi | roi_ci_low | safe_ci_low | high_roi | low_bad | pass |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for item in metrics:
        table_rows.append(
            "| {rule} | {accepted} | {roi:.6f} | {roi_ci} | {safe_ci} | {high} | {low_bad} | {passed} |".format(
                rule=item["rule"],
                accepted=item["accepted_batch_count"],
                roi=float(item["accepted_batch_roi"]),
                roi_ci=_fmt_float(item.get("accepted_batch_roi_ci_low")),
                safe_ci=_fmt_float(item.get("safe_precision_ci_low")),
                high=item["accepted_high_roi_opportunities"],
                low_bad=item["accepted_low_roi_or_bad"],
                passed=str(bool(item["passes_gate"])).lower(),
            )
        )
    lines = [
        "# GAT Batch Impact Cross-Checkpoint Selector Audit 报告",
        "",
        "日期：2026-06-16",
        "",
        "## 目的",
        "",
        "本报告检查 v18/v19/v20 这类 checkpoint 能否通过固定组合规则，把 v18 的",
        "coverage 和 v19/v20 的 low-ROI suppression 合并成一个 coverage-constrained",
        "ROI admission selector。它只使用已有 opportunity-mining validation records，",
        "不运行 BPC、pricing、RMP、worker 或 certificate。",
        "",
        "## 结论",
        "",
        "```text",
        f"validation_record_count = {summary['validation_record_count']}",
        f"minimum_all_success_count_for_safe_precision_ci = {summary['minimum_all_success_count_for_safe_precision_ci']}",
        f"feasible_rule_count = {summary['feasible_rule_count']}",
        f"best_diagnostic_rule = {best.get('rule')}",
        f"best_diagnostic_accepted_count = {best.get('accepted_batch_count')}",
        f"best_diagnostic_roi = {best.get('accepted_batch_roi')}",
        f"best_diagnostic_roi_ci_low = {best.get('accepted_batch_roi_ci_low')}",
        f"best_diagnostic_safe_precision_ci_low = {best.get('safe_precision_ci_low')}",
        f"best_diagnostic_low_roi_or_bad = {best.get('accepted_low_roi_or_bad')}",
        f"best_diagnostic_family_min_roi = {best.get('family_holdout_min_accepted_roi')}",
        f"recommended_primary = {recommended.get('primary')}",
        "production_ready = false",
        "selector_can_certificate = false",
        "```",
        "",
        "## Rule Frontier",
        "",
        *table_rows,
        "",
        "## Reject Reason Counts",
        "",
        "```json",
        json.dumps(dict(sorted(reject_counts.items())), ensure_ascii=False, indent=2),
        "```",
        "",
        "## Recommended Next Step",
        "",
        "```json",
        json.dumps(recommended, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Exactness Boundary",
        "",
        "- `diagnostic_only=true`；",
        "- `runs_bpc_or_pricing=false`；",
        "- `selector_is_pricing_oracle=false`；",
        "- `selector_can_certificate=false`；",
        "- `gate_can_permanently_discard_negative_columns=false`；",
        "- 该 selector 审计不能证明没有负 reduced-cost journey，最终 certificate 仍必须由 true-dual exact pricing full closure 给出。",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _fmt_float(value: Any) -> str:
    if value is None:
        return "None"
    return f"{float(value):.6f}"


if __name__ == "__main__":
    raise SystemExit(main())
