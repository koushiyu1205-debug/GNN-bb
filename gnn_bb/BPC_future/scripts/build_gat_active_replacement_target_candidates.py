#!/usr/bin/env python3
"""Extract active-replacement target candidates from exact capture logs.

This is an offline bridge from Stage 4 diagnostics back to target-worker
experiments. It reads existing JSONL logs and writes a candidates.json payload
for ``build_gat_target_priority_worker_ab_runbook.py``. It does not run BPC,
pricing, RMP, workers, or certificate logic.
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

from BPC_future.scripts.audit_gat_safe_source_online_coverage import _read_jsonl, _task_set
from BPC_future.scripts.build_gat_online_shadow_target_candidates import (
    _candidate_payload,
    _required_context_fields,
)
from BPC_future.solver.gat_candidate_id import journey_gat_candidate_id_from_signature


DEFAULT_LOG_DIR = Path(
    "BPC_future/results/gat_target_priority_worker_ab_v10_online_shadow_candidates_20260616/"
    "task020_tranq20_ctxac056820_cg07_r02_tasks1_5_mainline_baseline/logs"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/gat_active_replacement_target_candidates_tranq20_01_20260616"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260616_bpc_future_gat_target_mode_stage4_active_replacement_candidates_zh.md"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log-dir", type=Path, default=DEFAULT_LOG_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--max-active", type=int, default=8)
    parser.add_argument("--max-replacement-controls", type=int, default=4)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = build_active_replacement_target_candidates(
        log_dir=args.log_dir,
        output_dir=args.output_dir,
        report=args.report,
        max_active=max(1, int(args.max_active)),
        max_replacement_controls=max(0, int(args.max_replacement_controls)),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def build_active_replacement_target_candidates(
    *,
    log_dir: Path = DEFAULT_LOG_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    max_active: int = 8,
    max_replacement_controls: int = 4,
) -> dict[str, Any]:
    exact_candidates = _active_replacement_candidates(Path(log_dir))
    selected = _select_candidates(
        exact_candidates,
        max_active=max(1, int(max_active)),
        max_replacement_controls=max(0, int(max_replacement_controls)),
    )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    candidates_path = output_dir / "candidates.json"
    candidates_path.write_text(
        json.dumps({"candidates": selected}, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    category_counts = Counter(candidate["selection_category"] for candidate in exact_candidates)
    selected_category_counts = Counter(candidate["selection_category"] for candidate in selected)
    checks = {
        "diagnostic_only": True,
        "capture_candidates_nonempty": bool(exact_candidates),
        "selected_candidates_nonempty": bool(selected),
        "selected_active_candidates_nonempty": any(
            candidate["selection_category"] == "active_replacement"
            for candidate in selected
        ),
        "selected_candidates_have_context": all(
            all(str(candidate.get(field) or "") for field in _required_context_fields())
            for candidate in selected
        ),
        "selected_candidates_have_target_traces": all(
            bool(candidate.get("target_sortie_traces")) for candidate in selected
        ),
        "active_samples_not_truncated": not any(
            bool(candidate.get("active_changed_task_set_samples_truncated"))
            for candidate in selected
        ),
    }
    summary = {
        "schema_version": "gat_active_replacement_target_candidates_v1",
        "status": "active_replacement_target_candidates_built",
        "log_dir": str(log_dir),
        "output_dir": str(output_dir),
        "candidates_path": str(candidates_path),
        "capture_candidate_count": int(len(exact_candidates)),
        "capture_category_counts": dict(sorted(category_counts.items())),
        "selected_candidate_count": int(len(selected)),
        "selected_category_counts": dict(sorted(selected_category_counts.items())),
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


def _active_replacement_candidates(log_dir: Path) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for path in sorted(Path(log_dir).rglob("*.jsonl")):
        events = _read_jsonl(path)
        additions = _addition_events_by_iter(events)
        for event in events:
            if event.get("event") != "journey_counterfactual_replay_capture":
                continue
            if str(event.get("pricing_kind") or "") != "exact":
                continue
            if str(event.get("pricing_state") or "") == "LOCAL_NO_COLUMN_UNCERTIFIED":
                continue
            addition = _matching_addition(additions, event)
            if not addition:
                continue
            active_sets = set(_task_sets(addition.get("active_changed_task_set_samples")))
            replacement_sets = set(_task_sets(addition.get("replacement_task_set_samples")))
            if not active_sets and not replacement_sets:
                continue
            for rank, journey in enumerate(event.get("returned_journeys") or []):
                if not isinstance(journey, dict):
                    continue
                task_set = tuple(_task_set(journey.get("task_set")))
                category = _selection_category(task_set, active_sets, replacement_sets)
                if not category:
                    continue
                signature_id = journey_gat_candidate_id_from_signature(journey.get("signature"))
                key = (str(event.get("context_hash") or ""), signature_id)
                if key in seen:
                    continue
                seen.add(key)
                candidates.append(
                    {
                        **_candidate_payload(event, journey, rank=rank),
                        "signature_id": signature_id,
                        "selection_category": category,
                        "addition_productivity_class": str(
                            addition.get("addition_productivity_class") or ""
                        ),
                        "active_changed_task_set_count": int(
                            addition.get("active_changed_task_set_count") or 0
                        ),
                        "replacement_task_set_count": int(
                            addition.get("replacement_task_set_count") or 0
                        ),
                        "active_changed_task_set_samples_truncated": bool(
                            addition.get("active_changed_task_set_samples_truncated")
                        ),
                        "replacement_task_set_samples_truncated": bool(
                            addition.get("replacement_task_set_samples_truncated")
                        ),
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


def _addition_events_by_iter(events: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        if event.get("event") != "journey_column_addition":
            continue
        try:
            cg_iter = int(event.get("cg_iter") or 0)
        except (TypeError, ValueError):
            cg_iter = 0
        grouped[cg_iter].append(event)
    return grouped


def _matching_addition(
    additions: dict[int, list[dict[str, Any]]],
    capture: dict[str, Any],
) -> dict[str, Any] | None:
    try:
        cg_iter = int(capture.get("cg_iter") or 0)
    except (TypeError, ValueError):
        cg_iter = 0
    pricing_kind = str(capture.get("pricing_kind") or "")
    candidates = additions.get(cg_iter, [])
    if not candidates:
        return None
    exact = [item for item in candidates if str(item.get("pricing_kind") or "") == pricing_kind]
    return (exact or candidates)[0]


def _task_sets(value: Any) -> tuple[tuple[int, ...], ...]:
    if not isinstance(value, (list, tuple)):
        return tuple()
    result: list[tuple[int, ...]] = []
    for item in value:
        task_set = tuple(_task_set(item))
        if task_set:
            result.append(task_set)
    return tuple(result)


def _selection_category(
    task_set: tuple[int, ...],
    active_sets: set[tuple[int, ...]],
    replacement_sets: set[tuple[int, ...]],
) -> str:
    if task_set in active_sets and task_set in replacement_sets:
        return "active_replacement"
    if task_set in active_sets:
        return "active_changed"
    if task_set in replacement_sets:
        return "replacement_control"
    return ""


def _category_rank(category: str) -> int:
    order = {
        "active_replacement": 0,
        "active_changed": 1,
        "replacement_control": 2,
    }
    return order.get(str(category), 9)


def _select_candidates(
    candidates: list[dict[str, Any]],
    *,
    max_active: int,
    max_replacement_controls: int,
) -> list[dict[str, Any]]:
    active = [
        candidate
        for candidate in candidates
        if candidate["selection_category"] in {"active_replacement", "active_changed"}
    ][: int(max_active)]
    controls = [
        candidate
        for candidate in candidates
        if candidate["selection_category"] == "replacement_control"
    ][: int(max_replacement_controls)]
    return active + controls


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 2026-06-16 BPC_future GAT Target Mode Stage 4 Active-replacement Candidates 报告",
        "",
        "## 结论",
        "",
        "本报告从 exact capture batch 和同迭代 column-addition 事件中抽取 active/replacement target candidates。",
        "它只读日志，不运行 BPC / pricing / worker，也不改变 admission。",
        "",
        "```text",
        f"capture_candidate_count = {summary['capture_candidate_count']}",
        f"selected_candidate_count = {summary['selected_candidate_count']}",
        f"selected_category_counts = {summary['selected_category_counts']}",
        f"selected_task_sets = {summary['selected_task_sets']}",
        f"candidates_path = {summary['candidates_path']}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 选择策略",
        "",
        "- 优先选择同迭代 `active_changed_task_set_samples` 命中的 returned journeys；",
        "- 其中同时属于 `replacement_task_set_samples` 的标记为 `active_replacement`；",
        "- 少量保留 replacement-only controls，用于下一步区分 active ROI 与普通 replacement；",
        "- 输出只给 target-materialization runbook 使用，不是 admission safe-source。",
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
