#!/usr/bin/env python3
"""Summarize exact-context capture/replay status for root-cause work.

This is a read-only audit: it consumes existing summaries and emits a compact
status report. It does not run BPC, pricing, RMP, Pulse, or replay itself.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_exact_context_capture_status_20260613"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_exact_context_capture_status_zh.md"
)

READINESS_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_replay_readiness_20260613/"
    "summary.json"
)
CAPTURE_TARGETS_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_capture_targets_20260613/"
    "summary.json"
)
COVERAGE_INITIAL_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_capture_target_coverage_20260613/"
    "summary.json"
)
COVERAGE_AFTER_TARGET002_SUMMARY = Path(
    "BPC_future/results/"
    "root_cause_counterfactual_capture_target_coverage_after_target002_pt03_20260613/"
    "summary.json"
)
TRANQ20_MANIFEST_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_tranq20_20260613/"
    "replay_manifest/summary.json"
)
TRANQ20_IMPACT_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_tranq20_20260613/"
    "impact/summary.json"
)
TARGET001002_MANIFEST_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/"
    "replay_manifest/summary.json"
)
TARGET001002_IMPACT_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/"
    "impact/summary.json"
)
REPLAY_CALIBRATED_SELECTOR_SUMMARY = Path(
    "BPC_future/results/root_cause_replay_calibrated_selector_candidate_20260613/"
    "summary.json"
)
EVIDENCE_LEDGER_SUMMARY = Path(
    "BPC_future/results/root_cause_evidence_ledger_20260613/summary.json"
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _as_int(value: Any) -> int:
    if value in (None, ""):
        return 0
    return int(value)


def build_summary() -> dict[str, Any]:
    readiness = _read_json(READINESS_SUMMARY)
    targets = _read_json(CAPTURE_TARGETS_SUMMARY)
    coverage_initial = _read_json(COVERAGE_INITIAL_SUMMARY)
    coverage_after = _read_json(COVERAGE_AFTER_TARGET002_SUMMARY)
    tranq_manifest = _read_json(TRANQ20_MANIFEST_SUMMARY)
    tranq_impact = _read_json(TRANQ20_IMPACT_SUMMARY)
    target_manifest = _read_json(TARGET001002_MANIFEST_SUMMARY)
    target_impact = _read_json(TARGET001002_IMPACT_SUMMARY)
    selector = _read_json(REPLAY_CALIBRATED_SELECTOR_SUMMARY)
    ledger = _read_json(EVIDENCE_LEDGER_SUMMARY)

    ready_cases = _as_int(tranq_manifest.get("ready_case_count")) + _as_int(
        target_manifest.get("ready_case_count")
    )
    candidate_rows = _as_int(tranq_impact.get("candidate_row_count")) + _as_int(
        target_impact.get("candidate_row_count")
    )
    high_impact = _as_int(tranq_impact.get("high_impact_candidate_count")) + _as_int(
        target_impact.get("high_impact_candidate_count")
    )
    noop = _as_int(tranq_impact.get("noop_candidate_count")) + _as_int(
        target_impact.get("noop_candidate_count")
    )
    full_batch_improved = _as_int(
        tranq_impact.get("full_batch_improved_count")
    ) + _as_int(target_impact.get("full_batch_improved_count"))
    full_batch_count = _as_int(tranq_impact.get("full_batch_count")) + _as_int(
        target_impact.get("full_batch_count")
    )
    checks = {
        "initial_observational_candidates_not_replay_ready": (
            _as_int(readiness.get("ready_candidate_count")) == 0
        ),
        "capture_targets_exist": _as_int(targets.get("target_count")) == 3,
        "target_coverage_eventually_exact": (
            _as_int(coverage_after.get("target_with_exact_capture_count"))
            == _as_int(coverage_after.get("target_count"))
            and _as_int(coverage_after.get("target_count")) > 0
        ),
        "has_ready_exact_context_replay_cases": ready_cases > 0,
        "has_high_impact_and_noop_examples": high_impact > 0 and noop > 0,
        "selector_still_not_production_validated": (
            selector.get("production_validation", {}).get(
                "production_validated_selector"
            )
            is False
        ),
        "goal_still_not_complete": (
            ledger.get("goal_status", {}).get("goal_complete") is False
        ),
    }
    status = {
        "exact_context_capture_and_replay_dataset": (
            "ready_for_selector_calibration_attempt"
            if checks["target_coverage_eventually_exact"]
            and checks["has_ready_exact_context_replay_cases"]
            and checks["has_high_impact_and_noop_examples"]
            else "not_ready"
        ),
        "addition_before_selector": (
            "calibrated_candidate_available_not_production_validated"
            if checks["selector_still_not_production_validated"]
            else "unknown"
        ),
        "production_candidate_ab": "blocked_until_selector_holdout_and_20_speedup",
    }
    return {
        "schema_version": "exact_context_capture_status_v1",
        "sources": {
            "readiness_summary": str(READINESS_SUMMARY),
            "capture_targets_summary": str(CAPTURE_TARGETS_SUMMARY),
            "coverage_initial_summary": str(COVERAGE_INITIAL_SUMMARY),
            "coverage_after_target002_summary": str(COVERAGE_AFTER_TARGET002_SUMMARY),
            "tranq20_manifest_summary": str(TRANQ20_MANIFEST_SUMMARY),
            "tranq20_impact_summary": str(TRANQ20_IMPACT_SUMMARY),
            "target001002_manifest_summary": str(TARGET001002_MANIFEST_SUMMARY),
            "target001002_impact_summary": str(TARGET001002_IMPACT_SUMMARY),
            "selector_summary": str(REPLAY_CALIBRATED_SELECTOR_SUMMARY),
            "evidence_ledger": str(EVIDENCE_LEDGER_SUMMARY),
        },
        "initial_readiness": {
            "recommended_candidate_count": _as_int(
                readiness.get("recommended_candidate_count")
            ),
            "ready_candidate_count": _as_int(readiness.get("ready_candidate_count")),
            "descriptors_with_candidate_row_start_times": _as_int(
                readiness.get("descriptors_with_candidate_row_start_times")
            ),
            "descriptors_with_truncated_sampling": _as_int(
                readiness.get("descriptors_with_truncated_sampling")
            ),
        },
        "target_coverage": {
            "target_count": _as_int(targets.get("target_count")),
            "initial_exact_covered": _as_int(
                coverage_initial.get("target_with_exact_capture_count")
            ),
            "after_target002_exact_covered": _as_int(
                coverage_after.get("target_with_exact_capture_count")
            ),
            "after_target002_uncovered": _as_int(
                coverage_after.get("uncovered_target_count")
            ),
            "capture_event_count_after_target002": _as_int(
                coverage_after.get("capture_event_count")
            ),
        },
        "replay_dataset": {
            "ready_case_count": ready_cases,
            "candidate_row_count": candidate_rows,
            "high_impact_candidate_count": high_impact,
            "noop_candidate_count": noop,
            "full_batch_count": full_batch_count,
            "full_batch_improved_count": full_batch_improved,
            "tranq20_ready_case_count": _as_int(
                tranq_manifest.get("ready_case_count")
            ),
            "target001002_ready_case_count": _as_int(
                target_manifest.get("ready_case_count")
            ),
        },
        "selector_state": {
            "recommended_selector_candidate": selector.get(
                "recommended_selector_candidate"
            ),
            "row_count": _as_int(selector.get("row_count")),
            "false_positive_count": _as_int(
                selector.get("recommended_selector_false_positive_count")
            ),
            "false_negative_count": _as_int(
                selector.get("recommended_selector_false_negative_count")
            ),
            "production_validated_selector": selector.get(
                "production_validation", {}
            ).get("production_validated_selector"),
        },
        "status": status,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "Exact-context capture/replay data is now ready for calibration-only "
            "selector work, because captured contexts include high-impact and noop "
            "examples. It is not production evidence: no selector has passed context, "
            "instance, and dataset holdouts, and no 20-task wall-time speedup has "
            "been proven."
        ),
    }


def _write_report(summary: dict[str, Any], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    text = f"""# BPC_future Exact-context Capture Status 审计

