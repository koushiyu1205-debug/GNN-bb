#!/usr/bin/env python3
"""Build a concrete collection manifest for selector holdout calibration.

The current root-cause evidence says the next allowed work is still
calibration-only: collect no-certificate-effect exact-context rows with full
active-basis snapshots, then retry an addition-before selector holdout.  This
script turns the abstract collection plan into concrete context targets and
source-row anchors.  It does not run BPC, pricing, RMP, Pulse, workers,
certificates, or benchmarks.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_COLLECTION_PLAN = Path(
    "BPC_future/results/root_cause_selector_collection_plan_20260614/summary.json"
)
DEFAULT_SCHEMA_COVERAGE = Path(
    "BPC_future/results/root_cause_selector_collection_schema_coverage_20260614/"
    "summary.json"
)
DEFAULT_FEATURE_AVAILABILITY = Path(
    "BPC_future/results/root_cause_selector_feature_availability_audit_20260614/"
    "summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_holdout_collection_manifest_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_holdout_collection_manifest_zh.md"
)

CAPTURE_CONFIG_REQUIREMENTS = {
    "journey_counterfactual_replay_capture_enabled": True,
    "journey_counterfactual_replay_capture_active_basis_enabled": True,
    "journey_counterfactual_replay_capture_active_basis_max_rows": 0,
    "journey_counterfactual_replay_capture_max_journeys": 0,
    "journey_counterfactual_replay_capture_pool_max_journeys": 0,
    "journey_counterfactual_replay_capture_forbidden_signatures_enabled": True,
    "journey_counterfactual_replay_capture_forbidden_signature_max_count": 0,
    "journey_counterfactual_replay_capture_log_empty": True,
}
FORBIDDEN_EFFECTS = [
    "official certificate gate",
    "worker default enable",
    "production BPC A/B before selector holdout",
    "post-addition or hindsight features in online selector",
]


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _as_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _read_candidate_rows(paths: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for input_path in paths:
        path = Path(input_path)
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                enriched = dict(row)
                enriched["_input_path"] = str(path)
                rows.append(enriched)
    return rows


def _priority_contexts(collection_plan: dict[str, Any]) -> list[dict[str, Any]]:
    contexts: list[dict[str, Any]] = []
    for target in collection_plan.get("priority_context_targets", []) or []:
        target_id = str(target.get("target_id", ""))
        for sample in target.get("sample_contexts", []) or []:
            context_hash = str(sample.get("context_hash", "") or "")
            if not context_hash:
                continue
            contexts.append(
                {
                    "target_id": target_id,
                    "context_hash": context_hash,
                    "failure_kind": sample.get("failure_kind") or target_id,
                    "positive_count": _as_int(sample.get("positive_count")),
                    "noop_count": _as_int(sample.get("noop_count")),
                    "total": _as_int(sample.get("total")),
                    "positive_rate": sample.get("positive_rate"),
                    "selected_rule": sample.get("selected_rule"),
                    "required_label_mix": target.get("required_label_mix"),
                    "why": target.get("why"),
                }
            )
    return contexts


def _compact_source_rows(rows: list[dict[str, str]], limit: int = 8) -> list[dict[str, Any]]:
    compact: list[dict[str, Any]] = []
    for row in rows[:limit]:
        compact.append(
            {
                "input_path": row.get("_input_path", ""),
                "source_file": row.get("source_file", ""),
                "instance": row.get("instance", ""),
                "cg_iter": row.get("cg_iter", ""),
                "task_count": row.get("task_count", ""),
                "task_set": row.get("task_set", ""),
                "sequence": row.get("sequence", ""),
                "single_impact_class": row.get("single_impact_class", ""),
                "single_objective_delta": row.get("single_objective_delta", ""),
                "true_reduced_cost": row.get("true_reduced_cost", ""),
                "active_basis_snapshot_enabled_before": row.get(
                    "active_basis_snapshot_enabled_before", ""
                ),
                "active_basis_snapshot_complete_before": row.get(
                    "active_basis_snapshot_complete_before", ""
                ),
                "active_basis_churn_count_before": row.get(
                    "active_basis_churn_count_before", ""
                ),
                "rmp_degeneracy_pressure_before": row.get(
                    "rmp_degeneracy_pressure_before", ""
                ),
                "control_objective": row.get("control_objective", ""),
                "column_pool_size_before": row.get("column_pool_size_before", ""),
            }
        )
    return compact


def _active_basis_snapshot_row(row: dict[str, str]) -> bool:
    if _as_bool(row.get("active_basis_snapshot_enabled_before")) and _as_bool(
        row.get("active_basis_snapshot_complete_before")
    ):
        return True
    if str(row.get("active_basis_churn_source_before", "")).strip() in {
        "initial_active_basis_snapshot",
        "full_active_basis_signature_symmetric_difference",
    }:
        return True
    return False


def _capture_command_template(target: dict[str, Any]) -> str:
    source = target.get("recommended_source_row") or {}
    instance = str(source.get("instance") or target.get("representative_instance") or "")
    return " ".join(
        [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.",
            "/home/kai/miniconda3/envs/ecole/bin/python",
            "BPC_future/scripts/run_bpc_future.py",
            "--config <same-profile-config-as-source>",
            f"--instances {instance or '<instance>'}",
            "--log-dir BPC_future/results/root_cause_selector_holdout_collection_capture_20260614/logs",
            "--results-csv BPC_future/results/root_cause_selector_holdout_collection_capture_20260614/summary.csv",
            "--set journey_counterfactual_replay_capture_enabled=true",
            "--set journey_counterfactual_replay_capture_active_basis_enabled=true",
            "--set journey_counterfactual_replay_capture_active_basis_max_rows=0",
            "--set journey_counterfactual_replay_capture_max_journeys=0",
            "--set journey_counterfactual_replay_capture_pool_max_journeys=0",
            "--set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true",
            "--set journey_counterfactual_replay_capture_forbidden_signature_max_count=0",
            "--set journey_counterfactual_replay_capture_log_empty=true",
            "--quiet",
        ]
    )


def build_manifest(
    *,
    collection_plan_path: Path,
    schema_coverage_path: Path,
    feature_availability_path: Path,
) -> dict[str, Any]:
    collection_plan = _read_json(collection_plan_path)
    schema_coverage = _read_json(schema_coverage_path)
    feature_availability = _read_json(feature_availability_path)
    input_paths = list(feature_availability.get("input_paths", []) or [])
    rows = _read_candidate_rows(input_paths)
    contexts = _priority_contexts(collection_plan)
    current_snapshot_contexts = {
        str(row.get("context_hash", ""))
        for row in schema_coverage.get("row_summaries", []) or []
        if row.get("journey_payload_complete") is True
        and row.get("event_no_certificate_effect") is True
    }

    targets: list[dict[str, Any]] = []
    for index, context in enumerate(contexts, start=1):
        matching_rows = [
            row for row in rows if str(row.get("context_hash", "")) == context["context_hash"]
        ]
        label_counts = Counter(str(row.get("single_impact_class", "")) for row in matching_rows)
        snapshot_rows = [row for row in matching_rows if _active_basis_snapshot_row(row)]
        representative = matching_rows[0] if matching_rows else {}
        source_files = sorted({row.get("source_file", "") for row in matching_rows if row.get("source_file")})
        needs_snapshot_capture = bool(
            context["context_hash"] not in current_snapshot_contexts
            or not snapshot_rows
        )
        target = {
            "collection_target_id": f"selector_holdout_context_{index:03d}",
            **context,
            "candidate_row_count": len(matching_rows),
            "candidate_label_counts": dict(label_counts),
            "candidate_source_file_count": len(source_files),
            "candidate_source_files": source_files[:8],
            "has_current_active_basis_snapshot_context": (
                context["context_hash"] in current_snapshot_contexts
            ),
            "existing_snapshot_candidate_row_count": len(snapshot_rows),
            "needs_active_basis_snapshot_capture": needs_snapshot_capture,
            "representative_instance": representative.get("instance", ""),
            "representative_cg_iter": representative.get("cg_iter", ""),
            "representative_source_file": representative.get("source_file", ""),
            "recommended_source_row": _compact_source_rows([representative], limit=1)[0]
            if representative
            else {},
            "source_row_examples": _compact_source_rows(matching_rows),
            "capture_contract": {
                "diagnostic_only": True,
                "no_certificate_effect": True,
                "certificate_capable": False,
                "official_bound_effect": False,
                "calibration_only": True,
                "config_requirements": CAPTURE_CONFIG_REQUIREMENTS,
                "forbidden_effects": FORBIDDEN_EFFECTS,
            },
        }
        target["capture_command_template"] = _capture_command_template(target)
        targets.append(target)

    by_kind = Counter(target["failure_kind"] for target in targets)
    target_rows = sum(int(target["candidate_row_count"]) for target in targets)
    needs_snapshot = [
        target for target in targets if target["needs_active_basis_snapshot_capture"]
    ]
    existing_snapshot_targets = [
        target for target in targets if target["has_current_active_basis_snapshot_context"]
    ]
    checks = {
        "collection_plan_passed": collection_plan.get("all_checks_pass") is True,
        "schema_coverage_passed": schema_coverage.get("all_checks_pass") is True,
        "feature_availability_passed": feature_availability.get("all_checks_pass")
        is True,
        "has_priority_contexts": bool(contexts),
        "all_priority_contexts_mapped_to_rows": all(
            int(target["candidate_row_count"]) > 0 for target in targets
        ),
        "covers_all_failure_kinds": set(by_kind)
        == {
            "false_positive_no_positive_context",
            "missed_positive_context",
            "mixed_low_precision_or_recall_context",
        },
        "has_snapshot_gap_targets": bool(needs_snapshot),
        "has_at_least_one_existing_snapshot_anchor": bool(existing_snapshot_targets),
        "all_targets_no_certificate_effect": all(
            target["capture_contract"]["diagnostic_only"]
            and target["capture_contract"]["no_certificate_effect"]
            and not target["capture_contract"]["certificate_capable"]
            and not target["capture_contract"]["official_bound_effect"]
            for target in targets
        ),
        "still_calibration_only": True,
    }
    return {
        "schema_version": "root_cause_selector_holdout_collection_manifest_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "selector_holdout_collection_manifest_ready",
        "current_stage": "calibration_only_selector_holdout",
        "production_direction_proven": False,
        "collection_plan": str(collection_plan_path),
        "schema_coverage": str(schema_coverage_path),
        "feature_availability": str(feature_availability_path),
        "input_paths": input_paths,
        "priority_context_count": len(contexts),
        "collection_target_count": len(targets),
        "collection_target_candidate_row_count": target_rows,
        "failure_kind_counts": dict(by_kind),
        "targets_needing_active_basis_snapshot_count": len(needs_snapshot),
        "existing_active_basis_snapshot_anchor_count": len(existing_snapshot_targets),
        "capture_config_requirements": CAPTURE_CONFIG_REQUIREMENTS,
        "forbidden_effects": FORBIDDEN_EFFECTS,
        "targets": targets,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "当前 priority selector failure contexts 都能映射回已有 candidate rows，"
            "但大多数还缺 full active-basis snapshot 版本。下一步应只做"
            " no-certificate-effect / calibration-only 补采；该 manifest 不证明"
            " production selector、5/10 no-regression 或 20-task speedup。"
        ),
    }


def write_csv(summary: dict[str, Any], path: Path) -> None:
    fieldnames = [
        "collection_target_id",
        "failure_kind",
        "context_hash",
        "candidate_row_count",
        "candidate_label_counts",
        "needs_active_basis_snapshot_capture",
        "has_current_active_basis_snapshot_context",
        "representative_instance",
        "representative_cg_iter",
        "representative_source_file",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for target in summary["targets"]:
            writer.writerow({key: target.get(key, "") for key in fieldnames})


def write_report(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# Root Cause Selector Holdout Collection Manifest 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告把 selector 补采计划转成具体 context manifest。它只读已有",
        "summary/CSV，不运行 BPC / pricing / RMP / Pulse，也不改变 worker、",
        "certificate 或 solver 默认行为。",
        "",
        "## 机器字段",
        "",
        "```text",
        "root_cause_selector_holdout_collection_manifest = current",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"status = {summary['status']}",
        f"current_stage = {summary['current_stage']}",
        f"production_direction_proven = {str(summary['production_direction_proven']).lower()}",
        f"priority_context_count = {summary['priority_context_count']}",
        f"collection_target_count = {summary['collection_target_count']}",
        f"collection_target_candidate_row_count = {summary['collection_target_candidate_row_count']}",
        f"targets_needing_active_basis_snapshot_count = {summary['targets_needing_active_basis_snapshot_count']}",
        f"existing_active_basis_snapshot_anchor_count = {summary['existing_active_basis_snapshot_anchor_count']}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 结论",
        "",
        summary["interpretation"],
        "",
        "## 失败类型覆盖",
        "",
        "```json",
        json.dumps(summary["failure_kind_counts"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## 补采配置要求",
        "",
        "```json",
        json.dumps(
            summary["capture_config_requirements"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## 仍然禁止",
        "",
    ]
    for item in summary["forbidden_effects"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Context targets",
            "",
            "```json",
            json.dumps(
                [
                    {
                        key: target.get(key)
                        for key in [
                            "collection_target_id",
                            "failure_kind",
                            "context_hash",
                            "candidate_row_count",
                            "candidate_label_counts",
                            "needs_active_basis_snapshot_capture",
                            "has_current_active_basis_snapshot_context",
                            "representative_instance",
                            "representative_cg_iter",
                            "representative_source_file",
                            "capture_command_template",
                        ]
                    }
                    for target in summary["targets"]
                ],
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            "```",
            "",
            "## 检查项",
            "",
            "```json",
            json.dumps(summary["checks"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection-plan", default=str(DEFAULT_COLLECTION_PLAN))
    parser.add_argument("--schema-coverage", default=str(DEFAULT_SCHEMA_COVERAGE))
    parser.add_argument(
        "--feature-availability", default=str(DEFAULT_FEATURE_AVAILABILITY)
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    summary = build_manifest(
        collection_plan_path=Path(args.collection_plan),
        schema_coverage_path=Path(args.schema_coverage),
        feature_availability_path=Path(args.feature_availability),
    )
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_csv(summary, output_dir / "collection_targets.csv")
    write_report(summary, Path(args.report))
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
