#!/usr/bin/env python3
"""Audit whether full active-basis capture is feasible without solver changes.

This diagnostic is intentionally static/read-only.  It inspects the current
Journey RMP solution schema and journey driver diagnostics to determine whether
the missing active-basis/lambda snapshot can be captured from already-computed
objects.  It does not run BPC, pricing, RMP, Pulse, replay, or benchmarks.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


JOURNEY_RMP = Path("BPC_future/master/journey_rmp.py")
JOURNEY_DRIVER = Path("BPC_future/solver/journey_driver.py")
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_active_basis_capture_schema_feasibility_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_active_basis_capture_schema_feasibility_zh.md"
)


TARGET_SCHEMA_FIELDS = [
    "active_journey_pool_index",
    "active_lambda_value",
    "active_journey_signature",
    "active_journey_task_set",
    "active_journey_cost",
    "active_journey_trip_signatures",
    "active_journey_trip_task_sets",
    "active_journey_reduced_cost",
    "active_basis_snapshot_hash",
]
CURRENT_FULL_SNAPSHOT_KEYS = [
    "pool_active_journey_snapshots",
    "pool_active_basis_snapshot",
    "pool_active_journey_ids",
    "pool_active_lambda_values",
    "active_journeys_payload",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _function_text(source: str, name: str) -> str:
    marker = f"def {name}("
    start = source.find(marker)
    if start < 0:
        return ""
    next_def = source.find("\ndef ", start + len(marker))
    if next_def < 0:
        next_def = len(source)
    return source[start:next_def]


def _contains_all(source: str, needles: list[str]) -> bool:
    return all(needle in source for needle in needles)


def audit() -> dict[str, Any]:
    rmp_exists = JOURNEY_RMP.exists()
    driver_exists = JOURNEY_DRIVER.exists()
    rmp_text = _read(JOURNEY_RMP) if rmp_exists else ""
    driver_text = _read(JOURNEY_DRIVER) if driver_exists else ""
    diagnostics_body = _function_text(driver_text, "_journey_pool_structure_diagnostics")
    solve_body = _function_text(rmp_text, "solve_journey_rmp")

    solution_has_journey_values = (
        "journey_values: list[tuple[JourneyColumn, float]]" in rmp_text
    )
    solution_has_variable_values = "variable_values: dict[int, float]" in rmp_text
    solution_has_reduced_costs = "reduced_costs: dict[int, float]" in rmp_text
    solve_returns_active_values = _contains_all(
        solve_body,
        [
            "values = [",
            "(journeys[index], value)",
            "if value > 1.0e-9",
            "journey_values=values",
        ],
    )
    solve_returns_full_variable_values = _contains_all(
        solve_body,
        [
            "variable_values = {index: float(model.getVal(var))",
            "variable_values=variable_values",
        ],
    )
    solve_can_return_reduced_costs = _contains_all(
        solve_body,
        [
            "capture_reduced_costs",
            "model.getVarRedcost(var)",
            "reduced_costs=reduced_costs",
        ],
    )
    driver_passes_active_values_to_diagnostics = (
        "_journey_pool_structure_diagnostics(journey_pool, solution.journey_values)"
        in driver_text
    )
    driver_passes_variable_values_to_diagnostics = (
        "_journey_pool_structure_diagnostics(journey_pool, solution.variable_values)"
        in driver_text
    )
    counterfactual_capture_passes_active_variable_values = (
        "active_variable_values=solution.variable_values" in driver_text
    )
    counterfactual_capture_supports_active_basis_snapshot = _contains_all(
        driver_text,
        [
            "journey_counterfactual_replay_capture_active_basis_enabled",
            "active_basis_rows",
            "active_basis_snapshot_hash",
            "_journey_replay_capture_active_basis_snapshot",
        ],
    )
    diagnostics_emits_aggregate_active_fields = _contains_all(
        diagnostics_body,
        [
            '"pool_active_journey_count"',
            '"pool_active_task_set_count"',
            '"pool_active_task_set_hash"',
            '"pool_active_top_task_set_value_samples"',
        ],
    )
    diagnostics_emits_full_snapshot = any(
        f'"{key}"' in diagnostics_body for key in CURRENT_FULL_SNAPSHOT_KEYS
    )

    derivation = {
        "active_journey_pool_index": {
            "source": "solution.variable_values + journey_pool.journeys index",
            "feasible": bool(solution_has_variable_values and solve_returns_full_variable_values),
        },
        "active_lambda_value": {
            "source": "solution.variable_values[index]",
            "feasible": bool(solution_has_variable_values and solve_returns_full_variable_values),
        },
        "active_journey_signature": {
            "source": "journey_pool.journeys[index].signature",
            "feasible": bool(solve_returns_full_variable_values),
        },
        "active_journey_task_set": {
            "source": "journey_pool.journeys[index].task_set",
            "feasible": bool(solve_returns_full_variable_values),
        },
        "active_journey_cost": {
            "source": "journey_pool.journeys[index].cost",
            "feasible": bool(solve_returns_full_variable_values),
        },
        "active_journey_trip_signatures": {
            "source": "journey_pool.journeys[index].trips[*].signature",
            "feasible": bool(solve_returns_full_variable_values),
        },
        "active_journey_trip_task_sets": {
            "source": "journey_pool.journeys[index].trips[*].task_set",
            "feasible": bool(solve_returns_full_variable_values),
        },
        "active_journey_reduced_cost": {
            "source": "manual_journey_reduced_cost(journey, true_duals, cuts); optional solver reduced cost comes from solution.reduced_costs",
            "feasible": bool("manual_journey_reduced_cost(journey, duals, cuts=cuts)" in driver_text),
        },
        "active_basis_snapshot_hash": {
            "source": "stable hash of sorted active snapshot rows",
            "feasible": bool(solve_returns_full_variable_values),
        },
    }
    feasible_fields = [
        field for field, payload in derivation.items() if bool(payload["feasible"])
    ]
    missing_fields = [
        field for field, payload in derivation.items() if not bool(payload["feasible"])
    ]
    checks = {
        "source_files_exist": bool(rmp_exists and driver_exists),
        "solution_schema_has_active_values": bool(solution_has_journey_values),
        "solution_schema_has_full_variable_values": bool(solution_has_variable_values),
        "solution_schema_has_reduced_costs": bool(solution_has_reduced_costs),
        "solve_returns_active_values": bool(solve_returns_active_values),
        "solve_returns_full_variable_values": bool(solve_returns_full_variable_values),
        "solve_can_return_reduced_costs": bool(solve_can_return_reduced_costs),
        "current_diagnostics_are_aggregate_only": bool(
            driver_passes_active_values_to_diagnostics
            and diagnostics_emits_aggregate_active_fields
            and not diagnostics_emits_full_snapshot
        ),
        "current_diagnostics_do_not_use_variable_values": bool(
            not driver_passes_variable_values_to_diagnostics
        ),
        "counterfactual_capture_receives_variable_values": bool(
            counterfactual_capture_passes_active_variable_values
        ),
        "counterfactual_capture_has_active_basis_snapshot_schema": bool(
            counterfactual_capture_supports_active_basis_snapshot
        ),
        "target_schema_fields_derivable": len(missing_fields) == 0,
    }
    summary = {
        "schema_version": "active_basis_capture_schema_feasibility_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "source_files": [str(JOURNEY_RMP), str(JOURNEY_DRIVER)],
        "target_schema_fields": TARGET_SCHEMA_FIELDS,
        "feasible_target_schema_fields": feasible_fields,
        "missing_target_schema_fields": missing_fields,
        "feasible_target_schema_field_count": len(feasible_fields),
        "missing_target_schema_field_count": len(missing_fields),
        "solution_has_journey_values": solution_has_journey_values,
        "solution_has_variable_values": solution_has_variable_values,
        "solution_has_reduced_costs": solution_has_reduced_costs,
        "solve_returns_active_values": solve_returns_active_values,
        "solve_returns_full_variable_values": solve_returns_full_variable_values,
        "solve_can_return_reduced_costs": solve_can_return_reduced_costs,
        "driver_passes_active_values_to_diagnostics": driver_passes_active_values_to_diagnostics,
        "driver_passes_variable_values_to_diagnostics": driver_passes_variable_values_to_diagnostics,
        "counterfactual_capture_passes_active_variable_values": (
            counterfactual_capture_passes_active_variable_values
        ),
        "counterfactual_capture_supports_active_basis_snapshot": (
            counterfactual_capture_supports_active_basis_snapshot
        ),
        "diagnostics_emits_aggregate_active_fields": diagnostics_emits_aggregate_active_fields,
        "diagnostics_emits_full_snapshot": diagnostics_emits_full_snapshot,
        "requires_solver_model_change": False,
        "requires_pricing_change": False,
        "requires_certificate_effect": False,
        "requires_no_certificate_effect_logging_guard": True,
        "capture_schema_implementation_status": "implemented_default_off",
        "recommended_next_capture_location": (
            "journey_counterfactual_replay_capture with "
            "journey_counterfactual_replay_capture_active_basis_enabled=true"
        ),
        "field_derivation": derivation,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "The full active-basis/lambda snapshot is derivable from the current "
            "JourneyRMPSolution and journey pool without changing the solver model "
            "or pricing semantics.  A default-off counterfactual replay capture "
            "schema now exists for full active rows; existing replay artifacts remain "
            "incomplete until new no-certificate-effect captures are collected."
        ),
    }
    return summary


def write_report(summary: dict[str, Any], report_path: Path) -> None:
    lines = [
        "# Active Basis Capture Schema Feasibility 审计",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "检查完整 active basis / lambda 快照是否能从当前已计算对象中导出。",
        "该审计只读源码，不运行 BPC、pricing、RMP、Pulse 或 benchmark。",
        "",
        "## 机器字段",
        "",
        "```text",
        "active_basis_capture_schema_feasibility = current",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        "feasible_target_schema_field_count = "
        f"{summary['feasible_target_schema_field_count']}",
        "missing_target_schema_field_count = "
        f"{summary['missing_target_schema_field_count']}",
        "solution_has_journey_values = "
        f"{str(summary['solution_has_journey_values']).lower()}",
        "solution_has_variable_values = "
        f"{str(summary['solution_has_variable_values']).lower()}",
        "solution_has_reduced_costs = "
        f"{str(summary['solution_has_reduced_costs']).lower()}",
        "solve_returns_full_variable_values = "
        f"{str(summary['solve_returns_full_variable_values']).lower()}",
        "solve_can_return_reduced_costs = "
        f"{str(summary['solve_can_return_reduced_costs']).lower()}",
        "driver_passes_variable_values_to_diagnostics = "
        f"{str(summary['driver_passes_variable_values_to_diagnostics']).lower()}",
        "counterfactual_capture_passes_active_variable_values = "
        f"{str(summary['counterfactual_capture_passes_active_variable_values']).lower()}",
        "counterfactual_capture_supports_active_basis_snapshot = "
        f"{str(summary['counterfactual_capture_supports_active_basis_snapshot']).lower()}",
        "diagnostics_emits_full_snapshot = "
        f"{str(summary['diagnostics_emits_full_snapshot']).lower()}",
        "requires_solver_model_change = "
        f"{str(summary['requires_solver_model_change']).lower()}",
        "requires_pricing_change = "
        f"{str(summary['requires_pricing_change']).lower()}",
        "requires_certificate_effect = "
        f"{str(summary['requires_certificate_effect']).lower()}",
        "requires_no_certificate_effect_logging_guard = "
        f"{str(summary['requires_no_certificate_effect_logging_guard']).lower()}",
        "capture_schema_implementation_status = "
        f"{summary['capture_schema_implementation_status']}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 字段来源",
        "",
        "| target field | feasible | source |",
        "|---|---:|---|",
    ]
    for field in summary["target_schema_fields"]:
        payload = summary["field_derivation"][field]
        lines.append(
            f"| `{field}` | {str(payload['feasible']).lower()} | "
            f"{payload['source']} |"
        )
    lines.extend(
        [
            "",
            "## 关键判断",
            "",
            "- `JourneyRMPSolution` 已保留 `journey_values`、`variable_values` 和可选 `reduced_costs`；",
            "- `solution.variable_values` 与 `journey_pool.journeys[index]` 配对后可导出 pool index、lambda、signature、task set、cost 和 trip 结构；",
            "- 当前 driver 的 pool diagnostics 只接收 `solution.journey_values`，并只输出 aggregate/hash/top samples；",
            "- 默认关闭的 counterfactual replay capture 已支持 full active basis rows；",
            "- 因此当前 active-basis 观测缺口已经从 schema 缺口收窄为重新采集 no-certificate-effect replay 数据的缺口。",
            "",
            "## 结论",
            "",
            summary["interpretation"],
            "",
            "下一步若继续根因 selector 主线，应使用默认关闭的 no-certificate-effect",
            "诊断捕获重新采集 exact-context replay payload，并重新做 selector holdout；",
            "不应把 schema-ready 或 capture-ready 解释为优化方向已证明。",
            "",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    summary = audit()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_report(summary, args.report)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