日期：2026-06-13

## 目标

本报告只审计当前 exact-context capture / replay 数据是否足够进入
selector calibration。它不运行 BPC，不改变求解路径，不产生 certificate，也不证明
production speedup。

## 结论

```text
exact_context_capture_and_replay_dataset = {summary['status']['exact_context_capture_and_replay_dataset']}
addition_before_selector = {summary['status']['addition_before_selector']}
production_candidate_ab = {summary['status']['production_candidate_ab']}
```

解释：

- observational replay candidates 最初不是 replay-ready；
- 现在 planned capture targets 已经形成 exact coverage；
- replay dataset 中同时存在 high-impact 与 noop candidates；
- 因此可以进入 calibration-only selector 工作；
- 但还没有 production-validated selector，也没有 20-task wall-time speedup 证据。

## 关键数字

```text
initial_ready_candidate_count = {summary['initial_readiness']['ready_candidate_count']}
target_count = {summary['target_coverage']['target_count']}
initial_exact_covered = {summary['target_coverage']['initial_exact_covered']}
after_target002_exact_covered = {summary['target_coverage']['after_target002_exact_covered']}
after_target002_uncovered = {summary['target_coverage']['after_target002_uncovered']}
ready_case_count = {summary['replay_dataset']['ready_case_count']}
candidate_row_count = {summary['replay_dataset']['candidate_row_count']}
high_impact_candidate_count = {summary['replay_dataset']['high_impact_candidate_count']}
noop_candidate_count = {summary['replay_dataset']['noop_candidate_count']}
full_batch_improved_count = {summary['replay_dataset']['full_batch_improved_count']}
recommended_selector_candidate = {summary['selector_state']['recommended_selector_candidate']}
selector_false_positive_count = {summary['selector_state']['false_positive_count']}
selector_false_negative_count = {summary['selector_state']['false_negative_count']}
production_validated_selector = {summary['selector_state']['production_validated_selector']}
```

## 当前边界

这一关最多证明：

> capture/replay 数据已经足够支持下一轮 calibration-only selector attempt。

它不能证明：

- selector 可以上线；
- worker 可以默认启用；
- certificate gate 可以打开；
- 5/10 不退化；
- 20 wall-time / gap / status / final-judge tail 已改善。

## 下一步门槛

```text
calibration_only_until_selector_passes = true
required_selector_holdouts = context / instance / dataset
selector_feature_scope = addition_before_only
```

只有 addition-before selector 同时通过这些 holdout 后，才允许进入 full BPC A/B。
"""
    report_path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report-path", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    summary = build_summary()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(summary, Path(args.report_path))
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
