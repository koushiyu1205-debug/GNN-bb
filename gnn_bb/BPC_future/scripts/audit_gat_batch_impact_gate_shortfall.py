#!/usr/bin/env python3
"""Audit Stage 3 threshold-gate shortfalls from frontier artifacts.

This script is diagnostic-only. It reads an existing threshold frontier
summary/JSONL output and explains why no threshold can become a Stage 4
candidate yet. It does not load a model, run BPC, pricing, RMP, workers, or
certificate logic.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any


DEFAULT_THRESHOLD_SUMMARY = Path(
    "BPC_future/results/gat_batch_impact_threshold_frontier_v3_signature_20260616/summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/gat_batch_impact_gate_shortfall_v3_signature_20260616"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260616_bpc_future_gat_batch_impact_gate_shortfall_v3_signature_zh.md"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--threshold-summary", type=Path, default=DEFAULT_THRESHOLD_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--top-k", type=int, default=20)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = audit_gate_shortfall(
        threshold_summary=Path(args.threshold_summary),
        output_dir=Path(args.output_dir),
        report=Path(args.report),
        top_k=max(1, int(args.top_k)),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def audit_gate_shortfall(
    *,
    threshold_summary: Path = DEFAULT_THRESHOLD_SUMMARY,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    top_k: int = 20,
) -> dict[str, Any]:
    threshold_summary = Path(threshold_summary)
    source_summary = _read_json(threshold_summary)
    _assert_frontier_contract(source_summary)
    rows = _load_frontier_rows(source_summary)
    gate_config = dict(source_summary.get("gate_config") or {})
    enriched_rows = [
        enrich_shortfall_row(row, gate_config=gate_config)
        for row in rows
    ]
    ranked_rows = sorted(enriched_rows, key=_shortfall_sort_key)
    top_rows = ranked_rows[: int(top_k)]
    best = dict(top_rows[0]) if top_rows else {}
    family_summary = _family_shortfall_summary(top_rows)
    summary = {
        "schema_version": "gat_batch_impact_gate_shortfall_v1",
        "status": "gat_batch_impact_gate_shortfall_audited",
        "threshold_summary": str(threshold_summary),
        "output_dir": str(output_dir),
        "source_frontier_global_path": source_summary.get("frontier_global_path"),
        "source_frontier_family_local_path": source_summary.get("frontier_family_local_path"),
        "total_frontier_rows": len(enriched_rows),
        "feasible_threshold_count": int(source_summary.get("feasible_threshold_count") or 0),
        "checkpoint_feasible_threshold_count": int(
            source_summary.get("checkpoint_feasible_threshold_count") or 0
        ),
        "validation_record_count": int(source_summary.get("validation_record_count") or 0),
        "train_record_count": int(source_summary.get("train_record_count") or 0),
        "gate_config": gate_config,
        "best_near_miss": best,
        "top_near_misses": top_rows,
        "family_shortfall_summary": family_summary,
        "recommended_next_step": _recommended_next_step(best, family_summary),
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
    (output_dir / "top_near_misses.jsonl").write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in top_rows)
        + ("\n" if top_rows else ""),
        encoding="utf-8",
    )
    _write_report(Path(report), summary)
    return summary


def enrich_shortfall_row(row: dict[str, Any], *, gate_config: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(row)
    confidence_z = float(gate_config.get("confidence_z", 1.96))
    safe_success = _success_count_from_precision(
        row.get("safe_precision"),
        row.get("accepted_batch_count"),
    )
    safe_total = int(row.get("accepted_batch_count") or 0)
    high_priority_success = int(row.get("high_priority_true_positive_count") or 0)
    high_priority_total = int(row.get("high_priority_prediction_count") or 0)
    min_safe_ci = gate_config.get("min_safe_precision_ci_low")
    min_hp_ci = gate_config.get("min_high_priority_precision_ci_low")
    min_roi_ci = gate_config.get("min_accepted_batch_roi_ci_low")
    min_roi = gate_config.get("min_accepted_batch_roi")
    enriched.update(
        {
            "local_blocker_count": len(row.get("threshold_local_reject_reasons") or []),
            "safe_precision_success_count": safe_success,
            "safe_precision_total_count": safe_total,
            "safe_precision_additional_all_success_needed": additional_all_successes_for_wilson(
                safe_success,
                safe_total,
                min_safe_ci,
                z=confidence_z,
            ),
            "high_priority_precision_additional_all_success_needed": additional_all_successes_for_wilson(
                high_priority_success,
                high_priority_total,
                min_hp_ci,
                z=confidence_z,
            ),
            "accepted_batch_roi_point_gap": _positive_gap(
                row.get("accepted_batch_roi"),
                min_roi,
            ),
            "accepted_batch_roi_ci_low_gap": _positive_gap(
                row.get("accepted_batch_roi_ci_low"),
                min_roi_ci,
            ),
            "safe_precision_ci_low_gap": _positive_gap(
                row.get("safe_precision_ci_low"),
                min_safe_ci,
            ),
            "high_priority_precision_ci_low_gap": _positive_gap(
                row.get("high_priority_precision_ci_low"),
                min_hp_ci,
            ),
        }
    )
    return enriched


def additional_all_successes_for_wilson(
    success_count: int,
    total_count: int,
    target_ci_low: Any,
    *,
    z: float = 1.96,
    max_extra: int = 10000,
) -> int | None:
    if target_ci_low is None:
        return None
    target = float(target_ci_low)
    success = max(0, int(success_count))
    total = max(0, int(total_count))
    for extra in range(0, int(max_extra) + 1):
        low = _wilson_ci_low(success + extra, total + extra, z=z)
        if low is not None and low >= target:
            return extra
    return None


def _wilson_ci_low(success_count: int, total_count: int, *, z: float) -> float | None:
    if total_count <= 0:
        return None
    n = float(total_count)
    phat = float(success_count) / n
    z2 = float(z) * float(z)
    denom = 1.0 + z2 / n
    center = phat + z2 / (2.0 * n)
    margin = float(z) * ((phat * (1.0 - phat) + z2 / (4.0 * n)) / n) ** 0.5
    return (center - margin) / denom


def _success_count_from_precision(precision: Any, total_count: Any) -> int:
    total = int(total_count or 0)
    if total <= 0 or precision is None:
        return 0
    return max(0, min(total, int(round(float(precision) * float(total)))))


def _positive_gap(value: Any, target: Any) -> float | None:
    if target is None:
        return None
    if value is None:
        return float(target)
    return max(0.0, float(target) - float(value))


def _shortfall_sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        not bool(row.get("threshold_local_gate_pass")),
        int(row.get("local_blocker_count") or 0),
        _none_to_large(row.get("safe_precision_additional_all_success_needed")),
        _none_to_large(row.get("accepted_batch_roi_ci_low_gap")),
        _none_to_large(row.get("safe_precision_ci_low_gap")),
        -int(row.get("accepted_batch_count") or 0),
        -float(row.get("expected_trajectory_utility") or 0.0),
    )


def _none_to_large(value: Any) -> float:
    if value is None:
        return 1.0e18
    return float(value)


def _family_shortfall_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    missing = Counter()
    missed_opportunity = Counter()
    fallback = Counter()
    for row in rows:
        missing.update(str(item) for item in row.get("family_holdout_missing_accepted_families") or [])
        missed_opportunity.update(
            str(item) for item in row.get("family_holdout_missing_accepted_opportunity_families") or []
        )
        fallback.update(str(item) for item in row.get("family_specific_delay_fallback_families") or [])
    return {
        "top_missing_accepted_families": dict(sorted(missing.items())),
        "top_missing_accepted_opportunity_families": dict(sorted(missed_opportunity.items())),
        "top_family_specific_delay_fallback_families": dict(sorted(fallback.items())),
    }


def _recommended_next_step(best: dict[str, Any], family_summary: dict[str, Any]) -> dict[str, Any]:
    if not best:
        return {"primary": "no_frontier_rows"}
    safe_extra = best.get("safe_precision_additional_all_success_needed")
    roi_gap = best.get("accepted_batch_roi_ci_low_gap")
    family_missing = list(
        (family_summary.get("top_missing_accepted_opportunity_families") or {}).keys()
    )
    fallback = list(
        (family_summary.get("top_family_specific_delay_fallback_families") or {}).keys()
    )
    if roi_gap is not None and float(roi_gap) > 0.0:
        primary = "collect_more_high_roi_validation_accepts_or_improve_ranking"
    elif safe_extra is not None and int(safe_extra) > 0:
        primary = "collect_more_safe_validation_accepts"
    elif family_missing:
        primary = "collect_or_fix_family_specific_missed_opportunities"
    else:
        primary = "rerun_knn_ood_or_stage4_shadow_after_local_gate_passes"
    return {
        "primary": primary,
        "safe_precision_additional_all_success_needed": safe_extra,
        "accepted_batch_roi_ci_low_gap": roi_gap,
        "families_with_missed_opportunity": family_missing,
        "families_recommended_for_delay_fallback": fallback,
    }


def _load_frontier_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in ("frontier_global_path", "frontier_family_local_path"):
        path_value = summary.get(key)
        if not path_value:
            continue
        path = Path(str(path_value))
        if not path.exists():
            raise FileNotFoundError(path)
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                row["frontier_source"] = key
                rows.append(row)
    return rows


def _assert_frontier_contract(summary: dict[str, Any]) -> None:
    if summary.get("schema_version") != "gat_batch_impact_threshold_frontier_v1":
        raise ValueError("threshold summary schema mismatch")
    if not bool(summary.get("diagnostic_only")):
        raise ValueError("threshold frontier must be diagnostic_only")
    if bool(summary.get("runs_bpc_or_pricing")):
        raise ValueError("threshold frontier must not run BPC or pricing")
    if bool(summary.get("production_ready")):
        raise ValueError("threshold frontier must not be production_ready")
    if bool(summary.get("selector_can_certificate")):
        raise ValueError("GAT selector cannot be a certificate source")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    best = dict(summary.get("best_near_miss") or {})
    recommended = dict(summary.get("recommended_next_step") or {})
    lines = [
        "# GAT Batch Impact Gate Shortfall 报告",
        "",
        "日期：2026-06-16",
        "",
        "## 结论",
        "",
        "本报告只审计 Stage 3 threshold frontier 的 gate shortfall，不运行 BPC、pricing、RMP 或 certificate。",
        "它的用途是把 `stage4_candidate_ready=false` 拆成可执行的补数据 / 调阈值方向，而不是放宽 gate。",
        "",
        "```text",
        f"total_frontier_rows = {summary['total_frontier_rows']}",
        f"feasible_threshold_count = {summary['feasible_threshold_count']}",
        f"checkpoint_feasible_threshold_count = {summary['checkpoint_feasible_threshold_count']}",
        f"best_threshold_scope = {best.get('threshold_scope')}",
        f"best_threshold_mode = {best.get('threshold_mode')}",
        f"best_accepted_batch_count = {best.get('accepted_batch_count')}",
        f"best_safe_precision_ci_low = {best.get('safe_precision_ci_low')}",
        f"best_safe_precision_extra_all_success_needed = {best.get('safe_precision_additional_all_success_needed')}",
        f"best_accepted_batch_roi = {best.get('accepted_batch_roi')}",
        f"best_accepted_batch_roi_ci_low = {best.get('accepted_batch_roi_ci_low')}",
        f"best_accepted_batch_roi_ci_low_gap = {best.get('accepted_batch_roi_ci_low_gap')}",
        f"recommended_primary = {recommended.get('primary')}",
        "production_ready = false",
        "selector_can_certificate = false",
        "```",
        "",
        "## Family Shortfall",
        "",
        "```json",
        json.dumps(summary["family_shortfall_summary"], ensure_ascii=False, indent=2, sort_keys=True),
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
        "- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
