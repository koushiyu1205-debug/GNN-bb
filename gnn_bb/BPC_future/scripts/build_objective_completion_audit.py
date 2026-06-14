"""Extract the current user-objective completion audit from the evidence ledger.

This script is diagnostic-only.  It does not run BPC or alter solver behavior.
It turns the ledger's nested objective audit into a compact standalone artifact
that can be consumed by follow-up scripts or new handoff conversations.
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
    "BPC_future/results/root_cause_objective_completion_audit_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_objective_completion_audit_zh.md"
)


EXPECTED_PROVED = [
    "root_cause_explanation_has_evidence",
    "not_limited_to_pulse",
    "no_unvalidated_mainline_change_before_proof",
    "unproven_experiments_not_counted_as_completion",
    "five_ten_no_regression_is_noop_guard_not_worker_success",
]
EXPECTED_NOT_PROVED = [
    "stable_production_optimization_direction",
    "exact_5_10_no_regression_and_20_speedup",
]
EXPECTED_MISSING = [
    "five_ten_full_no_regression_ab",
    "production_validated_selector",
    "twenty_walltime_speedup",
]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _audit_statuses(audit_items: list[dict[str, Any]]) -> dict[str, str]:
    return {
        str(item.get("requirement", "")): str(item.get("status", ""))
        for item in audit_items
    }


def build_audit(ledger_path: Path) -> dict[str, Any]:
    ledger = _read_json(ledger_path)
    objective_audit = ledger.get("objective_requirement_audit", {})
    audit_items = list(objective_audit.get("audit_items", []))
    statuses = _audit_statuses(audit_items)
    completion_decision = ledger.get("completion_decision", {})
    goal_status = ledger.get("goal_status", {})
    production_gate = ledger.get("production_ab_entry_gate", {})
    missing_names = list(goal_status.get("missing_requirement_names", []))
    ledger_core_status_consistent = (
        goal_status.get("goal_complete") is False
        and goal_status.get("should_mark_goal_complete") is False
        and completion_decision.get("status") == "keep_goal_active"
        and missing_names == EXPECTED_MISSING
    )
    checks = {
        "ledger_core_status_consistent": ledger_core_status_consistent,
        "goal_complete_false": goal_status.get("goal_complete") is False,
        "should_mark_goal_complete_false": goal_status.get(
            "should_mark_goal_complete"
        )
        is False,
        "completion_decision_keep_goal_active": (
            completion_decision.get("status") == "keep_goal_active"
        ),
        "proved_requirements_match_expected": all(
            statuses.get(requirement) == "proved" for requirement in EXPECTED_PROVED
        ),
        "not_proved_requirements_match_expected": all(
            statuses.get(requirement) == "not_proved"
            for requirement in EXPECTED_NOT_PROVED
        ),
        "missing_requirements_match_expected": missing_names == EXPECTED_MISSING,
        "production_ab_entry_gate_blocked": (
            production_gate.get("status") == "blocked"
        ),
        "worker_default_forbidden": (
            production_gate.get("must_not_enable_worker_default") is True
        ),
        "certificate_gate_forbidden": (
            production_gate.get("must_not_open_certificate_gate") is True
        ),
    }
    return {
        "schema_version": "objective_completion_audit_v1",
        "source_ledger": str(ledger_path),
        "goal_complete": goal_status.get("goal_complete"),
        "should_mark_goal_complete": goal_status.get("should_mark_goal_complete"),
        "completion_decision": completion_decision.get("status"),
        "proved_requirements": EXPECTED_PROVED,
        "not_proved_requirements": EXPECTED_NOT_PROVED,
        "missing_requirements": missing_names,
        "audit_item_statuses": statuses,
        "blocking_missing_requirements": objective_audit.get(
            "blocking_missing_requirements", []
        ),
        "production_ab_entry_gate": production_gate,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "当前根因解释和边界审计已被证据支持，但稳定生产优化方向与 "
            "5/10 不退化加 20-task 加速的联合条件仍未证明。因此目标必须"
            "保持 active，不能标记完成。"
        ),
    }


def write_report(audit: dict[str, Any], path: Path) -> None:
    statuses = audit["audit_item_statuses"]
    gate = audit["production_ab_entry_gate"]
    text = f"""# Objective Completion Audit 报告

日期：2026-06-14

## 目的

本报告从 evidence ledger 抽取用户原始目标的完成审计。它只读
`summary.json`，不运行 solver，不改变 pricing / worker / certificate。

## 机器字段

```text
objective_completion_audit_catalog = current
goal_complete = {str(audit['goal_complete']).lower()}
should_mark_goal_complete = {str(audit['should_mark_goal_complete']).lower()}
completion_decision = {audit['completion_decision']}
missing_requirements = {','.join(audit['missing_requirements'])}
production_candidate_ab_entry_status = {gate.get('status')}
must_not_enable_worker_default = {str(gate.get('must_not_enable_worker_default')).lower()}
must_not_open_certificate_gate = {str(gate.get('must_not_open_certificate_gate')).lower()}
all_checks_pass = {str(audit['all_checks_pass']).lower()}
```

## 已证明要求

```text
root_cause_explanation_has_evidence = {statuses.get('root_cause_explanation_has_evidence')}
not_limited_to_pulse = {statuses.get('not_limited_to_pulse')}
no_unvalidated_mainline_change_before_proof = {statuses.get('no_unvalidated_mainline_change_before_proof')}
unproven_experiments_not_counted_as_completion = {statuses.get('unproven_experiments_not_counted_as_completion')}
five_ten_no_regression_is_noop_guard_not_worker_success = {statuses.get('five_ten_no_regression_is_noop_guard_not_worker_success')}
```

## 未证明要求

```text
stable_production_optimization_direction = {statuses.get('stable_production_optimization_direction')}
exact_5_10_no_regression_and_20_speedup = {statuses.get('exact_5_10_no_regression_and_20_speedup')}
```

## 结论

{audit['interpretation']}
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger-summary", default=str(DEFAULT_LEDGER_SUMMARY))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    audit = build_audit(Path(args.ledger_summary))
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
