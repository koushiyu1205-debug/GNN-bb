#!/usr/bin/env python3
"""Build target-intervention candidates from online GAT shadow capture logs.

The output is a candidate JSON file for
``build_gat_target_priority_worker_ab_runbook.py``.  This is an offline bridge:
it reads shadow/counterfactual-capture logs, but does not run BPC, pricing,
RMP, workers, or certificate logic.
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
    _offline_candidates,
    _read_json,
    _read_jsonl,
    _task_set,
)
from BPC_future.solver.gat_candidate_id import journey_gat_candidate_id_from_signature


DEFAULT_SAFE_SOURCE = Path(
    "BPC_future/results/gat_batch_impact_safe_source_v10_random_wave_task50_5751_20260616/"
    "safe_source.json"
)
DEFAULT_DECISION_RECORDS = Path(
    "BPC_future/results/gat_batch_impact_knn_ood_audit_v10_mixed_random_wave_task50_5751_knn34_20260616/"
    "decision_records.jsonl"
)
DEFAULT_CAPTURE_LOG_DIR = Path(
    "BPC_future/results/gat_target_mode_stage4_v10_20_shadow_capture_context_20260616/"
    "logs_sector_tranq20_01_shadow_capture"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/gat_online_shadow_target_candidates_v10_tranq20_01_20260616"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260616_bpc_future_gat_target_mode_stage4_v10_online_shadow_target_candidates_zh.md"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--safe-source", type=Path, default=DEFAULT_SAFE_SOURCE)
    parser.add_argument("--decision-records", type=Path, default=DEFAULT_DECISION_RECORDS)
    parser.add_argument("--capture-log-dir", type=Path, default=DEFAULT_CAPTURE_LOG_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--max-candidates", type=int, default=8)
    parser.add_argument("--max-conflict-controls", type=int, default=2)
    parser.add_argument("--max-miss-controls", type=int, default=2)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = build_online_shadow_target_candidates(
        safe_source=args.safe_source,
        decision_records=args.decision_records,
        capture_log_dir=args.capture_log_dir,
        output_dir=args.output_dir,
        report=args.report,
        max_candidates=max(1, int(args.max_candidates)),
        max_conflict_controls=max(0, int(args.max_conflict_controls)),
        max_miss_controls=max(0, int(args.max_miss_controls)),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def build_online_shadow_target_candidates(
    *,
    safe_source: Path = DEFAULT_SAFE_SOURCE,
    decision_records: Path = DEFAULT_DECISION_RECORDS,
    capture_log_dir: Path = DEFAULT_CAPTURE_LOG_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    max_candidates: int = 8,
    max_conflict_controls: int = 2,
    max_miss_controls: int = 2,
) -> dict[str, Any]:
    safe = _read_json(Path(safe_source))
    records = _read_jsonl(Path(decision_records))
    offline = _offline_candidates(records, source_cache={})
    safe_ids = {str(item) for item in safe.get("safe_candidate_ids", []) if str(item)}
    offline_high_task_sets = {
        candidate["task_set_key"]
        for candidate in offline
        if candidate.get("safe_source_high_priority") and candidate.get("task_set_key")
    }
    offline_delay_task_sets = {
        candidate["task_set_key"]
        for candidate in offline
        if not bool(candidate.get("label_high_priority")) and candidate.get("task_set_key")
    }
    conflict_task_sets = offline_high_task_sets & offline_delay_task_sets

    capture_candidates = _capture_candidates(
        Path(capture_log_dir),
        safe_ids=safe_ids,
        offline_high_task_sets=offline_high_task_sets,
        conflict_task_sets=conflict_task_sets,
    )
    selected = _select_candidates(
        capture_candidates,
        max_candidates=max(1, int(max_candidates)),
        max_conflict_controls=max(0, int(max_conflict_controls)),
        max_miss_controls=max(0, int(max_miss_controls)),
    )
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    candidates_path = output_dir / "candidates.json"
    candidates_path.write_text(
        json.dumps({"candidates": selected}, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    category_counts = Counter(candidate["selection_category"] for candidate in capture_candidates)
    selected_category_counts = Counter(candidate["selection_category"] for candidate in selected)
    context_counts = Counter(candidate["expected_context_hash"] for candidate in selected)
    checks = {
        "safe_source_ready": bool(safe.get("safe_source_ready", False)),
        "capture_candidates_nonempty": bool(capture_candidates),
        "selected_candidates_nonempty": bool(selected),
        "selected_candidates_have_context": all(
            all(str(candidate.get(field) or "") for field in _required_context_fields())
            for candidate in selected
        ),
        "selected_candidates_have_target_traces": all(
            bool(candidate.get("target_sortie_traces")) for candidate in selected
        ),
        "no_exact_safe_id_hit_selected": all(
            candidate["selection_category"] != "exact_safe_id_hit" for candidate in selected
        ),
    }
    summary = {
        "schema_version": "gat_online_shadow_target_candidates_v1",
        "status": "online_shadow_target_candidates_built",
        "safe_source": str(safe_source),
        "decision_records": str(decision_records),
        "capture_log_dir": str(capture_log_dir),
        "output_dir": str(output_dir),
        "candidates_path": str(candidates_path),
        "safe_candidate_id_count": int(len(safe_ids)),
        "offline_high_task_set_count": int(len(offline_high_task_sets)),
        "offline_conflict_task_set_count": int(len(conflict_task_sets)),
        "capture_candidate_count": int(len(capture_candidates)),
        "capture_category_counts": dict(sorted(category_counts.items())),
        "selected_candidate_count": int(len(selected)),
        "selected_category_counts": dict(sorted(selected_category_counts.items())),
        "selected_context_count": int(len(context_counts)),
        "selected_context_counts": dict(sorted(context_counts.items())),
        "selected_task_sets": [candidate["target_task_set"] for candidate in selected],
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
        "all_checks_pass": all(bool(value) for value in checks.values()),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(Path(report), summary)
    return summary


def _required_context_fields() -> tuple[str, ...]:
    return (
        "expected_context_hash",
        "true_dual_hash",
        "cut_hash",
        "branch_hash",
        "forbidden_signature_hash",
        "active_hash_before",
        "pool_signature_hash",
        "pool_task_set_hash",
    )


def _capture_candidates(
    capture_log_dir: Path,
    *,
    safe_ids: set[str],
    offline_high_task_sets: set[tuple[int, ...]],
    conflict_task_sets: set[tuple[int, ...]],
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
                key = (str(event.get("context_hash") or ""), signature_id)
                if key in seen:
                    continue
                seen.add(key)
                task_set = tuple(_task_set(journey.get("task_set")))
                category = _selection_category(
                    signature_id=signature_id,
                    task_set=task_set,
                    safe_ids=safe_ids,
                    offline_high_task_sets=offline_high_task_sets,
                    conflict_task_sets=conflict_task_sets,
                )
                candidates.append(
                    {
                        **_candidate_payload(event, journey, rank=rank),
                        "signature_id": signature_id,
                        "selection_category": category,
                        "offline_task_set_high_priority": bool(task_set in offline_high_task_sets),
                        "offline_task_set_conflict": bool(task_set in conflict_task_sets),
                    }
                )
    candidates.sort(
        key=lambda item: (
            _category_rank(str(item["selection_category"])),
            float(item.get("true_reduced_cost") or 0.0),
            int(item.get("cg_iter") or 0),
            int(item.get("rank") or 0),
        )
    )
    return candidates


def _selection_category(
    *,
    signature_id: str,
    task_set: tuple[int, ...],
    safe_ids: set[str],
    offline_high_task_sets: set[tuple[int, ...]],
    conflict_task_sets: set[tuple[int, ...]],
) -> str:
    if signature_id in safe_ids:
        return "exact_safe_id_hit"
    if task_set in offline_high_task_sets and task_set not in conflict_task_sets:
        return "task_set_overlap_no_conflict"
    if task_set in offline_high_task_sets and task_set in conflict_task_sets:
        return "task_set_overlap_conflict_control"
    return "no_offline_task_set_overlap_control"


def _category_rank(category: str) -> int:
    order = {
        "task_set_overlap_no_conflict": 0,
        "task_set_overlap_conflict_control": 1,
        "no_offline_task_set_overlap_control": 2,
        "exact_safe_id_hit": 3,
    }
    return order.get(str(category), 9)


def _candidate_payload(event: dict[str, Any], journey: dict[str, Any], *, rank: int) -> dict[str, Any]:
    traces = _target_sortie_traces(journey)
    flattened_sequence = [task for trace in traces for task in trace["sequence"]]
    flattened_arcs = [arc for trace in traces for arc in trace["arc_option_sequence"]]
    task_set = sorted(_task_set(journey.get("task_set")))
    context_hash = str(event.get("context_hash") or "")
    name = _safe_name(
        f"tranq20_ctx{context_hash[:8]}_cg{int(event.get('cg_iter') or 0):02d}_"
        f"r{int(rank):02d}_tasks{'_'.join(str(task) for task in task_set)}"
    )
    return {
        "name": name,
        "instance": str(event.get("instance_path") or ""),
        "task_count": int(event.get("task_count") or 20),
        "instance_family": "sector-wave",
        "region": "tranquillitatis_balmer_like_20km",
        "expected_context_hash": context_hash,
        "true_dual_hash": str(event.get("true_dual_hash") or ""),
        "cut_hash": str(event.get("cut_hash") or ""),
        "branch_hash": str(event.get("branch_hash") or ""),
        "forbidden_signature_hash": str(event.get("forbidden_signature_hash") or ""),
        "active_hash_before": str(event.get("active_hash_before") or ""),
        "pool_signature_hash": str(event.get("pool_signature_hash") or ""),
        "pool_task_set_hash": str(event.get("pool_task_set_hash") or ""),
        "capture_pricing_kind": str(event.get("pricing_kind") or ""),
        "source_file": str(event.get("source_log_path") or ""),
        "cg_iter": int(event.get("cg_iter") or 0),
        "rank": int(rank),
        "true_reduced_cost": float(journey.get("true_reduced_cost") or 0.0),
        "target_sequence": flattened_sequence,
        "target_priority_sequence": flattened_sequence,
        "target_arc_option_sequence": flattened_arcs,
        "target_sortie_traces": traces,
        "target_task_set": task_set,
    }


def _target_sortie_traces(journey: dict[str, Any]) -> list[dict[str, Any]]:
    traces: list[dict[str, Any]] = []
    trips = journey.get("trips")
    if isinstance(trips, list) and trips:
        for trip in trips:
            if not isinstance(trip, dict):
                continue
            raw_tasks = trip.get("tasks")
            if isinstance(raw_tasks, (list, tuple)):
                sequence = [int(task) for task in raw_tasks]
            else:
                sequence = [int(task) for task in _task_set(raw_tasks)]
            arcs = [str(value) for value in (trip.get("arc_option_ids") or [])]
            traces.append(
                {
                    "sequence": sequence,
                    "start_time": float(trip.get("start_time") or 0.0),
                    "arc_option_sequence": arcs,
                }
            )
    if traces:
        return traces
    for item in journey.get("signature") or []:
        if not isinstance(item, (list, tuple)) or len(item) < 3:
            continue
        traces.append(
            {
                "sequence": [int(value) for value in (item[0] or [])],
                "start_time": float(item[2] or 0.0),
                "arc_option_sequence": [str(value) for value in (item[1] or [])],
            }
        )
    return traces


def _select_candidates(
    candidates: list[dict[str, Any]],
    *,
    max_candidates: int,
    max_conflict_controls: int,
    max_miss_controls: int,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        by_category[str(candidate["selection_category"])].append(candidate)
    main_limit = max(0, int(max_candidates) - int(max_conflict_controls) - int(max_miss_controls))
    selected.extend(by_category["task_set_overlap_no_conflict"][:main_limit])
    selected.extend(by_category["task_set_overlap_conflict_control"][: int(max_conflict_controls)])
    selected.extend(by_category["no_offline_task_set_overlap_control"][: int(max_miss_controls)])
    if len(selected) < int(max_candidates):
        seen = {str(item["signature_id"]) for item in selected}
        for candidate in candidates:
            if str(candidate["signature_id"]) in seen:
                continue
            selected.append(candidate)
            seen.add(str(candidate["signature_id"]))
            if len(selected) >= int(max_candidates):
                break
    return selected[: int(max_candidates)]


def _safe_name(text: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in str(text))
    safe = "_".join(part for part in safe.split("_") if part)
    return safe[:160] or "target"


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 2026-06-16 BPC_future GAT Target Mode Stage 4 v10 Online Shadow Target Candidates 报告",
        "",
        "## 结论",
        "",
        "本报告从 20-task shadow+capture 日志中抽取下一轮 same-context target intervention 候选。",
        "它只读日志和 Stage 3 safe-source artifacts，不运行 BPC / pricing / worker，也不改变 admission。",
        "",
        "```text",
        f"capture_candidate_count = {summary['capture_candidate_count']}",
        f"selected_candidate_count = {summary['selected_candidate_count']}",
        f"selected_category_counts = {summary['selected_category_counts']}",
        f"selected_context_count = {summary['selected_context_count']}",
        f"candidates_path = {summary['candidates_path']}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 选择策略",
        "",
        "- 优先选择 offline high-priority task-set 命中且无 offline delay 冲突的 online 候选；",
        "- 少量保留 conflict / miss control，用于下一轮同上下文 ROI 标签区分；",
        "- 所有候选都带完整 context / dual / cut / branch / forbidden / pool hash；",
        "- 输出只给 target-materialization runbook 使用，不是 admission safe-source。",
        "",
        "## Selected Task Sets",
        "",
        "```text",
        *[str(item) for item in summary["selected_task_sets"]],
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
