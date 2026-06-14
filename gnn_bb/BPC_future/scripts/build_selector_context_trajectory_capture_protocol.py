#!/usr/bin/env python3
"""Build the next selector context/trajectory capture protocol.

This diagnostic-only helper converts the latest priority-target and capture-miss
evidence into a machine-checkable protocol for the next data collection round.
It does not run BPC, pricing, RMP, Pulse, workers, replay, certificates, or
benchmarks.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_TARGET_PRIORITY_MATRIX = Path(
    "BPC_future/results/root_cause_selector_holdout_target_priority_matrix_20260614/"
    "summary.json"
)
DEFAULT_PRIORITY_CAPTURE_MISS = Path(
    "BPC_future/results/root_cause_selector_holdout_priority_capture_miss_20260614/"
    "summary.json"
)
DEFAULT_NEXT_ACTION_PLAN = Path(
    "BPC_future/results/root_cause_next_action_plan_20260614/summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_context_trajectory_capture_protocol_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_context_trajectory_capture_protocol_zh.md"
)

EXACT_CONTEXT_COMPONENTS = [
    "context_hash",
    "active_hash_before",
    "pool_signature_hash",
    "forbidden_signature_hash",
    "pool_task_set_hash",
    "returned_task_set_hash",
    "rmp_objective_before",
    "pricing_state",
    "pricing_best_reduced_cost",
]

REQUIRED_CAPTURE_PAYLOAD = [
    "no_certificate_effect",
    "complete_active_basis_snapshot",
    "complete_returned_batch",
    "explicit_forbidden_signature_payload",
    "pool_signature_payload",
    "true_dual_hash_and_vector",
    "cuts_hash",
    "branch_hash",
    "pricing_config_hash",
]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _category_count(summary: dict[str, Any], key: str) -> int:
    return _as_int((summary.get("category_counts", {}) or {}).get(key))


def _top_targets(summary: dict[str, Any], limit: int = 8) -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = []
    for item in (summary.get("top_priority_targets") or [])[:limit]:
        targets.append(
            {
                "context_hash": item.get("context_hash"),
                "priority_score": item.get("priority_score"),
                "row_count": item.get("row_count"),
                "label_counts": item.get("label_counts"),
                "gap_tags": item.get("gap_tags"),
                "complete_snapshot_row_count": item.get(
                    "complete_snapshot_row_count"
                ),
                "explicit_forbidden_row_count": item.get(
                    "explicit_forbidden_row_count"
                ),
                "instance_counts": item.get("instance_counts"),
            }
        )
    return targets


def build_summary(
    *,
    target_priority_matrix_path: Path,
    priority_capture_miss_path: Path,
    next_action_plan_path: Path,
) -> dict[str, Any]:
    target_priority = _read_json(target_priority_matrix_path)
    priority_miss = _read_json(priority_capture_miss_path)
    next_action = _read_json(next_action_plan_path)

    match_policy = [
        {
            "case": "all_exact_components_match",
            "decision": "fills_target_context",
            "reason": "The replay/capture row belongs to the intended pricing universe.",
        },
        {
            "case": "same_active_hash_but_component_drift",
            "decision": "new_context_sample_only",
            "reason": (
                "Same active hash is not sufficient: pool, forbidden, returned batch, "
                "RMP objective, or pricing outcome can change the downstream trajectory."
            ),
        },
        {
            "case": "source_active_hash_not_reached",
            "decision": "new_context_sample_only",
            "reason": (
                "The source profile rerun did not reach the intended active-basis "
                "neighborhood, so it cannot close the target holdout gap."
            ),
        },
        {
            "case": "missing_required_payload",
            "decision": "reject_for_selector_holdout",
            "reason": "Incomplete payload would make the selector label unverifiable.",
        },
    ]

    collection_steps = [
        "collect no-certificate-effect capture events for priority mixed/noop contexts",
        "record every reached context instead of only checking target context hashes",
        "classify exact target hits by full component match, not by active hash alone",
        "route near misses into new context rows with their own hashes and components",
        "rerun selector holdout only after mixed/noop full-snapshot rows are present",
    ]

    checks = {
        "target_priority_matrix_passed": target_priority.get("all_checks_pass") is True,
        "priority_capture_miss_passed": priority_miss.get("all_checks_pass") is True,
        "next_action_plan_passed": next_action.get("all_checks_pass") is True,
        "protocol_is_diagnostic_only": True,
        "source_profile_rerun_is_not_sufficient": (
            _as_int(priority_miss.get("expected_context_count")) > 0
            and _as_int(priority_miss.get("exact_hit_context_count")) == 0
        ),
        "same_active_hash_is_not_sufficient": (
            _as_int(
                priority_miss.get("same_active_component_drift_context_count")
            )
            > 0
        ),
        "source_active_hash_miss_is_observed": (
            _as_int(priority_miss.get("source_active_hash_missing_context_count"))
            > 0
        ),
        "mixed_noop_targets_exist": (
            _category_count(target_priority, "mixed_missing_full_snapshot") > 0
            and _category_count(target_priority, "noop_missing_full_snapshot") > 0
        ),
        "exact_match_requires_full_components": (
            "active_hash_before" in EXACT_CONTEXT_COMPONENTS
            and "pool_signature_hash" in EXACT_CONTEXT_COMPONENTS
            and "forbidden_signature_hash" in EXACT_CONTEXT_COMPONENTS
            and "returned_task_set_hash" in EXACT_CONTEXT_COMPONENTS
            and len(EXACT_CONTEXT_COMPONENTS) >= 8
        ),
        "payload_requires_no_certificate_effect": (
            "no_certificate_effect" in REQUIRED_CAPTURE_PAYLOAD
            and "complete_active_basis_snapshot" in REQUIRED_CAPTURE_PAYLOAD
            and "explicit_forbidden_signature_payload" in REQUIRED_CAPTURE_PAYLOAD
        ),
        "no_production_ab_or_certificate_gate": (
            next_action.get("production_direction_proven") is False
            and next_action.get("goal_complete") is False
        ),
    }

    return {
        "schema_version": "selector_context_trajectory_capture_protocol_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "selector_context_trajectory_capture_protocol_ready",
        "exact_context_components": EXACT_CONTEXT_COMPONENTS,
        "required_capture_payload": REQUIRED_CAPTURE_PAYLOAD,
        "match_policy": match_policy,
        "collection_steps": collection_steps,
        "target_priority_evidence": {
            "recommended_next_stage": target_priority.get("recommended_next_stage"),
            "priority_context_count": target_priority.get("priority_context_count"),
            "mixed_missing_full_snapshot_context_count": _category_count(
                target_priority, "mixed_missing_full_snapshot"
            ),
            "noop_missing_full_snapshot_context_count": _category_count(
                target_priority, "noop_missing_full_snapshot"
            ),
            "uncovered_priority_context_count": target_priority.get(
                "uncovered_priority_context_count"
            ),
            "top_targets": _top_targets(target_priority),
        },
        "priority_capture_miss_evidence": {
            "expected_context_count": priority_miss.get("expected_context_count"),
            "exact_hit_context_count": priority_miss.get("exact_hit_context_count"),
            "source_active_hash_missing_context_count": priority_miss.get(
                "source_active_hash_missing_context_count"
            ),
            "same_active_component_drift_context_count": priority_miss.get(
                "same_active_component_drift_context_count"
            ),
            "observed_event_count": priority_miss.get("observed_event_count"),
        },
        "sources": {
            "target_priority_matrix": str(target_priority_matrix_path),
            "priority_capture_miss": str(priority_capture_miss_path),
            "next_action_plan": str(next_action_plan_path),
        },
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }


def write_report(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# Root Cause Selector Context Trajectory Capture Protocol 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告把 priority target / capture miss 证据转成下一轮 selector holdout",
        "补采协议。它只读已有 summary，不运行 BPC / pricing / RMP / Pulse，也不",
        "改变 worker 或 certificate 行为。",
        "",
        "```text",
        "root_cause_selector_context_trajectory_capture_protocol = current",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"status = {summary['status']}",
        "source_profile_rerun_is_not_sufficient = "
        f"{str(summary['checks']['source_profile_rerun_is_not_sufficient']).lower()}",
        "same_active_hash_is_not_sufficient = "
        f"{str(summary['checks']['same_active_hash_is_not_sufficient']).lower()}",
        "exact_context_component_count = "
        f"{len(summary['exact_context_components'])}",
        "required_capture_payload_count = "
        f"{len(summary['required_capture_payload'])}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## Exact Context Components",
        "",
    ]
    for item in summary["exact_context_components"]:
        lines.append(f"- `{item}`")

    lines.extend(["", "## Required Capture Payload", ""])
    for item in summary["required_capture_payload"]:
        lines.append(f"- `{item}`")

    lines.extend(["", "## Match Policy", ""])
    for item in summary["match_policy"]:
        lines.append(
            f"- `{item['case']}` -> `{item['decision']}`：{item['reason']}"
        )

    lines.extend(["", "## Collection Steps", ""])
    for item in summary["collection_steps"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Target Priority Evidence",
            "",
            "```json",
            json.dumps(
                summary["target_priority_evidence"],
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            "```",
            "",
            "## Priority Capture Miss Evidence",
            "",
            "```json",
            json.dumps(
                summary["priority_capture_miss_evidence"],
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            "```",
            "",
            "## Checks",
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
    parser.add_argument(
        "--target-priority-matrix", default=str(DEFAULT_TARGET_PRIORITY_MATRIX)
    )
    parser.add_argument("--priority-capture-miss", default=str(DEFAULT_PRIORITY_CAPTURE_MISS))
    parser.add_argument("--next-action-plan", default=str(DEFAULT_NEXT_ACTION_PLAN))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    summary = build_summary(
        target_priority_matrix_path=Path(args.target_priority_matrix),
        priority_capture_miss_path=Path(args.priority_capture_miss),
        next_action_plan_path=Path(args.next_action_plan),
    )
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_report(summary, Path(args.report))
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
