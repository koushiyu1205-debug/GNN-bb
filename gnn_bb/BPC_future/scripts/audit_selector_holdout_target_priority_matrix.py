#!/usr/bin/env python3
"""Rank selector holdout contexts that should be recollected next.

The selector gap matrix proves that the remaining blocker is not field
availability alone, but sparse negative/noop and mixed-context coverage under
the full-snapshot schema.  This diagnostic-only script turns that blocker into
a concrete target matrix.  It reads existing candidate-impact CSV files and
collection manifests; it does not run BPC, pricing, RMP, Pulse, replay, workers,
or benchmarks.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_CSV_GLOB = "BPC_future/results/**/*candidate*impact*rows.csv"
DEFAULT_GAP_MATRIX = Path(
    "BPC_future/results/root_cause_selector_holdout_gap_matrix_20260614/"
    "summary.json"
)
DEFAULT_COLLECTION_MANIFEST = Path(
    "BPC_future/results/root_cause_selector_holdout_collection_manifest_20260614/"
    "summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_holdout_target_priority_matrix_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_holdout_target_priority_matrix_zh.md"
)
BASE_SELECTOR_DATASET = (
    "root_cause_counterfactual_replay_impact_dataset_20260613/combined/"
    "combined_candidate_impact_rows.csv"
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _float_or_none(value: Any) -> float | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _source_class(path: str) -> str:
    if path.endswith(BASE_SELECTOR_DATASET):
        return "base_replay_selector"
    if "root_cause_component_payload_addition_before_rows" in path:
        return "component_payload_addition_before"
    if "root_cause_active_basis_snapshot" in path:
        return "active_basis_snapshot_smoke"
    if "counterfactual_replay" in path or "counterfactual_target" in path:
        return "counterfactual_replay_dataset"
    return "other"


def _read_rows(csv_glob: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(Path().glob(csv_glob)):
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("single_impact_class") not in {"improved", "noop"}:
                    continue
                context_hash = str(row.get("context_hash", "")).strip()
                if not context_hash:
                    continue
                copied = dict(row)
                copied["_source_csv"] = str(path)
                copied["_source_class"] = _source_class(str(path))
                rows.append(copied)
    return rows


def _label_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    return dict(Counter(row.get("single_impact_class", "") for row in rows))


def _complete_snapshot(row: dict[str, str]) -> bool:
    return _truthy(row.get("active_basis_snapshot_complete_before"))


def _explicit_forbidden(row: dict[str, str]) -> bool:
    return _truthy(row.get("explicit_forbidden_signature_list_available"))


def _row_sample(row: dict[str, str]) -> dict[str, Any]:
    return {
        "candidate_id": row.get("candidate_id"),
        "case_id": row.get("case_id"),
        "cg_iter": row.get("cg_iter"),
        "instance": row.get("instance"),
        "sequence": row.get("sequence"),
        "task_set": row.get("task_set"),
        "true_reduced_cost": _float_or_none(row.get("true_reduced_cost")),
        "single_impact_class": row.get("single_impact_class"),
        "single_objective_delta": _float_or_none(row.get("single_objective_delta")),
        "active_basis_snapshot_complete_before": _complete_snapshot(row),
        "explicit_forbidden_signature_list_available": _explicit_forbidden(row),
        "source_class": row.get("_source_class"),
        "source_csv": row.get("_source_csv"),
        "source_file": row.get("source_file"),
    }


def _manifest_contexts(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    contexts: dict[str, dict[str, Any]] = {}
    for target in manifest.get("targets", []) or []:
        context_hash = str(target.get("context_hash", "")).strip()
        if context_hash:
            contexts[context_hash] = {
                "collection_target_id": target.get("collection_target_id"),
                "failure_kind": target.get("failure_kind"),
                "candidate_row_count": target.get("candidate_row_count"),
                "candidate_label_counts": target.get("candidate_label_counts"),
                "needs_active_basis_snapshot_capture": target.get(
                    "needs_active_basis_snapshot_capture"
                ),
            }
    return contexts


def _summarize_context(
    context_hash: str,
    rows: list[dict[str, str]],
    manifest_contexts: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    labels = _label_counts(rows)
    complete_rows = [row for row in rows if _complete_snapshot(row)]
    explicit_rows = [row for row in rows if _explicit_forbidden(row)]
    complete_explicit_rows = [
        row for row in rows if _complete_snapshot(row) and _explicit_forbidden(row)
    ]
    instances = Counter(row.get("instance", "") for row in rows if row.get("instance"))
    source_classes = Counter(row.get("_source_class", "") for row in rows)
    source_csvs = sorted({row.get("_source_csv", "") for row in rows})
    true_rc_values = [
        value
        for value in (_float_or_none(row.get("true_reduced_cost")) for row in rows)
        if value is not None
    ]
    objective_deltas = [
        value
        for value in (_float_or_none(row.get("single_objective_delta")) for row in rows)
        if value is not None
    ]
    is_mixed = labels.get("improved", 0) > 0 and labels.get("noop", 0) > 0
    has_noop = labels.get("noop", 0) > 0
    has_improved = labels.get("improved", 0) > 0
    complete_labels = _label_counts(complete_rows)
    explicit_labels = _label_counts(explicit_rows)
    complete_explicit_labels = _label_counts(complete_explicit_rows)
    missing_full_snapshot = len(complete_rows) == 0
    missing_explicit_forbidden = len(explicit_rows) == 0

    gap_tags: list[str] = []
    score = 0
    if is_mixed and missing_full_snapshot:
        gap_tags.append("mixed_missing_full_snapshot")
        score += 120
    if is_mixed and not (
        complete_labels.get("improved", 0) > 0 and complete_labels.get("noop", 0) > 0
    ):
        gap_tags.append("mixed_context_not_represented_as_complete_mixed")
        score += 80
    if has_noop and missing_full_snapshot:
        gap_tags.append("noop_missing_full_snapshot")
        score += 70
    if has_noop and missing_explicit_forbidden:
        gap_tags.append("noop_missing_explicit_forbidden")
        score += 55
    if has_improved and missing_full_snapshot:
        gap_tags.append("positive_missing_full_snapshot")
        score += 30
    if complete_explicit_labels == {"improved": len(complete_explicit_rows)} and (
        len(complete_explicit_rows) > 0
    ):
        gap_tags.append("complete_explicit_positive_only")
    if context_hash in manifest_contexts:
        gap_tags.append("existing_collection_manifest_target")
        score += 20

    score += min(len(rows), 50)
    score += min(len(source_csvs), 5) * 3
    score += min(len(instances), 3) * 2

    return {
        "context_hash": context_hash,
        "priority_score": score,
        "gap_tags": gap_tags,
        "row_count": len(rows),
        "label_counts": labels,
        "complete_snapshot_row_count": len(complete_rows),
        "complete_snapshot_label_counts": complete_labels,
        "explicit_forbidden_row_count": len(explicit_rows),
        "explicit_forbidden_label_counts": explicit_labels,
        "complete_explicit_forbidden_row_count": len(complete_explicit_rows),
        "complete_explicit_forbidden_label_counts": complete_explicit_labels,
        "manifest_target": manifest_contexts.get(context_hash),
        "instance_counts": dict(instances),
        "source_class_counts": dict(source_classes),
        "source_csv_count": len(source_csvs),
        "true_rc_min": min(true_rc_values) if true_rc_values else None,
        "true_rc_max": max(true_rc_values) if true_rc_values else None,
        "objective_delta_min": min(objective_deltas) if objective_deltas else None,
        "objective_delta_max": max(objective_deltas) if objective_deltas else None,
        "sample_rows": [_row_sample(row) for row in rows[:5]],
    }


def _count_tag(targets: list[dict[str, Any]], tag: str) -> int:
    return sum(1 for target in targets if tag in target.get("gap_tags", []))


def audit(
    *,
    csv_glob: str,
    gap_matrix_path: Path,
    collection_manifest_path: Path,
) -> dict[str, Any]:
    gap_matrix = _read_json(gap_matrix_path)
    collection_manifest = _read_json(collection_manifest_path)
    manifest_contexts = _manifest_contexts(collection_manifest)
    rows = _read_rows(csv_glob)

    by_context: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_context[row["context_hash"]].append(row)

    context_targets = [
        _summarize_context(context_hash, context_rows, manifest_contexts)
        for context_hash, context_rows in sorted(by_context.items())
    ]
    context_targets.sort(
        key=lambda item: (
            int(item["priority_score"]),
            int(item["row_count"]),
            str(item["context_hash"]),
        ),
        reverse=True,
    )

    priority_targets = [
        target
        for target in context_targets
        if any(
            tag in target["gap_tags"]
            for tag in [
                "mixed_missing_full_snapshot",
                "noop_missing_full_snapshot",
                "noop_missing_explicit_forbidden",
            ]
        )
    ]
    top_priority_targets = priority_targets[:12]
    manifest_context_set = set(manifest_contexts)
    priority_context_set = {target["context_hash"] for target in priority_targets}
    uncovered_priority_contexts = sorted(priority_context_set - manifest_context_set)

    category_counts = {
        "mixed_missing_full_snapshot": _count_tag(
            context_targets, "mixed_missing_full_snapshot"
        ),
        "mixed_context_not_represented_as_complete_mixed": _count_tag(
            context_targets, "mixed_context_not_represented_as_complete_mixed"
        ),
        "noop_missing_full_snapshot": _count_tag(
            context_targets, "noop_missing_full_snapshot"
        ),
        "noop_missing_explicit_forbidden": _count_tag(
            context_targets, "noop_missing_explicit_forbidden"
        ),
        "positive_missing_full_snapshot": _count_tag(
            context_targets, "positive_missing_full_snapshot"
        ),
        "existing_collection_manifest_target": _count_tag(
            context_targets, "existing_collection_manifest_target"
        ),
    }
    checks = {
        "candidate_rows_present": len(rows) >= 630,
        "gap_matrix_passed": gap_matrix.get("all_checks_pass") is True,
        "gap_matrix_recommends_negative_mixed": (
            gap_matrix.get("recommended_next_stage")
            == "collect_negative_and_mixed_full_snapshot_contexts"
        ),
        "collection_manifest_passed": (
            collection_manifest.get("all_checks_pass") is True
        ),
        "mixed_missing_full_snapshot_contexts_present": (
            category_counts["mixed_missing_full_snapshot"] >= 7
        ),
        "noop_missing_full_snapshot_contexts_present": (
            category_counts["noop_missing_full_snapshot"] >= 1
        ),
        "priority_targets_have_samples": all(
            target.get("sample_rows") for target in top_priority_targets
        ),
        "manifest_covers_some_priority_contexts": bool(
            priority_context_set & manifest_context_set
        ),
        "uncovered_priority_contexts_identified": bool(uncovered_priority_contexts),
        "diagnostic_not_solver_run": True,
    }

    return {
        "schema_version": "selector_holdout_target_priority_matrix_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "selector_holdout_target_priority_matrix_audited",
        "csv_glob": csv_glob,
        "total_candidate_row_count": len(rows),
        "context_count": len(context_targets),
        "priority_context_count": len(priority_targets),
        "category_counts": category_counts,
        "manifest_context_count": len(manifest_context_set),
        "manifest_priority_context_overlap_count": len(
            priority_context_set & manifest_context_set
        ),
        "uncovered_priority_context_count": len(uncovered_priority_contexts),
        "uncovered_priority_contexts": uncovered_priority_contexts[:20],
        "top_priority_targets": top_priority_targets,
        "recommended_next_stage": "collect_priority_negative_noop_mixed_full_snapshot_contexts",
        "forbidden_next_actions": [
            "production_bpc_ab_before_selector_holdout",
            "default_worker_or_audit_enable",
            "official_certificate_gate",
            "treat_positive_only_payload_rows_as_selector",
        ],
        "sources": {
            "gap_matrix": str(gap_matrix_path),
            "collection_manifest": str(collection_manifest_path),
        },
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "现有候选行已经能定位下一批补采目标：优先补 mixed/noop contexts "
            "的 complete full-snapshot 与 explicit-forbidden payload。已有 "
            "collection manifest 只覆盖一部分高优先 context，仍有 priority "
            "contexts 未覆盖；因此下一步应补采这些 target，而不是进入 production "
            "A/B、默认 worker 或 certificate gate。"
        ),
    }


def write_report(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# Selector Holdout Target Priority Matrix 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告把 selector holdout gap 转成下一批补采优先 context。它只读",
        "已有 CSV / summary，不运行 BPC / pricing / RMP / Pulse。",
        "",
        "## 机器字段",
        "",
        "```text",
        "selector_holdout_target_priority_matrix = current",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"status = {summary['status']}",
        f"total_candidate_row_count = {summary['total_candidate_row_count']}",
        f"context_count = {summary['context_count']}",
        f"priority_context_count = {summary['priority_context_count']}",
        "mixed_missing_full_snapshot_context_count = "
        f"{summary['category_counts']['mixed_missing_full_snapshot']}",
        "noop_missing_full_snapshot_context_count = "
        f"{summary['category_counts']['noop_missing_full_snapshot']}",
        f"manifest_priority_context_overlap_count = {summary['manifest_priority_context_overlap_count']}",
        f"uncovered_priority_context_count = {summary['uncovered_priority_context_count']}",
        f"recommended_next_stage = {summary['recommended_next_stage']}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 结论",
        "",
        summary["interpretation"],
        "",
        "## Category counts",
        "",
        "```json",
        json.dumps(summary["category_counts"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Top priority targets",
        "",
        "```json",
        json.dumps(
            summary["top_priority_targets"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## Uncovered priority contexts",
        "",
        "```json",
        json.dumps(
            summary["uncovered_priority_contexts"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## Checks",
        "",
        "```json",
        json.dumps(summary["checks"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv-glob", default=DEFAULT_CSV_GLOB)
    parser.add_argument("--gap-matrix", default=str(DEFAULT_GAP_MATRIX))
    parser.add_argument(
        "--collection-manifest", default=str(DEFAULT_COLLECTION_MANIFEST)
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    summary = audit(
        csv_glob=str(args.csv_glob),
        gap_matrix_path=Path(args.gap_matrix),
        collection_manifest_path=Path(args.collection_manifest),
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_report(summary, args.report)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
