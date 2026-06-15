#!/usr/bin/env python3
"""Build same-run GAT batch-impact labels from solver JSONL logs.

This dataset avoids off-policy replay labels.  A row is valid only when the
same solver run contains:

* a ``journey_counterfactual_replay_capture`` event at CG iteration t,
* a matching ``journey_column_addition`` event for the same pricing stage t,
* the RMP state before t and the next RMP state after t.

It is read-only: it never runs BPC, pricing, RMP, workers, or certificates.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


DEFAULT_LOG_ROOTS = (
    Path(
        "BPC_future/results/gat_target_priority_worker_ab_20260614/"
        "same_context_capture_smoke_7e0afd_target19_20260615/logs"
    ),
)
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/gat_same_run_batch_impact_dataset_20260615")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260615_bpc_future_gat_same_run_batch_impact_dataset_zh.md"
)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            try:
                event = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict):
                rows.append(event)
    return rows


def _jsonl_files(log_roots: Iterable[Path]) -> list[Path]:
    files: list[Path] = []
    for root in log_roots:
        path = Path(root)
        if path.is_file() and path.suffix == ".jsonl":
            files.append(path)
        elif path.exists():
            files.extend(sorted(path.glob("**/*.jsonl")))
    return sorted(dict.fromkeys(files))


def _as_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _task_set(value: Any) -> tuple[int, ...]:
    if not isinstance(value, list):
        return tuple()
    result: list[int] = []
    for item in value:
        try:
            result.append(int(item))
        except (TypeError, ValueError):
            return tuple()
    return tuple(sorted(result))


def _journey_task_sets(journeys: Any, *, max_items: int = 16) -> list[list[int]]:
    result: list[list[int]] = []
    if not isinstance(journeys, list):
        return result
    seen: set[tuple[int, ...]] = set()
    for journey in journeys:
        if not isinstance(journey, dict):
            continue
        task_set = _task_set(journey.get("task_set"))
        if not task_set:
            sequence_payload = journey.get("sequence")
            if isinstance(sequence_payload, list):
                flattened: list[int] = []
                for sortie in sequence_payload:
                    if isinstance(sortie, list):
                        for task in sortie:
                            try:
                                flattened.append(int(task))
                            except (TypeError, ValueError):
                                flattened = []
                                break
                    if not flattened and sortie:
                        break
                task_set = tuple(sorted(set(flattened)))
        if task_set and task_set not in seen:
            seen.add(task_set)
            result.append(list(task_set))
        if len(result) >= int(max_items):
            break
    return result


def _best_true_rc(capture: dict[str, Any]) -> float | None:
    values: list[float] = []
    for journey in capture.get("returned_journeys") or []:
        if not isinstance(journey, dict):
            continue
        for key in ("true_reduced_cost", "manual_true_reduced_cost", "reduced_cost"):
            if key in journey:
                try:
                    values.append(float(journey[key]))
                    break
                except (TypeError, ValueError):
                    pass
    if not values:
        return None
    return min(values)


def _stage_key(event: dict[str, Any]) -> tuple[int, str, int, int]:
    return (
        _as_int(event.get("cg_iter"), -1),
        str(event.get("pricing_kind") or ""),
        _as_int(event.get("node_id"), 0),
        _as_int(event.get("depth"), 0),
    )


def _instance_region(instance_path: str, instance: str) -> str:
    text = str(instance_path or instance or "")
    parts = Path(text).parts
    for idx, part in enumerate(parts):
        if part == "sector-wave" and idx + 1 < len(parts):
            return str(parts[idx + 1])
    lowered = text.lower()
    if "tranquillitatis" in lowered:
        return "tranquillitatis_balmer_like_20km"
    if "apollo" in lowered:
        return "apollo15_20km"
    return "unknown"


def _build_rows_for_file(path: Path) -> tuple[list[dict[str, Any]], dict[str, int]]:
    events = _read_jsonl(path)
    skipped: dict[str, int] = {}

    def skip(reason: str) -> None:
        skipped[reason] = skipped.get(reason, 0) + 1

    rmp_by_iter: dict[tuple[int, int, int], dict[str, Any]] = {}
    captures: dict[tuple[int, str, int, int], dict[str, Any]] = {}
    additions: dict[tuple[int, str, int, int], dict[str, Any]] = {}
    for event in events:
        event_name = event.get("event")
        node_id = _as_int(event.get("node_id"), 0)
        depth = _as_int(event.get("depth"), 0)
        cg_iter = _as_int(event.get("cg_iter"), -1)
        if event_name == "journey_rmp" and cg_iter >= 0:
            rmp_by_iter[(cg_iter, node_id, depth)] = event
        elif event_name == "journey_counterfactual_replay_capture":
            captures[_stage_key(event)] = event
        elif event_name == "journey_column_addition":
            additions[_stage_key(event)] = event

    rows: list[dict[str, Any]] = []
    for key, capture in sorted(captures.items()):
        cg_iter, pricing_kind, node_id, depth = key
        addition = additions.get(key)
        if addition is None:
            skip("missing_matching_column_addition")
            continue
        added = _as_int(addition.get("added_journeys"))
        if added <= 0:
            skip("nonpositive_added_journeys")
            continue
        before = rmp_by_iter.get((cg_iter, node_id, depth))
        after = rmp_by_iter.get((cg_iter + 1, node_id, depth))
        if before is None or after is None:
            skip("missing_before_or_after_rmp")
            continue
        objective_before = _as_float(before.get("objective"))
        objective_after = _as_float(after.get("objective"))
        objective_delta = objective_after - objective_before
        objective_improvement = objective_before - objective_after
        returned_count = _as_int(capture.get("returned_journey_count"))
        if returned_count <= 0:
            skip("empty_returned_batch")
            continue
        rows.append(
            {
                "schema_version": "gat_same_run_batch_impact_row_v1",
                "diagnostic_only": True,
                "runs_bpc_or_pricing": False,
                "certificate_effect": False,
                "official_bound_effect": False,
                "source_file": str(path),
                "instance": str(capture.get("instance") or ""),
                "instance_path": str(capture.get("instance_path") or ""),
                "instance_region": _instance_region(
                    str(capture.get("instance_path") or ""),
                    str(capture.get("instance") or ""),
                ),
                "cg_iter": int(cg_iter),
                "node_id": int(node_id),
                "depth": int(depth),
                "pricing_kind": str(pricing_kind),
                "context_hash": str(capture.get("context_hash") or ""),
                "true_dual_hash": str(capture.get("true_dual_hash") or ""),
                "cut_hash": str(capture.get("cut_hash") or ""),
                "branch_hash": str(capture.get("branch_hash") or ""),
                "forbidden_signature_hash": str(
                    capture.get("forbidden_signature_hash") or ""
                ),
                "returned_journey_count": int(returned_count),
                "added_journeys": int(added),
                "new_journeys": _as_int(addition.get("new_journeys")),
                "replacement_journeys": _as_int(addition.get("replacement_journeys")),
                "new_task_set_count": _as_int(addition.get("new_task_set_count")),
                "replacement_task_set_count": _as_int(
                    addition.get("replacement_task_set_count")
                ),
                "active_changed_task_set_count": _as_int(
                    addition.get("active_changed_task_set_count")
                ),
                "addition_productivity_class": str(
                    addition.get("addition_productivity_class") or ""
                ),
                "best_true_reduced_cost": _best_true_rc(capture),
                "objective_before": objective_before,
                "objective_after": objective_after,
                "objective_delta": objective_delta,
                "objective_improvement": objective_improvement,
                "label_objective_improved": int(objective_improvement > 1.0e-9),
                "label_active_support_changing": int(
                    _as_int(addition.get("active_changed_task_set_count")) > 0
                ),
                "label_new_task_set_added": int(
                    _as_int(addition.get("new_task_set_count")) > 0
                ),
                "candidate_task_set_samples": _journey_task_sets(
                    capture.get("returned_journeys")
                ),
                "same_run_intervention_observed": True,
                "training_label_allowed": True,
                "training_label_scope": "same_run_returned_batch",
            }
        )
    return rows, skipped


def build_dataset(
    *,
    log_roots: Iterable[Path] = DEFAULT_LOG_ROOTS,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    min_rows_for_training: int = 50,
    min_positive_for_training: int = 10,
    min_negative_for_training: int = 10,
    min_instances_for_training: int = 6,
    min_regions_for_training: int = 2,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    skipped_counts: dict[str, int] = {}
    source_files = _jsonl_files(log_roots)
    for path in source_files:
        file_rows, file_skipped = _build_rows_for_file(path)
        rows.extend(file_rows)
        for key, value in file_skipped.items():
            skipped_counts[key] = skipped_counts.get(key, 0) + int(value)

    row_jsonl = output_dir / "same_run_batch_impact_rows.jsonl"
    row_jsonl.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows)
        + ("\n" if rows else ""),
        encoding="utf-8",
    )
    positive_count = sum(1 for row in rows if row["label_objective_improved"])
    negative_count = sum(1 for row in rows if not row["label_objective_improved"])
    active_count = sum(1 for row in rows if row["label_active_support_changing"])
    new_count = sum(1 for row in rows if row["label_new_task_set_added"])
    instances = sorted({str(row["instance_path"] or row["instance"]) for row in rows})
    regions = sorted({str(row["instance_region"]) for row in rows})
    pricing_kinds = sorted({str(row["pricing_kind"]) for row in rows})
    region_label_counts: dict[str, dict[str, int]] = {}
    for region in regions:
        region_rows = [row for row in rows if str(row["instance_region"]) == region]
        region_positive = sum(
            1 for row in region_rows if row["label_objective_improved"]
        )
        region_label_counts[region] = {
            "positive_objective_improvement": int(region_positive),
            "non_improving_objective": int(len(region_rows) - region_positive),
            "row_count": int(len(region_rows)),
        }
    productivity_class_counts = Counter(
        str(row["addition_productivity_class"] or "unknown") for row in rows
    )
    training_blockers: list[str] = []
    if len(rows) < int(min_rows_for_training):
        training_blockers.append("need_more_same_run_rows")
    if positive_count < int(min_positive_for_training):
        training_blockers.append("need_more_positive_objective_rows")
    if negative_count < int(min_negative_for_training):
        training_blockers.append("need_more_non_improving_objective_rows")
    if len(instances) < int(min_instances_for_training):
        training_blockers.append("need_more_instances")
    if len(regions) < int(min_regions_for_training):
        training_blockers.append("need_more_regions")
    label_distribution_ready = bool(
        len(rows) >= int(min_rows_for_training)
        and positive_count >= int(min_positive_for_training)
        and negative_count >= int(min_negative_for_training)
        and len(instances) >= int(min_instances_for_training)
        and len(regions) >= int(min_regions_for_training)
    )
    checks = {
        "diagnostic_only": True,
        "runs_bpc_or_pricing_false": True,
        "no_certificate_effect": all(not row["certificate_effect"] for row in rows),
        "no_official_bound_effect": all(not row["official_bound_effect"] for row in rows),
        "has_rows": bool(rows),
        "all_rows_same_run_intervention": all(
            row["same_run_intervention_observed"] for row in rows
        ),
        "all_training_labels_allowed": all(row["training_label_allowed"] for row in rows),
        "has_positive_and_negative_labels": bool(positive_count > 0 and negative_count > 0),
    }
    summary = {
        "schema_version": "gat_same_run_batch_impact_summary_v1",
        "status": "built" if rows else "no_rows",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "log_roots": [str(path) for path in log_roots],
        "source_file_count": len(source_files),
        "row_count": len(rows),
        "positive_objective_improvement_count": int(positive_count),
        "non_improving_objective_count": int(negative_count),
        "objective_positive_rate": (
            round(float(positive_count) / float(len(rows)), 6) if rows else 0.0
        ),
        "objective_non_improving_rate": (
            round(float(negative_count) / float(len(rows)), 6) if rows else 0.0
        ),
        "active_support_changing_count": int(active_count),
        "new_task_set_added_count": int(new_count),
        "objective_label_by_region": region_label_counts,
        "addition_productivity_class_counts": dict(
            sorted(productivity_class_counts.items())
        ),
        "instance_count": len(instances),
        "instance_regions": regions,
        "instance_region_count": len(regions),
        "pricing_kinds": pricing_kinds,
        "min_rows_for_training": int(min_rows_for_training),
        "min_positive_for_training": int(min_positive_for_training),
        "min_negative_for_training": int(min_negative_for_training),
        "min_instances_for_training": int(min_instances_for_training),
        "min_regions_for_training": int(min_regions_for_training),
        "rows_needed_for_training": max(0, int(min_rows_for_training) - len(rows)),
        "positive_rows_needed_for_training": max(
            0, int(min_positive_for_training) - positive_count
        ),
        "non_improving_rows_needed_for_training": max(
            0, int(min_negative_for_training) - negative_count
        ),
        "instances_needed_for_training": max(
            0, int(min_instances_for_training) - len(instances)
        ),
        "regions_needed_for_training": max(
            0, int(min_regions_for_training) - len(regions)
        ),
        "training_blockers": training_blockers,
        "label_distribution_ready": label_distribution_ready,
        "skipped_counts": dict(sorted(skipped_counts.items())),
        "jsonl_path": str(row_jsonl),
        "production_ready": False,
        "default_enabled": False,
        "certificate_ready": False,
        "official_bound_effect": False,
        "training_ready": bool(label_distribution_ready),
        "training_readiness_reason": "ready" if label_distribution_ready else (
            "same_run_rows_valid_but_need_more_balanced_scale_family_labels"
        ),
        "checks": checks,
        "all_checks_pass": all(bool(value) for value in checks.values()),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(Path(report), summary, rows)
    return summary


def _write_report(path: Path, summary: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    examples = rows[:8]
    lines = [
        "# GAT Same-Run Batch Impact Dataset 报告",
        "",
        "日期：2026-06-15",
        "",
        "## 目的",
        "",
        "本报告从同一次求解日志中配对 capture、column addition 和下一轮 RMP，",
        "构造不会发生 context replay drift 的 GAT batch-impact 标签。",
        "它不运行 BPC / pricing / RMP / worker，不产生 certificate 或 official lower bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "gat_same_run_batch_impact_dataset = current",
        f"status = {summary['status']}",
        f"source_file_count = {summary['source_file_count']}",
        f"row_count = {summary['row_count']}",
        "positive_objective_improvement_count = "
        f"{summary['positive_objective_improvement_count']}",
        f"non_improving_objective_count = {summary['non_improving_objective_count']}",
        f"objective_positive_rate = {summary['objective_positive_rate']}",
        f"objective_non_improving_rate = {summary['objective_non_improving_rate']}",
        f"active_support_changing_count = {summary['active_support_changing_count']}",
        f"new_task_set_added_count = {summary['new_task_set_added_count']}",
        f"instance_count = {summary['instance_count']}",
        f"instance_region_count = {summary['instance_region_count']}",
        f"instance_regions = {summary['instance_regions']}",
        f"pricing_kinds = {summary['pricing_kinds']}",
        f"label_distribution_ready = {str(summary['label_distribution_ready']).lower()}",
        f"training_blockers = {summary['training_blockers']}",
        "non_improving_rows_needed_for_training = "
        f"{summary['non_improving_rows_needed_for_training']}",
        f"objective_label_by_region = {summary['objective_label_by_region']}",
        "addition_productivity_class_counts = "
        f"{summary['addition_productivity_class_counts']}",
        f"skipped_counts = {summary['skipped_counts']}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"default_enabled = {str(summary['default_enabled']).lower()}",
        f"certificate_ready = {str(summary['certificate_ready']).lower()}",
        f"official_bound_effect = {str(summary['official_bound_effect']).lower()}",
        f"training_ready = {str(summary['training_ready']).lower()}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 样例",
        "",
        "```json",
        json.dumps(examples, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## 结论",
        "",
        "- 这类样本比 offline replay 更干净，因为 target/context/加列/下一轮 RMP 都来自同一次运行；",
        "- 只有 `training_ready=true` 才允许进入 GAT 训练；当前若为 false，说明样本量、正负标签或实例/family 分布不足；",
        "- 如果 `need_more_non_improving_objective_rows` 存在，说明当前 exact add-column 样本天然偏向改善动作，需要继续采 hard-tail 中加列但 RMP 不动或弱动的同一上下文对照；",
        "- 该数据只允许做离线 GAT trajectory-impact 监督，不能参与 pricing certificate。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log-root", type=Path, action="append", default=None)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--min-rows-for-training", type=int, default=50)
    parser.add_argument("--min-positive-for-training", type=int, default=10)
    parser.add_argument("--min-negative-for-training", type=int, default=10)
    parser.add_argument("--min-instances-for-training", type=int, default=6)
    parser.add_argument("--min-regions-for-training", type=int, default=2)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = build_dataset(
        log_roots=args.log_root or list(DEFAULT_LOG_ROOTS),
        output_dir=args.output_dir,
        report=args.report,
        min_rows_for_training=max(1, int(args.min_rows_for_training)),
        min_positive_for_training=max(1, int(args.min_positive_for_training)),
        min_negative_for_training=max(1, int(args.min_negative_for_training)),
        min_instances_for_training=max(1, int(args.min_instances_for_training)),
        min_regions_for_training=max(1, int(args.min_regions_for_training)),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
