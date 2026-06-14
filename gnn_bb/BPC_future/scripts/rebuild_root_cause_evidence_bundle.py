"""Rebuild the current root-cause evidence bundle from existing summaries.

This script is intentionally read-only with respect to solver behavior.  It
does not run BPC, pricing, RMP, or Pulse.  It only refreshes diagnostic catalogs
from existing JSON/CSV summaries and then runs the evidence verifier.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_evidence_rebuild_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_evidence_rebuild_zh.md"
)
LEDGER_SUMMARY = Path(
    "BPC_future/results/root_cause_evidence_ledger_20260613/summary.json"
)


BUILD_SCRIPTS = [
    "BPC_future/scripts/build_selector_counterexample_catalog.py",
    "BPC_future/scripts/build_production_selector_blocker_catalog.py",
    "BPC_future/scripts/build_selector_failure_mechanism_audit.py",
    "BPC_future/scripts/build_selector_context_feature_gap_audit.py",
    "BPC_future/scripts/build_selector_feature_availability_audit.py",
    "BPC_future/scripts/build_capture_schema_feasibility_audit.py",
    "BPC_future/scripts/audit_remaining_rmp_trajectory_field_recovery.py",
    "BPC_future/scripts/audit_active_basis_observability_gap.py",
    "BPC_future/scripts/audit_active_basis_capture_schema_feasibility.py",
    "BPC_future/scripts/audit_selector_enriched_rmp_feature_holdout.py",
    "BPC_future/scripts/audit_selector_enriched_multifeature_model_holdout.py",
    "BPC_future/scripts/build_production_ab_entry_gate_catalog.py",
    "BPC_future/scripts/build_objective_completion_audit.py",
    "BPC_future/scripts/build_next_evidence_protocol_catalog.py",
    "BPC_future/scripts/audit_root_cause_failure_matrix.py",
    "BPC_future/scripts/build_optimization_direction_candidate_registry.py",
    "BPC_future/scripts/audit_selector_component_feature_readiness.py",
    "BPC_future/scripts/audit_selector_component_capture_schema_contract.py",
    "BPC_future/scripts/audit_component_payload_addition_before_rows.py",
    "BPC_future/scripts/audit_component_payload_selector_holdout_extension.py",
    "BPC_future/scripts/audit_selector_context_sufficiency_gap.py",
    "BPC_future/scripts/audit_selector_pool_overlap_feature_probe.py",
    "BPC_future/scripts/audit_selector_next_feature_gate.py",
    "BPC_future/scripts/audit_selector_context_schema_gap.py",
    "BPC_future/scripts/audit_selector_snapshot_sample_coverage.py",
    "BPC_future/scripts/audit_selector_holdout_gap_matrix.py",
    "BPC_future/scripts/audit_selector_holdout_target_priority_matrix.py",
    "BPC_future/scripts/build_selector_holdout_priority_collection_runbook.py",
    "BPC_future/scripts/audit_selector_holdout_priority_collection_capture.py",
    "BPC_future/scripts/audit_selector_holdout_priority_capture_miss.py",
    "BPC_future/scripts/build_selector_context_trajectory_capture_protocol.py",
    "BPC_future/scripts/build_selector_holdout_context_worklist.py",
    "BPC_future/scripts/build_selector_holdout_context_action_plan.py",
    "BPC_future/scripts/build_root_cause_selector_collection_plan.py",
    "BPC_future/scripts/audit_selector_collection_schema_coverage.py",
    "BPC_future/scripts/build_selector_holdout_collection_manifest.py",
    "BPC_future/scripts/build_selector_holdout_collection_runbook.py",
    "BPC_future/scripts/audit_selector_holdout_collection_capture.py",
    "BPC_future/scripts/audit_selector_holdout_blocker_status.py",
    "BPC_future/scripts/audit_worker_negative_column_roi_blocker.py",
    "BPC_future/scripts/build_why_many_attempts_failed_report.py",
    "BPC_future/scripts/build_root_cause_causal_chain_audit.py",
    "BPC_future/scripts/build_root_cause_current_answer.py",
    "BPC_future/scripts/build_root_cause_next_action_plan.py",
    "BPC_future/scripts/audit_root_cause_document_consistency.py",
    "BPC_future/scripts/build_root_cause_direction_readiness_matrix.py",
    "BPC_future/scripts/audit_selector_holdout_target002_drift.py",
    "BPC_future/scripts/audit_selector_holdout_target002_probe_matrix.py",
    "BPC_future/scripts/audit_selector_holdout_target002_trajectory_branch.py",
    "BPC_future/scripts/audit_selector_holdout_missing_context_diagnosis.py",
    "BPC_future/scripts/audit_selector_holdout_target002_component_drift.py",
    "BPC_future/scripts/audit_root_cause_stale_claims.py",
    "BPC_future/scripts/audit_root_cause_missing_requirement_evidence_scan.py",
    "BPC_future/scripts/build_root_cause_evidence_bundle_manifest.py",
]
VERIFIER_COMMAND = [
    "BPC_future/scripts/verify_root_cause_evidence.py",
    "--output-dir",
    "BPC_future/results/root_cause_evidence_ledger_20260613",
]


def _run_command(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, *command],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return {
        "command": [sys.executable, *command],
        "returncode": int(completed.returncode),
        "stdout_tail": completed.stdout[-2000:],
        "stderr_tail": completed.stderr[-2000:],
    }


def rebuild(*, skip_final_verifier: bool = False) -> dict[str, Any]:
    commands: list[list[str]] = [[script] for script in BUILD_SCRIPTS]
    if not skip_final_verifier:
        commands.append(VERIFIER_COMMAND)
        # The verifier rewrites the ledger; refresh ledger-derived catalogs once
        # more so their summaries reflect the final checked ledger.
        commands.extend([[script] for script in BUILD_SCRIPTS[2:]])
        commands.append(VERIFIER_COMMAND)
    results = [_run_command(command) for command in commands]
    all_commands_pass = all(result["returncode"] == 0 for result in results)
    ledger = {}
    if LEDGER_SUMMARY.exists():
        ledger = json.loads(LEDGER_SUMMARY.read_text(encoding="utf-8"))
    return {
        "schema_version": "root_cause_evidence_rebuild_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "command_count": len(results),
        "commands": results,
        "all_commands_pass": all_commands_pass,
        "final_ledger_all_checks_pass": ledger.get("all_checks_pass"),
        "final_goal_complete": ledger.get("goal_status", {}).get("goal_complete"),
        "final_completion_decision": ledger.get("completion_decision", {}).get(
            "status"
        ),
        "all_checks_pass": bool(
            all_commands_pass
            and ledger.get("all_checks_pass") is True
            and ledger.get("goal_status", {}).get("goal_complete") is False
            and ledger.get("completion_decision", {}).get("status")
            == "keep_goal_active"
        ),
    }


def write_report(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# Root Cause Evidence Rebuild 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告记录根因证据包 rebuild 结果。该 rebuild 只运行诊断聚合脚本和",
        "verifier，不运行 BPC / pricing / RMP / Pulse。",
        "",
        "## 机器字段",
        "",
        "```text",
        "root_cause_evidence_rebuild = current",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"command_count = {summary['command_count']}",
        f"all_commands_pass = {str(summary['all_commands_pass']).lower()}",
        f"final_ledger_all_checks_pass = {str(summary['final_ledger_all_checks_pass']).lower()}",
        f"final_goal_complete = {str(summary['final_goal_complete']).lower()}",
        f"final_completion_decision = {summary['final_completion_decision']}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 命令",
        "",
    ]
    for index, result in enumerate(summary["commands"], 1):
        lines.extend(
            [
                f"### {index}",
                "",
                "```text",
                " ".join(str(part) for part in result["command"]),
                f"returncode = {result['returncode']}",
                "```",
                "",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--skip-final-verifier", action="store_true")
    args = parser.parse_args()

    summary = rebuild(skip_final_verifier=bool(args.skip_final_verifier))
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
