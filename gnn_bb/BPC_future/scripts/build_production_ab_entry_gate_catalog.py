"""Build a production A/B entry-gate catalog for root-cause evidence.

This diagnostic-only script reads the current root-cause evidence ledger and
production-selector blocker catalog.  It makes one narrow point explicit:
production BPC A/B is blocked until an addition-before selector is production
validated and the required 5/10 and selected-20 evidence gates are satisfied.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_LEDGER_SUMMARY = Path(
    "BPC_future/results/root_cause_evidence_ledger_20260613/summary.json"
)
DEFAULT_SELECTOR_BLOCKER_SUMMARY = Path(
    "BPC_future/results/root_cause_production_selector_blocker_catalog_20260614/"
    "summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_production_ab_entry_gate_catalog_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_production_ab_entry_gate_catalog_zh.md"
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _readiness_by_gate(ledger: dict[str, Any], gate: str) -> dict[str, Any]:
    readiness = (
        ledger.get("next_evidence_protocol", {}).get("readiness")
        or ledger.get("next_required_evidence", {}).get("protocol_readiness")
        or []
    )
    for item in readiness:
        if item.get("gate") == gate:
            return dict(item)
    return {}


def _missing_requirement_names(ledger: dict[str, Any]) -> list[str]:
    names = ledger.get("goal_status", {}).get("missing_requirement_names")
    if isinstance(names, list):
        return [str(name) for name in names]
    return [
        str(item.get("requirement", ""))
        for item in ledger.get("missing_requirements", [])
        if item.get("requirement")
    ]


def build_catalog(
    ledger_path: Path,
    selector_blocker_path: Path,
) -> dict[str, Any]:
    ledger = _read_json(ledger_path)
    selector_blocker = _read_json(selector_blocker_path)
    completion = ledger.get("completion_requirements", {})
    goal = ledger.get("goal_status", {})
    next_required = ledger.get("next_required_evidence", {})
    selector_feature_scope = next_required.get("selector_feature_scope")
    required_selector_holdouts = list(
        next_required.get("required_selector_holdouts", [])
    )
    forbidden_shortcuts = list(next_required.get("forbidden_shortcuts", []))
    production_readiness = _readiness_by_gate(ledger, "production_candidate_ab")
    missing_names = _missing_requirement_names(ledger)
    ledger_core_status_consistent = (
        goal.get("goal_complete") is False
        and ledger.get("completion_decision", {}).get("status") == "keep_goal_active"
        and missing_names
        == [
            "five_ten_full_no_regression_ab",
            "production_validated_selector",
            "twenty_walltime_speedup",
        ]
    )
    required_blockers = [
        "selector_not_validated",
        "five_ten_full_no_regression_missing",
        "twenty_speedup_missing",
    ]
    blockers = [
        {
            "blocker_id": "selector_not_validated",
            "status": "blocking",
            "evidence": {
                "has_replay_calibrated_selector_candidate": completion.get(
                    "has_replay_calibrated_selector_candidate"
                ),
                "has_production_validated_selector": completion.get(
                    "has_production_validated_selector"
                ),
                "production_selector_status": selector_blocker.get("status"),
                "production_selector_blocker_count": len(
                    selector_blocker.get("blockers", [])
                ),
            },
        },
        {
            "blocker_id": "five_ten_full_no_regression_missing",
            "status": "blocking",
            "evidence": {
                "has_task5_noop_no_regression_guard": completion.get(
                    "has_task5_noop_no_regression_guard"
                ),
                "has_task10_noop_no_regression_guard": completion.get(
                    "has_task10_noop_no_regression_guard"
                ),
                "has_task10_triggered_regression_evidence": completion.get(
                    "has_task10_triggered_regression_evidence"
                ),
                "has_full_5_10_production_ab_evidence": completion.get(
                    "has_full_5_10_production_ab_evidence"
                ),
            },
        },
        {
            "blocker_id": "twenty_speedup_missing",
            "status": "blocking",
            "evidence": {
                "has_20_negative_columns": completion.get("has_20_negative_columns"),
                "has_local_rmp_impact": completion.get("has_local_rmp_impact"),
                "has_20_walltime_speedup_evidence": completion.get(
                    "has_20_walltime_speedup_evidence"
                ),
                "production_direction_proven": completion.get(
                    "production_direction_proven"
                ),
            },
        },
    ]
    checks = {
        "ledger_core_status_consistent": ledger_core_status_consistent,
        "completion_decision_keeps_goal_active": (
            ledger.get("completion_decision", {}).get("status")
            == "keep_goal_active"
        ),
        "missing_requirements_match_gate_blockers": missing_names
        == [
            "five_ten_full_no_regression_ab",
            "production_validated_selector",
            "twenty_walltime_speedup",
        ],
        "production_candidate_ab_readiness_blocked": (
            production_readiness.get("gate") == "production_candidate_ab"
            and production_readiness.get("passed_for_current_stage") is False
        ),
        "selector_not_production_validated": (
            completion.get("has_production_validated_selector") is False
            and selector_blocker.get("status") == "production_selector_not_validated"
            and selector_blocker.get("all_checks_pass") is True
        ),
        "full_5_10_ab_missing": (
            completion.get("has_full_5_10_production_ab_evidence") is False
        ),
        "twenty_speedup_missing": (
            completion.get("has_20_walltime_speedup_evidence") is False
            and completion.get("production_direction_proven") is False
        ),
        "certificate_effect_forbidden": (
            "certificate_effect"
            in tuple(forbidden_shortcuts)
        ),
        "selector_feature_scope_is_addition_before_only": (
            selector_feature_scope == "addition_before_only"
        ),
        "required_selector_holdouts_are_context_instance_dataset": (
            required_selector_holdouts == ["context", "instance", "dataset"]
        ),
        "worker_default_must_remain_disabled": (
            goal.get("goal_complete") is False
            and completion.get("production_direction_proven") is False
        ),
    }
    return {
        "schema_version": "production_ab_entry_gate_catalog_v1",
        "production_candidate_ab_entry_status": "blocked",
        "entry_gate_blockers": required_blockers,
        "must_not_enable_worker_default": True,
        "must_not_open_certificate_gate": True,
        "requires_selector_holdout_before_ab": True,
        "requires_5_10_full_no_regression_before_ab": True,
        "requires_selected_20_speedup_before_ab": True,
        "selector_feature_scope": selector_feature_scope,
        "required_selector_holdouts": required_selector_holdouts,
        "forbidden_shortcuts": forbidden_shortcuts,
        "production_candidate_ab": "blocked",
        "blockers": blockers,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "当前 ledger 支持根因解释，但 production BPC A/B 入口仍被阻塞。"
            "原因不是没有 calibration signal，而是 selector 未通过生产 holdout，"
            "5/10 full no-regression A/B 缺失，20-task wall-time speedup 缺失。"
            "在这些门槛解除前，不应默认启用 worker，也不应打开 official "
            "certificate gate。"
        ),
        "sources": {
            "ledger": str(ledger_path),
            "production_selector_blocker": str(selector_blocker_path),
        },
    }


def write_report(catalog: dict[str, Any], path: Path) -> None:
    selector = catalog["blockers"][0]["evidence"]
    five_ten = catalog["blockers"][1]["evidence"]
    twenty = catalog["blockers"][2]["evidence"]
    text = f"""# Production A/B Entry Gate Catalog 报告

