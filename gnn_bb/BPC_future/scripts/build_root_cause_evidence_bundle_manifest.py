"""Build a compact manifest for the current root-cause evidence bundle.

The manifest is a read-only index over the evidence ledger.  It records which
conclusions are supported or blocking, which artifacts prove them, and which
command refreshes the authoritative ledger.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_LEDGER_SUMMARY = Path(
    "BPC_future/results/root_cause_evidence_ledger_20260613/summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_evidence_bundle_manifest_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_evidence_bundle_manifest_zh.md"
)
REBUILD_SCRIPT = Path("BPC_future/scripts/rebuild_root_cause_evidence_bundle.py")
READINESS_MATRIX_SUMMARY = Path(
    "BPC_future/results/root_cause_direction_readiness_matrix_20260614/"
    "summary.json"
)
READINESS_MATRIX_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_direction_readiness_matrix_zh.md"
)
HOLDOUT_GAP_MATRIX_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_holdout_gap_matrix_20260614/"
    "summary.json"
)
HOLDOUT_GAP_MATRIX_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_holdout_gap_matrix_zh.md"
)
TARGET_PRIORITY_MATRIX_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_holdout_target_priority_matrix_20260614/"
    "summary.json"
)
TARGET_PRIORITY_MATRIX_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_holdout_target_priority_matrix_zh.md"
)
PRIORITY_COLLECTION_RUNBOOK_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_holdout_priority_collection_runbook_20260614/"
    "summary.json"
)
PRIORITY_COLLECTION_RUNBOOK_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_holdout_priority_collection_runbook_zh.md"
)
PRIORITY_COLLECTION_RUNBOOK_COMMANDS = Path(
    "BPC_future/results/root_cause_selector_holdout_priority_collection_runbook_20260614/"
    "commands.sh"
)
PRIORITY_COLLECTION_CAPTURE_AUDIT_SUMMARY = Path(
    "BPC_future/results/"
    "root_cause_selector_holdout_priority_collection_capture_audit_20260614/"
    "summary.json"
)
PRIORITY_COLLECTION_CAPTURE_AUDIT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_holdout_priority_collection_capture_audit_zh.md"
)
PRIORITY_CAPTURE_MISS_SUMMARY = Path(
    "BPC_future/results/"
    "root_cause_selector_holdout_priority_capture_miss_20260614/summary.json"
)
PRIORITY_CAPTURE_MISS_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_holdout_priority_capture_miss_zh.md"
)
HOLDOUT_BLOCKER_STATUS_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_holdout_blocker_status_20260614/"
    "summary.json"
)
HOLDOUT_BLOCKER_STATUS_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_holdout_blocker_status_zh.md"
)
WORKER_NEGATIVE_ROI_BLOCKER_SUMMARY = Path(
    "BPC_future/results/root_cause_worker_negative_column_roi_blocker_20260614/"
    "summary.json"
)
WORKER_NEGATIVE_ROI_BLOCKER_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_worker_negative_column_roi_blocker_zh.md"
)
CONTEXT_TRAJECTORY_PROTOCOL_SUMMARY = Path(
    "BPC_future/results/"
    "root_cause_selector_context_trajectory_capture_protocol_20260614/summary.json"
)
CONTEXT_TRAJECTORY_PROTOCOL_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_context_trajectory_capture_protocol_zh.md"
)
CONTEXT_WORKLIST_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_holdout_context_worklist_20260614/"
    "summary.json"
)
CONTEXT_WORKLIST_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_holdout_context_worklist_zh.md"
)
CONTEXT_WORKLIST_CSV = Path(
    "BPC_future/results/root_cause_selector_holdout_context_worklist_20260614/"
    "context_worklist.csv"
)
CONTEXT_ACTION_PLAN_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_holdout_context_action_plan_20260614/"
    "summary.json"
)
CONTEXT_ACTION_PLAN_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_holdout_context_action_plan_zh.md"
)
CONTEXT_ACTION_PLAN_CSV = Path(
    "BPC_future/results/root_cause_selector_holdout_context_action_plan_20260614/"
    "context_action_plan.csv"
)
CAUSAL_CHAIN_AUDIT_SUMMARY = Path(
    "BPC_future/results/root_cause_causal_chain_audit_20260614/summary.json"
)
CAUSAL_CHAIN_AUDIT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_causal_chain_audit_zh.md"
)
DOCUMENT_CONSISTENCY_SUMMARY = Path(
    "BPC_future/results/root_cause_document_consistency_20260614/summary.json"
)
DOCUMENT_CONSISTENCY_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_document_consistency_zh.md"
)

EXPECTED_CONCLUSIONS = [
    "small_scale_fixed_overhead_sensitivity",
    "twenty_negative_columns_not_sufficient",
    "true_rc_negative_can_be_high_impact_or_noop",
    "selector_not_production_validated",
    "exact_context_capture_ready_but_calibration_only",
    "objective_completion_blocked",
]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _artifact_exists(path: str) -> bool:
    return Path(path).exists()


def build_manifest(ledger_path: Path) -> dict[str, Any]:
    ledger = _read_json(ledger_path)
    entries = [dict(entry) for entry in ledger.get("evidence_source_index", {}).get("entries", [])]
    for entry in entries:
        artifacts = list(entry.get("primary_artifacts", []))
        extra_paths: list[str] = []
        if entry.get("conclusion_id") == "selector_not_production_validated":
            extra_paths.extend(
                [
                    str(HOLDOUT_GAP_MATRIX_SUMMARY),
                    str(HOLDOUT_GAP_MATRIX_REPORT),
                    str(TARGET_PRIORITY_MATRIX_SUMMARY),
                    str(TARGET_PRIORITY_MATRIX_REPORT),
                    str(PRIORITY_COLLECTION_RUNBOOK_SUMMARY),
                    str(PRIORITY_COLLECTION_RUNBOOK_REPORT),
                    str(PRIORITY_COLLECTION_RUNBOOK_COMMANDS),
                    str(PRIORITY_COLLECTION_CAPTURE_AUDIT_SUMMARY),
                    str(PRIORITY_COLLECTION_CAPTURE_AUDIT_REPORT),
                    str(PRIORITY_CAPTURE_MISS_SUMMARY),
                    str(PRIORITY_CAPTURE_MISS_REPORT),
                    str(HOLDOUT_BLOCKER_STATUS_SUMMARY),
                    str(HOLDOUT_BLOCKER_STATUS_REPORT),
                    str(CONTEXT_TRAJECTORY_PROTOCOL_SUMMARY),
                    str(CONTEXT_TRAJECTORY_PROTOCOL_REPORT),
                    str(CONTEXT_WORKLIST_SUMMARY),
                    str(CONTEXT_WORKLIST_REPORT),
                    str(CONTEXT_WORKLIST_CSV),
                    str(CONTEXT_ACTION_PLAN_SUMMARY),
                    str(CONTEXT_ACTION_PLAN_REPORT),
                    str(CONTEXT_ACTION_PLAN_CSV),
                    str(CAUSAL_CHAIN_AUDIT_SUMMARY),
                    str(CAUSAL_CHAIN_AUDIT_REPORT),
                    str(DOCUMENT_CONSISTENCY_SUMMARY),
                    str(DOCUMENT_CONSISTENCY_REPORT),
                ]
            )
        if entry.get("conclusion_id") == "twenty_negative_columns_not_sufficient":
            extra_paths.extend(
                [
                    str(WORKER_NEGATIVE_ROI_BLOCKER_SUMMARY),
                    str(WORKER_NEGATIVE_ROI_BLOCKER_REPORT),
                ]
            )
        if entry.get("conclusion_id") == "objective_completion_blocked":
            extra_paths.extend(
                [
                    str(READINESS_MATRIX_SUMMARY),
                    str(READINESS_MATRIX_REPORT),
                    str(HOLDOUT_GAP_MATRIX_SUMMARY),
                    str(HOLDOUT_GAP_MATRIX_REPORT),
                    str(TARGET_PRIORITY_MATRIX_SUMMARY),
                    str(TARGET_PRIORITY_MATRIX_REPORT),
                    str(PRIORITY_COLLECTION_RUNBOOK_SUMMARY),
                    str(PRIORITY_COLLECTION_RUNBOOK_REPORT),
                    str(PRIORITY_COLLECTION_RUNBOOK_COMMANDS),
                    str(PRIORITY_COLLECTION_CAPTURE_AUDIT_SUMMARY),
                    str(PRIORITY_COLLECTION_CAPTURE_AUDIT_REPORT),
                    str(PRIORITY_CAPTURE_MISS_SUMMARY),
                    str(PRIORITY_CAPTURE_MISS_REPORT),
                    str(HOLDOUT_BLOCKER_STATUS_SUMMARY),
                    str(HOLDOUT_BLOCKER_STATUS_REPORT),
                    str(WORKER_NEGATIVE_ROI_BLOCKER_SUMMARY),
                    str(WORKER_NEGATIVE_ROI_BLOCKER_REPORT),
                    str(CONTEXT_TRAJECTORY_PROTOCOL_SUMMARY),
                    str(CONTEXT_TRAJECTORY_PROTOCOL_REPORT),
                    str(CONTEXT_WORKLIST_SUMMARY),
                    str(CONTEXT_WORKLIST_REPORT),
                    str(CONTEXT_WORKLIST_CSV),
                    str(CONTEXT_ACTION_PLAN_SUMMARY),
                    str(CONTEXT_ACTION_PLAN_REPORT),
                    str(CONTEXT_ACTION_PLAN_CSV),
                    str(DOCUMENT_CONSISTENCY_SUMMARY),
                    str(DOCUMENT_CONSISTENCY_REPORT),
                ]
            )
        for path in extra_paths:
            if path not in artifacts:
                artifacts.append(path)
        entry["primary_artifacts"] = artifacts
    conclusion_ids = [str(entry.get("conclusion_id", "")) for entry in entries]
    primary_artifacts = sorted(
        {
            str(artifact)
            for entry in entries
            for artifact in entry.get("primary_artifacts", [])
            if artifact
        }
    )
    missing_artifacts = [
        artifact for artifact in primary_artifacts if not _artifact_exists(artifact)
    ]
    missing_names = list(
        ledger.get("goal_status", {}).get("missing_requirement_names", [])
    )
    ledger_core_status_consistent = (
        ledger.get("goal_status", {}).get("goal_complete") is False
        and ledger.get("completion_decision", {}).get("status") == "keep_goal_active"
        and missing_names
        == [
            "five_ten_full_no_regression_ab",
            "production_validated_selector",
            "twenty_walltime_speedup",
        ]
    )
    checks = {
        "ledger_core_status_consistent": ledger_core_status_consistent,
        "goal_complete_false": ledger.get("goal_status", {}).get("goal_complete")
        is False,
        "conclusion_ids_match_expected": conclusion_ids == EXPECTED_CONCLUSIONS,
        "has_blocking_conclusion": any(
            entry.get("status") == "blocking" for entry in entries
        ),
        "primary_artifacts_exist": not missing_artifacts,
        "completion_decision_keep_active": (
            ledger.get("completion_decision", {}).get("status")
            == "keep_goal_active"
        ),
        "bundle_rebuild_script_exists": REBUILD_SCRIPT.exists(),
    }
    return {
        "schema_version": "root_cause_evidence_bundle_manifest_v1",
        "source_ledger": str(ledger_path),
        "ledger_refresh_command": (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. "
            "/home/kai/miniconda3/envs/ecole/bin/python "
            "BPC_future/scripts/verify_root_cause_evidence.py "
            "--output-dir BPC_future/results/root_cause_evidence_ledger_20260613"
        ),
        "bundle_rebuild_command": (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. "
            "/home/kai/miniconda3/envs/ecole/bin/python "
            "BPC_future/scripts/rebuild_root_cause_evidence_bundle.py"
        ),
        "bundle_rebuild_script": str(REBUILD_SCRIPT),
        "bundle_rebuild_script_exists": REBUILD_SCRIPT.exists(),
        "goal_complete": ledger.get("goal_status", {}).get("goal_complete"),
        "completion_decision": ledger.get("completion_decision", {}).get("status"),
        "conclusion_ids": conclusion_ids,
        "entry_count": len(entries),
        "primary_artifact_count": len(primary_artifacts),
        "missing_artifacts": missing_artifacts,
        "entries": [
            {
                "conclusion_id": entry.get("conclusion_id"),
                "status": entry.get("status"),
                "summary": entry.get("summary"),
                "primary_artifact_count": len(entry.get("primary_artifacts", [])),
                "primary_artifacts": entry.get("primary_artifacts", []),
            }
            for entry in entries
        ],
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "这是当前根因证据包的索引。它证明证据链可复查，但不改变"
            "完成结论：目标仍未完成，production selector 和 20-task speedup "
            "仍是阻塞项。"
        ),
    }


def write_report(manifest: dict[str, Any], path: Path) -> None:
    lines = [
        "# Root Cause Evidence Bundle Manifest 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告是当前根因证据包索引。它只读 evidence ledger，不运行 solver，",
        "不改变 pricing / worker / certificate。",
        "",
        "## 机器字段",
        "",
        "```text",
        "root_cause_evidence_bundle_manifest = current",
        f"goal_complete = {str(manifest['goal_complete']).lower()}",
        f"completion_decision = {manifest['completion_decision']}",
        f"evidence_bundle_entry_count = {manifest['entry_count']}",
        f"evidence_bundle_primary_artifact_count = {manifest['primary_artifact_count']}",
        f"missing_artifact_count = {len(manifest['missing_artifacts'])}",
        f"conclusion_ids = {','.join(manifest['conclusion_ids'])}",
        f"all_checks_pass = {str(manifest['all_checks_pass']).lower()}",
        "```",
        "",
        "## 复核命令",
        "",
        "```bash",
        manifest["ledger_refresh_command"],
        "```",
        "",
        "## 重建命令",
        "",
        "```bash",
        manifest["bundle_rebuild_command"],
        "```",
        "",
        "## 结论索引",
        "",
    ]
    for entry in manifest["entries"]:
        lines.extend(
            [
                f"### {entry['conclusion_id']}",
                "",
                "```text",
                f"status = {entry['status']}",
                f"primary_artifact_count = {entry['primary_artifact_count']}",
                "```",
                "",
                str(entry["summary"]),
                "",
            ]
        )
    lines.extend(["## 总结", "", manifest["interpretation"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger-summary", default=str(DEFAULT_LEDGER_SUMMARY))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    manifest = build_manifest(Path(args.ledger_summary))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_report(manifest, Path(args.report))
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    return 0 if manifest["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
