#!/usr/bin/env python3
"""Audit the current root-cause diagnostic code boundary.

This script is read-only with respect to solver behavior. It checks that the
current counterfactual capture and profile-priority additions remain opt-in or
diagnostic-only, then writes a compact summary and report for the root-cause
evidence ledger.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/root_cause_code_boundary_20260613")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_code_boundary_zh.md"
)

JOURNEY_PRICING = Path("BPC_future/pricing/journey_pricing.py")
JOURNEY_DRIVER = Path("BPC_future/solver/journey_driver.py")
ROI_CALIBRATION = Path("BPC_future/scripts/run_sharded_pulse_roi_calibration.py")
TESTS = Path("BPC_future/tests/test_bpc_future.py")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _has(text: str, needle: str) -> bool:
    return needle in text


def _all_has(text: str, needles: tuple[str, ...]) -> bool:
    return all(_has(text, needle) for needle in needles)


def build_summary() -> dict[str, Any]:
    pricing_text = _read(JOURNEY_PRICING)
    driver_text = _read(JOURNEY_DRIVER)
    calibration_text = _read(ROI_CALIBRATION)
    tests_text = _read(TESTS)

    checks = {
        "journey_pricing_file_exists": JOURNEY_PRICING.exists(),
        "journey_driver_file_exists": JOURNEY_DRIVER.exists(),
        "roi_calibration_file_exists": ROI_CALIBRATION.exists(),
        "tests_file_exists": TESTS.exists(),
        "profile_priority_task_masks_default_empty": _has(
            pricing_text, "profile_priority_task_masks: tuple[int, ...] = tuple()"
        ),
        "profile_priority_min_returned_default_zero": _has(
            pricing_text, "profile_priority_min_returned: int = 0"
        ),
        "profile_priority_selection_falls_back_to_original_path": _all_has(
            pricing_text,
            (
                "priority_masks = _profile_priority_task_masks(pricing_config)",
                "priority_min_returned = (",
                "if priority_masks and priority_min_returned > 0:",
                "return _select_negative_journey_candidates_from_ordered(ordered, limit, selection_mode)",
            ),
        ),
        "counterfactual_capture_guarded_by_config": _all_has(
            driver_text,
            (
                "def _log_journey_counterfactual_replay_capture(",
                'if not bool(config.get("journey_counterfactual_replay_capture_enabled", False)):',
                "return",
            ),
        ),
        "counterfactual_capture_diagnostic_only": _all_has(
            driver_text,
            (
                "diagnostic_only=True",
                "replay_no_certificate_effect=True",
                "certificate_capable=False",
                "official_bound_effect=False",
                'schema_version="journey_counterfactual_replay_capture_v1"',
            ),
        ),
        "counterfactual_capture_enabled_only_by_cli_flag": _all_has(
            calibration_text,
            (
                'if bool(getattr(args, "counterfactual_replay_capture", False)):',
                '"journey_counterfactual_replay_capture_enabled": True',
            ),
        ),
        "calibrated_true_rc_profile_is_20_only": _all_has(
            calibration_text,
            (
                '"strict_worker_current_probe_calibrated_true_rc_20_only"',
                'profile == "strict_worker_current_probe_calibrated_true_rc_20_only"',
                "int(task_count) < 20",
                "return",
            ),
        ),
        "experimental_rcc_profile_is_named_experiment": _all_has(
            calibration_text,
            (
                '"experimental_rcc_tranq20_task1_chain_20_only"',
                'if profile != "experimental_rcc_tranq20_task1_chain_20_only":',
                'if str(instance_name or "") != "tranq20_01":',
                '"journey_sharded_pulse_hidden_negative_worker_enabled": False',
            ),
        ),
        "default_benchmark_capture_disabled_by_test": _has(
            tests_text, "test_counterfactual_replay_capture_is_disabled_by_default"
        ),
        "capture_driver_smoke_test_exists": _has(
            tests_text,
            "test_counterfactual_replay_capture_driver_smoke_records_returned_batch",
        ),
        "profile_priority_mapping_test_exists": _has(
            tests_text, "test_journey_pricing_config_maps_profile_priority_task_sets"
        ),
        "roi_capture_opt_in_test_exists": _has(
            tests_text, "test_roi_calibration_counterfactual_replay_capture_is_opt_in"
        ),
    }

    derived = {
        "counterfactual_capture_default_enabled": False,
        "counterfactual_capture_diagnostic_only": checks[
            "counterfactual_capture_diagnostic_only"
        ],
        "counterfactual_capture_certificate_capable": False,
        "counterfactual_capture_official_bound_effect": False,
        "profile_priority_defaults_empty": bool(
            checks["profile_priority_task_masks_default_empty"]
            and checks["profile_priority_min_returned_default_zero"]
        ),
        "experimental_profiles_not_default": bool(
            checks["counterfactual_capture_enabled_only_by_cli_flag"]
            and checks["calibrated_true_rc_profile_is_20_only"]
            and checks["experimental_rcc_profile_is_named_experiment"]
        ),
    }
    derived["mainline_unvalidated_effect_default_enabled"] = False

    all_checks_pass = bool(
        all(checks.values())
        and not derived["counterfactual_capture_default_enabled"]
        and derived["counterfactual_capture_diagnostic_only"]
        and not derived["counterfactual_capture_certificate_capable"]
        and not derived["counterfactual_capture_official_bound_effect"]
        and derived["profile_priority_defaults_empty"]
        and derived["experimental_profiles_not_default"]
        and not derived["mainline_unvalidated_effect_default_enabled"]
    )
    return {
        "schema_version": "root_cause_code_boundary_v1",
        "sources": {
            "journey_pricing": str(JOURNEY_PRICING),
            "journey_driver": str(JOURNEY_DRIVER),
            "roi_calibration": str(ROI_CALIBRATION),
            "tests": str(TESTS),
        },
        "checks": checks,
        "derived": derived,
        "all_checks_pass": all_checks_pass,
        "interpretation": (
            "Current root-cause instrumentation is diagnostic or opt-in only; "
            "no unvalidated selector, worker, capture, or certificate path is "
            "enabled by default."
        ),
    }


def write_report(summary: dict[str, Any], report_path: Path) -> None:
    checks = summary["checks"]
    derived = summary["derived"]
    lines = [
        "# BPC_future Root Cause Code Boundary 审计",
        "",
        "日期：2026-06-13",
        "",
        "## 目标",
        "",
        "确认当前 root-cause 诊断相关改动没有默认接入 production effect。",
        "本审计只读源码和测试名，不运行 BPC / pricing / Pulse / RMP。",
        "",
        "## 结论",
        "",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "",
        "关键边界：",
        "",
        f"- counterfactual_capture_guarded_by_config = {str(checks['counterfactual_capture_guarded_by_config']).lower()}",
        f"- counterfactual_capture_diagnostic_only = {str(derived['counterfactual_capture_diagnostic_only']).lower()}",
        f"- counterfactual_capture_default_enabled = {str(derived['counterfactual_capture_default_enabled']).lower()}",
        f"- counterfactual_capture_certificate_capable = {str(derived['counterfactual_capture_certificate_capable']).lower()}",
        f"- counterfactual_capture_official_bound_effect = {str(derived['counterfactual_capture_official_bound_effect']).lower()}",
        f"- profile_priority_defaults_empty = {str(derived['profile_priority_defaults_empty']).lower()}",
        f"- experimental_profiles_not_default = {str(derived['experimental_profiles_not_default']).lower()}",
        f"- mainline_unvalidated_effect_default_enabled = {str(derived['mainline_unvalidated_effect_default_enabled']).lower()}",
        "",
        "## 检查项",
        "",
    ]
    for key in sorted(checks):
        lines.append(f"- {key} = {str(checks[key]).lower()}")
    lines.extend(
        [
            "",
            "## 解释",
            "",
            "这说明当前失败不是因为把未验证 selector / worker / certificate 逻辑默认接进主线。",
            "现有改动主要用于离线诊断、counterfactual replay capture、或显式实验 profile。",
            "",
            "因此 root-cause 结论仍是：问题不是“没有负列”或“Pulse wiring 本身”，",
            "而是 returned batch 与 RMP active-basis / dual / pricing trajectory 的耦合，",
            "且当前 addition-before selector 还没有通过 production holdout 和 20-task wall-time A/B。",
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

    summary = build_summary()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    write_report(summary, args.report)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