日期：2026-06-14

## 目的

本报告只读当前 evidence ledger 和 production selector blocker catalog，明确
production BPC A/B 还不能启动的入口门槛。它不运行 solver，也不改变任何
worker / certificate 配置。

## 机器字段

```text
production_ab_entry_gate_catalog = current
production_candidate_ab_entry_status = {catalog['production_candidate_ab_entry_status']}
production_candidate_ab = {catalog['production_candidate_ab']}
entry_gate_blockers = {','.join(catalog['entry_gate_blockers'])}
must_not_enable_worker_default = {str(catalog['must_not_enable_worker_default']).lower()}
must_not_open_certificate_gate = {str(catalog['must_not_open_certificate_gate']).lower()}
requires_selector_holdout_before_ab = {str(catalog['requires_selector_holdout_before_ab']).lower()}
requires_5_10_full_no_regression_before_ab = {str(catalog['requires_5_10_full_no_regression_before_ab']).lower()}
requires_selected_20_speedup_before_ab = {str(catalog['requires_selected_20_speedup_before_ab']).lower()}
selector_feature_scope = {catalog['selector_feature_scope']}
required_selector_holdouts = {'/'.join(catalog['required_selector_holdouts'])}
forbidden_shortcuts = {','.join(catalog['forbidden_shortcuts'])}
all_checks_pass = {str(catalog['all_checks_pass']).lower()}
```

## 阻塞点

### 1. selector 仍未 production validated

```text
has_replay_calibrated_selector_candidate = {str(selector['has_replay_calibrated_selector_candidate']).lower()}
has_production_validated_selector = {str(selector['has_production_validated_selector']).lower()}
production_selector_status = {selector['production_selector_status']}
production_selector_blocker_count = {selector['production_selector_blocker_count']}
```

### 2. 5/10 full no-regression A/B 仍缺失

```text
has_task5_noop_no_regression_guard = {str(five_ten['has_task5_noop_no_regression_guard']).lower()}
has_task10_noop_no_regression_guard = {str(five_ten['has_task10_noop_no_regression_guard']).lower()}
has_task10_triggered_regression_evidence = {str(five_ten['has_task10_triggered_regression_evidence']).lower()}
has_full_5_10_production_ab_evidence = {str(five_ten['has_full_5_10_production_ab_evidence']).lower()}
```

### 3. 20-task wall-time speedup 仍缺失

```text
has_20_negative_columns = {str(twenty['has_20_negative_columns']).lower()}
has_local_rmp_impact = {str(twenty['has_local_rmp_impact']).lower()}
has_20_walltime_speedup_evidence = {str(twenty['has_20_walltime_speedup_evidence']).lower()}
production_direction_proven = {str(twenty['production_direction_proven']).lower()}
```

## 结论

{catalog['interpretation']}
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger-summary", default=str(DEFAULT_LEDGER_SUMMARY))
    parser.add_argument(
        "--selector-blocker-summary",
        default=str(DEFAULT_SELECTOR_BLOCKER_SUMMARY),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    catalog = build_catalog(
        Path(args.ledger_summary),
        Path(args.selector_blocker_summary),
    )
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
