#!/usr/bin/env python3
"""Score online shadow candidates with offline GAT safe-source evidence.

This script is diagnostic-only. It reads Stage 3 decision records and Stage 4
shadow logs, then ranks online true-RC negative candidates whose coarse keys
have offline high-priority evidence. It does not run BPC, pricing, RMP, workers,
or certificate logic, and its output is not an admission rule.
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

from BPC_future.scripts.audit_gat_safe_source_online_coverage import (
    DEFAULT_DECISION_RECORDS,
    DEFAULT_SAFE_SOURCE,
    DEFAULT_SHADOW_LOG_DIR,
    _float_or_none,
    _offline_candidates,
    _online_shadow_candidates,
    _read_json,
    _read_jsonl,
    _safe_divide,
)


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/gat_model_scored_online_safe_source_v12_scale_tranq20_01_20260616"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260616_bpc_future_gat_target_mode_stage4_model_scored_online_safe_source_audit_zh.md"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--safe-source", type=Path, default=DEFAULT_SAFE_SOURCE)
    parser.add_argument("--decision-records", type=Path, default=DEFAULT_DECISION_RECORDS)
    parser.add_argument("--shadow-log-dir", type=Path, default=DEFAULT_SHADOW_LOG_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--min-roi", type=float, default=0.65)
    parser.add_argument("--top-k", type=int, default=25)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = audit_model_scored_online_safe_source(
        safe_source=Path(args.safe_source),
        decision_records=Path(args.decision_records),
        shadow_log_dir=Path(args.shadow_log_dir),
        output_dir=Path(args.output_dir),
        report=Path(args.report),
        min_roi=float(args.min_roi),
        top_k=max(1, int(args.top_k)),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def audit_model_scored_online_safe_source(
    *,
    safe_source: Path = DEFAULT_SAFE_SOURCE,
    decision_records: Path = DEFAULT_DECISION_RECORDS,
    shadow_log_dir: Path = DEFAULT_SHADOW_LOG_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    min_roi: float = 0.65,
    top_k: int = 25,
) -> dict[str, Any]:
    safe = _read_json(Path(safe_source))
    records = _read_jsonl(Path(decision_records))
    source_cache: dict[str, list[dict[str, Any]]] = {}
    offline_candidates = _offline_candidates(records, source_cache=source_cache)
    online_candidates, shadow_stats = _online_shadow_candidates(Path(shadow_log_dir))
    safe_ids = {str(item) for item in safe.get("safe_candidate_ids", []) if str(item)}

    indexes = {
        key_name: _build_key_index(offline_candidates, key_field=key_field, min_roi=min_roi)
        for key_name, key_field in (
            ("route_no_start", "route_no_start_key"),
            ("sequence", "sequence_key"),
            ("task_set", "task_set_key"),
        )
    }
    scored = [
        _score_online_candidate(candidate, safe_ids=safe_ids, indexes=indexes)
        for candidate in online_candidates
    ]
    scored.sort(
        key=lambda item: (
            int(item["diagnostic_priority_hint"]),
            float(item["evidence_score"]),
            abs(float(item["true_reduced_cost"] or 0.0)),
        ),
        reverse=True,
    )
    diagnostic_candidates = [
        item for item in scored if bool(item["diagnostic_priority_hint"])
    ]
    exact_safe_hits = [item for item in scored if bool(item["exact_safe_id_hit"])]
    blocked_reasons = _blocked_reasons(
        exact_safe_hit_count=len(exact_safe_hits),
        diagnostic_priority_hint_count=len(diagnostic_candidates),
    )
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    scored_path = output_dir / "online_candidate_evidence.jsonl"
    scored_path.write_text(
        "\n".join(json.dumps(item, ensure_ascii=False, sort_keys=True) for item in scored)
        + ("\n" if scored else ""),
        encoding="utf-8",
    )
    summary = {
        "schema_version": "gat_model_scored_online_safe_source_audit_v1",
        "status": "gat_model_scored_online_safe_source_audited",
        "safe_source": str(safe_source),
        "decision_records": str(decision_records),
        "shadow_log_dir": str(shadow_log_dir),
        "output_dir": str(output_dir),
        "online_candidate_evidence_path": str(scored_path),
        "safe_source_ready": bool(safe.get("safe_source_ready", False)),
        "safe_candidate_id_count": len(safe_ids),
        "decision_record_count": len(records),
        "offline_candidate_count": len(offline_candidates),
        "online_shadow_events": int(shadow_stats["shadow_events"]),
        "online_declared_candidate_journeys": int(shadow_stats["declared_candidate_journeys"]),
        "online_sampled_candidate_journeys": len(online_candidates),
        "online_sample_coverage_complete": bool(shadow_stats["sample_coverage_complete"]),
        "exact_safe_id_hit_count": len(exact_safe_hits),
        "diagnostic_priority_hint_count": len(diagnostic_candidates),
        "admission_ready_count": 0,
        "diagnostic_priority_hint_rate": _safe_divide(len(diagnostic_candidates), len(online_candidates)),
        "diagnostic_priority_hint_by_key_level": dict(
            sorted(Counter(item["best_key_level"] for item in diagnostic_candidates).items())
        ),
        "diagnostic_priority_hint_by_pricing_kind": dict(
            sorted(Counter(item["pricing_kind"] for item in diagnostic_candidates).items())
        ),
        "top_diagnostic_candidates": diagnostic_candidates[: int(top_k)],
        "blocked_reasons": blocked_reasons,
        "stage4_model_scored_online_safe_source_ready": False,
        "stage4_mutating_admission_ready": False,
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "default_enabled": False,
        "official_bound_effect": False,
        "selector_is_pricing_oracle": False,
        "selector_can_certificate": False,
        "gate_can_permanently_discard_negative_columns": False,
        "negative_columns_must_remain_eventually_reachable": True,
        "all_checks_pass": True,
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(Path(report), summary)
    return summary


def _build_key_index(
    offline_candidates: list[dict[str, Any]],
    *,
    key_field: str,
    min_roi: float,
) -> dict[Any, dict[str, Any]]:
    grouped: dict[Any, list[dict[str, Any]]] = defaultdict(list)
    for candidate in offline_candidates:
        key = candidate.get(key_field)
        if key:
            grouped[key].append(candidate)
    index: dict[Any, dict[str, Any]] = {}
    for key, items in grouped.items():
        high = [item for item in items if bool(item.get("safe_source_high_priority"))]
        delay = [item for item in items if not bool(item.get("label_high_priority"))]
        high_roi = [
            item
            for item in high
            if _value_or_neg_inf(item.get("accepted_batch_roi_label")) >= float(min_roi)
        ]
        index[key] = _evidence_summary(key=key, high=high, delay=delay, high_roi=high_roi)
    return index


def _evidence_summary(
    *,
    key: Any,
    high: list[dict[str, Any]],
    delay: list[dict[str, Any]],
    high_roi: list[dict[str, Any]],
) -> dict[str, Any]:
    high_rois = [
        float(item["accepted_batch_roi_label"])
        for item in high
        if item.get("accepted_batch_roi_label") is not None
    ]
    high_scores = [
        float(item["batch_score"])
        for item in high
        if item.get("batch_score") is not None
    ]
    return {
        "key": key,
        "offline_high_count": len(high),
        "offline_delay_conflict_count": len(delay),
        "offline_high_roi_count": len(high_roi),
        "offline_high_roi_mean": _mean_or_none(high_rois),
        "offline_high_roi_max": max(high_rois) if high_rois else None,
        "offline_batch_score_mean": _mean_or_none(high_scores),
        "offline_batch_score_min": min(high_scores) if high_scores else None,
        "offline_context_count": len({str(item.get("context_hash") or "") for item in high}),
        "offline_families": sorted({str(item.get("instance_family") or "") for item in high if item.get("instance_family")}),
        "offline_task_counts": sorted({str(item.get("instance_task_count") or "") for item in high if item.get("instance_task_count")}),
        "offline_unsafe_count": sum(
            1
            for item in high
            if bool(item.get("is_knn_unsafe")) or bool(item.get("is_ood")) or bool(item.get("is_label_unsafe"))
        ),
    }


def _score_online_candidate(
    candidate: dict[str, Any],
    *,
    safe_ids: set[str],
    indexes: dict[str, dict[Any, dict[str, Any]]],
) -> dict[str, Any]:
    exact_safe_id_hit = str(candidate.get("signature_id") or "") in safe_ids
    best_level = "none"
    best_evidence: dict[str, Any] | None = None
    for level in ("route_no_start", "sequence", "task_set"):
        key_field = f"{level}_key"
        evidence = indexes[level].get(candidate.get(key_field))
        if evidence and int(evidence["offline_high_count"]) > 0:
            best_level = level
            best_evidence = evidence
            break
    if best_evidence is None:
        best_evidence = _empty_evidence()
    conflict_count = int(best_evidence["offline_delay_conflict_count"])
    high_count = int(best_evidence["offline_high_count"])
    high_roi_count = int(best_evidence["offline_high_roi_count"])
    evidence_score = _evidence_score(best_evidence)
    diagnostic_priority_hint = bool(
        not exact_safe_id_hit
        and high_count > 0
        and high_roi_count > 0
        and conflict_count == 0
        and _context_compatible(candidate, best_evidence)
    )
    return {
        "candidate_id": str(candidate.get("signature_id") or ""),
        "task_set": list(candidate.get("task_set_key") or ()),
        "pricing_kind": str(candidate.get("pricing_kind") or ""),
        "cg_iter": int(candidate.get("cg_iter") or 0),
        "online_family": str(candidate.get("instance_family") or ""),
        "online_task_count": str(candidate.get("instance_task_count") or ""),
        "shadow_decision": str(candidate.get("decision") or ""),
        "shadow_reason": str(candidate.get("reason") or ""),
        "true_reduced_cost": _float_or_none(candidate.get("true_reduced_cost")),
        "exact_safe_id_hit": exact_safe_id_hit,
        "best_key_level": best_level,
        "context_compatible": _context_compatible(candidate, best_evidence),
        "diagnostic_priority_hint": diagnostic_priority_hint,
        "admission_ready": False,
        "admission_blocker": (
            _admission_blocker(
                exact_safe_id_hit=exact_safe_id_hit,
                diagnostic_priority_hint=diagnostic_priority_hint,
            )
        ),
        "evidence_score": evidence_score,
        "offline_high_count": high_count,
        "offline_delay_conflict_count": conflict_count,
        "offline_high_roi_count": high_roi_count,
        "offline_high_roi_mean": best_evidence.get("offline_high_roi_mean"),
        "offline_high_roi_max": best_evidence.get("offline_high_roi_max"),
        "offline_batch_score_mean": best_evidence.get("offline_batch_score_mean"),
        "offline_batch_score_min": best_evidence.get("offline_batch_score_min"),
        "offline_context_count": int(best_evidence.get("offline_context_count") or 0),
        "offline_families": list(best_evidence.get("offline_families") or []),
        "offline_task_counts": list(best_evidence.get("offline_task_counts") or []),
        "offline_unsafe_count": int(best_evidence.get("offline_unsafe_count") or 0),
    }


def _blocked_reasons(
    *,
    exact_safe_hit_count: int,
    diagnostic_priority_hint_count: int,
) -> list[str]:
    reasons: list[str] = []
    if exact_safe_hit_count <= 0:
        reasons.append("exact_safe_id_overlap_missing")
    else:
        reasons.append("exact_safe_id_overlap_is_not_trajectory_roi_proof")
    if diagnostic_priority_hint_count > 0:
        reasons.append("coarse_key_evidence_is_diagnostic_only")
    reasons.append("online_trajectory_roi_unverified")
    return reasons


def _admission_blocker(
    *,
    exact_safe_id_hit: bool,
    diagnostic_priority_hint: bool,
) -> str:
    if exact_safe_id_hit:
        return "exact_safe_id_hit_but_online_trajectory_roi_unverified"
    if diagnostic_priority_hint:
        return "coarse_key_hint_but_online_trajectory_roi_unverified"
    return "no_safe_evidence_or_exact_safe_id_missing"


def _evidence_score(evidence: dict[str, Any]) -> float:
    high_count = int(evidence.get("offline_high_count") or 0)
    conflict_count = int(evidence.get("offline_delay_conflict_count") or 0)
    high_roi_count = int(evidence.get("offline_high_roi_count") or 0)
    roi = max(0.0, float(evidence.get("offline_high_roi_mean") or 0.0))
    precision_proxy = _safe_divide(high_count, high_count + conflict_count) or 0.0
    return float(precision_proxy * (1.0 + high_roi_count) * roi)


def _context_compatible(candidate: dict[str, Any], evidence: dict[str, Any]) -> bool:
    family = str(candidate.get("instance_family") or "")
    task_count = str(candidate.get("instance_task_count") or "")
    families = {str(value) for value in evidence.get("offline_families", []) if str(value)}
    task_counts = {str(value) for value in evidence.get("offline_task_counts", []) if str(value)}
    family_ok = not family or not families or family in families
    task_ok = not task_count or not task_counts or task_count in task_counts
    return bool(family_ok and task_ok)


def _empty_evidence() -> dict[str, Any]:
    return {
        "offline_high_count": 0,
        "offline_delay_conflict_count": 0,
        "offline_high_roi_count": 0,
        "offline_high_roi_mean": None,
        "offline_high_roi_max": None,
        "offline_batch_score_mean": None,
        "offline_batch_score_min": None,
        "offline_context_count": 0,
        "offline_families": [],
        "offline_task_counts": [],
        "offline_unsafe_count": 0,
    }


def _value_or_neg_inf(value: Any) -> float:
    parsed = _float_or_none(value)
    if parsed is None:
        return float("-inf")
    return float(parsed)


def _mean_or_none(values: list[float]) -> float | None:
    if not values:
        return None
    return float(sum(values) / len(values))


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 2026-06-16 BPC_future GAT Stage 4 Model-scored Online Safe-source Audit 报告",
        "",
        "## 结论",
        "",
        "本报告只读 Stage 3 safe-source、decision records 和 Stage 4 shadow 日志；",
        "不运行 BPC / pricing / RMP，不改变 admission，也不产生 certificate。",
        "",
        "核心结果：",
        "",
        f"- online sampled candidates = {summary['online_sampled_candidate_journeys']}",
        f"- exact safe-id hit count = {summary['exact_safe_id_hit_count']}",
        f"- diagnostic priority hint count = {summary['diagnostic_priority_hint_count']}",
        f"- admission ready count = {summary['admission_ready_count']}",
        "",
        "这些 diagnostic hints 只能说明 coarse key 上存在离线 high-ROI / high-priority 证据；",
        "审计已要求 online family / task scale 与 offline evidence 兼容，以避免跨 family/scale 误迁移。",
        "它们还没有 online trajectory ROI、tail-risk 或 family/context holdout 证明，不能作为 mutating admission rule。",
        "",
        "## Top Diagnostic Candidates",
        "",
        "```text",
        *[
            json.dumps(item, ensure_ascii=False, sort_keys=True)
            for item in summary["top_diagnostic_candidates"][:10]
        ],
        "```",
        "",
        "## 判定",
        "",
        "```text",
        f"stage4_model_scored_online_safe_source_ready = {str(summary['stage4_model_scored_online_safe_source_ready']).lower()}",
        f"stage4_mutating_admission_ready = {str(summary['stage4_mutating_admission_ready']).lower()}",
        "stage4_next_direction = collect_online_trajectory_roi_for_diagnostic_hints",
        "```",
        "",
        "## Exactness Boundary",
        "",
        "```text",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"selector_is_pricing_oracle = {str(summary['selector_is_pricing_oracle']).lower()}",
        f"selector_can_certificate = {str(summary['selector_can_certificate']).lower()}",
        f"official_bound_effect = {str(summary['official_bound_effect']).lower()}",
        f"gate_can_permanently_discard_negative_columns = {str(summary['gate_can_permanently_discard_negative_columns']).lower()}",
        "```",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
