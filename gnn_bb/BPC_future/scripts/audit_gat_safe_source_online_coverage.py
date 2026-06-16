#!/usr/bin/env python3
"""Audit offline GAT safe-source coverage against online shadow candidates.

This diagnostic explains why a Stage 3 safe-source did or did not hit Stage 4
online candidates. It is read-only: it does not run BPC, pricing, RMP, or
certificate logic, and it must not be used as an admission rule by itself.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import sys
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from BPC_future.solver.gat_candidate_id import journey_gat_candidate_id_from_signature


DEFAULT_SAFE_SOURCE = Path(
    "BPC_future/results/gat_batch_impact_safe_source_v10_random_wave_task50_5751_20260616/"
    "safe_source.json"
)
DEFAULT_DECISION_RECORDS = Path(
    "BPC_future/results/gat_batch_impact_knn_ood_audit_v10_mixed_random_wave_task50_5751_knn34_20260616/"
    "decision_records.jsonl"
)
DEFAULT_SHADOW_LOG_DIR = Path(
    "BPC_future/results/gat_target_mode_stage4_v10_safe_source_20_shadow_hit_probe_fullsamples_20260616/"
    "logs_sector_tranq20_01_shadow_fullsamples"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/gat_safe_source_online_coverage_v10_tranq20_01_20260616"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260616_bpc_future_gat_target_mode_stage4_v10_safe_source_online_coverage_audit_zh.md"
)

_KNOWN_INSTANCE_FAMILIES = ("sector-wave", "random-wave", "greedy-anchor", "balanced")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--safe-source", type=Path, default=DEFAULT_SAFE_SOURCE)
    parser.add_argument("--decision-records", type=Path, default=DEFAULT_DECISION_RECORDS)
    parser.add_argument("--shadow-log-dir", type=Path, default=DEFAULT_SHADOW_LOG_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = audit_safe_source_online_coverage(
        safe_source=args.safe_source,
        decision_records=args.decision_records,
        shadow_log_dir=args.shadow_log_dir,
        output_dir=args.output_dir,
        report=args.report,
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def audit_safe_source_online_coverage(
    *,
    safe_source: Path = DEFAULT_SAFE_SOURCE,
    decision_records: Path = DEFAULT_DECISION_RECORDS,
    shadow_log_dir: Path = DEFAULT_SHADOW_LOG_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
) -> dict[str, Any]:
    safe = _read_json(Path(safe_source))
    records = _read_jsonl(Path(decision_records))
    source_cache: dict[str, list[dict[str, Any]]] = {}

    offline_candidates = _offline_candidates(records, source_cache=source_cache)
    online_candidates, shadow_stats = _online_shadow_candidates(Path(shadow_log_dir))

    safe_ids = {str(item) for item in safe.get("safe_candidate_ids", []) if str(item)}
    offline_high = [candidate for candidate in offline_candidates if candidate["safe_source_high_priority"]]
    offline_high_ids = {str(candidate["signature_id"]) for candidate in offline_high}
    online_ids = {str(candidate["signature_id"]) for candidate in online_candidates}

    exact_safe_hits = safe_ids & online_ids
    exact_offline_high_hits = offline_high_ids & online_ids
    key_summaries = {
        "route_no_start": _key_overlap_summary(
            offline_candidates,
            online_candidates,
            key_field="route_no_start_key",
        ),
        "sequence": _key_overlap_summary(
            offline_candidates,
            online_candidates,
            key_field="sequence_key",
        ),
        "task_set": _key_overlap_summary(
            offline_candidates,
            online_candidates,
            key_field="task_set_key",
        ),
    }
    task_set_high_keys = {
        candidate["task_set_key"]
        for candidate in offline_high
        if candidate["task_set_key"]
    }
    task_set_online_hit_samples = [
        _online_candidate_report_sample(candidate)
        for candidate in online_candidates
        if candidate["task_set_key"] in task_set_high_keys
    ][:20]

    offline_hp_by_family_task = Counter(
        (str(candidate["instance_family"]), str(candidate["instance_task_count"]))
        for candidate in offline_high
    )
    online_by_pricing_kind = Counter(str(candidate.get("pricing_kind", "")) for candidate in online_candidates)

    coverage_gate_pass = bool(exact_safe_hits)
    summary = {
        "schema_version": "gat_safe_source_online_coverage_audit_v1",
        "status": "safe_source_online_coverage_audited",
        "safe_source": str(safe_source),
        "decision_records": str(decision_records),
        "shadow_log_dir": str(shadow_log_dir),
        "output_dir": str(output_dir),
        "safe_source_ready": bool(safe.get("safe_source_ready", False)),
        "safe_candidate_id_count": int(len(safe_ids)),
        "decision_record_count": int(len(records)),
        "offline_candidate_count": int(len(offline_candidates)),
        "offline_high_priority_candidate_count": int(len(offline_high)),
        "offline_high_priority_unique_signature_ids": int(len(offline_high_ids)),
        "offline_high_priority_unique_task_sets": int(
            len({candidate["task_set_key"] for candidate in offline_high if candidate["task_set_key"]})
        ),
        "offline_high_priority_by_family_task": {
            f"{family}:{task_count}": count
            for (family, task_count), count in sorted(offline_hp_by_family_task.items())
        },
        "online_shadow_events": int(shadow_stats["shadow_events"]),
        "online_declared_candidate_journeys": int(shadow_stats["declared_candidate_journeys"]),
        "online_sampled_candidate_journeys": int(len(online_candidates)),
        "online_sample_coverage_complete": bool(shadow_stats["sample_coverage_complete"]),
        "online_unique_signature_ids": int(len(online_ids)),
        "online_unique_task_sets": int(
            len({candidate["task_set_key"] for candidate in online_candidates if candidate["task_set_key"]})
        ),
        "online_by_pricing_kind": dict(sorted(online_by_pricing_kind.items())),
        "exact_safe_id_overlap_count": int(len(exact_safe_hits)),
        "exact_offline_high_id_overlap_count": int(len(exact_offline_high_hits)),
        "exact_safe_id_overlap_rate_online": _safe_divide(len(exact_safe_hits), len(online_ids)),
        "coverage_gate_pass": coverage_gate_pass,
        "route_no_start_overlap": key_summaries["route_no_start"],
        "sequence_overlap": key_summaries["sequence"],
        "task_set_overlap": key_summaries["task_set"],
        "exact_safe_hit_samples": sorted(exact_safe_hits)[:10],
        "online_task_set_samples": [
            list(candidate["task_set_key"])
            for candidate in sorted(online_candidates, key=lambda item: (item["task_set_key"], item["signature_id"]))[:20]
        ],
        "overlap_task_set_samples": [
            list(value)
            for value in key_summaries["task_set"]["overlap_key_samples"]
        ],
        "task_set_online_hit_samples": task_set_online_hit_samples,
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "default_enabled": False,
        "official_bound_effect": False,
        "selector_is_pricing_oracle": False,
        "selector_can_certificate": False,
        "gate_can_permanently_discard_negative_columns": False,
        "negative_columns_must_remain_eventually_reachable": True,
        "all_checks_pass": True,
    }
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(Path(report), summary)
    return summary


def _offline_candidates(
    records: list[dict[str, Any]],
    *,
    source_cache: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for record in records:
        signature_ids = [str(value) for value in record.get("candidate_signature_ids", [])]
        if not signature_ids:
            continue
        by_id = _candidate_payloads_by_id(record, source_cache=source_cache)
        high_priority_ids = {
            str(value) for value in record.get("high_priority_candidate_signature_ids", []) if str(value)
        }
        label_high_priority = bool(int(record.get("label_high_priority") or 0))
        safe_source_record = int(record.get("decision") or 0) == 1 or str(record.get("decision_name")) == "HIGH_PRIORITY"
        for signature_id in signature_ids:
            payload = by_id.get(signature_id, {})
            signature = payload.get("signature")
            task_set = _task_set(payload.get("task_set"))
            if not task_set:
                task_set = _task_set_from_signature(signature)
            candidates.append(
                {
                    "signature_id": signature_id,
                    "signature": signature,
                    "task_set_key": tuple(sorted(task_set)),
                    "sequence_key": _sequence_key(signature),
                    "route_no_start_key": _route_no_start_key(signature),
                    "label_high_priority": label_high_priority,
                    "safe_source_high_priority": bool(
                        safe_source_record and signature_id in high_priority_ids
                    ),
                    "decision_name": str(record.get("decision_name", "")),
                    "decision_reason": str(record.get("decision_reason", "")),
                    "instance_family": str(record.get("instance_family", "")),
                    "instance_task_count": str(record.get("instance_task_count", "")),
                    "context_hash": str(record.get("context_hash", "")),
                    "accepted_batch_roi_label": _float_or_none(record.get("accepted_batch_roi_label")),
                    "batch_score": _float_or_none(record.get("batch_score")),
                    "batch_threshold": _float_or_none(record.get("batch_threshold")),
                    "candidate_threshold": _float_or_none(record.get("candidate_threshold")),
                    "is_knn_unsafe": bool(record.get("is_knn_unsafe", False)),
                    "is_ood": bool(record.get("is_ood", False)),
                    "is_label_unsafe": bool(record.get("is_label_unsafe", False)),
                    "candidate_false_high_priority_on_delay_count": int(
                        record.get("candidate_false_high_priority_on_delay_count") or 0
                    ),
                }
            )
    return candidates


def _candidate_payloads_by_id(
    record: dict[str, Any],
    *,
    source_cache: dict[str, list[dict[str, Any]]],
) -> dict[str, dict[str, Any]]:
    explicit_task_sets = record.get("candidate_task_sets")
    signature_ids = [str(value) for value in record.get("candidate_signature_ids", [])]
    if isinstance(explicit_task_sets, list) and len(explicit_task_sets) == len(signature_ids):
        return {
            signature_id: {"task_set": task_set, "signature": None}
            for signature_id, task_set in zip(signature_ids, explicit_task_sets)
        }

    source_file = str(record.get("source_file") or "")
    context_hash = str(record.get("context_hash") or "")
    if not source_file or not context_hash:
        return {}
    events = source_cache.get(source_file)
    if events is None:
        path = Path(source_file)
        events = []
        if path.exists():
            events = [
                event
                for event in _read_jsonl(path)
                if event.get("event") == "journey_counterfactual_replay_capture"
            ]
        source_cache[source_file] = events
    matching = [event for event in events if str(event.get("context_hash") or "") == context_hash]
    if not matching:
        return {}
    wanted = set(signature_ids)
    best_event = max(
        matching,
        key=lambda event: len(_event_candidate_ids(event) & wanted),
    )
    by_id: dict[str, dict[str, Any]] = {}
    for journey in best_event.get("returned_journeys") or []:
        if not isinstance(journey, dict):
            continue
        signature_id = journey_gat_candidate_id_from_signature(journey.get("signature"))
        by_id[signature_id] = journey
    return by_id


def _event_candidate_ids(event: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for journey in event.get("returned_journeys") or []:
        if isinstance(journey, dict):
            ids.add(journey_gat_candidate_id_from_signature(journey.get("signature")))
    return ids


def _online_shadow_candidates(log_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    shadow_events = 0
    declared = 0
    complete = True
    for path in sorted(Path(log_dir).rglob("*.jsonl")):
        instance_family, instance_task_count = _infer_online_context_from_path(path)
        for event in _read_jsonl(path):
            if event.get("event") != "journey_gat_target_mode_shadow":
                continue
            if event.get("status") != "logged":
                continue
            shadow_events += 1
            event_candidate_count = int(event.get("candidate_journeys") or 0)
            declared += event_candidate_count
            samples = list(event.get("decision_samples") or [])
            if len(samples) != event_candidate_count:
                complete = False
            for sample in samples:
                signature = sample.get("signature")
                task_set = _task_set(sample.get("task_set"))
                if not task_set:
                    task_set = _task_set_from_signature(signature)
                candidates.append(
                    {
                        "signature_id": str(sample.get("candidate_id") or ""),
                        "signature": signature,
                        "task_set_key": tuple(sorted(task_set)),
                        "sequence_key": _sequence_key(signature),
                        "route_no_start_key": _route_no_start_key(signature),
                        "decision": str(sample.get("decision", "")),
                        "reason": str(sample.get("reason", "")),
                        "true_reduced_cost": sample.get("true_reduced_cost"),
                        "pricing_kind": str(event.get("pricing_kind", "")),
                        "cg_iter": int(event.get("cg_iter") or 0),
                        "instance_family": instance_family,
                        "instance_task_count": instance_task_count,
                        "log_path": str(path),
                    }
                )
    return candidates, {
        "shadow_events": shadow_events,
        "declared_candidate_journeys": declared,
        "sample_coverage_complete": bool(complete),
    }


def _key_overlap_summary(
    offline_candidates: list[dict[str, Any]],
    online_candidates: list[dict[str, Any]],
    *,
    key_field: str,
) -> dict[str, Any]:
    offline_high_keys = {
        candidate[key_field]
        for candidate in offline_candidates
        if candidate.get("safe_source_high_priority") and candidate.get(key_field)
    }
    offline_delay_keys = {
        candidate[key_field]
        for candidate in offline_candidates
        if not bool(candidate.get("label_high_priority")) and candidate.get(key_field)
    }
    online_keys = {
        candidate[key_field]
        for candidate in online_candidates
        if candidate.get(key_field)
    }
    overlap = offline_high_keys & online_keys
    conflict = offline_high_keys & offline_delay_keys
    online_hit_candidates = [
        candidate for candidate in online_candidates if candidate.get(key_field) in offline_high_keys
    ]
    online_conflict_candidates = [
        candidate for candidate in online_candidates if candidate.get(key_field) in conflict
    ]
    return {
        "offline_high_key_count": int(len(offline_high_keys)),
        "offline_delay_key_count": int(len(offline_delay_keys)),
        "offline_conflict_key_count": int(len(conflict)),
        "online_key_count": int(len(online_keys)),
        "overlap_key_count": int(len(overlap)),
        "online_candidate_hit_count": int(len(online_hit_candidates)),
        "online_candidate_hit_rate": _safe_divide(len(online_hit_candidates), len(online_candidates)),
        "online_conflict_candidate_hit_count": int(len(online_conflict_candidates)),
        "overlap_key_samples": sorted(overlap, key=repr)[:20],
        "conflict_key_samples": sorted(conflict, key=repr)[:20],
    }


def _infer_online_context_from_path(path: Path) -> tuple[str, str]:
    parts = list(path.parts)
    family = ""
    task_count = ""
    for idx, part in enumerate(parts):
        if part.startswith("tasks_"):
            suffix = part.split("tasks_", 1)[1]
            if suffix.isdigit():
                task_count = str(int(suffix))
            family = _infer_online_family_near_tasks(parts, idx)
            break
    if not family:
        family = _infer_family_from_text(" ".join(parts))
    return family, task_count


def _infer_online_family_near_tasks(parts: list[str], tasks_idx: int) -> str:
    if tasks_idx + 1 < len(parts):
        next_part = str(parts[tasks_idx + 1])
        if next_part in _KNOWN_INSTANCE_FAMILIES:
            return next_part
        family = _infer_family_from_text(next_part)
        if family:
            return family
    return _infer_family_from_text(parts[-1] if parts else "")


def _infer_family_from_text(text: str) -> str:
    lower = str(text).lower()
    for family in _KNOWN_INSTANCE_FAMILIES:
        if family in lower:
            return family
    return ""


def _task_set(value: Any) -> tuple[int, ...]:
    if value is None:
        return tuple()
    if isinstance(value, (list, tuple, set)):
        result: list[int] = []
        for item in value:
            try:
                result.append(int(item))
            except (TypeError, ValueError):
                continue
        return tuple(sorted(set(result)))
    return tuple()


def _online_candidate_report_sample(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "task_set": list(candidate.get("task_set_key") or ()),
        "candidate_id": str(candidate.get("signature_id") or ""),
        "pricing_kind": str(candidate.get("pricing_kind") or ""),
        "cg_iter": int(candidate.get("cg_iter") or 0),
        "decision": str(candidate.get("decision") or ""),
        "reason": str(candidate.get("reason") or ""),
        "true_reduced_cost": candidate.get("true_reduced_cost"),
    }


def _task_set_from_signature(signature: Any) -> tuple[int, ...]:
    tasks: set[int] = set()
    for sequence, _arcs, _start in _signature_trips(signature):
        tasks.update(sequence)
    return tuple(sorted(tasks))


def _sequence_key(signature: Any) -> tuple[tuple[int, ...], ...]:
    return tuple(sequence for sequence, _arcs, _start in _signature_trips(signature))


def _route_no_start_key(signature: Any) -> tuple[tuple[tuple[int, ...], tuple[str, ...]], ...]:
    return tuple((sequence, arcs) for sequence, arcs, _start in _signature_trips(signature))


def _signature_trips(signature: Any) -> tuple[tuple[tuple[int, ...], tuple[str, ...], float | None], ...]:
    trips: list[tuple[tuple[int, ...], tuple[str, ...], float | None]] = []
    if signature is None:
        return tuple()
    if not isinstance(signature, (list, tuple)):
        return tuple()
    for trip in signature:
        if not isinstance(trip, (list, tuple)) or len(trip) < 2:
            continue
        sequence = _int_tuple(trip[0])
        arcs = tuple(str(item) for item in (trip[1] if isinstance(trip[1], (list, tuple)) else []))
        start_time = None
        if len(trip) >= 3:
            try:
                start_time = float(trip[2])
            except (TypeError, ValueError):
                start_time = None
        if sequence:
            trips.append((sequence, arcs, start_time))
    return tuple(trips)


def _int_tuple(value: Any) -> tuple[int, ...]:
    if not isinstance(value, (list, tuple, set)):
        return tuple()
    result: list[int] = []
    for item in value:
        try:
            result.append(int(item))
        except (TypeError, ValueError):
            continue
    return tuple(result)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            try:
                record = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                records.append(record)
    return records


def _safe_divide(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return float(numerator) / float(denominator)


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    route = summary["route_no_start_overlap"]
    sequence = summary["sequence_overlap"]
    task_set = summary["task_set_overlap"]
    source_label = _safe_source_report_label(str(summary["safe_source"]))
    if task_set["offline_conflict_key_count"] > 0:
        coarse_key_note = (
            "而且 task-set / sequence 级放宽存在离线冲突，不能直接作为 HIGH_PRIORITY admission rule。"
        )
    else:
        coarse_key_note = (
            "task-set 级放宽虽然本次没有离线冲突，但 coverage 仍很低，不能直接作为 HIGH_PRIORITY admission rule。"
        )
    lines = [
        f"# 2026-06-16 BPC_future GAT Target Mode Stage 4 {source_label} Online Coverage Audit 报告",
        "",
        "## 结论",
        "",
        "本报告只读 Stage 3 safe-source、kNN/OOD decision records 和 Stage 4 online shadow 日志。",
        "它不运行 BPC / pricing / RMP，不改变 admission，也不产生 certificate。",
        "",
        "核心结论：",
        "",
        f"- exact safe id online overlap = {summary['exact_safe_id_overlap_count']};",
        f"- online sampled candidates = {summary['online_sampled_candidate_journeys']};",
        f"- online sample coverage complete = {str(summary['online_sample_coverage_complete']).lower()};",
        f"- task-set 层有 {task_set['overlap_key_count']} 个 key 重叠，覆盖 "
        f"{task_set['online_candidate_hit_count']} 个 online candidates；",
        f"- task-set 层 offline conflict key count = {task_set['offline_conflict_key_count']}。",
        "",
        f"因此 {source_label} 当前失败不是因为当前 online logs 完全没有相似列族，",
        "而是因为导出的是 exact signature id 白名单，跨 seed / context / timing 后在线命中为 0。",
        coarse_key_note,
        "",
        "## 输入",
        "",
        "```text",
        f"safe_source = {summary['safe_source']}",
        f"decision_records = {summary['decision_records']}",
        f"shadow_log_dir = {summary['shadow_log_dir']}",
        "```",
        "",
        "## Exact-id Coverage",
        "",
        "```text",
        f"safe_candidate_id_count = {summary['safe_candidate_id_count']}",
        f"offline_high_priority_unique_signature_ids = {summary['offline_high_priority_unique_signature_ids']}",
        f"online_unique_signature_ids = {summary['online_unique_signature_ids']}",
        f"exact_safe_id_overlap_count = {summary['exact_safe_id_overlap_count']}",
        f"exact_safe_id_overlap_rate_online = {summary['exact_safe_id_overlap_rate_online']}",
        f"coverage_gate_pass = {str(summary['coverage_gate_pass']).lower()}",
        "```",
        "",
        "## Coarse-key Coverage Diagnostic",
        "",
        "```text",
        f"route_no_start.overlap_key_count = {route['overlap_key_count']}",
        f"route_no_start.online_candidate_hit_count = {route['online_candidate_hit_count']}",
        f"route_no_start.offline_conflict_key_count = {route['offline_conflict_key_count']}",
        "",
        f"sequence.overlap_key_count = {sequence['overlap_key_count']}",
        f"sequence.online_candidate_hit_count = {sequence['online_candidate_hit_count']}",
        f"sequence.offline_conflict_key_count = {sequence['offline_conflict_key_count']}",
        "",
        f"task_set.overlap_key_count = {task_set['overlap_key_count']}",
        f"task_set.online_candidate_hit_count = {task_set['online_candidate_hit_count']}",
        f"task_set.offline_conflict_key_count = {task_set['offline_conflict_key_count']}",
        f"task_set.online_conflict_candidate_hit_count = {task_set['online_conflict_candidate_hit_count']}",
        "```",
        "",
        "重叠 task-set 样本：",
        "",
        "```text",
        *[str(sample) for sample in summary["overlap_task_set_samples"][:20]],
        "```",
        "",
        "命中 online candidate 样本：",
        "",
        "```text",
        *[
            json.dumps(sample, ensure_ascii=False, sort_keys=True)
            for sample in summary.get("task_set_online_hit_samples", [])[:20]
        ],
        "```",
        "",
        "## 判定",
        "",
        "```text",
        "stage4_exact_safe_id_coverage_gate = failed",
        "stage4_coarse_key_direct_admission_ready = false",
        "stage4_next_direction = train_or_audit_context_aware_online_safe_source",
        "```",
        "",
        "下一步应做 context-aware / model-scored online safe-source，而不是把 exact id 改成",
        "task-set 白名单直接上线。更宽的 key 只能作为 pricing priority / candidate mining hint，",
        "进入 admission 前仍必须 true-RC verified，并且必须通过 precision / ROI / conflict gate。",
        "",
        "## Exactness Boundary",
        "",
        "```text",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"selector_is_pricing_oracle = {str(summary['selector_is_pricing_oracle']).lower()}",
        f"selector_can_certificate = {str(summary['selector_can_certificate']).lower()}",
        f"official_bound_effect = {str(summary['official_bound_effect']).lower()}",
        f"gate_can_permanently_discard_negative_columns = {str(summary['gate_can_permanently_discard_negative_columns']).lower()}",
        "```",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _safe_source_report_label(safe_source: str) -> str:
    parent = Path(safe_source).parent.name or "safe-source"
    if "v12" in parent and "scale" in parent:
        return "v12 scale safe-source"
    if "v10" in parent:
        return "v10 safe-source"
    return parent


if __name__ == "__main__":
    raise SystemExit(main())
