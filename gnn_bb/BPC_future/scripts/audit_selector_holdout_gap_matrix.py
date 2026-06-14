#!/usr/bin/env python3
"""Audit the remaining selector holdout data gaps.

This diagnostic-only script scans existing candidate-impact CSV files and
answers a narrow question: which label/schema/context combinations are still
missing before an addition-before selector can be treated as production
candidate material.  It does not run BPC, pricing, RMP, Pulse, workers, replay,
or benchmarks.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_holdout_gap_matrix_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_holdout_gap_matrix_zh.md"
)
DEFAULT_GLOB = "BPC_future/results/**/*candidate*impact*rows.csv"
BASE_SELECTOR_DATASET = (
    "root_cause_counterfactual_replay_impact_dataset_20260613/combined/"
    "combined_candidate_impact_rows.csv"
)


def _truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _read_rows(paths: list[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in paths:
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("single_impact_class") not in {"improved", "noop"}:
                    continue
                copied = dict(row)
                copied["_source_csv"] = str(path)
                copied["_source_class"] = _source_class(str(path))
                rows.append(copied)
    return rows


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


def _label_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    return dict(Counter(row.get("single_impact_class", "") for row in rows))


def _count_nonempty(rows: list[dict[str, str]], field: str) -> int:
    return sum(1 for row in rows if str(row.get(field, "")).strip())


def _complete_snapshot(row: dict[str, str]) -> bool:
    return _truthy(row.get("active_basis_snapshot_complete_before"))


def _explicit_forbidden(row: dict[str, str]) -> bool:
    return _truthy(row.get("explicit_forbidden_signature_list_available"))


def _summary_for_rows(rows: list[dict[str, str]]) -> dict[str, Any]:
    contexts = {row.get("context_hash", "") for row in rows if row.get("context_hash")}
    instances = {row.get("instance", "") for row in rows if row.get("instance")}
    datasets = {row.get("_source_csv", "") for row in rows if row.get("_source_csv")}
    complete_rows = [row for row in rows if _complete_snapshot(row)]
    explicit_rows = [row for row in rows if _explicit_forbidden(row)]
    complete_and_explicit = [
        row for row in rows if _complete_snapshot(row) and _explicit_forbidden(row)
    ]
    return {
        "row_count": len(rows),
        "label_counts": _label_counts(rows),
        "context_count": len(contexts),
        "instance_count": len(instances),
        "dataset_count": len(datasets),
        "complete_snapshot_row_count": len(complete_rows),
        "explicit_forbidden_row_count": len(explicit_rows),
        "complete_snapshot_and_explicit_forbidden_row_count": len(
            complete_and_explicit
        ),
        "complete_snapshot_label_counts": _label_counts(complete_rows),
        "explicit_forbidden_label_counts": _label_counts(explicit_rows),
        "complete_snapshot_and_explicit_forbidden_label_counts": _label_counts(
            complete_and_explicit
        ),
        "active_basis_churn_nonempty_count": _count_nonempty(
            rows, "active_basis_churn_count_before"
        ),
        "rmp_degeneracy_pressure_nonempty_count": _count_nonempty(
            rows, "rmp_degeneracy_pressure_before"
        ),
    }


def _context_label_mix(rows: list[dict[str, str]]) -> dict[str, Any]:
    by_context: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        context_hash = str(row.get("context_hash", "")).strip()
        if context_hash:
            by_context[context_hash].append(row)
    mixed: list[dict[str, Any]] = []
    positive_only = 0
    noop_only = 0
    for context_hash, items in sorted(by_context.items()):
        labels = _label_counts(items)
        if labels.get("improved", 0) and labels.get("noop", 0):
            mixed.append(
                {
                    "context_hash": context_hash,
                    "row_count": len(items),
                    "label_counts": labels,
                    "source_classes": dict(
                        Counter(item.get("_source_class", "") for item in items)
                    ),
                }
            )
        elif labels.get("improved", 0):
            positive_only += 1
        elif labels.get("noop", 0):
            noop_only += 1
    return {
        "context_count": len(by_context),
        "mixed_label_context_count": len(mixed),
        "positive_only_context_count": positive_only,
        "noop_only_context_count": noop_only,
        "mixed_label_context_samples": mixed[:10],
    }


def audit(*, csv_glob: str) -> dict[str, Any]:
    paths = sorted(Path().glob(csv_glob))
    rows = _read_rows(paths)
    by_source: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_source[row["_source_class"]].append(row)

    base_rows = by_source.get("base_replay_selector", [])
    component_rows = by_source.get("component_payload_addition_before", [])
    active_snapshot_rows = by_source.get("active_basis_snapshot_smoke", [])
    complete_rows = [row for row in rows if _complete_snapshot(row)]
    complete_explicit_rows = [
        row for row in rows if _complete_snapshot(row) and _explicit_forbidden(row)
    ]
    selector_ready_proxy_rows = [
        row
        for row in rows
        if _complete_snapshot(row)
        and str(row.get("context_hash", "")).strip()
        and str(row.get("instance", "")).strip()
    ]

    source_summaries = {
        source: _summary_for_rows(source_rows)
        for source, source_rows in sorted(by_source.items())
    }
    complete_context_mix = _context_label_mix(complete_rows)
    complete_explicit_context_mix = _context_label_mix(complete_explicit_rows)
    selector_ready_proxy_context_mix = _context_label_mix(selector_ready_proxy_rows)

    gap_items = [
        {
            "gap_id": "base_selector_rows_have_no_full_snapshot",
            "status": "blocking",
            "evidence": {
                "base_row_count": len(base_rows),
                "base_complete_snapshot_row_count": sum(
                    1 for row in base_rows if _complete_snapshot(row)
                ),
            },
            "required_next_evidence": (
                "重新采集或重放 no-certificate-effect selector rows，必须带完整"
                " active-basis snapshot 和加列前 RMP trajectory 字段。"
            ),
        },
        {
            "gap_id": "component_payload_rows_are_positive_only",
            "status": "blocking",
            "evidence": {
                "component_row_count": len(component_rows),
                "component_label_counts": _label_counts(component_rows),
                "component_complete_explicit_label_counts": _label_counts(
                    [
                        row
                        for row in component_rows
                        if _complete_snapshot(row) and _explicit_forbidden(row)
                    ]
                ),
            },
            "required_next_evidence": (
                "采集同类 component payload 下的 noop / false-positive / "
                "low-impact rows；否则只能校准正例，不能训练生产 selector。"
            ),
        },
        {
            "gap_id": "complete_snapshot_rows_label_mix_too_sparse",
            "status": "blocking",
            "evidence": {
                "complete_snapshot_row_count": len(complete_rows),
                "complete_snapshot_label_counts": _label_counts(complete_rows),
                "complete_snapshot_context_mix": complete_context_mix,
            },
            "required_next_evidence": (
                "补充 full-snapshot improved/noop mixed contexts；不能只增加"
                " positive rows 或单类 context。"
            ),
        },
        {
            "gap_id": "complete_explicit_forbidden_rows_have_no_negative_label",
            "status": "blocking",
            "evidence": {
                "complete_explicit_row_count": len(complete_explicit_rows),
                "complete_explicit_label_counts": _label_counts(
                    complete_explicit_rows
                ),
                "complete_explicit_context_mix": complete_explicit_context_mix,
            },
            "required_next_evidence": (
                "需要 explicit forbidden/pool payload 同时覆盖 improved 和 noop；"
                "否则 forbidden pressure 只能解释正例，不能学习拒绝条件。"
            ),
        },
        {
            "gap_id": "production_ab_still_requires_selector_and_5_10_20_gates",
            "status": "blocking",
            "evidence": {
                "selector_ready_proxy_row_count": len(selector_ready_proxy_rows),
                "selector_ready_proxy_context_mix": selector_ready_proxy_context_mix,
            },
            "required_next_evidence": (
                "selector 通过 context/instance/dataset holdout 后，仍必须先跑"
                " 5/10 full no-regression，再跑 selected 20 hard-repeat speedup。"
            ),
        },
    ]

    checks = {
        "candidate_rows_exist": len(rows) > 0,
        "base_selector_rows_present": len(base_rows) == 280,
        "component_rows_present": len(component_rows) == 48,
        "active_snapshot_rows_present": len(active_snapshot_rows) >= 14,
        "base_rows_have_no_full_snapshot": (
            sum(1 for row in base_rows if _complete_snapshot(row)) == 0
        ),
        "component_rows_positive_only": _label_counts(component_rows)
        == {"improved": 48},
        "component_rows_complete_and_explicit": (
            sum(
                1
                for row in component_rows
                if _complete_snapshot(row) and _explicit_forbidden(row)
            )
            == 48
        ),
        "complete_snapshot_rows_have_sparse_noops": (
            _label_counts(complete_rows).get("noop", 0) == 3
            and _label_counts(complete_rows).get("improved", 0) == 59
        ),
        "complete_explicit_rows_positive_only": _label_counts(
            complete_explicit_rows
        )
        == {"improved": 48},
        "has_blocking_gap_items": all(
            item["status"] == "blocking" for item in gap_items
        ),
        "diagnostic_not_solver_run": True,
    }
    return {
        "schema_version": "selector_holdout_gap_matrix_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "selector_holdout_gap_matrix_audited",
        "csv_glob": csv_glob,
        "csv_path_count": len(paths),
        "total_candidate_row_count": len(rows),
        "source_summaries": source_summaries,
        "complete_snapshot_total": _summary_for_rows(complete_rows),
        "complete_explicit_forbidden_total": _summary_for_rows(
            complete_explicit_rows
        ),
        "selector_ready_proxy_total": _summary_for_rows(selector_ready_proxy_rows),
        "complete_snapshot_context_label_mix": complete_context_mix,
        "complete_explicit_forbidden_context_label_mix": complete_explicit_context_mix,
        "selector_ready_proxy_context_label_mix": selector_ready_proxy_context_mix,
        "gap_items": gap_items,
        "recommended_next_stage": "collect_negative_and_mixed_full_snapshot_contexts",
        "forbidden_next_actions": [
            "production_bpc_ab_before_selector_holdout",
            "default_worker_or_audit_enable",
            "official_certificate_gate",
            "treat_component_payload_positive_rows_as_selector",
        ],
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "当前缺口已经不是字段完全不可得：component payload rows 具备完整"
            " active-basis 和 explicit forbidden payload。但这些 48 行全是 improved，"
            "complete explicit forbidden rows 也全是 improved；base 280 行又没有完整"
            " full-snapshot。因此 production selector 的剩余缺口是负例/混合 context "
            "与 full-snapshot schema 的交叉覆盖不足。"
        ),
    }


def write_report(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# Selector Holdout Gap Matrix 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告扫描现有 candidate impact CSV，量化 addition-before selector",
        "仍缺哪些 label/schema/context 组合。它不运行 BPC / pricing / RMP / Pulse。",
        "",
        "## 机器字段",
        "",
        "```text",
        "selector_holdout_gap_matrix = current",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"status = {summary['status']}",
        f"total_candidate_row_count = {summary['total_candidate_row_count']}",
        f"complete_snapshot_row_count = {summary['complete_snapshot_total']['row_count']}",
        "complete_snapshot_label_counts = "
        f"{summary['complete_snapshot_total']['label_counts']}",
        "complete_explicit_forbidden_row_count = "
        f"{summary['complete_explicit_forbidden_total']['row_count']}",
        "complete_explicit_forbidden_label_counts = "
        f"{summary['complete_explicit_forbidden_total']['label_counts']}",
        f"recommended_next_stage = {summary['recommended_next_stage']}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 结论",
        "",
        summary["interpretation"],
        "",
        "## Source summaries",
        "",
        "```json",
        json.dumps(
            summary["source_summaries"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## Gap items",
        "",
        "```json",
        json.dumps(
            summary["gap_items"],
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
    parser.add_argument("--csv-glob", default=DEFAULT_GLOB)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    summary = audit(csv_glob=str(args.csv_glob))
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
