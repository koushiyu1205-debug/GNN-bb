"""Extract the next-evidence protocol from the root-cause ledger.

This is a diagnostic-only helper.  It does not run BPC, pricing, RMP, or Pulse.
It makes the current next step explicit: remain calibration-only until the
addition-before selector evidence is strong enough to enter production BPC A/B.
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
    "BPC_future/results/root_cause_next_evidence_protocol_catalog_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_next_evidence_protocol_catalog_zh.md"
)

EXPECTED_GATES = [
    "exact_context_capture_and_replay_dataset",
    "addition_before_selector",
    "production_candidate_ab",
]
EXPECTED_READINESS = {
    "exact_context_capture_and_replay_dataset": True,
    "addition_before_selector": True,
    "production_candidate_ab": False,
}
EXPECTED_FORBIDDEN_SHORTCUTS = [
    "post_addition_or_hindsight_features",
    "single_context_replay_success",
    "worker_negative_columns_without_walltime_roi",
    "certificate_effect",
]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _items_by_gate(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item.get("gate", "")): dict(item) for item in items}


def build_catalog(ledger_path: Path) -> dict[str, Any]:
    ledger = _read_json(ledger_path)
    completion = ledger.get("completion_requirements", {})
    protocol = ledger.get("next_evidence_protocol", {})
    next_required = ledger.get("next_required_evidence", {})
    gates = list(protocol.get("gates", []))
    readiness = list(protocol.get("readiness", []))
    readiness_by_gate = _items_by_gate(readiness)
    gate_names = [str(item.get("gate", "")) for item in gates]
    readiness_status = {
        gate: bool(readiness_by_gate.get(gate, {}).get("passed_for_current_stage"))
        for gate in EXPECTED_GATES
    }
    production_selector_validated = bool(
        completion.get("has_production_validated_selector")
    )
    addition_before_selector_status = (
        "production_validated"
        if production_selector_validated
        else "calibrated_candidate_available_not_production_validated"
    )
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
        "status_is_calibration_only": (
            protocol.get("status") == "calibration_only_until_selector_passes"
        ),
        "gate_order_matches_expected": gate_names == EXPECTED_GATES,
        "readiness_matches_expected": readiness_status == EXPECTED_READINESS,
        "selector_feature_scope_is_addition_before_only": (
            next_required.get("selector_feature_scope") == "addition_before_only"
        ),
        "required_selector_holdouts_are_context_instance_dataset": (
            next_required.get("required_selector_holdouts")
            == ["context", "instance", "dataset"]
        ),
        "forbidden_shortcuts_match_expected": (
            next_required.get("forbidden_shortcuts") == EXPECTED_FORBIDDEN_SHORTCUTS
        ),
        "production_candidate_ab_still_blocked": (
            readiness_by_gate.get("production_candidate_ab", {}).get(
                "passed_for_current_stage"
            )
            is False
            and readiness_by_gate.get("production_candidate_ab", {}).get(
                "current_status"
            )
            == "blocked_until_production_selector_and_20_speedup_pass"
        ),
        "addition_before_selector_not_misread_as_production_validated": (
            readiness_status.get("addition_before_selector") is True
            and production_selector_validated is False
            and addition_before_selector_status
            == "calibrated_candidate_available_not_production_validated"
        ),
        "no_worker_default_before_gate": (
            ledger.get("production_ab_entry_gate", {}).get(
                "must_not_enable_worker_default"
            )
            is True
        ),
        "no_certificate_gate_before_gate": (
            ledger.get("production_ab_entry_gate", {}).get(
                "must_not_open_certificate_gate"
            )
            is True
        ),
    }
    return {
        "schema_version": "next_evidence_protocol_catalog_v1",
        "source_ledger": str(ledger_path),
        "status": protocol.get("status"),
        "gate_order": gate_names,
        "readiness_status": readiness_status,
        "current_stage": "calibration_only_selector_holdout",
        "production_candidate_ab_status": readiness_by_gate.get(
            "production_candidate_ab", {}
        ).get("current_status"),
        "addition_before_selector_status": addition_before_selector_status,
        "production_selector_validated": production_selector_validated,
        "selector_feature_scope": next_required.get("selector_feature_scope"),
        "required_selector_holdouts": next_required.get("required_selector_holdouts"),
        "forbidden_shortcuts": next_required.get("forbidden_shortcuts"),
        "require_5_10_no_regression_gate_before_production": next_required.get(
            "require_5_10_no_regression_gate_before_production"
        ),
        "require_selected_20_hard_repeat_ab_before_production": next_required.get(
            "require_selected_20_hard_repeat_ab_before_production"
        ),
        "gates": gates,
        "readiness": readiness,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "当前下一步协议不是 production A/B，也不是默认启用 worker。"
            "可继续的是 calibration-only selector holdout：只使用 "
            "addition-before features，并且必须通过 context / instance / dataset "
            "holdout。通过后才允许进入 5/10 no-regression 与 selected 20 hard "
            "repeat A/B。"
        ),
    }


def write_report(catalog: dict[str, Any], path: Path) -> None:
    readiness = catalog["readiness_status"]
    text = f"""# Next Evidence Protocol Catalog 报告

日期：2026-06-14

## 目的

本报告从 evidence ledger 抽取下一步证据协议。它只读 `summary.json`，
不运行 solver，也不改变 pricing / worker / certificate。

## 机器字段

```text
next_evidence_protocol_catalog = current
next_evidence_protocol_status = {catalog['status']}
current_stage = {catalog['current_stage']}
gate_order = {','.join(catalog['gate_order'])}
exact_context_capture_and_replay_dataset_passed = {str(readiness['exact_context_capture_and_replay_dataset']).lower()}
addition_before_selector_passed = {str(readiness['addition_before_selector']).lower()}
addition_before_selector_status = {catalog['addition_before_selector_status']}
production_selector_validated = {str(catalog['production_selector_validated']).lower()}
production_candidate_ab_passed = {str(readiness['production_candidate_ab']).lower()}
production_candidate_ab_status = {catalog['production_candidate_ab_status']}
selector_feature_scope = {catalog['selector_feature_scope']}
required_selector_holdouts = {'/'.join(catalog['required_selector_holdouts'])}
forbidden_shortcuts = {','.join(catalog['forbidden_shortcuts'])}
require_5_10_no_regression_gate_before_production = {str(catalog['require_5_10_no_regression_gate_before_production']).lower()}
require_selected_20_hard_repeat_ab_before_production = {str(catalog['require_selected_20_hard_repeat_ab_before_production']).lower()}
all_checks_pass = {str(catalog['all_checks_pass']).lower()}
```

## 结论

{catalog['interpretation']}
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger-summary", default=str(DEFAULT_LEDGER_SUMMARY))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    catalog = build_catalog(Path(args.ledger_summary))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_report(catalog, Path(args.report))
    print(json.dumps(catalog, ensure_ascii=False, sort_keys=True))
    return 0 if catalog["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
