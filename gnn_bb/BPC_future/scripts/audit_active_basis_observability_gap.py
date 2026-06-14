#!/usr/bin/env python3
"""Audit whether exact active-basis trajectory features are observable.

This diagnostic is read-only.  It inspects existing exact-context replay
manifests and JSONL logs, and checks whether they contain enough information to
compute exact addition-before active-basis churn and degeneracy features.  It
does not run BPC, pricing, RMP, Pulse, replay, or benchmarks.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
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
    "BPC_future/results/root_cause_active_basis_observability_gap_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_active_basis_observability_gap_zh.md"
)
ENRICHED_SINGLE_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_enriched_rmp_feature_holdout_20260614/"
    "summary.json"
)
ENRICHED_MODEL_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_enriched_multifeature_model_holdout_20260614/"
    "summary.json"
)


FULL_ACTIVE_EVENT_KEYS = (
    "pool_active_task_sets",
    "active_task_sets",
    "pool_active_journey_ids",
    "active_journey_ids",
    "active_journeys_payload",
    "lambda_values",
    "active_lambda_values",
)
FULL_ACTIVE_MANIFEST_KEYS = (
    "active_task_sets",
    "active_journey_ids",
    "active_lambdas",
    "lambda_values",
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
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


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value)
    if isinstance(value, (list, tuple, dict, set)):
        return bool(value)
    return True


def _load_cases(impact_summaries: list[Path]) -> tuple[list[dict[str, Any]], list[str]]:
    cases: list[dict[str, Any]] = []
    missing_inputs: list[str] = []
    for summary_path in impact_summaries:
        if not summary_path.exists():
            missing_inputs.append(str(summary_path))
            continue
        summary = _read_json(summary_path)
        manifest_path = Path(str(summary.get("manifest_path") or ""))
        if not manifest_path.exists():
            missing_inputs.append(str(manifest_path))
            continue
        manifest = _read_json(manifest_path)
        for case in manifest.get("cases", []) or []:
            if isinstance(case, dict):
                enriched = dict(case)
                enriched["_impact_summary"] = str(summary_path)
                enriched["_manifest_path"] = str(manifest_path)
                cases.append(enriched)
    return cases, missing_inputs


def _events_for_cg(events: list[dict[str, Any]], event_name: str, cg_iter: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for event in events:
        if event.get("event") != event_name:
            continue
        if _as_int(event.get("cg_iter"), default=-1) == cg_iter:
            selected.append(event)
    return selected


def _has_full_active_manifest_snapshot(case: dict[str, Any]) -> bool:
    return any(_has_value(case.get(key)) for key in FULL_ACTIVE_MANIFEST_KEYS)


def _has_full_active_event_snapshot(events: list[dict[str, Any]]) -> bool:
    for event in events:
        if any(_has_value(event.get(key)) for key in FULL_ACTIVE_EVENT_KEYS):
            return True
    return False


def _pool_journeys_have_active_marker(case: dict[str, Any]) -> bool:
    pool = case.get("pool_journeys")
    if not isinstance(pool, list):
        return False
    active_keys = {"active", "lambda", "value", "basis_value", "rmp_value"}
    for journey in pool:
        if isinstance(journey, dict) and any(key in journey for key in active_keys):
            return True
    return False


def _first_pool_event(events: list[dict[str, Any]], cg_iter: int) -> dict[str, Any]:
    pool_events = _events_for_cg(events, "journey_pool_structure_diagnostics", cg_iter)
    return pool_events[-1] if pool_events else {}


def audit(impact_summaries: list[Path]) -> dict[str, Any]:
    cases, missing_inputs = _load_cases(impact_summaries)
    source_cache: dict[Path, list[dict[str, Any]]] = {}
    counters: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    sample_lengths: list[int] = []
    active_counts: list[int] = []
    examples: list[dict[str, Any]] = []

    for case in cases:
        counters["manifest_case_count"] += 1
        source = Path(str(case.get("source_file") or ""))
        if source.exists():
            counters["source_file_exists_count"] += 1
        else:
            reason_counts["missing_source_file"] += 1
            continue
        if source not in source_cache:
            source_cache[source] = _read_jsonl(source)
        events = source_cache[source]
        cg_iter = _as_int(case.get("cg_iter"), default=-1)
        pool_event = _first_pool_event(events, cg_iter)

        if isinstance(case.get("pool_journeys"), list):
            counters["cases_with_pool_journeys"] += 1
        if _pool_journeys_have_active_marker(case):
            counters["cases_with_pool_journey_active_marker"] += 1
        else:
            reason_counts["pool_journeys_have_no_active_or_lambda_marker"] += 1

        if _has_full_active_manifest_snapshot(case):
            counters["cases_with_full_active_manifest_snapshot"] += 1
        else:
            reason_counts["manifest_has_no_full_active_snapshot"] += 1

        if _has_full_active_event_snapshot(_events_for_cg(events, "journey_pool_structure_diagnostics", cg_iter)):
            counters["cases_with_full_active_event_snapshot"] += 1
        else:
            reason_counts["event_has_no_full_active_snapshot"] += 1

        if _has_value(pool_event.get("pool_active_task_set_hash")):
            counters["cases_with_active_hash"] += 1
        else:
            reason_counts["missing_active_hash"] += 1

        samples = pool_event.get("pool_active_top_task_set_value_samples")
        active_count = _as_int(pool_event.get("pool_active_task_set_count"), default=0)
        if isinstance(samples, list) and samples:
            counters["cases_with_active_top_samples"] += 1
            sample_lengths.append(len(samples))
            active_counts.append(active_count)
            if active_count > len(samples):
                counters["cases_with_truncated_active_top_samples"] += 1
            else:
                counters["cases_with_samples_covering_count_but_no_schema_guarantee"] += 1
        else:
            reason_counts["missing_active_top_samples"] += 1

        if len(examples) < 5 and pool_event:
            examples.append(
                {
                    "case_id": case.get("case_id"),
                    "instance": case.get("instance"),
                    "cg_iter": cg_iter,
                    "active_task_set_count": pool_event.get("pool_active_task_set_count"),
                    "active_hash_present": bool(pool_event.get("pool_active_task_set_hash")),
                    "top_sample_count": len(samples) if isinstance(samples, list) else 0,
                    "pool_journey_count": len(case.get("pool_journeys"))
                    if isinstance(case.get("pool_journeys"), list)
                    else None,
                }
            )

    exact_active_basis_churn_reconstructable_case_count = min(
        counters["cases_with_full_active_manifest_snapshot"]
        + counters["cases_with_full_active_event_snapshot"],
        counters["source_file_exists_count"],
    )
    exact_rmp_degeneracy_pressure_reconstructable_case_count = min(
        counters["cases_with_pool_journey_active_marker"]
        + counters["cases_with_full_active_event_snapshot"],
        counters["source_file_exists_count"],
    )

    enriched_single = _read_json(ENRICHED_SINGLE_SUMMARY) if ENRICHED_SINGLE_SUMMARY.exists() else {}
    enriched_model = _read_json(ENRICHED_MODEL_SUMMARY) if ENRICHED_MODEL_SUMMARY.exists() else {}
    single_holdout = enriched_single.get("holdout_by_feature", {})
    active_basis_proxy = single_holdout.get("active_basis_hash_churn_count_before", {})
    degeneracy_proxy = single_holdout.get("rmp_degeneracy_proxy_score_before", {})
    best_model_name = enriched_model.get("best_context_model")
    best_model_holdout = {}
    if isinstance(best_model_name, str):
        best_model_holdout = enriched_model.get("holdout_by_model", {}).get(
            best_model_name, {}
        )

    summary = {
        "schema_version": "active_basis_observability_gap_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "impact_summaries": [str(path) for path in impact_summaries],
        "missing_inputs": missing_inputs,
        "manifest_case_count": counters["manifest_case_count"],
        "source_file_exists_count": counters["source_file_exists_count"],
        "cases_with_pool_journeys": counters["cases_with_pool_journeys"],
        "cases_with_pool_journey_active_marker": counters[
            "cases_with_pool_journey_active_marker"
        ],
        "cases_with_full_active_manifest_snapshot": counters[
            "cases_with_full_active_manifest_snapshot"
        ],
        "cases_with_full_active_event_snapshot": counters[
            "cases_with_full_active_event_snapshot"
        ],
        "cases_with_active_hash": counters["cases_with_active_hash"],
        "cases_with_active_top_samples": counters["cases_with_active_top_samples"],
        "cases_with_truncated_active_top_samples": counters[
            "cases_with_truncated_active_top_samples"
        ],
        "cases_with_samples_covering_count_but_no_schema_guarantee": counters[
            "cases_with_samples_covering_count_but_no_schema_guarantee"
        ],
        "exact_active_basis_churn_reconstructable_case_count": (
            exact_active_basis_churn_reconstructable_case_count
        ),
        "exact_rmp_degeneracy_pressure_reconstructable_case_count": (
            exact_rmp_degeneracy_pressure_reconstructable_case_count
        ),
        "active_basis_proxy_context_folds": (
            active_basis_proxy.get("context_hash", {}).get("passing_fold_count")
        ),
        "degeneracy_proxy_context_folds": (
            degeneracy_proxy.get("context_hash", {}).get("passing_fold_count")
        ),
        "best_multifeature_model": best_model_name,
        "best_multifeature_context_folds": (
            best_model_holdout.get("context_hash", {}).get("passing_fold_count")
        ),
        "robust_enriched_feature_count": len(
            enriched_single.get("robust_all_holdout_enriched_features", []) or []
        ),
        "robust_model_count": len(
            enriched_model.get("robust_all_holdout_models", []) or []
        ),
        "reason_counts": dict(reason_counts),
        "example_cases": examples,
        "checks": {},
        "interpretation": (
            "Existing replay artifacts expose active-basis counts, hashes, and top "
            "samples, but not a full active journey/task-set/lambda snapshot.  "
            "Therefore exact active-basis churn and exact degeneracy pressure cannot "
            "be reconstructed from the current evidence bundle; only proxy fields "
            "are available, and those proxies already failed production holdouts."
        ),
    }
    checks = {
        "has_manifest_cases": summary["manifest_case_count"] > 0,
        "source_logs_exist": summary["source_file_exists_count"] > 0,
        "active_hash_available": summary["cases_with_active_hash"] > 0,
        "top_samples_are_partial_somewhere": (
            summary["cases_with_truncated_active_top_samples"] > 0
        ),
        "pool_journeys_lack_active_markers": (
            summary["cases_with_pool_journey_active_marker"] == 0
        ),
        "full_active_snapshot_missing": (
            summary["exact_active_basis_churn_reconstructable_case_count"] == 0
        ),
        "exact_degeneracy_snapshot_missing": (
            summary["exact_rmp_degeneracy_pressure_reconstructable_case_count"] == 0
        ),
        "proxy_holdout_not_production_ready": (
            summary["robust_enriched_feature_count"] == 0
            and summary["robust_model_count"] == 0
        ),
    }
    summary["checks"] = checks
    summary["all_checks_pass"] = all(checks.values()) and not missing_inputs
    return summary


def write_report(summary: dict[str, Any], report_path: Path) -> None:
    lines = [
        "# Active Basis Observability Gap 审计",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "检查当前 exact-context replay 证据包是否足以恢复真正的 active-basis churn",
        "和 RMP degeneracy pressure。该审计只读现有 summary / manifest / JSONL，",
        "不运行 BPC、pricing、RMP、Pulse 或 replay。",
        "",
        "## 机器字段",
        "",
        "```text",
        "active_basis_observability_gap = current",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"manifest_case_count = {summary['manifest_case_count']}",
        f"source_file_exists_count = {summary['source_file_exists_count']}",
        f"cases_with_pool_journeys = {summary['cases_with_pool_journeys']}",
        "cases_with_pool_journey_active_marker = "
        f"{summary['cases_with_pool_journey_active_marker']}",
        "cases_with_full_active_manifest_snapshot = "
        f"{summary['cases_with_full_active_manifest_snapshot']}",
        "cases_with_full_active_event_snapshot = "
        f"{summary['cases_with_full_active_event_snapshot']}",
        f"cases_with_active_hash = {summary['cases_with_active_hash']}",
        f"cases_with_active_top_samples = {summary['cases_with_active_top_samples']}",
        "cases_with_truncated_active_top_samples = "
        f"{summary['cases_with_truncated_active_top_samples']}",
        "exact_active_basis_churn_reconstructable_case_count = "
        f"{summary['exact_active_basis_churn_reconstructable_case_count']}",
        "exact_rmp_degeneracy_pressure_reconstructable_case_count = "
        f"{summary['exact_rmp_degeneracy_pressure_reconstructable_case_count']}",
        "robust_enriched_feature_count = "
        f"{summary['robust_enriched_feature_count']}",
        f"robust_model_count = {summary['robust_model_count']}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 关键观察",
        "",
        "- `pool_journeys` 存在，但 journey payload 不带 active/lambda 标记；",
        "- JSONL 有 active task-set count、hash 和 top samples，但没有完整 active task-set / journey / lambda 快照；",
        "- top samples 在部分 case 中短于 active task-set count，因此不能当作完整 active basis；",
        "- 当前只能构造 hash churn / degeneracy proxy，而这些 proxy 已经没有通过 production holdout。",
        "",
        "## 示例 case",
        "",
        "| case_id | instance | cg_iter | active_task_set_count | top_sample_count | active_hash_present | pool_journey_count |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for example in summary.get("example_cases", []):
        lines.append(
            "| "
            + str(example.get("case_id"))
            + " | "
            + str(example.get("instance"))
            + " | "
            + str(example.get("cg_iter"))
            + " | "
            + str(example.get("active_task_set_count"))
            + " | "
            + str(example.get("top_sample_count"))
            + " | "
            + str(example.get("active_hash_present"))
            + " | "
            + str(example.get("pool_journey_count"))
            + " |"
        )
    lines.extend(
        [
            "",
            "## 结论",
            "",
            summary["interpretation"],
            "",
            "因此下一步如果继续 selector 主线，必须先补 no-certificate-effect capture schema：",
            "在加列前记录完整 active basis task sets / journey ids / lambda values。",
            "在此之前，active-basis churn 和 degeneracy pressure 只能作为 proxy，不能作为",
            "production-safe 优化方向。",
            "",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--impact-summary",
        action="append",
        default=None,
        help="Impact summary.json path. May be provided multiple times.",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    impact_summaries = (
        [Path(path) for path in args.impact_summary]
        if args.impact_summary
        else list(DEFAULT_IMPACT_SUMMARIES)
    )
    summary = audit(impact_summaries)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.output_dir / "summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_report(summary, args.report)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
