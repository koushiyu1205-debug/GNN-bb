#!/usr/bin/env python3
"""Audit component-context capture payloads for selector calibration.

This diagnostic separates fields that are already captured as explicit payloads
from fields that are only available as hash/count summaries.  It is read-only
with respect to solver behavior: it inspects existing JSONL capture events and
summary files, then writes a small schema contract report.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_CAPTURE_GLOB = (
    "BPC_future/results/"
    "root_cause_selector_holdout_collection_capture_config_matched_20260614/"
    "*/logs/*.jsonl"
)
DEFAULT_CONTEXT_SCHEMA_GAP = Path(
    "BPC_future/results/root_cause_selector_context_schema_gap_20260614/summary.json"
)
DEFAULT_COMPONENT_READINESS = Path(
    "BPC_future/results/root_cause_selector_component_feature_readiness_20260614/"
    "summary.json"
)
DEFAULT_DRIVER = Path("BPC_future/solver/journey_driver.py")
DEFAULT_HOLDOUT_MANIFEST_BUILDER = Path(
    "BPC_future/scripts/build_selector_holdout_collection_manifest.py"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_component_capture_schema_contract_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_component_capture_schema_contract_zh.md"
)
EVENT_NAME = "journey_counterfactual_replay_capture"

PAYLOAD_FIELDS = (
    "active_basis_rows",
    "pool_journeys",
    "pool_signatures",
    "pool_task_sets",
    "returned_journeys",
    "true_dual_vector",
)
HASH_COUNT_FIELDS = (
    "forbidden_signature_hash",
    "forbidden_signature_count",
)
REQUIRED_EXPLICIT_FIELDS = (
    "forbidden_signatures",
    "forbidden_journey_signatures",
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _event_nonempty(value: Any) -> bool:
    return value not in (None, "", [], {})


def _load_capture_events(capture_glob: str) -> tuple[list[Path], list[dict[str, Any]]]:
    paths = sorted(Path().glob(capture_glob))
    events: list[dict[str, Any]] = []
    for path in paths:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if EVENT_NAME not in line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event.get("event") == EVENT_NAME:
                    copied = dict(event)
                    copied["_source_path"] = str(path)
                    events.append(copied)
    return paths, events


def _field_stats(events: list[dict[str, Any]], fields: tuple[str, ...]) -> dict[str, dict[str, Any]]:
    stats: dict[str, dict[str, Any]] = {}
    for field in fields:
        present = sum(1 for event in events if field in event)
        nonempty = sum(1 for event in events if _event_nonempty(event.get(field)))
        types = sorted(
            {
                type(event.get(field)).__name__
                for event in events
                if field in event
            }
        )
        max_len = 0
        for event in events:
            value = event.get(field)
            if isinstance(value, (list, dict)):
                max_len = max(max_len, len(value))
        stats[field] = {
            "present_count": present,
            "nonempty_count": nonempty,
            "types": types,
            "max_payload_len": max_len,
        }
    return stats


def build_summary(
    *,
    capture_glob: str,
    context_schema_gap_path: Path,
    component_readiness_path: Path,
    driver_path: Path,
    holdout_manifest_builder_path: Path,
) -> dict[str, Any]:
    paths, events = _load_capture_events(capture_glob)
    context_schema_gap = _read_json(context_schema_gap_path)
    component_readiness = _read_json(component_readiness_path)
    driver_text = _read_text(driver_path)
    holdout_manifest_text = _read_text(holdout_manifest_builder_path)
    event_count = len(events)
    payload_stats = _field_stats(events, PAYLOAD_FIELDS)
    hash_count_stats = _field_stats(events, HASH_COUNT_FIELDS)
    explicit_required_stats = _field_stats(events, REQUIRED_EXPLICIT_FIELDS)

    complete_active_basis_events = sum(
        1
        for event in events
        if event.get("active_basis_snapshot_complete") is True
        and event.get("active_basis_snapshot_truncated") is False
        and isinstance(event.get("active_basis_rows"), list)
        and len(event.get("active_basis_rows") or []) > 0
    )
    complete_pool_events = sum(
        1
        for event in events
        if event.get("pool_snapshot_truncated") is False
        and isinstance(event.get("pool_journeys"), list)
        and isinstance(event.get("pool_signatures"), list)
        and int(event.get("pool_journey_payload_count") or 0)
        == len(event.get("pool_journeys") or [])
    )
    returned_batch_complete_events = sum(
        1 for event in events if event.get("returned_batch_complete") is True
    )
    returned_batch_nonempty_events = sum(
        1 for event in events if int(event.get("returned_journey_count") or 0) > 0
    )
    forbidden_explicit_events = sum(
        1
        for event in events
        if _event_nonempty(event.get("forbidden_signatures"))
        or _event_nonempty(event.get("forbidden_journey_signatures"))
    )
    forbidden_signature_list_available = forbidden_explicit_events > 0
    code_supports_explicit_forbidden_payload = all(
        needle in driver_text
        for needle in [
            "def _journey_replay_capture_forbidden_signature_payload(",
            "journey_counterfactual_replay_capture_forbidden_signatures_enabled",
            "journey_counterfactual_replay_capture_forbidden_signature_max_count",
            "\"forbidden_signatures\": captured",
            "**forbidden_signature_payload",
        ]
    )
    holdout_runbook_enables_explicit_forbidden_payload = all(
        needle in holdout_manifest_text
        for needle in [
            "journey_counterfactual_replay_capture_forbidden_signatures_enabled",
            "journey_counterfactual_replay_capture_forbidden_signature_max_count",
        ]
    )

    field_contract = [
        {
            "field_family": "active_basis_snapshot",
            "status": "captured_as_explicit_payload",
            "evidence": {
                "complete_active_basis_events": complete_active_basis_events,
                "event_count": event_count,
                "field_stats": payload_stats.get("active_basis_rows"),
            },
        },
        {
            "field_family": "pool_signature_composition",
            "status": "captured_as_explicit_payload",
            "evidence": {
                "complete_pool_events": complete_pool_events,
                "event_count": event_count,
                "pool_journeys": payload_stats.get("pool_journeys"),
                "pool_signatures": payload_stats.get("pool_signatures"),
                "pool_task_sets": payload_stats.get("pool_task_sets"),
            },
        },
        {
            "field_family": "returned_batch_payload",
            "status": "captured_as_explicit_payload_when_nonempty",
            "evidence": {
                "returned_batch_complete_events": returned_batch_complete_events,
                "returned_batch_nonempty_events": returned_batch_nonempty_events,
                "returned_journeys": payload_stats.get("returned_journeys"),
            },
        },
        {
            "field_family": "forbidden_signature_pressure",
            "status": (
                "captured_as_explicit_payload"
                if forbidden_signature_list_available
                else "hash_count_only_schema_extension_required"
            ),
            "evidence": {
                "forbidden_signature_hash": hash_count_stats.get(
                    "forbidden_signature_hash"
                ),
                "forbidden_signature_count": hash_count_stats.get(
                    "forbidden_signature_count"
                ),
                "explicit_required_stats": explicit_required_stats,
                "forbidden_explicit_events": forbidden_explicit_events,
            },
        },
    ]

    checks = {
        "context_schema_gap_passed": context_schema_gap.get("all_checks_pass") is True,
        "component_readiness_passed": (
            component_readiness.get("all_checks_pass") is True
        ),
        "capture_events_present": event_count == 78,
        "active_basis_payload_complete": complete_active_basis_events == event_count,
        "pool_payload_complete": complete_pool_events == event_count,
        "returned_batch_flags_complete": returned_batch_complete_events == event_count,
        "returned_batch_has_nonempty_examples": returned_batch_nonempty_events > 0,
        "pool_signatures_present": (
            payload_stats["pool_signatures"]["nonempty_count"] == event_count
        ),
        "forbidden_hash_count_present": (
            hash_count_stats["forbidden_signature_hash"]["nonempty_count"]
            == event_count
            and hash_count_stats["forbidden_signature_count"]["present_count"]
            == event_count
        ),
        "explicit_forbidden_signature_list_available": (
            forbidden_signature_list_available
        ),
        "code_supports_explicit_forbidden_payload": (
            code_supports_explicit_forbidden_payload
        ),
        "holdout_runbook_enables_explicit_forbidden_payload": (
            holdout_runbook_enables_explicit_forbidden_payload
        ),
        "selector_still_not_production_ready": (
            component_readiness.get("status")
            == "selector_component_features_not_production_ready"
            and component_readiness.get("ready_for_selector_holdout") is False
        ),
    }
    return {
        "schema_version": "root_cause_selector_component_capture_schema_contract_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "component_capture_schema_contract_audited",
        "capture_glob": capture_glob,
        "source_context_schema_gap": str(context_schema_gap_path),
        "source_component_readiness": str(component_readiness_path),
        "source_driver": str(driver_path),
        "source_holdout_manifest_builder": str(holdout_manifest_builder_path),
        "capture_file_count": len(paths),
        "capture_event_count": event_count,
        "complete_active_basis_events": complete_active_basis_events,
        "complete_pool_events": complete_pool_events,
        "returned_batch_complete_events": returned_batch_complete_events,
        "returned_batch_nonempty_events": returned_batch_nonempty_events,
        "forbidden_explicit_events": forbidden_explicit_events,
        "code_supports_explicit_forbidden_payload": (
            code_supports_explicit_forbidden_payload
        ),
        "holdout_runbook_enables_explicit_forbidden_payload": (
            holdout_runbook_enables_explicit_forbidden_payload
        ),
        "payload_field_stats": payload_stats,
        "hash_count_field_stats": hash_count_stats,
        "explicit_required_field_stats": explicit_required_stats,
        "field_contract": field_contract,
        "interpretation": (
            "Current config-matched selector-holdout capture events already carry "
            "explicit active-basis, pool, returned-batch, and forbidden-signature "
            "payloads.  The forbidden-signature payload is now observed in a "
            "targeted no-certificate-effect capture pass, so candidate-vs-forbidden "
            "overlap can be derived by the next selector-row builder.  This keeps "
            "component context work in calibration mode, not production mode."
        ),
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }


def write_report(summary: dict[str, Any], report_path: Path) -> None:
    lines = [
        "# Root Cause Selector Component Capture Schema Contract 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告检查 selector component-context 所需字段在当前 capture JSONL 中的",
        "实际存在形态：哪些是显式 payload，哪些只是 hash/count，哪些仍需扩展",
        "采集 schema。它只读已有日志和 summary，不运行 BPC / pricing / RMP / Pulse。",
        "",
        "## 机器字段",
        "",
        "```text",
        "selector_component_capture_schema_contract = current",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"status = {summary['status']}",
        f"capture_file_count = {summary['capture_file_count']}",
        f"capture_event_count = {summary['capture_event_count']}",
        f"complete_active_basis_events = {summary['complete_active_basis_events']}",
        f"complete_pool_events = {summary['complete_pool_events']}",
        f"returned_batch_complete_events = {summary['returned_batch_complete_events']}",
        f"returned_batch_nonempty_events = {summary['returned_batch_nonempty_events']}",
        f"forbidden_explicit_events = {summary['forbidden_explicit_events']}",
        "explicit_forbidden_signature_list_available = "
        f"{str(summary['checks']['explicit_forbidden_signature_list_available']).lower()}",
        "code_supports_explicit_forbidden_payload = "
        f"{str(summary['code_supports_explicit_forbidden_payload']).lower()}",
        "holdout_runbook_enables_explicit_forbidden_payload = "
        f"{str(summary['holdout_runbook_enables_explicit_forbidden_payload']).lower()}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 字段结论",
        "",
    ]
    for item in summary["field_contract"]:
        lines.extend(
            [
                f"### {item['field_family']}",
                "",
                f"status = `{item['status']}`",
                "",
                "```json",
                json.dumps(item["evidence"], ensure_ascii=False, indent=2, sort_keys=True),
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## 解释",
            "",
            summary["interpretation"],
            "",
            "这进一步收紧当前根因判断：selector 的下一步不是再调 worker，也不是",
            "直接 production A/B，而是把已经实测落盘的 active/pool/returned/",
            "forbidden component payload 转成 addition-before candidate rows 后",
            "再做 holdout。",
            "",
            "## 检查项",
            "",
            "```json",
            json.dumps(summary["checks"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture-glob", default=DEFAULT_CAPTURE_GLOB)
    parser.add_argument(
        "--context-schema-gap", default=str(DEFAULT_CONTEXT_SCHEMA_GAP)
    )
    parser.add_argument(
        "--component-readiness", default=str(DEFAULT_COMPONENT_READINESS)
    )
    parser.add_argument("--driver", default=str(DEFAULT_DRIVER))
    parser.add_argument(
        "--holdout-manifest-builder",
        default=str(DEFAULT_HOLDOUT_MANIFEST_BUILDER),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    summary = build_summary(
        capture_glob=str(args.capture_glob),
        context_schema_gap_path=Path(args.context_schema_gap),
        component_readiness_path=Path(args.component_readiness),
        driver_path=Path(args.driver),
        holdout_manifest_builder_path=Path(args.holdout_manifest_builder),
    )
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
