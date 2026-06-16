#!/usr/bin/env python3
"""Audit GAT target-mode logs for certificate-boundary violations.

The audit is read-only.  It checks that GAT shadow/admission events never claim
pricing-oracle, official-bound, or certificate authority, and that true-RC
negative candidates are not rejected by the learned scheduler view.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


GAT_EVENTS = {
    "journey_gat_target_mode_shadow",
    "journey_gat_target_mode_admission",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--log-dir",
        action="append",
        type=Path,
        required=True,
        help="Directory or jsonl file to audit. May be supplied multiple times.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("BPC_future/results/gat_target_mode_certificate_audit_20260615"),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path(
            "BPC_future/logical_graph/run_reports/"
            "20260615_bpc_future_gat_target_mode_certificate_audit_zh.md"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = audit_gat_target_mode_certificate_closure(
        log_paths=args.log_dir,
        output_dir=args.output_dir,
        report=args.report,
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def audit_gat_target_mode_certificate_closure(
    *,
    log_paths: Iterable[Path],
    output_dir: Path,
    report: Path | None = None,
) -> dict[str, Any]:
    log_files = _expand_log_files(log_paths)
    summary = {
        "log_files": len(log_files),
        "events": 0,
        "gat_events": 0,
        "shadow_events": 0,
        "admission_events": 0,
        "finish_events": 0,
        "optimal_finish_events": 0,
        "global_certificate_pricing_events": 0,
        "certificate_candidate_gat_events": 0,
        "certificate_candidate_delayed_negative_events": 0,
        "candidate_journeys": 0,
        "true_negative_journeys": 0,
        "high_priority_journeys": 0,
        "delay_queue_journeys": 0,
        "reject_nonnegative_only_journeys": 0,
        "shadow_candidate_journeys": 0,
        "shadow_true_negative_journeys": 0,
        "shadow_high_priority_journeys": 0,
        "shadow_delay_queue_journeys": 0,
        "shadow_reject_nonnegative_only_journeys": 0,
        "admission_candidate_journeys": 0,
        "admission_true_negative_journeys": 0,
        "admission_high_priority_journeys": 0,
        "admission_delay_queue_journeys": 0,
        "admission_reject_nonnegative_only_journeys": 0,
        "admission_online_safe_hit_journeys": 0,
        "pricing_kinds": {},
        "violations": [],
    }
    pricing_kinds: Counter[str] = Counter()
    violations: list[dict[str, Any]] = []

    for path in log_files:
        for line_no, event in _iter_jsonl(path):
            summary["events"] += 1
            event_name = str(event.get("event") or "")
            if event_name == "finish":
                summary["finish_events"] += 1
                if str(event.get("status") or "") == "OPTIMAL":
                    summary["optimal_finish_events"] += 1
                if str(event.get("status") or "") != "OPTIMAL" and _has_official_dual_bound(event):
                    violations.append(
                        _violation(
                            path,
                            line_no,
                            "non_optimal_finish_has_official_dual_bound",
                            event,
                        )
                    )
                continue
            if event_name == "journey_pricing" and bool(event.get("global_certificate")):
                summary["global_certificate_pricing_events"] += 1
                continue
            if event_name not in GAT_EVENTS:
                continue
            summary["gat_events"] += 1
            if event_name == "journey_gat_target_mode_shadow":
                summary["shadow_events"] += 1
            if event_name == "journey_gat_target_mode_admission":
                summary["admission_events"] += 1
            pricing_kind = str(event.get("pricing_kind") or "unknown")
            pricing_kinds[pricing_kind] += 1
            for key in (
                "candidate_journeys",
                "true_negative_journeys",
                "high_priority_journeys",
                "delay_queue_journeys",
                "reject_nonnegative_only_journeys",
            ):
                value = int(event.get(key) or 0)
                summary[key] += value
                if event_name == "journey_gat_target_mode_shadow":
                    summary[f"shadow_{key}"] += value
                elif event_name == "journey_gat_target_mode_admission":
                    summary[f"admission_{key}"] += value
            if event_name == "journey_gat_target_mode_admission":
                summary["admission_online_safe_hit_journeys"] += int(
                    event.get("online_safe_hit_journeys") or 0
                )
            if bool(event.get("certificate_candidate")):
                summary["certificate_candidate_gat_events"] += 1
                if int(event.get("delayed_negative_journeys") or 0) > 0:
                    summary["certificate_candidate_delayed_negative_events"] += 1
            if bool(event.get("selector_can_certificate")):
                violations.append(_violation(path, line_no, "selector_can_certificate_true", event))
            if bool(event.get("selector_is_pricing_oracle")):
                violations.append(_violation(path, line_no, "selector_is_pricing_oracle_true", event))
            if bool(event.get("official_bound_effect")):
                violations.append(_violation(path, line_no, "official_bound_effect_true", event))
            if bool(event.get("hard_filter_enabled")):
                violations.append(_violation(path, line_no, "hard_filter_enabled_true", event))
            if _rejects_true_negative(event):
                violations.append(_violation(path, line_no, "true_rc_negative_rejected", event))

    summary["pricing_kinds"] = dict(sorted(pricing_kinds.items()))
    summary["violations"] = violations
    summary["violation_count"] = len(violations)
    summary["all_checks_pass"] = len(violations) == 0

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    if report is not None:
        report = Path(report)
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(_render_report(summary), encoding="utf-8")
    return summary


def _expand_log_files(paths: Iterable[Path]) -> list[Path]:
    files: list[Path] = []
    for raw_path in paths:
        path = Path(raw_path)
        if path.is_file():
            if path.suffix == ".jsonl":
                files.append(path)
            continue
        if path.is_dir():
            files.extend(sorted(path.rglob("*.jsonl")))
    return sorted(dict.fromkeys(files))


def _iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield line_no, json.loads(line)
            except json.JSONDecodeError as exc:
                yield line_no, {"event": "__invalid_json__", "error": str(exc)}


def _rejects_true_negative(event: dict[str, Any]) -> bool:
    for sample in event.get("decision_samples") or []:
        try:
            true_rc = float(sample.get("true_reduced_cost"))
        except (TypeError, ValueError):
            continue
        if true_rc < -1.0e-9 and str(sample.get("decision")) == "REJECT_NONNEGATIVE_ONLY":
            return True
    return False


def _has_official_dual_bound(event: dict[str, Any]) -> bool:
    dual = event.get("dual_bound")
    if dual is None:
        return False
    if isinstance(dual, str) and dual.strip().lower() in {"", "none", "nan"}:
        return False
    return True


def _violation(path: Path, line_no: int, reason: str, event: dict[str, Any]) -> dict[str, Any]:
    return {
        "file": str(path),
        "line": int(line_no),
        "reason": str(reason),
        "event": str(event.get("event") or ""),
        "pricing_kind": event.get("pricing_kind"),
        "candidate_journeys": event.get("candidate_journeys"),
        "true_negative_journeys": event.get("true_negative_journeys"),
    }


def _render_report(summary: dict[str, Any]) -> str:
    violations = summary.get("violations") or []
    violation_lines = "\n".join(
        f"- {item['reason']} at {item['file']}:{item['line']}"
        for item in violations[:20]
    )
    if not violation_lines:
        violation_lines = "- none"
    pricing_kinds = ", ".join(
        f"{key}:{value}" for key, value in (summary.get("pricing_kinds") or {}).items()
    ) or "none"
    return "\n".join(
        [
            "# 2026-06-15 BPC_future GAT Target Mode Certificate Audit 报告",
            "",
            "## 结论",
            "",
            f"all_checks_pass = {str(bool(summary.get('all_checks_pass'))).lower()}",
            f"violation_count = {int(summary.get('violation_count') or 0)}",
            "",
            "该审计只读 solver jsonl 日志，用来检查 GAT target-mode 事件是否越过 exact-safe 边界。",
            "",
            "## 统计",
            "",
            f"log_files = {int(summary.get('log_files') or 0)}",
            f"gat_events = {int(summary.get('gat_events') or 0)}",
            f"shadow_events = {int(summary.get('shadow_events') or 0)}",
            f"admission_events = {int(summary.get('admission_events') or 0)}",
            f"candidate_journeys = {int(summary.get('candidate_journeys') or 0)}",
            f"true_negative_journeys = {int(summary.get('true_negative_journeys') or 0)}",
            f"high_priority_journeys = {int(summary.get('high_priority_journeys') or 0)}",
            f"delay_queue_journeys = {int(summary.get('delay_queue_journeys') or 0)}",
            f"reject_nonnegative_only_journeys = {int(summary.get('reject_nonnegative_only_journeys') or 0)}",
            f"shadow_delay_queue_journeys = {int(summary.get('shadow_delay_queue_journeys') or 0)}",
            f"admission_delay_queue_journeys = {int(summary.get('admission_delay_queue_journeys') or 0)}",
            f"admission_online_safe_hit_journeys = {int(summary.get('admission_online_safe_hit_journeys') or 0)}",
            f"certificate_candidate_gat_events = {int(summary.get('certificate_candidate_gat_events') or 0)}",
            (
                "certificate_candidate_delayed_negative_events = "
                f"{int(summary.get('certificate_candidate_delayed_negative_events') or 0)}"
            ),
            f"global_certificate_pricing_events = {int(summary.get('global_certificate_pricing_events') or 0)}",
            f"pricing_kinds = {pricing_kinds}",
            "",
            "## 检查项",
            "",
            "- `selector_can_certificate` 必须为 false；",
            "- `selector_is_pricing_oracle` 必须为 false；",
            "- `official_bound_effect` 必须为 false；",
            "- `hard_filter_enabled` 必须为 false；",
            "- true-RC negative sample 不能被 `REJECT_NONNEGATIVE_ONLY`；",
            "- 非 OPTIMAL finish 不能带 official `dual_bound`。",
            "",
            "## Violations",
            "",
            violation_lines,
            "",
            "## Exactness Boundary",
            "",
            "GAT/CBF/kNN/OOD 只能做 ordering、priority 或 finite-delay scheduling。",
            "最终 certificate 仍必须来自当前 branch/cut/dual 下的 exact pricing full closure。",
            "",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
