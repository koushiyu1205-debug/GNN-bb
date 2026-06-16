#!/usr/bin/env python3
"""Export exact safe-id online hits as target-materialization candidates.

This audit-only bridge turns Stage 4 online coverage hits into a candidates.json
payload for ``build_gat_target_priority_worker_ab_runbook.py``. It reads an
offline safe-source, optional model-scored online evidence, and existing
counterfactual replay capture logs. It does not run BPC, pricing, RMP, workers,
or certificate logic.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from BPC_future.scripts.audit_gat_safe_source_online_coverage import _read_json, _read_jsonl
from BPC_future.scripts.build_gat_online_shadow_target_candidates import (
    _candidate_payload,
    _required_context_fields,
)
from BPC_future.solver.gat_candidate_id import journey_gat_candidate_id_from_signature


DEFAULT_SAFE_SOURCE = Path(
    "BPC_future/results/gat_batch_impact_safe_source_v14_random_wave_task50_margin_tl130_global_20260616/"
    "safe_source.json"
)
DEFAULT_CAPTURE_LOG_DIR = Path(
    "BPC_future/results/gat_target_mode_stage4_v10_20_shadow_capture_context_20260616/"
    "logs_sector_tranq20_01_shadow_capture"
)
DEFAULT_MODEL_EVIDENCE = Path(
    "BPC_future/results/gat_model_scored_online_safe_source_v14_global_tranq20_01_20260616/"
    "online_candidate_evidence.jsonl"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/gat_exact_safe_hit_target_candidates_v14_global_tranq20_01_20260616"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260616_bpc_future_gat_target_mode_stage4_v14_exact_safe_hit_target_candidates_zh.md"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--safe-source", type=Path, default=DEFAULT_SAFE_SOURCE)
    parser.add_argument("--capture-log-dir", type=Path, default=DEFAULT_CAPTURE_LOG_DIR)
    parser.add_argument("--model-evidence", type=Path, default=DEFAULT_MODEL_EVIDENCE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--max-candidates", type=int, default=32)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = build_exact_safe_hit_target_candidates(
        safe_source=args.safe_source,
        capture_log_dir=args.capture_log_dir,
        model_evidence=args.model_evidence,
        output_dir=args.output_dir,
        report=args.report,
        max_candidates=max(1, int(args.max_candidates)),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def build_exact_safe_hit_target_candidates(
    *,
    safe_source: Path = DEFAULT_SAFE_SOURCE,
    capture_log_dir: Path = DEFAULT_CAPTURE_LOG_DIR,
    model_evidence: Path | None = DEFAULT_MODEL_EVIDENCE,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    max_candidates: int = 32,
) -> dict[str, Any]:
    safe = _read_json(Path(safe_source))
    safe_ids = {str(item) for item in safe.get("safe_candidate_ids", []) if str(item)}
    evidence_by_id = _model_evidence_by_id(Path(model_evidence) if model_evidence else None)
    capture_candidates = _capture_exact_safe_hits(
        Path(capture_log_dir),
        safe_ids=safe_ids,
        evidence_by_id=evidence_by_id,
    )
    selected = capture_candidates[: max(1, int(max_candidates))]

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    candidates_path = output_dir / "candidates.json"
    candidates_path.write_text(
        json.dumps({"candidates": selected}, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    context_counts = Counter(str(candidate.get("expected_context_hash") or "") for candidate in selected)
    pricing_counts = Counter(str(candidate.get("capture_pricing_kind") or "") for candidate in selected)
    checks = {
        "safe_source_ready": bool(safe.get("safe_source_ready", False)),
        "safe_ids_nonempty": bool(safe_ids),
        "capture_candidates_nonempty": bool(capture_candidates),
        "selected_candidates_nonempty": bool(selected),
        "selected_candidates_are_exact_safe_hits": all(
            bool(candidate.get("exact_safe_id_hit")) for candidate in selected
        ),
        "selected_candidates_have_context": all(
            all(str(candidate.get(field) or "") for field in _required_context_fields())
            for candidate in selected
        ),
        "selected_candidates_have_target_traces": all(
            bool(candidate.get("target_sortie_traces")) for candidate in selected
        ),
        "selected_candidates_need_trajectory_roi": all(
            str(candidate.get("admission_ready")).lower() == "false"
            and str(candidate.get("admission_blocker") or "").endswith("online_trajectory_roi_unverified")
            for candidate in selected
        ),
    }
    summary = {
        "schema_version": "gat_exact_safe_hit_target_candidates_v1",
        "status": "exact_safe_hit_target_candidates_built",
        "safe_source": str(safe_source),
        "capture_log_dir": str(capture_log_dir),
        "model_evidence": str(model_evidence) if model_evidence else "",
        "output_dir": str(output_dir),
        "candidates_path": str(candidates_path),
        "safe_candidate_id_count": int(len(safe_ids)),
        "model_evidence_exact_hit_count": int(
            sum(1 for item in evidence_by_id.values() if bool(item.get("exact_safe_id_hit")))
        ),
        "capture_exact_safe_hit_count": int(len(capture_candidates)),
        "selected_candidate_count": int(len(selected)),
        "selected_context_count": int(len(context_counts)),
        "selected_context_counts": dict(sorted(context_counts.items())),
        "selected_pricing_kind_counts": dict(sorted(pricing_counts.items())),
        "selected_task_sets": [candidate["target_task_set"] for candidate in selected],
        "selected_candidate_ids": [candidate["signature_id"] for candidate in selected],
        "selected_true_reduced_cost_min": _min_or_none(
            float(candidate.get("true_reduced_cost") or 0.0) for candidate in selected
        ),
        "selected_true_reduced_cost_max": _max_or_none(
            float(candidate.get("true_reduced_cost") or 0.0) for candidate in selected
        ),
        "checks": checks,
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "default_enabled": False,
        "official_bound_effect": False,
        "selector_is_pricing_oracle": False,
        "selector_can_certificate": False,
        "gate_can_permanently_discard_negative_columns": False,
        "negative_columns_must_remain_eventually_reachable": True,
        "stage4_mutating_admission_ready": False,
        "all_checks_pass": all(bool(value) for value in checks.values()),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(Path(report), summary)
    return summary


def _model_evidence_by_id(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None or not path.exists():
        return {}
    records: dict[str, dict[str, Any]] = {}
    for item in _read_jsonl(path):
        candidate_id = str(item.get("candidate_id") or "")
        if candidate_id:
            records[candidate_id] = item
    return records


def _capture_exact_safe_hits(
    capture_log_dir: Path,
    *,
    safe_ids: set[str],
    evidence_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for path in sorted(Path(capture_log_dir).rglob("*.jsonl")):
        for event in _read_jsonl(path):
            if event.get("event") != "journey_counterfactual_replay_capture":
                continue
            if str(event.get("pricing_state") or "") == "LOCAL_NO_COLUMN_UNCERTIFIED":
                continue
            for rank, journey in enumerate(event.get("returned_journeys") or []):
                if not isinstance(journey, dict):
                    continue
                signature_id = journey_gat_candidate_id_from_signature(journey.get("signature"))
                if signature_id not in safe_ids:
                    continue
                key = (str(event.get("context_hash") or ""), signature_id)
                if key in seen:
                    continue
                seen.add(key)
                evidence = evidence_by_id.get(signature_id, {})
                candidates.append(
                    {
                        **_candidate_payload(event, journey, rank=rank),
                        "signature_id": signature_id,
                        "selection_category": "exact_safe_id_hit",
                        "exact_safe_id_hit": True,
                        "admission_ready": bool(evidence.get("admission_ready", False)),
                        "admission_blocker": str(
                            evidence.get("admission_blocker")
                            or "exact_safe_id_hit_but_online_trajectory_roi_unverified"
                        ),
                        "model_evidence_score": evidence.get("evidence_score"),
                        "model_best_key_level": str(evidence.get("best_key_level") or ""),
                        "model_offline_high_count": int(evidence.get("offline_high_count") or 0),
                        "model_offline_delay_conflict_count": int(
                            evidence.get("offline_delay_conflict_count") or 0
                        ),
                        "model_offline_high_roi_count": int(
                            evidence.get("offline_high_roi_count") or 0
                        ),
                        "model_offline_high_roi_mean": evidence.get("offline_high_roi_mean"),
                    }
                )
    candidates.sort(
        key=lambda item: (
            float(item.get("true_reduced_cost") or 0.0),
            int(item.get("cg_iter") or 0),
            int(item.get("rank") or 0),
            str(item.get("signature_id") or ""),
        )
    )
    return candidates


def _min_or_none(values: Any) -> float | None:
    items = list(values)
    if not items:
        return None
    return float(min(items))


def _max_or_none(values: Any) -> float | None:
    items = list(values)
    if not items:
        return None
    return float(max(items))


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 2026-06-16 BPC_future GAT Stage 4 v14 Exact Safe-hit Target Candidates 报告",
        "",
        "## 结论",
        "",
        "本报告把 v14 online coverage 中的 exact safe-id hits 导出为 target-materialization",
        "runbook 可消费的 candidates.json。它只读 safe-source、model-scored evidence 和",
        "counterfactual replay capture 日志；不运行 BPC / pricing / RMP / worker，也不改变 admission。",
        "",
        "```text",
        f"capture_exact_safe_hit_count = {summary['capture_exact_safe_hit_count']}",
        f"selected_candidate_count = {summary['selected_candidate_count']}",
        f"selected_context_counts = {summary['selected_context_counts']}",
        f"selected_pricing_kind_counts = {summary['selected_pricing_kind_counts']}",
        f"selected_true_reduced_cost_min = {summary['selected_true_reduced_cost_min']}",
        f"selected_true_reduced_cost_max = {summary['selected_true_reduced_cost_max']}",
        f"candidates_path = {summary['candidates_path']}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## Selected Task Sets",
        "",
        "```text",
        *[str(item) for item in summary["selected_task_sets"]],
        "```",
        "",
        "## 判定",
        "",
        "这些候选已经是 exact safe-id hit，但仍只表示候选可被定位；",
        "它们尚未证明加入 RMP 后会改善 objective、dual、basis、tail retry 或 certificate tail。",
        "",
        "```text",
        "stage4_mutating_admission_ready = false",
        "next_step = target_materialization_online_trajectory_roi_ab",
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
