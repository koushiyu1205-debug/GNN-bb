#!/usr/bin/env python3
"""Audit whether target-priority candidates are reachable by worker logs.

The audit is read-only.  It consumes GAT target-priority runbook summaries and
existing solver JSONL logs, then classifies whether a candidate has an observed
same-context worker intervention.  It never runs BPC, pricing, RMP, workers, or
certificates.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_RUNBOOK_SUMMARIES = (
    Path("BPC_future/results/gat_target_priority_worker_ab_20260614/summary.json"),
    Path("BPC_future/results/gat_target_priority_worker_ab_family_20260614/summary.json"),
)
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/gat_target_intervention_reachability_20260614")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_gat_target_intervention_reachability_zh.md"
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8")) if Path(path).exists() else {}


def _sequence_tuple(value: Any) -> tuple[int, ...]:
    if not isinstance(value, list):
        return tuple()
    try:
        return tuple(int(item) for item in value)
    except (TypeError, ValueError):
        return tuple()


def _sequence_sample_matches_target(samples: Any, target: tuple[int, ...]) -> bool:
    if not target or not isinstance(samples, list):
        return False
    for sample in samples:
        if isinstance(sample, list) and sample and all(isinstance(item, list) for item in sample):
            flattened: list[int] = []
            valid = True
            for sortie in sample:
                for task in sortie:
                    try:
                        flattened.append(int(task))
                    except (TypeError, ValueError):
                        valid = False
                        break
                if not valid:
                    break
            if valid and tuple(flattened) == target:
                return True
        elif _sequence_tuple(sample) == target:
            return True
    return False


def _target_causal_match(event: dict[str, Any], target_sequence: list[Any]) -> bool:
    target = _sequence_tuple(target_sequence)
    if not target:
        return False
    configured_match = any(
        _sequence_tuple(event.get(key)) == target
        for key in (
            "pulse_worker_target_first_task_priority_sequence",
            "pulse_worker_target_transition_priority_sequence",
            "pulse_worker_target_sequence",
        )
    )
    if configured_match and bool(event.get("pulse_worker_target_sequence_materialized")):
        return True
    return bool(
        _sequence_sample_matches_target(
            event.get("pulse_worker_returned_candidate_sequence_samples"),
            target,
        )
        or _sequence_sample_matches_target(
            event.get("pulse_worker_harvested_sequence_samples"),
            target,
        )
    )


def _worker_log_files(worker_csv: Any) -> list[Path]:
    worker_csv_text = str(worker_csv or "").strip()
    if not worker_csv_text:
        return []
    log_dir = Path(worker_csv_text).parent / "logs"
    if not log_dir.exists():
        return []
    return sorted(log_dir.glob("**/*.jsonl"))


def _worker_events(worker_csv: Any) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for path in _worker_log_files(worker_csv):
        with path.open(encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                text = line.strip()
                if not text or "journey_sharded_pulse_hidden_negative_worker" not in text:
                    continue
                try:
                    event = json.loads(text)
                except json.JSONDecodeError:
                    continue
                if event.get("event") == "journey_sharded_pulse_hidden_negative_worker":
                    events.append(event)
    return events


def _command_for_candidate(commands: Iterable[dict[str, Any]], candidate_name: str) -> str:
    command_types = {
        f"task020_{candidate_name}_target_priority_worker",
        f"task020_{candidate_name}_worker_roi_gat_priority",
    }
    for item in commands:
        if item.get("command_type") in command_types:
            return str(item.get("command") or "")
    return ""


def _stage_compatible(candidate: dict[str, Any], command: str) -> bool:
    capture_kind = str(candidate.get("capture_pricing_kind") or "").strip().lower()
    if capture_kind == "exact":
        return (
            "journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False" in command
            and "journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True" in command
        )
    if capture_kind == "heuristic":
        return (
            "journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=True" in command
            and "journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True" not in command
        )
    return False


def _classify_candidate(candidate: dict[str, Any], commands: Iterable[dict[str, Any]]) -> dict[str, Any]:
    expected_context = str(candidate.get("expected_context_hash") or "").strip()
    command = _command_for_candidate(commands, str(candidate.get("name") or ""))
    events = _worker_events(candidate.get("worker_csv"))
    context_events = [
        event
        for event in events
        if str(event.get("pulse_worker_context_hash") or "").strip() == expected_context
    ]
    executed_context_events = [
        event for event in context_events if not bool(event.get("pulse_worker_skipped", False))
    ]
    target_matches = [
        event
        for event in executed_context_events
        if _target_causal_match(event, list(candidate.get("target_sequence") or []))
    ]
    stage_compatible = _stage_compatible(candidate, command)
    learning_kept = "journey_learning_enabled=False" not in command
    no_certificate_effect = not any(
        token in command
        for token in (
            "journey_final_judge_sharding_enabled=True",
            "journey_pulse_final_judge_enabled=True",
            "journey_sharded_pulse_audit_allow_certificate_effect=True",
            "allow_test_dummy_certificate=True",
            "dummy_certificate=True",
            "official_bound_effect=True",
        )
    )
    if not stage_compatible:
        reachability = "worker_stage_mismatch"
    elif not learning_kept:
        reachability = "capture_learning_policy_mismatch"
    elif not _worker_log_files(candidate.get("worker_csv")):
        reachability = "missing_worker_log"
    elif not events:
        reachability = "worker_hook_not_triggered"
    elif not context_events:
        reachability = "worker_context_not_reached"
    elif not executed_context_events:
        reachability = "worker_skipped_at_expected_context"
    elif not target_matches:
        reachability = "worker_executed_without_target_causal_match"
    else:
        reachability = "target_intervention_reachable"
    first_context_event = context_events[0] if context_events else {}
    first_executed_event = executed_context_events[0] if executed_context_events else {}
    return {
        "schema_version": "gat_target_intervention_reachability_record_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "name": str(candidate.get("name") or ""),
        "instance": str(candidate.get("instance") or ""),
        "expected_context_hash": expected_context,
        "capture_pricing_kind": str(candidate.get("capture_pricing_kind") or ""),
        "target_sequence": list(candidate.get("target_sequence") or []),
        "target_arc_option_sequence": list(candidate.get("target_arc_option_sequence") or []),
        "worker_csv": str(candidate.get("worker_csv") or ""),
        "worker_log_count": len(_worker_log_files(candidate.get("worker_csv"))),
        "worker_event_count": len(events),
        "expected_context_worker_event_count": len(context_events),
        "expected_context_executed_event_count": len(executed_context_events),
        "target_causal_match_count": len(target_matches),
        "stage_compatible": bool(stage_compatible),
        "learning_policy_kept": bool(learning_kept),
        "no_certificate_effect": bool(no_certificate_effect),
        "reachability_class": reachability,
        "training_label_allowed": reachability == "target_intervention_reachable",
        "first_expected_context_skip_reason": str(
            first_context_event.get("pulse_worker_skip_reason") or ""
        ),
        "first_executed_status": str(first_executed_event.get("pulse_worker_status") or ""),
        "first_executed_returned_journeys": int(
            first_executed_event.get("pulse_worker_returned_journeys") or 0
        ),
        "first_executed_best_rc": first_executed_event.get("pulse_worker_best_rc"),
    }


def audit_reachability(
    *,
    runbook_summaries: Iterable[Path] = DEFAULT_RUNBOOK_SUMMARIES,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    loaded_summaries: list[str] = []
    records: list[dict[str, Any]] = []
    for summary_path in runbook_summaries:
        path = Path(summary_path)
        if not path.exists():
            continue
        summary = _read_json(path)
        loaded_summaries.append(str(path))
        if summary.get("certificate_ready") or summary.get("official_bound_effect"):
            raise ValueError(f"runbook summary has forbidden certificate effect: {path}")
        commands = list(summary.get("commands") or [])
        for candidate in summary.get("candidate_runs") or []:
            if isinstance(candidate, dict):
                records.append(_classify_candidate(candidate, commands))

    reachability_counts: dict[str, int] = {}
    for record in records:
        key = str(record["reachability_class"])
        reachability_counts[key] = reachability_counts.get(key, 0) + 1
    reachable_count = int(reachability_counts.get("target_intervention_reachable", 0))
    if reachable_count > 0:
        next_decision = "collect_reachable_target_roi_labels"
    elif reachability_counts.get("worker_executed_without_target_causal_match", 0) > 0:
        next_decision = "improve_target_reachability_or_budget_before_labeling"
    elif reachability_counts.get("worker_hook_not_triggered", 0) > 0:
        next_decision = "build_same_stage_target_worker_hook"
    elif reachability_counts.get("worker_context_not_reached", 0) > 0:
        next_decision = "recapture_same_context_candidates"
    else:
        next_decision = "collect_more_worker_logs"
    checks = {
        "diagnostic_only": True,
        "runs_bpc_or_pricing_false": True,
        "no_certificate_effect": all(record["no_certificate_effect"] for record in records),
        "no_official_bound_effect": all(not record["official_bound_effect"] for record in records),
        "has_records": bool(records),
        "invalid_samples_not_training_labels": all(
            bool(record["training_label_allowed"])
            == (record["reachability_class"] == "target_intervention_reachable")
            for record in records
        ),
    }
    summary = {
        "schema_version": "gat_target_intervention_reachability_summary_v1",
        "status": "audited" if records else "no_records",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "runbook_summaries": loaded_summaries,
        "record_count": len(records),
        "reachable_target_intervention_count": reachable_count,
        "reachability_class_counts": dict(sorted(reachability_counts.items())),
        "records": records,
        "production_ready": False,
        "default_enabled": False,
        "certificate_ready": False,
        "official_bound_effect": False,
        "training_ready": False,
        "checks": checks,
        "all_checks_pass": all(bool(value) for value in checks.values()),
        "next_decision": next_decision,
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "records.jsonl").write_text(
        "\n".join(json.dumps(record, ensure_ascii=False, sort_keys=True) for record in records)
        + ("\n" if records else ""),
        encoding="utf-8",
    )
    _write_report(Path(report), summary)
    return summary


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GAT Target Intervention Reachability Audit 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告只读 target-priority runbook 和已有 JSONL 日志，判断候选是否真的",
        "进入了同上下文 worker target intervention。它不运行 BPC / pricing / RMP / worker，",
        "不产生 certificate 或 official lower bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "gat_target_intervention_reachability = current",
        f"status = {summary['status']}",
        f"record_count = {summary['record_count']}",
        "reachable_target_intervention_count = "
        f"{summary['reachable_target_intervention_count']}",
        f"reachability_class_counts = {summary['reachability_class_counts']}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"default_enabled = {str(summary['default_enabled']).lower()}",
        f"certificate_ready = {str(summary['certificate_ready']).lower()}",
        f"official_bound_effect = {str(summary['official_bound_effect']).lower()}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 解释",
        "",
        "- `target_intervention_reachable` 才允许进入 ROI label 构建；",
        "- `worker_context_not_reached` 表示 dual/cuts/branch/forbidden context 没复现；",
        "- `worker_hook_not_triggered` 表示日志里没有 worker 事件；",
        "- `worker_stage_mismatch` / `capture_learning_policy_mismatch` 是 runbook 配置错误；",
        "- 其他状态必须进 invalid bucket，不能当 GAT 正负标签。",
        "",
        "## Records",
        "",
        "```json",
        json.dumps(summary["records"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## 下一步",
        "",
        str(summary["next_decision"]),
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runbook-summary", type=Path, action="append", default=[])
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    summaries = args.runbook_summary or list(DEFAULT_RUNBOOK_SUMMARIES)
    summary = audit_reachability(
        runbook_summaries=summaries,
        output_dir=args.output_dir,
        report=args.report,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
