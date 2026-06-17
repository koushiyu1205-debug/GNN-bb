#!/usr/bin/env python3
"""Build same-context multi-batch intervention targets for GAT ROI training.

This script bridges the current batch-impact artifacts to the next data
collection step required by Stage 3.  It is read-only: it consumes the existing
dataset manifest, opportunity audit rows, and capture JSONL logs, then emits a
candidate file that can be passed to the guarded target-priority worker A/B
runbook.  It never runs BPC, pricing, RMP, workers, or certificates.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import json
from pathlib import Path
from typing import Any, Iterable

from BPC_future.scripts.build_gat_same_run_target_priority_candidates import (
    DEFAULT_SUPPORT_CHANGE_JACCARD_THRESHOLD,
    REQUIRED_CAPTURE_CONTEXT_FIELDS,
    _active_replacement_rank,
    _candidate_impact_features,
    _capture_events_by_context,
    _first_sortie_target,
    _flatten_trace_sequence,
    _impact_bucket_rank,
    _instance_metadata,
    _journey_sortie_traces,
    _safe_name,
    _true_reduced_cost,
)


DEFAULT_DATASET_DIR = Path("BPC_future/data/gat_batch_impact/v3_signature_20260616")
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/"
    "gat_batch_impact_multibatch_intervention_plan_v3_signature_hard_roi_20260616"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260616_bpc_future_gat_target_mode_stage3_multibatch_intervention_plan_zh.md"
)
DEFAULT_OPPORTUNITY_JSONL = (
    Path(
        "BPC_future/results/"
        "gat_batch_impact_opportunity_mining_v3_signature_hard_roi_20260616/"
        "top_missed_high_roi_opportunities.jsonl"
    ),
    Path(
        "BPC_future/results/"
        "gat_batch_impact_opportunity_mining_v3_signature_hard_roi_20260616/"
        "validation_opportunities.jsonl"
    ),
)
SUPPORTED_SELECTION_RANKINGS = ("best_rc", "impact", "active_replacement", "diverse")
CONTEXT_PRIORITY_FIELDS = (
    "context_priority_score",
    "context_priority_action",
    "context_priority_primary_blocker",
    "context_priority_negative_neighbor_count",
    "context_priority_deep_gap_count",
    "context_false_delay_false_high_priority_on_delay_count",
    "context_false_delay_candidate_signature_count",
    "context_false_delay_batch_record_count",
    "context_false_delay_accepted_batch_count",
    "context_false_delay_max_delay_risk_score",
    "context_false_delay_median_delay_risk_score",
    "context_false_delay_median_raw_high_priority_score",
    "context_repair_candidate_count",
    "context_repair_delayed_high_roi_count",
    "context_repair_accepted_high_point_roi_unstable_count",
    "context_repair_max_roi",
    "context_repair_median_roi",
    "context_repair_source_variants",
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            text = line.strip()
            if text:
                rows.append(json.loads(text))
    return rows


def _float_value(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _int_value(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _context_catalog(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    catalog: dict[str, dict[str, Any]] = {}
    for sample in manifest.get("samples") or []:
        if not isinstance(sample, dict):
            continue
        context_hash = str(sample.get("context_hash") or "")
        source_file = str(sample.get("source_file") or "")
        if not context_hash or not source_file:
            continue
        catalog.setdefault(context_hash, dict(sample))
    return catalog


def _opportunity_rows(paths: Iterable[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        item_path = Path(path)
        if not item_path.exists():
            continue
        rows.extend(_read_jsonl(item_path))
    return rows


def _context_priority_rows(paths: Iterable[Path] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths or []:
        item_path = Path(path)
        if not item_path.exists():
            continue
        rows.extend(_read_jsonl(item_path))
    return rows


def _priority_row_as_opportunity(row: dict[str, Any]) -> dict[str, Any]:
    item = dict(row)
    max_roi = _float_value(
        item.get("max_missed_roi"),
        _float_value(
            item.get("max_accepted_batch_roi_label"),
            _float_value(item.get("mean_missed_roi"), _float_value(item.get("mean_accepted_batch_roi_label"))),
        ),
    )
    repair_count = _int_value(item.get("repair_candidate_count"))
    delayed_high_roi_count = _int_value(item.get("delayed_high_roi_count"))
    accepted_unstable_count = _int_value(item.get("accepted_high_point_roi_unstable_count"))
    missed_count = _int_value(
        item.get("missed_high_roi_count_proxy"),
        max(1, delayed_high_roi_count + accepted_unstable_count, repair_count),
    )
    item.setdefault("accepted_batch_roi_label", max_roi)
    item.setdefault("candidate_count", missed_count)
    item.setdefault("is_high_roi_opportunity", True)
    if item.get("schema_version") == "gat_batch_impact_neighbor_roi_context_repair_v1":
        item.setdefault("is_missed_high_roi_opportunity", bool(delayed_high_roi_count))
    else:
        item.setdefault("is_missed_high_roi_opportunity", True)
    item.setdefault("task_count", item.get("instance_task_count"))
    item.setdefault("family", item.get("instance_family"))
    item.setdefault("instance_path", item.get("instance"))
    item["context_priority_score"] = _float_value(item.get("priority_score"))
    item["context_priority_action"] = str(item.get("primary_action") or "")
    item["context_priority_primary_blocker"] = str(item.get("primary_blocker") or "")
    item["context_priority_negative_neighbor_count"] = _int_value(
        item.get("nearest_negative_closer_count")
    )
    item["context_priority_deep_gap_count"] = _int_value(item.get("deep_candidate_gap_count"))
    item["context_repair_candidate_count"] = repair_count
    item["context_repair_delayed_high_roi_count"] = delayed_high_roi_count
    item["context_repair_accepted_high_point_roi_unstable_count"] = accepted_unstable_count
    item["context_repair_max_roi"] = _float_value(item.get("max_accepted_batch_roi_label"), max_roi)
    item["context_repair_median_roi"] = _float_value(
        item.get("median_accepted_batch_roi_label"), max_roi
    )
    item["context_repair_source_variants"] = list(item.get("source_variants") or [])
    return item


def _merge_context_priorities(
    opportunity_rows: list[dict[str, Any]],
    priority_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not priority_rows:
        return list(opportunity_rows)
    merged = _opportunity_by_context(opportunity_rows)
    for priority in priority_rows:
        context_hash = str(priority.get("context_hash") or "")
        if not context_hash:
            continue
        priority_opportunity = _priority_row_as_opportunity(priority)
        current = merged.get(context_hash, {})
        merged[context_hash] = {**current, **priority_opportunity}
    return list(merged.values())


def _opportunity_by_context(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    best: dict[str, dict[str, Any]] = {}
    for row in rows:
        context_hash = str(row.get("context_hash") or "")
        if not context_hash:
            continue
        current = best.get(context_hash)
        if current is None or _context_priority_key(row) > _context_priority_key(current):
            best[context_hash] = dict(row)
    return best


def _context_priority_key(row: dict[str, Any]) -> tuple[float, float, float, float, float, float, float]:
    explicit_priority = row.get("context_priority_score", row.get("priority_score"))
    has_explicit_priority = explicit_priority is not None
    return (
        2.0 if has_explicit_priority else 1.0,
        _float_value(explicit_priority) if has_explicit_priority else 0.0,
        1.0 if bool(row.get("is_missed_high_roi_opportunity")) else 0.0,
        1.0 if bool(row.get("is_high_roi_opportunity")) else 0.0,
        _float_value(row.get("accepted_batch_roi_label"), _float_value(row.get("accepted_batch_roi"))),
        _float_value(row.get("candidate_count")),
        -1.0 if bool(row.get("is_accepted_low_roi_or_bad")) else 0.0,
    )


def _source_instance_path(source_file: Any) -> str:
    text = str(source_file or "")
    if text.endswith(".jsonl"):
        text = text[: -len(".jsonl")]
    marker = "BPC_future/logical_graph/"
    index = text.find(marker)
    if index >= 0:
        text = text[index:]
    return text


def _row_instance_path(sample: dict[str, Any], row: dict[str, Any]) -> str:
    for value in (
        row.get("instance_path"),
        row.get("instance"),
        sample.get("instance_path"),
        sample.get("graph_path"),
        sample.get("logical_graph_path"),
    ):
        text = str(value or "").strip()
        if text.endswith(".json"):
            return text
    return _source_instance_path(row.get("source_file") or sample.get("source_file"))


def _split_instances(split_summary: Path | None, split_mode: str) -> set[str] | None:
    mode = str(split_mode or "all").strip().lower()
    if mode == "all":
        return None
    if split_summary is None:
        raise ValueError("--split-summary is required when --split-mode is not all")
    payload = _read_json(Path(split_summary))
    split = payload.get("split") or payload.get("deployment_gate", {}).get("split") or {}
    key = "train_instances" if mode == "train" else "validation_instances"
    instances = {str(value) for value in split.get(key) or []}
    if not instances:
        raise ValueError(f"split summary has no {key}")
    return instances


def _candidate_contexts(
    *,
    catalog: dict[str, dict[str, Any]],
    opportunity_rows: Iterable[dict[str, Any]],
    max_contexts: int,
    include_task_counts: Iterable[int] | None = (20,),
    include_families: Iterable[str] | None = None,
    require_opportunity_context: bool = False,
    split_instances: set[str] | None = None,
) -> list[dict[str, Any]]:
    by_context = _opportunity_by_context(opportunity_rows)
    allowed_task_counts = (
        None if include_task_counts is None else {int(value) for value in include_task_counts}
    )
    allowed_families = (
        None
        if include_families is None
        else {str(value).strip() for value in include_families if str(value).strip()}
    )
    records: list[dict[str, Any]] = []
    for context_hash, sample in catalog.items():
        row = by_context.get(context_hash, {})
        if require_opportunity_context and not row:
            continue
        roi = row.get("accepted_batch_roi_label", sample.get("accepted_batch_roi"))
        candidate_count = row.get("candidate_count", sample.get("candidate_count"))
        task_count = _int_value(row.get("task_count"), _int_value(sample.get("task_count"), 0))
        if allowed_task_counts is not None and task_count not in allowed_task_counts:
            continue
        instance_path = _row_instance_path(sample, row)
        if allowed_families is not None:
            family = str(row.get("family") or sample.get("family") or "")
            if not family:
                family = str(_instance_metadata(instance_path).get("instance_family") or "")
            if family not in allowed_families:
                continue
        if split_instances is not None and instance_path not in split_instances:
            continue
        records.append(
            {
                "context_hash": context_hash,
                "sample": sample,
                "opportunity": row,
                "priority_key": _context_priority_key(
                    {
                        **sample,
                        **row,
                        "accepted_batch_roi_label": roi,
                        "candidate_count": candidate_count,
                    }
                ),
            }
        )
    records.sort(key=lambda item: item["priority_key"], reverse=True)
    return records[: max(0, int(max_contexts))]


def _task_set_from_traces(traces: tuple[dict[str, Any], ...]) -> frozenset[int]:
    tasks: set[int] = set()
    for trace in traces:
        for task in trace.get("sequence") or []:
            try:
                tasks.add(int(task))
            except (TypeError, ValueError):
                return frozenset()
    return frozenset(tasks)


def _jaccard(left: frozenset[int], right: frozenset[int]) -> float:
    if not left and not right:
        return 1.0
    union = left | right
    if not union:
        return 0.0
    return float(len(left & right)) / float(len(union))


def _negative_materialized_items(
    event: dict[str, Any],
    *,
    support_change_jaccard_threshold: float,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    seen: set[tuple[tuple[int, ...], tuple[str, ...]]] = set()
    for index, journey in enumerate(event.get("returned_journeys") or []):
        if not isinstance(journey, dict):
            continue
        true_rc = _true_reduced_cost(journey)
        if true_rc is None or true_rc >= 0.0:
            continue
        sequence, arcs = _first_sortie_target(journey)
        traces = _journey_sortie_traces(journey)
        if not sequence or not arcs or not traces:
            continue
        flattened_sequence = _flatten_trace_sequence(traces)
        arc_key = tuple(
            str(arc)
            for trace in traces
            for arc in (trace.get("arc_option_sequence") or [])
        )
        key = (flattened_sequence, arc_key)
        if key in seen:
            continue
        seen.add(key)
        impact = _candidate_impact_features(
            event,
            journey,
            traces,
            support_change_jaccard_threshold=float(support_change_jaccard_threshold),
        )
        items.append(
            {
                "source_index": index,
                "journey": journey,
                "true_reduced_cost": float(true_rc),
                "target_priority_sequence": sequence,
                "target_arc_option_sequence": arcs,
                "target_sortie_traces": traces,
                "target_sequence": flattened_sequence,
                "target_task_set": _task_set_from_traces(traces),
                "impact": impact,
            }
        )
    return items


def _ranked_items(items: list[dict[str, Any]], ranking: str) -> list[dict[str, Any]]:
    if ranking == "impact":
        return sorted(
            items,
            key=lambda item: (
                _impact_bucket_rank(str(item["impact"].get("target_impact_bucket"))),
                -len(item["impact"].get("target_task_set") or []),
                item["true_reduced_cost"],
                item["source_index"],
            ),
        )
    if ranking == "active_replacement":
        return sorted(
            items,
            key=lambda item: (
                _active_replacement_rank(item["impact"]),
                -len(item["impact"].get("target_task_set") or []),
                item["true_reduced_cost"],
                item["source_index"],
            ),
        )
    if ranking == "diverse":
        selected: list[dict[str, Any]] = []
        remaining = sorted(items, key=lambda item: (item["true_reduced_cost"], item["source_index"]))
        while remaining:
            if not selected:
                selected.append(remaining.pop(0))
                continue
            scored = []
            selected_sets = [item["target_task_set"] for item in selected]
            for index, item in enumerate(remaining):
                max_overlap = max(_jaccard(item["target_task_set"], other) for other in selected_sets)
                scored.append((max_overlap, item["true_reduced_cost"], item["source_index"], index))
            _, _, _, best_index = min(scored)
            selected.append(remaining.pop(best_index))
        return selected
    return sorted(items, key=lambda item: (item["true_reduced_cost"], item["source_index"]))


def _select_targets(
    items: list[dict[str, Any]],
    *,
    targets_per_context: int,
    rankings: tuple[str, ...],
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    selected_keys: set[tuple[tuple[int, ...], tuple[str, ...]]] = set()
    target_limit = max(1, int(targets_per_context))
    for ranking in rankings:
        for item in _ranked_items(items, ranking):
            key = (
                tuple(int(task) for task in item["target_sequence"]),
                tuple(
                    str(arc)
                    for trace in item["target_sortie_traces"]
                    for arc in (trace.get("arc_option_sequence") or [])
                ),
            )
            if key in selected_keys:
                continue
            selected_keys.add(key)
            selected.append({**item, "selection_ranking": ranking, "context_target_rank": len(selected) + 1})
            break
        if len(selected) >= target_limit:
            return selected
    for item in _ranked_items(items, "best_rc"):
        if len(selected) >= target_limit:
            break
        key = (
            tuple(int(task) for task in item["target_sequence"]),
            tuple(
                str(arc)
                for trace in item["target_sortie_traces"]
                for arc in (trace.get("arc_option_sequence") or [])
            ),
        )
        if key in selected_keys:
            continue
        selected_keys.add(key)
        selected.append({**item, "selection_ranking": "best_rc_fill", "context_target_rank": len(selected) + 1})
    return selected


def _missing_capture_context_fields(event: dict[str, Any]) -> list[str]:
    return [
        field
        for field in REQUIRED_CAPTURE_CONTEXT_FIELDS
        if str(event.get(field) or "").strip() == ""
    ]


def _candidate_record(
    *,
    event: dict[str, Any],
    sample: dict[str, Any],
    opportunity: dict[str, Any],
    source_file: Path,
    target: dict[str, Any],
    context_target_count: int,
    support_change_jaccard_threshold: float,
) -> dict[str, Any]:
    instance_path = str(
        event.get("instance_path")
        or opportunity.get("instance_path")
        or sample.get("instance_path")
        or sample.get("instance")
        or ""
    )
    instance_metadata = _instance_metadata(instance_path)
    context_hash = str(event.get("context_hash") or sample.get("context_hash") or "")
    instance_name = str(event.get("instance") or opportunity.get("instance") or Path(instance_path).stem)
    name = _safe_name(
        f"{instance_name}_{context_hash}_mb{target['context_target_rank']}_"
        f"{'_'.join(str(task) for task in target['target_sequence'])}"
    )
    return {
        "schema_version": "gat_batch_impact_multibatch_intervention_candidate_v1",
        "name": name,
        "instance": instance_path,
        **instance_metadata,
        "context_hash": context_hash,
        "expected_context_hash": context_hash,
        "true_dual_hash": str(event.get("true_dual_hash") or ""),
        "cut_hash": str(event.get("cut_hash") or ""),
        "branch_hash": str(event.get("branch_hash") or ""),
        "forbidden_signature_hash": str(event.get("forbidden_signature_hash") or ""),
        "active_hash_before": str(event.get("active_hash_before") or ""),
        "pool_signature_hash": str(event.get("pool_signature_hash") or ""),
        "pool_task_set_hash": str(event.get("pool_task_set_hash") or ""),
        "target_sequence": list(target["target_sequence"]),
        "target_priority_sequence": list(target["target_priority_sequence"]),
        "target_arc_option_sequence": list(target["target_arc_option_sequence"]),
        "target_sortie_traces": list(target["target_sortie_traces"]),
        "best_true_reduced_cost": float(target["true_reduced_cost"]),
        "source_file": str(source_file),
        "sample_path": str(sample.get("path") or ""),
        "source_row_index": _int_value(sample.get("row_index"), -1),
        "context_target_rank": int(target["context_target_rank"]),
        "context_target_count": int(context_target_count),
        "selection_ranking": str(target["selection_ranking"]),
        "capture_cg_iter": _int_value(event.get("cg_iter"), -1),
        "capture_pricing_kind": str(event.get("pricing_kind") or ""),
        "capture_returned_journey_count": _int_value(event.get("returned_journey_count"), 0),
        "opportunity_score": _float_value(
            opportunity.get("accepted_batch_roi_label"),
            _float_value(sample.get("accepted_batch_roi")),
        ),
        "opportunity_is_missed_high_roi": bool(opportunity.get("is_missed_high_roi_opportunity")),
        "opportunity_is_high_roi": bool(opportunity.get("is_high_roi_opportunity")),
        "opportunity_is_accepted_low_roi_or_bad": bool(opportunity.get("is_accepted_low_roi_or_bad")),
        **{
            field: opportunity.get(field)
            for field in CONTEXT_PRIORITY_FIELDS
            if field in opportunity
        },
        "support_change_jaccard_threshold": float(support_change_jaccard_threshold),
        **target["impact"],
        "gate_role": "stage3_same_context_multibatch_intervention_sampling",
        "worker_role": "explicit_opt_in_same_context_target_intervention_probe",
        "training_label_allowed_before_worker_reachability": False,
        "requires_worker_target_causal_match": True,
        "certificate_effect": False,
        "official_bound_effect": False,
    }


def _runbook_command(output_dir: Path, candidates_path: Path) -> str:
    runbook_dir = output_dir / "worker_ab_runbook"
    report_path = output_dir / "worker_ab_runbook.md"
    return " ".join(
        [
            "PYTHONDONTWRITEBYTECODE=1",
            "PYTHONPATH=.",
            "python",
            "BPC_future/scripts/build_gat_target_priority_worker_ab_runbook.py",
            "--candidates-file",
            str(candidates_path),
            "--output-dir",
            str(runbook_dir),
            "--report",
            str(report_path),
            "--worker-method",
            "target_materialization_fixed",
            "--worker-batch-size",
            "1",
        ]
    )


def build_intervention_plan(
    *,
    dataset_dir: Path = DEFAULT_DATASET_DIR,
    opportunity_jsonl_paths: Iterable[Path] = DEFAULT_OPPORTUNITY_JSONL,
    context_priority_jsonl_paths: Iterable[Path] | None = None,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    max_contexts: int = 12,
    targets_per_context: int = 3,
    min_negative_targets_per_context: int = 2,
    rankings: Iterable[str] = SUPPORTED_SELECTION_RANKINGS,
    include_task_counts: Iterable[int] | None = (20,),
    include_families: Iterable[str] | None = None,
    support_change_jaccard_threshold: float = DEFAULT_SUPPORT_CHANGE_JACCARD_THRESHOLD,
    require_opportunity_context: bool = False,
    split_summary: Path | None = None,
    split_mode: str = "all",
) -> dict[str, Any]:
    ranking_tuple = tuple(str(item) for item in rankings)
    unknown_rankings = sorted(set(ranking_tuple) - set(SUPPORTED_SELECTION_RANKINGS))
    if unknown_rankings:
        raise ValueError(f"unsupported rankings: {unknown_rankings}")
    manifest_path = Path(dataset_dir) / "manifest.json"
    manifest = _read_json(manifest_path)
    catalog = _context_catalog(manifest)
    raw_opportunities = _opportunity_rows(opportunity_jsonl_paths)
    context_priorities = _context_priority_rows(context_priority_jsonl_paths)
    opportunities = _merge_context_priorities(raw_opportunities, context_priorities)
    split_instance_set = _split_instances(split_summary, split_mode)
    selected_contexts = _candidate_contexts(
        catalog=catalog,
        opportunity_rows=opportunities,
        max_contexts=max_contexts,
        include_task_counts=include_task_counts,
        include_families=include_families,
        require_opportunity_context=bool(require_opportunity_context),
        split_instances=split_instance_set,
    )
    capture_cache: dict[str, dict[str, dict[str, Any]]] = {}
    skipped: Counter[str] = Counter()
    candidates: list[dict[str, Any]] = []
    context_records: list[dict[str, Any]] = []

    for item in selected_contexts:
        sample = item["sample"]
        opportunity = item["opportunity"]
        context_hash = str(item["context_hash"])
        source_file = Path(str(sample.get("source_file") or ""))
        if not source_file.exists():
            skipped["missing_source_file"] += 1
            context_records.append({"context_hash": context_hash, "status": "skipped", "reason": "missing_source_file"})
            continue
        events = capture_cache.get(str(source_file))
        if events is None:
            events = _capture_events_by_context(source_file)
            capture_cache[str(source_file)] = events
        event = events.get(context_hash)
        if event is None:
            skipped["missing_capture_event"] += 1
            context_records.append({"context_hash": context_hash, "status": "skipped", "reason": "missing_capture_event"})
            continue
        missing_fields = _missing_capture_context_fields(event)
        if missing_fields:
            skipped["missing_capture_context_fields"] += 1
            context_records.append(
                {
                    "context_hash": context_hash,
                    "status": "skipped",
                    "reason": "missing_capture_context_fields",
                    "missing_fields": missing_fields,
                }
            )
            continue
        negative_items = _negative_materialized_items(
            event,
            support_change_jaccard_threshold=float(support_change_jaccard_threshold),
        )
        if len(negative_items) < max(1, int(min_negative_targets_per_context)):
            skipped["not_enough_unique_negative_targets"] += 1
            context_records.append(
                {
                    "context_hash": context_hash,
                    "status": "skipped",
                    "reason": "not_enough_unique_negative_targets",
                    "unique_negative_target_count": len(negative_items),
                }
            )
            continue
        selected_targets = _select_targets(
            negative_items,
            targets_per_context=max(1, int(targets_per_context)),
            rankings=ranking_tuple,
        )
        if len(selected_targets) < max(1, int(min_negative_targets_per_context)):
            skipped["not_enough_selected_targets"] += 1
            context_records.append(
                {
                    "context_hash": context_hash,
                    "status": "skipped",
                    "reason": "not_enough_selected_targets",
                    "unique_negative_target_count": len(negative_items),
                    "selected_target_count": len(selected_targets),
                }
            )
            continue
        for target in selected_targets:
            candidates.append(
                _candidate_record(
                    event=event,
                    sample=sample,
                    opportunity=opportunity,
                    source_file=source_file,
                    target=target,
                    context_target_count=len(selected_targets),
                    support_change_jaccard_threshold=float(support_change_jaccard_threshold),
                )
            )
        context_records.append(
            {
                "context_hash": context_hash,
                "status": "selected",
                "source_file": str(source_file),
                "instance": str(event.get("instance_path") or sample.get("instance") or ""),
                "task_count": _int_value(sample.get("task_count"), _int_value(event.get("task_count"), 0)),
                "opportunity_score": _float_value(
                    opportunity.get("accepted_batch_roi_label"),
                    _float_value(sample.get("accepted_batch_roi")),
                ),
                "opportunity_is_missed_high_roi": bool(opportunity.get("is_missed_high_roi_opportunity")),
                "context_priority_score": opportunity.get("context_priority_score"),
                "context_priority_action": opportunity.get("context_priority_action"),
                "context_priority_negative_neighbor_count": opportunity.get(
                    "context_priority_negative_neighbor_count"
                ),
                "context_priority_deep_gap_count": opportunity.get("context_priority_deep_gap_count"),
                "context_false_delay_false_high_priority_on_delay_count": opportunity.get(
                    "context_false_delay_false_high_priority_on_delay_count"
                ),
                "context_false_delay_candidate_signature_count": opportunity.get(
                    "context_false_delay_candidate_signature_count"
                ),
                "context_false_delay_batch_record_count": opportunity.get(
                    "context_false_delay_batch_record_count"
                ),
                "context_false_delay_accepted_batch_count": opportunity.get(
                    "context_false_delay_accepted_batch_count"
                ),
                "context_false_delay_max_delay_risk_score": opportunity.get(
                    "context_false_delay_max_delay_risk_score"
                ),
                "context_false_delay_median_delay_risk_score": opportunity.get(
                    "context_false_delay_median_delay_risk_score"
                ),
                "context_false_delay_median_raw_high_priority_score": opportunity.get(
                    "context_false_delay_median_raw_high_priority_score"
                ),
                "context_repair_candidate_count": opportunity.get("context_repair_candidate_count"),
                "context_repair_delayed_high_roi_count": opportunity.get(
                    "context_repair_delayed_high_roi_count"
                ),
                "context_repair_accepted_high_point_roi_unstable_count": opportunity.get(
                    "context_repair_accepted_high_point_roi_unstable_count"
                ),
                "context_repair_max_roi": opportunity.get("context_repair_max_roi"),
                "context_repair_median_roi": opportunity.get("context_repair_median_roi"),
                "unique_negative_target_count": len(negative_items),
                "selected_target_count": len(selected_targets),
                "selection_rankings": [str(target["selection_ranking"]) for target in selected_targets],
            }
        )

    per_context_counts = Counter(str(item["expected_context_hash"]) for item in candidates)
    candidates_path = Path(output_dir) / "candidates.json"
    runbook_command = _runbook_command(Path(output_dir), candidates_path)
    checks = {
        "diagnostic_only": True,
        "runs_bpc_or_pricing_false": True,
        "no_certificate_effect": True,
        "has_candidate": bool(candidates),
        "has_pairwise_context_targets": any(
            count >= max(2, int(min_negative_targets_per_context))
            for count in per_context_counts.values()
        ),
        "all_candidates_true_rc_negative": all(
            float(item["best_true_reduced_cost"]) < 0.0 for item in candidates
        ),
        "all_candidate_instances_exist": all(
            Path(str(item["instance"])).exists() for item in candidates
        ),
        "all_candidates_have_arc_targets": all(
            bool(item.get("target_arc_option_sequence")) for item in candidates
        ),
        "all_candidates_have_full_sortie_traces": all(
            bool(item.get("target_sortie_traces")) for item in candidates
        ),
        "all_candidates_have_full_capture_context": all(
            all(str(item.get(field) or "").strip() for field in REQUIRED_CAPTURE_CONTEXT_FIELDS)
            for item in candidates
        ),
        "labels_blocked_until_worker_reachability": all(
            item["training_label_allowed_before_worker_reachability"] is False
            and item["requires_worker_target_causal_match"] is True
            for item in candidates
        ),
    }
    summary = {
        "schema_version": "gat_batch_impact_multibatch_intervention_plan_v1",
        "status": "ready" if candidates else "no_candidates",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "dataset_dir": str(dataset_dir),
        "manifest_path": str(manifest_path),
        "opportunity_jsonl_paths": [str(path) for path in opportunity_jsonl_paths],
        "context_priority_jsonl_paths": [
            str(path) for path in (context_priority_jsonl_paths or [])
        ],
        "raw_opportunity_row_count": len(raw_opportunities),
        "context_priority_row_count": len(context_priorities),
        "opportunity_row_count": len(opportunities),
        "manifest_sample_count": _int_value(manifest.get("sample_count"), len(catalog)),
        "available_context_count": len(catalog),
        "include_task_counts": []
        if include_task_counts is None
        else [int(value) for value in include_task_counts],
        "include_families": []
        if include_families is None
        else sorted({str(value).strip() for value in include_families if str(value).strip()}),
        "planned_context_count": len(selected_contexts),
        "selected_context_count": sum(1 for item in context_records if item["status"] == "selected"),
        "pairwise_context_target_count": sum(1 for count in per_context_counts.values() if count >= 2),
        "candidate_count": len(candidates),
        "targets_per_context": max(1, int(targets_per_context)),
        "min_negative_targets_per_context": max(1, int(min_negative_targets_per_context)),
        "selection_rankings": list(ranking_tuple),
        "support_change_jaccard_threshold": float(support_change_jaccard_threshold),
        "require_opportunity_context": bool(require_opportunity_context),
        "split_summary": str(split_summary) if split_summary else "",
        "split_mode": str(split_mode or "all"),
        "split_instance_count": 0 if split_instance_set is None else len(split_instance_set),
        "candidate_task_count_counts": {
            str(task_count): count
            for task_count, count in sorted(
                Counter(item.get("instance_task_count") for item in candidates).items(),
                key=lambda pair: (-1 if pair[0] is None else int(pair[0])),
            )
        },
        "candidate_family_region_counts": {
            f"{family}|{region}": count
            for (family, region), count in sorted(
                Counter(
                    (
                        str(item.get("instance_family") or "unknown"),
                        str(item.get("instance_region") or "unknown"),
                    )
                    for item in candidates
                ).items()
            )
        },
        "candidate_selection_ranking_counts": dict(
            sorted(Counter(str(item.get("selection_ranking") or "") for item in candidates).items())
        ),
        "candidate_impact_bucket_counts": dict(
            sorted(Counter(str(item.get("target_impact_bucket") or "") for item in candidates).items())
        ),
        "skipped_counts": dict(sorted(skipped.items())),
        "contexts": context_records,
        "candidates": candidates,
        "output_candidates_json": str(candidates_path),
        "runbook_command": runbook_command,
        "output_runbook_command_txt": str(Path(output_dir) / "runbook_command.txt"),
        "production_ready": False,
        "default_enabled": False,
        "certificate_ready": False,
        "official_bound_effect": False,
        "candidate_policy": {
            "purpose": "collect_same_context_multi_batch_pairs_for_precision_constrained_roi_training",
            "safe_negative_action": "run_explicit_opt_in_target_materialization_probe",
            "training_label_requires_worker_target_causal_match": True,
            "permanent_negative_filter_allowed": False,
            "certificate_effect": False,
            "official_bound_effect": False,
        },
        "checks": checks,
        "all_checks_pass": all(bool(value) for value in checks.values()),
    }
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    candidates_path.write_text(
        json.dumps({"candidates": candidates}, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    (Path(output_dir) / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (Path(output_dir) / "runbook_command.txt").write_text(runbook_command + "\n", encoding="utf-8")
    _write_report(Path(report), summary)
    return summary


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GAT Batch-Impact Multi-Batch Intervention Plan 报告",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 目的",
        "",
        "Stage 3 现在按 precision-constrained ROI maximization 验收，不能只靠单例",
        "context 样本训练普通分类器。本报告生成同一 RMP context 下多个 target",
        " materialization 候选，用于下一轮 opt-in worker A/B 后形成 same-context",
        " high-ROI / low-ROI pairwise 监督。",
        "",
        "该脚本只读 manifest / opportunity / capture JSONL，不运行 BPC / pricing / RMP / worker，",
        "不产生 certificate 或 official lower bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "gat_batch_impact_multibatch_intervention_plan = current",
        f"status = {summary['status']}",
        f"planned_context_count = {summary['planned_context_count']}",
        f"selected_context_count = {summary['selected_context_count']}",
        f"pairwise_context_target_count = {summary['pairwise_context_target_count']}",
        f"candidate_count = {summary['candidate_count']}",
        f"targets_per_context = {summary['targets_per_context']}",
        f"min_negative_targets_per_context = {summary['min_negative_targets_per_context']}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"default_enabled = {str(summary['default_enabled']).lower()}",
        f"certificate_ready = {str(summary['certificate_ready']).lower()}",
        f"official_bound_effect = {str(summary['official_bound_effect']).lower()}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 摘要",
        "",
        "```json",
        json.dumps(
            {
                "candidate_count": summary["candidate_count"],
                "include_task_counts": summary["include_task_counts"],
                "include_families": summary["include_families"],
                "selected_context_count": summary["selected_context_count"],
                "pairwise_context_target_count": summary["pairwise_context_target_count"],
                "candidate_task_count_counts": summary["candidate_task_count_counts"],
                "candidate_family_region_counts": summary["candidate_family_region_counts"],
                "candidate_selection_ranking_counts": summary["candidate_selection_ranking_counts"],
                "candidate_impact_bucket_counts": summary["candidate_impact_bucket_counts"],
                "skipped_counts": summary["skipped_counts"],
                "require_opportunity_context": summary["require_opportunity_context"],
                "split_mode": summary["split_mode"],
                "split_instance_count": summary["split_instance_count"],
                "context_priority_row_count": summary["context_priority_row_count"],
                "context_priority_jsonl_paths": summary["context_priority_jsonl_paths"],
                "checks": summary["checks"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## Selected Contexts",
        "",
        "| context | task | opportunity | false-delay FP | delayed high ROI | accepted high point ROI | targets | unique negatives | action |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for context in summary.get("contexts") or []:
        if context.get("status") != "selected":
            continue
        lines.append(
            "| {context_hash} | {task_count} | {opportunity_score:.4f} | {false_delay} | {delayed} | {accepted} | {targets} | {negatives} | {action} |".format(
                context_hash=str(context.get("context_hash") or ""),
                task_count=int(context.get("task_count") or 0),
                opportunity_score=_float_value(context.get("opportunity_score")),
                false_delay=_int_value(
                    context.get("context_false_delay_false_high_priority_on_delay_count")
                ),
                delayed=_int_value(context.get("context_repair_delayed_high_roi_count")),
                accepted=_int_value(
                    context.get("context_repair_accepted_high_point_roi_unstable_count")
                ),
                targets=_int_value(context.get("selected_target_count")),
                negatives=_int_value(context.get("unique_negative_target_count")),
                action=str(context.get("context_priority_action") or ""),
            )
        )
    lines.extend(
        [
        "",
        "## 下一步命令",
        "",
        "先生成 guarded worker A/B runbook；实际运行仍是显式 opt-in：",
        "",
        "```bash",
        summary["runbook_command"],
        "```",
        "",
        "## 边界",
        "",
        "- 候选只用于补 same-context 多 batch intervention 数据；",
        "- 候选必须是 materialized true-RC negative，但这不等于它可以跳过 exact pricing；",
        "- worker 跑完前不能把这些候选当训练标签；必须确认 expected context reachability 与 target causal match；",
        "- 失败或低 ROI 的 true-RC negative 只能进入 DELAY_QUEUE/诊断样本，不能永久丢弃；",
        "- 最终 OPTIMAL / no-negative certificate 仍只能来自当前 branch/cut/dual 下的 exact pricing closure。",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_rankings(values: Iterable[str] | None) -> tuple[str, ...]:
    if not values:
        return SUPPORTED_SELECTION_RANKINGS
    parsed: list[str] = []
    for value in values:
        for part in str(value).split(","):
            item = part.strip()
            if item:
                parsed.append(item)
    return tuple(parsed) or SUPPORTED_SELECTION_RANKINGS


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument(
        "--opportunity-jsonl",
        type=Path,
        action="append",
        default=None,
        help="May be repeated. Defaults to the hard-ROI opportunity mining outputs.",
    )
    parser.add_argument(
        "--context-priority-jsonl",
        type=Path,
        action="append",
        default=None,
        help=(
            "Optional context-level priority rows from "
            "audit_gat_batch_impact_context_contrast_priority.py. "
            "They only alter offline context ordering/selection."
        ),
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--max-contexts", type=int, default=12)
    parser.add_argument("--targets-per-context", type=int, default=3)
    parser.add_argument("--min-negative-targets-per-context", type=int, default=2)
    parser.add_argument(
        "--include-task-counts",
        nargs="*",
        type=int,
        default=[20],
        help=(
            "Task-count allow-list. Default is 20 because the current guarded "
            "target-priority worker runbook uses the task20 config."
        ),
    )
    parser.add_argument(
        "--ranking",
        action="append",
        default=None,
        help="Target selection ranking; may be repeated or comma-separated.",
    )
    parser.add_argument(
        "--include-families",
        nargs="*",
        default=None,
        help="Optional instance family allow-list, e.g. sector-wave random-wave.",
    )
    parser.add_argument(
        "--support-change-jaccard-threshold",
        type=float,
        default=DEFAULT_SUPPORT_CHANGE_JACCARD_THRESHOLD,
    )
    parser.add_argument(
        "--require-opportunity-context",
        action="store_true",
        help=(
            "Only select contexts present in the supplied opportunity JSONL. "
            "Use this when opportunity rows come from a validation split and "
            "manifest fallback would mix train contexts into the worker plan."
        ),
    )
    parser.add_argument(
        "--split-summary",
        type=Path,
        default=None,
        help=(
            "Training metrics/summary JSON containing split.train_instances and "
            "split.validation_instances. Required when --split-mode is train or validation."
        ),
    )
    parser.add_argument(
        "--split-mode",
        choices=("all", "train", "validation"),
        default="all",
        help="Restrict candidate contexts by the supplied split summary.",
    )
    args = parser.parse_args(argv)
    summary = build_intervention_plan(
        dataset_dir=args.dataset_dir,
        opportunity_jsonl_paths=args.opportunity_jsonl or DEFAULT_OPPORTUNITY_JSONL,
        context_priority_jsonl_paths=args.context_priority_jsonl,
        output_dir=args.output_dir,
        report=args.report,
        max_contexts=max(0, int(args.max_contexts)),
        targets_per_context=max(1, int(args.targets_per_context)),
        min_negative_targets_per_context=max(1, int(args.min_negative_targets_per_context)),
        rankings=_parse_rankings(args.ranking),
        include_task_counts=args.include_task_counts,
        include_families=args.include_families,
        support_change_jaccard_threshold=float(args.support_change_jaccard_threshold),
        require_opportunity_context=bool(args.require_opportunity_context),
        split_summary=args.split_summary,
        split_mode=args.split_mode,
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
