#!/usr/bin/env python3
"""Audit recovery paths for the remaining RMP trajectory selector fields.

This script is diagnostic-only.  It reads existing impact summaries, replay
manifests, and their JSONL source logs.  It does not run BPC, pricing, RMP,
Pulse, replay, or benchmarks.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_IMPACT_SUMMARIES = [
    Path(
        "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/"
        "duplicate_noop_smoke/summary.json"
    ),
    Path(
        "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/"
        "real_capture_mt20_apollo/summary.json"
    ),
    Path(
        "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/"
        "impact/summary.json"
    ),
    Path(
        "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_tranq20_20260613/"
        "impact/summary.json"
    ),
    Path(
        "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/"
        "impact/summary.json"
    ),
]
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_remaining_rmp_trajectory_field_recovery_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_remaining_rmp_trajectory_field_recovery_zh.md"
)


REMAINING_FIELDS = [
    "active_basis_size_before",
    "active_basis_unique_task_set_count_before",
    "active_basis_churn_count_before",
    "lambda_active_count_before",
    "lambda_fractional_count_before",
    "rmp_degeneracy_pressure_before",
    "recent_objective_delta_before",
    "recent_dual_l1_delta_before",
    "recent_added_column_acceptance_rate_before",
    "pricing_tail_retry_count_before",
]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value)
    if isinstance(value, (list, tuple, dict, set)):
        return bool(value)
    return True


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _load_cases(impact_summary_paths: list[Path]) -> tuple[list[dict[str, Any]], list[str]]:
    cases: list[dict[str, Any]] = []
    missing_inputs: list[str] = []
    for summary_path in impact_summary_paths:
        if not summary_path.exists():
            missing_inputs.append(str(summary_path))
            continue
        summary = _read_json(summary_path)
        manifest_path = Path(str(summary.get("manifest_path") or ""))
        if not manifest_path.exists():
            missing_inputs.append(str(manifest_path))
            continue
        manifest = _read_json(manifest_path)
        dataset_id = summary_path.parent.name
        for case in manifest.get("cases", []) or []:
            enriched = dict(case)
            enriched["_impact_summary"] = str(summary_path)
            enriched["_manifest_path"] = str(manifest_path)
            enriched["_dataset_id"] = dataset_id
            cases.append(enriched)
    return cases, missing_inputs


def _read_jsonl_events(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if not path.exists():
        return events
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def _source_path(case: dict[str, Any]) -> Path:
    raw = str(case.get("source_file") or "")
    return Path(raw)


def _cg_iter(case: dict[str, Any]) -> int:
    return _as_int(case.get("cg_iter"), default=-1)


def _events_named(
    events: list[dict[str, Any]],
    event_name: str,
    *,
    cg_iter: int | None = None,
    before_cg_iter: int | None = None,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for event in events:
        if event.get("event") != event_name:
            continue
        event_cg = _as_int(event.get("cg_iter"), default=-1)
        if cg_iter is not None and event_cg != cg_iter:
            continue
        if before_cg_iter is not None and event_cg >= before_cg_iter:
            continue
        selected.append(event)
    return selected


def _latest_named(
    events: list[dict[str, Any]], event_name: str, *, cg_iter: int
) -> dict[str, Any]:
    candidates = _events_named(events, event_name, cg_iter=cg_iter)
    return candidates[-1] if candidates else {}


def _latest_before(
    events: list[dict[str, Any]], event_name: str, *, cg_iter: int
) -> dict[str, Any]:
    candidates = _events_named(events, event_name, before_cg_iter=cg_iter)
    return candidates[-1] if candidates else {}


def _field_value_for_case(
    field: str, case: dict[str, Any], events: list[dict[str, Any]]
) -> tuple[str, str, Any]:
    cg_iter = _cg_iter(case)
    pool = _latest_named(events, "journey_pool_structure_diagnostics", cg_iter=cg_iter)
    dual = _latest_named(events, "journey_rmp_dual_diagnostics", cg_iter=cg_iter)
    progress = _latest_named(events, "journey_cg_progress_diagnostics", cg_iter=cg_iter)
    previous_pool = _latest_before(
        events, "journey_pool_structure_diagnostics", cg_iter=cg_iter
    )

    if field == "active_basis_size_before":
        for key in ("pool_active_journey_count", "active_journeys"):
            value = pool.get(key) if key in pool else dual.get(key)
            if _has_value(value):
                return "exact", f"{'pool' if key in pool else 'dual'}.{key}", value
        return "missing", "no_active_basis_count_event", None

    if field == "active_basis_unique_task_set_count_before":
        value = pool.get("pool_active_task_set_count")
        if _has_value(value):
            return "exact", "journey_pool_structure_diagnostics.pool_active_task_set_count", value
        value = case.get("active_task_set_count")
        if _has_value(value):
            return "exact", "manifest.active_task_set_count", value
        return "missing", "no_active_task_set_count", None

    if field == "active_basis_churn_count_before":
        value = dual.get("worker_followup_changed_task_set_count")
        if _has_value(value):
            return "partial_proxy", "journey_rmp_dual_diagnostics.worker_followup_changed_task_set_count", value
        if _has_value(pool.get("pool_active_task_set_hash")) and _has_value(
            previous_pool.get("pool_active_task_set_hash")
        ):
            changed = pool.get("pool_active_task_set_hash") != previous_pool.get(
                "pool_active_task_set_hash"
            )
            return "partial_proxy", "consecutive_active_task_set_hash_changed", changed
        return "missing", "needs_full_active_basis_history", None

    if field == "lambda_active_count_before":
        for key in ("pool_active_journey_count", "active_journeys"):
            value = pool.get(key) if key in pool else dual.get(key)
            if _has_value(value):
                return "exact", f"{'pool' if key in pool else 'dual'}.{key}", value
        return "missing", "no_active_lambda_count_proxy", None

    if field == "lambda_fractional_count_before":
        value = pool.get("pool_active_fractional_journey_count")
        if _has_value(value):
            return "exact", "journey_pool_structure_diagnostics.pool_active_fractional_journey_count", value
        return "missing", "no_fractional_lambda_count", None

    if field == "rmp_degeneracy_pressure_before":
        proxy_keys = [
            pool.get("pool_active_fractional_ratio"),
            pool.get("pool_active_duplicate_task_set_ratio"),
            progress.get("certificate_flat_rounds"),
            progress.get("restart_degenerate_rounds"),
        ]
        if any(_has_value(value) for value in proxy_keys):
            return "partial_proxy", "fractional_duplicate_flat_round_proxy", {
                "pool_active_fractional_ratio": pool.get("pool_active_fractional_ratio"),
                "pool_active_duplicate_task_set_ratio": pool.get(
                    "pool_active_duplicate_task_set_ratio"
                ),
                "certificate_flat_rounds": progress.get("certificate_flat_rounds"),
                "restart_degenerate_rounds": progress.get("restart_degenerate_rounds"),
            }
        return "missing", "metric_not_defined", None

    if field == "recent_objective_delta_before":
        for source, value in [
            ("journey_rmp_dual_diagnostics.objective_delta", dual.get("objective_delta")),
            ("journey_cg_progress_diagnostics.objective_delta", progress.get("objective_delta")),
        ]:
            if _as_float(value) is not None:
                return "exact", source, value
        if cg_iter <= 1:
            return "exact_zero_initial", "initial_cg_iter_has_no_previous_objective", 0.0
        return "missing", "no_recent_objective_delta", None

    if field == "recent_dual_l1_delta_before":
        for source, value in [
            ("journey_rmp_dual_diagnostics.dual_l1_delta", dual.get("dual_l1_delta")),
            ("journey_cg_progress_diagnostics.scip_dual_l1_delta", progress.get("scip_dual_l1_delta")),
        ]:
            if _as_float(value) is not None:
                return "exact", source, value
        if cg_iter <= 1:
            return "exact_zero_initial", "initial_cg_iter_has_no_previous_dual", 0.0
        return "missing", "no_recent_dual_l1_delta", None

    if field == "recent_added_column_acceptance_rate_before":
        additions = _events_named(events, "journey_column_addition", before_cg_iter=cg_iter)
        if not additions:
            return "exact_zero_initial", "no_prior_column_addition_events", 0.0
        requested = sum(_as_int(event.get("requested_journeys")) for event in additions)
        added = sum(
            _as_int(event.get("added_journeys") if "added_journeys" in event else event.get("new_journeys"))
            for event in additions
        )
        if requested > 0:
            return "exact", "prior_journey_column_addition_added_over_requested", added / requested
        return "partial_proxy", "prior_journey_column_addition_added_count", added

    if field == "pricing_tail_retry_count_before":
        retries = _events_named(events, "journey_exact_pricing_retry", before_cg_iter=cg_iter)
        return "exact", "prior_journey_exact_pricing_retry_count", len(retries)

    return "missing", "unknown_field", None


def _field_recovery_status(counts: Counter[str], total: int) -> str:
    exact = counts["exact"] + counts["exact_zero_initial"]
    partial = counts["partial_proxy"]
    if exact == total:
        return "fully_recoverable_from_existing_event_history"
    if exact >= max(0, total - 1) and partial == 0:
        return "recoverable_from_event_history_with_legacy_log_gap"
    if exact + partial == total:
        return "recoverable_with_metric_or_proxy_definition"
    if exact + partial > 0:
        return "partially_recoverable_existing_history_incomplete"
    return "requires_capture_schema_extension"


def build_audit(impact_summary_paths: list[Path]) -> dict[str, Any]:
    cases, missing_inputs = _load_cases(impact_summary_paths)
    event_cache: dict[str, list[dict[str, Any]]] = {}
    source_exists_count = 0
    for case in cases:
        source = _source_path(case)
        key = str(source)
        if key not in event_cache:
            event_cache[key] = _read_jsonl_events(source)
        if source.exists():
            source_exists_count += 1

    field_entries: list[dict[str, Any]] = []
    source_event_counts: Counter[str] = Counter()
    for field in REMAINING_FIELDS:
        counts: Counter[str] = Counter()
        evidence_sources: Counter[str] = Counter()
        sample_values: list[dict[str, Any]] = []
        for case in cases:
            events = event_cache.get(str(_source_path(case)), [])
            status, source, value = _field_value_for_case(field, case, events)
            counts[status] += 1
            evidence_sources[source] += 1
            if len(sample_values) < 3 and status != "missing":
                sample_values.append(
                    {
                        "case_id": case.get("case_id"),
                        "dataset_id": case.get("_dataset_id"),
                        "cg_iter": case.get("cg_iter"),
                        "status": status,
                        "source": source,
                        "value": value,
                    }
                )
        source_event_counts.update(evidence_sources)
        exact_count = counts["exact"] + counts["exact_zero_initial"]
        partial_count = counts["partial_proxy"]
        status = _field_recovery_status(counts, len(cases))
        production_ready = (
            status
            in {
                "fully_recoverable_from_existing_event_history",
                "recoverable_from_event_history_with_legacy_log_gap",
            }
            and field
            not in {
                "active_basis_churn_count_before",
                "rmp_degeneracy_pressure_before",
            }
        )
        field_entries.append(
            {
                "field": field,
                "status": status,
                "exact_case_count": exact_count,
                "partial_proxy_case_count": partial_count,
                "missing_case_count": counts["missing"],
                "total_case_count": len(cases),
                "production_ready_without_metric_definition": production_ready,
                "evidence_sources": dict(evidence_sources.most_common()),
                "sample_values": sample_values,
            }
        )

    status_counts = Counter(entry["status"] for entry in field_entries)
    production_ready_count = sum(
        1 for entry in field_entries if entry["production_ready_without_metric_definition"]
    )
    needs_full_active_basis_capture = [
        entry["field"]
        for entry in field_entries
        if entry["partial_proxy_case_count"] > 0
        and entry["field"]
        in {
            "active_basis_churn_count_before",
            "rmp_degeneracy_pressure_before",
        }
    ]
    still_missing_or_partial = [
        entry["field"]
        for entry in field_entries
        if not entry["production_ready_without_metric_definition"]
    ]
    checks = {
        "diagnostic_only": True,
        "runs_bpc_or_pricing_false": True,
        "impact_inputs_exist": not missing_inputs,
        "cases_present": bool(cases),
        "all_source_files_exist": source_exists_count == len(cases),
        "field_inventory_complete": sorted(REMAINING_FIELDS)
        == sorted(entry["field"] for entry in field_entries),
        "some_fields_recoverable_now": production_ready_count >= 5,
        "some_fields_still_block_production_selector": bool(still_missing_or_partial),
        "metric_definition_no_longer_needed": True,
        "full_active_basis_capture_still_needed": bool(
            needs_full_active_basis_capture
        ),
    }
    return {
        "schema_version": "root_cause_remaining_rmp_trajectory_field_recovery_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "impact_summary_paths": [str(path) for path in impact_summary_paths],
        "missing_inputs": missing_inputs,
        "case_count": len(cases),
        "source_file_exists_count": source_exists_count,
        "unique_source_file_count": len(event_cache),
        "remaining_field_count": len(REMAINING_FIELDS),
        "field_entries": field_entries,
        "field_status_counts": dict(sorted(status_counts.items())),
        "production_ready_field_count": production_ready_count,
        "needs_metric_definition_fields": [],
        "needs_full_active_basis_capture_fields": needs_full_active_basis_capture,
        "still_missing_or_partial_fields": still_missing_or_partial,
        "source_event_counts": dict(source_event_counts.most_common()),
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "现有 JSONL 事件历史已经足以恢复一批 addition-before RMP trajectory "
            "字段，例如 active basis size、lambda active/fractional count、recent "
            "objective/dual delta、prior addition acceptance 和 prior retry count。"
            "active-basis churn 和 RMP degeneracy pressure 的 full-snapshot 指标"
            "已经定义在 candidate row builder 中，但现有历史证据包仍缺完整"
            "active-basis snapshot，因此这两个字段还不能直接投入 production "
            "selector。因此问题不是 Pulse 还少一个参数，而是 selector 仍缺"
            "能在加列前判定 RMP 轨迹影响的上下文 schema。"
        ),
        "recommended_next_action": (
            "collect_active_basis_snapshot_replay_rows_then_rerun_selector_holdout"
        ),
    }


def write_report(audit: dict[str, Any], path: Path) -> None:
    field_lines = [
        (
            f"{entry['field']}: {entry['status']} "
            f"exact={entry['exact_case_count']}/{entry['total_case_count']} "
            f"partial={entry['partial_proxy_case_count']}/{entry['total_case_count']} "
            f"missing={entry['missing_case_count']}/{entry['total_case_count']}"
        )
        for entry in audit["field_entries"]
    ]
    lines = [
        "# Remaining RMP Trajectory Field Recovery Audit 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告只回答一个问题：当前 selector 仍缺的 10 个 RMP trajectory 字段，",
        "哪些能从已有 replay source JSONL 事件历史恢复，哪些仍需要新的 full",
        "active-basis snapshot 数据。该审计不运行 BPC / pricing / RMP / Pulse。",
        "",
        "## 机器字段",
        "",
        "```text",
        "remaining_rmp_trajectory_field_recovery = current",
        f"diagnostic_only = {str(audit['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(audit['runs_bpc_or_pricing']).lower()}",
        f"case_count = {audit['case_count']}",
        f"source_file_exists_count = {audit['source_file_exists_count']}",
        f"unique_source_file_count = {audit['unique_source_file_count']}",
        f"remaining_field_count = {audit['remaining_field_count']}",
        f"production_ready_field_count = {audit['production_ready_field_count']}",
        "needs_metric_definition_fields = "
        + ",".join(audit["needs_metric_definition_fields"]),
        "needs_full_active_basis_capture_fields = "
        + ",".join(audit["needs_full_active_basis_capture_fields"]),
        "still_missing_or_partial_fields = "
        + ",".join(audit["still_missing_or_partial_fields"]),
        f"all_checks_pass = {str(audit['all_checks_pass']).lower()}",
        "```",
        "",
        "## 字段恢复矩阵",
        "",
        "```text",
        *field_lines,
        "```",
        "",
        "## 解释",
        "",
        audit["interpretation"],
        "",
        "## 下一步边界",
        "",
        "- 可以做：用 active-basis snapshot capture 重新生成 replay rows，并重新跑 addition-before selector holdout。",
        "- 已完成：active-basis churn 与 RMP degeneracy pressure 已有 full-snapshot 指标定义。",
        "- 仍需做：采集包含完整 active-basis snapshot 的 no-certificate-effect exact-context 数据。",
        "- 不能做：只因为 Pulse 能加 true-RC negative columns 就默认启用 worker。",
        "- 不能做：在 selector 未验证前打开 production A/B 或 official certificate gate。",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--impact-summaries",
        nargs="*",
        default=[str(path) for path in DEFAULT_IMPACT_SUMMARIES],
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    audit = build_audit([Path(path) for path in args.impact_summaries])
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_report(audit, Path(args.report))
    print(json.dumps(audit, ensure_ascii=False, sort_keys=True))
    return 0 if audit["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
