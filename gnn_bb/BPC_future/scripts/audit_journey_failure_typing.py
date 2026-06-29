#!/usr/bin/env python3
"""Classify Journey solver failures from existing audit artifacts.

The script is diagnostic-only. It merges batch results, tail-action audit,
completion-tail audit, and branch-impact audit outputs into per-instance
failure typing rows. It never runs BPC, pricing, or RMP.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_failure_typing_v474_20260627")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260627_bpc_future_journey_failure_typing_v474_zh.md"
)


ROW_FIELDS = [
    "instance",
    "short_name",
    "status",
    "wall_time",
    "capped_wall_time",
    "primary_failure_type",
    "failure_tags",
    "recommended_next_action",
    "branch_count",
    "root_branch_count",
    "max_branch_depth",
    "right_censored_branch_count",
    "unprocessed_child_count",
    "branch_completion_bound_tail_count",
    "branch_negative_chain_count",
    "branch_unprocessed_children_count",
    "child_exact_pricing_events",
    "child_negative_pricing_events",
    "child_completion_bound_retries",
    "child_fathom_events",
    "completion_retry_class",
    "completion_retry_count",
    "completion_retry_profile_generation_time",
    "completion_retry_generated_sequences",
    "completion_retry_negative_journeys",
    "completion_retry_selected_trips",
    "completion_retry_tail_min_fill_candidate_count",
    "completion_retry_tail_min_fill_applied_count",
    "tail_action_b_count",
    "tail_action_c_count",
    "tail_action_d_count",
    "tail_action_fathom_possible_count",
    "tail_action_last",
    "tail_action_last_reason",
    "tail_action_last_rmp_to_incumbent_gap",
    "tail_action_last_fathom_possible_if_rc_zero",
    "no_column_gate_count",
    "no_column_gate_disabled_count",
    "no_column_gate_d_count",
    "early_branch_trigger_count",
]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _iter_csv(path: Path) -> Iterable[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        yield from csv.DictReader(handle)


def _key_from_log_file(log_file: str) -> str:
    marker = "/logs/"
    text = str(log_file)
    if marker in text:
        text = text.split(marker, 1)[1]
    if text.endswith(".jsonl"):
        text = text[:-6]
    return text


def _key_from_instance(instance: str) -> str:
    return str(instance)


def _short_name(instance: str) -> str:
    return Path(instance).stem.replace("_logical_graph", "")


def _float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _load_results(path: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for row in _iter_csv(path):
        instance = row.get("instance", "")
        if not instance:
            continue
        key = _key_from_instance(instance)
        wall = _float(row.get("wall_time"), 600.0)
        rows[key] = {
            "instance": instance,
            "short_name": _short_name(instance),
            "status": row.get("status", ""),
            "wall_time": wall,
            "capped_wall_time": min(600.0, wall if wall > 0.0 else 600.0),
        }
    return rows


def _load_completion(path: Path) -> dict[str, dict[str, Any]]:
    summary = _read_json(path)
    rows: dict[str, dict[str, Any]] = {}
    for record in summary.get("records", []):
        key = _key_from_log_file(str(record.get("log_file", "")))
        rows[key] = {
            "completion_retry_class": record.get("completion_retry_class", ""),
            "completion_retry_count": _int(record.get("completion_retry_count")),
            "completion_retry_profile_generation_time": _float(
                record.get("completion_retry_total_profile_generation_time")
            ),
            "completion_retry_generated_sequences": _int(
                record.get("completion_retry_total_generated_sequences")
            ),
            "completion_retry_negative_journeys": _int(
                record.get("completion_retry_total_negative_journeys")
            ),
            "completion_retry_selected_trips": _int(
                record.get("completion_retry_total_selected_trips")
            ),
            "completion_retry_tail_min_fill_candidate_count": _int(
                record.get("completion_retry_tail_min_fill_candidate_count")
            ),
            "completion_retry_tail_min_fill_applied_count": _int(
                record.get("completion_retry_tail_min_fill_applied_count")
            ),
        }
    return rows


def _load_branch(path: Path) -> dict[str, dict[str, Any]]:
    summary = _read_json(path)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in summary.get("records", []):
        grouped[_key_from_log_file(str(record.get("log_file", "")))].append(record)

    rows: dict[str, dict[str, Any]] = {}
    for key, records in grouped.items():
        tail_counts = Counter(str(record.get("tail_class") or "") for record in records)
        rows[key] = {
            "branch_count": len(records),
            "root_branch_count": sum(1 for record in records if _int(record.get("depth")) == 0),
            "max_branch_depth": max((_int(record.get("depth")) for record in records), default=0),
            "right_censored_branch_count": sum(1 for record in records if bool(record.get("right_censored"))),
            "unprocessed_child_count": sum(_int(record.get("unprocessed_child_count")) for record in records),
            "branch_completion_bound_tail_count": tail_counts.get("completion_bound_tail", 0),
            "branch_negative_chain_count": tail_counts.get("negative_chain_continues", 0),
            "branch_unprocessed_children_count": tail_counts.get("unprocessed_children", 0),
            "child_exact_pricing_events": sum(
                _int(record.get("sum_child_exact_pricing_event_count")) for record in records
            ),
            "child_negative_pricing_events": sum(
                _int(record.get("sum_child_negative_pricing_event_count")) for record in records
            ),
            "child_completion_bound_retries": sum(
                _int(record.get("sum_child_completion_bound_retry_count")) for record in records
            ),
            "child_fathom_events": sum(
                _int(record.get("sum_child_fathom_event_count")) for record in records
            ),
        }
    return rows


def _load_tail_rows(tail_csv: Path, gate_csv: Path, early_branch_csv: Path) -> dict[str, dict[str, Any]]:
    grouped_tail: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in _iter_csv(tail_csv):
        grouped_tail[_key_from_log_file(row.get("log_file", ""))].append(row)

    grouped_gate: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in _iter_csv(gate_csv):
        grouped_gate[_key_from_log_file(row.get("log_file", ""))].append(row)

    grouped_trigger: dict[str, list[dict[str, Any]]] = defaultdict(list)
    if early_branch_csv.exists():
        for row in _iter_csv(early_branch_csv):
            grouped_trigger[_key_from_log_file(row.get("log_file", ""))].append(row)

    keys = set(grouped_tail) | set(grouped_gate) | set(grouped_trigger)
    rows: dict[str, dict[str, Any]] = {}
    for key in keys:
        tail_records = grouped_tail.get(key, [])
        gate_records = grouped_gate.get(key, [])
        class_counts = Counter(str(row.get("tail_action_class") or "") for row in tail_records)
        last = tail_records[-1] if tail_records else {}
        rows[key] = {
            "tail_action_b_count": class_counts.get("B_BROAD_PLATEAU", 0),
            "tail_action_c_count": class_counts.get("C_CONTINUE_CG", 0),
            "tail_action_d_count": class_counts.get("D_EARLY_BRANCH", 0),
            "tail_action_fathom_possible_count": sum(
                1 for row in tail_records if str(row.get("fathom_possible_if_rc_zero")) == "True"
            ),
            "tail_action_last": last.get("tail_action", ""),
            "tail_action_last_reason": last.get("tail_action_reason", ""),
            "tail_action_last_rmp_to_incumbent_gap": _float(last.get("rmp_to_incumbent_gap")),
            "tail_action_last_fathom_possible_if_rc_zero": str(
                last.get("fathom_possible_if_rc_zero", "")
            ),
            "no_column_gate_count": len(gate_records),
            "no_column_gate_disabled_count": sum(
                1 for row in gate_records if row.get("gate_reason") == "before_final_probe_disabled"
            ),
            "no_column_gate_d_count": sum(
                1 for row in gate_records if row.get("tail_action_class") == "D_EARLY_BRANCH"
            ),
            "early_branch_trigger_count": len(grouped_trigger.get(key, [])),
        }
    return rows


def _classify(row: dict[str, Any]) -> tuple[str, list[str], str]:
    if row["status"] == "OPTIMAL":
        return "solved_reference", ["solved"], "保持为对照样本，用于学习成功分支路径和 proof cost。"

    tags: list[str] = []
    branch_count = _int(row.get("branch_count"))
    max_depth = _int(row.get("max_branch_depth"))
    unprocessed = _int(row.get("unprocessed_child_count"))
    right_censored = _int(row.get("right_censored_branch_count"))
    completion_count = _int(row.get("completion_retry_count"))
    completion_time = _float(row.get("completion_retry_profile_generation_time"))
    completion_class = str(row.get("completion_retry_class") or "")
    child_retries = _int(row.get("child_completion_bound_retries"))
    child_negative = _int(row.get("child_negative_pricing_events"))
    d_count = _int(row.get("tail_action_d_count"))
    b_count = _int(row.get("tail_action_b_count"))
    c_count = _int(row.get("tail_action_c_count"))
    gap = _float(row.get("tail_action_last_rmp_to_incumbent_gap"))
    no_column_disabled = _int(row.get("no_column_gate_disabled_count"))

    if branch_count == 0:
        tags.append("root_no_branch")
    if right_censored > 0 or unprocessed > 0:
        tags.append("branch_tree_right_censored")
    if branch_count >= 8 or max_depth >= 4 or unprocessed >= 4:
        tags.append("branch_tree_too_wide_or_deep")
    if completion_count >= 10 or completion_time >= 120.0 or child_retries >= 30:
        tags.append("completion_bound_proof_cost")
    if "time_limit" in completion_class:
        tags.append("completion_bound_uncertified_time_limit")
    if child_negative >= 20 or c_count >= 10:
        tags.append("negative_chain_continues")
    if d_count >= 5 and gap > 1.0:
        tags.append("lp_bound_below_incumbent")
    if b_count >= 3:
        tags.append("broad_plateau_or_missing_refinement_target")
    if no_column_disabled > 0:
        tags.append("early_branch_before_final_probe_disabled")

    if "branch_tree_right_censored" in tags and "completion_bound_proof_cost" in tags:
        primary = "branch_tree_plus_completion_tail"
        action = "训练/约束深层 branch ordering，并降低 child proof-cost；root pair 继续盲测收益有限。"
    elif "branch_tree_right_censored" in tags:
        primary = "branch_tree_too_wide_or_deep"
        action = "补深层 branch replay 标签、child ordering 和宽度惩罚，不只学习 root pair。"
    elif "lp_bound_below_incumbent" in tags:
        primary = "lp_bound_below_incumbent"
        action = "需要 incumbent、cuts/formulation 或强分支提高 LP bound；pricing proof 本身不能剪枝。"
    elif "completion_bound_proof_cost" in tags or "completion_bound_uncertified_time_limit" in tags:
        primary = "completion_bound_proof_cost"
        action = "优化 completion-bound/final-probe tail，启用可验证的批量 harvest/cache/profile。"
    elif "negative_chain_continues" in tags:
        primary = "negative_chain_continues"
        action = "继续改善 CG/GAT pricing 顺序和 active-support 收口，避免重复弱负列。"
    elif "broad_plateau_or_missing_refinement_target" in tags:
        primary = "broad_plateau_or_refinement_gap"
        action = "只在 A 类节点做 Tier 1；宽平台转 aggregate bound/cuts/formulation。"
    else:
        primary = "unresolved_other"
        action = "需要更细日志或单实例 replay。"

    return primary, tags or ["untyped"], action


def build_rows(
    *,
    results_csv: Path,
    completion_summary: Path,
    branch_summary: Path,
    tail_action_dir: Path,
) -> list[dict[str, Any]]:
    results = _load_results(results_csv)
    completion = _load_completion(completion_summary)
    branch = _load_branch(branch_summary)
    tail = _load_tail_rows(
        tail_action_dir / "tail_action_rows.csv",
        tail_action_dir / "no_column_gate_rows.csv",
        tail_action_dir / "early_branch_trigger_rows.csv",
    )

    rows: list[dict[str, Any]] = []
    for key, result_row in sorted(results.items(), key=lambda item: item[0]):
        row: dict[str, Any] = dict(result_row)
        row.update(completion.get(key, {}))
        row.update(branch.get(key, {}))
        row.update(tail.get(key, {}))
        for field in ROW_FIELDS:
            row.setdefault(field, "")
        primary, tags, action = _classify(row)
        row["primary_failure_type"] = primary
        row["failure_tags"] = ";".join(tags)
        row["recommended_next_action"] = action
        rows.append(row)
    return rows


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    unsolved = [row for row in rows if row.get("status") != "OPTIMAL"]
    return {
        "schema_version": "journey_failure_typing_v1",
        "runs_bpc_or_pricing": False,
        "diagnostic_only": True,
        "official_bound_effect": False,
        "certificate_effect": False,
        "row_count": len(rows),
        "unsolved_count": len(unsolved),
        "status_counts": dict(Counter(str(row.get("status") or "") for row in rows)),
        "primary_failure_type_counts": dict(
            Counter(str(row.get("primary_failure_type") or "") for row in unsolved)
        ),
        "failure_tag_counts": dict(
            Counter(
                tag
                for row in unsolved
                for tag in str(row.get("failure_tags") or "").split(";")
                if tag
            )
        ),
        "unsolved_top_completion_cost": [
            {
                "short_name": row.get("short_name"),
                "status": row.get("status"),
                "completion_retry_count": row.get("completion_retry_count"),
                "completion_retry_profile_generation_time": row.get(
                    "completion_retry_profile_generation_time"
                ),
                "branch_count": row.get("branch_count"),
                "max_branch_depth": row.get("max_branch_depth"),
                "primary_failure_type": row.get("primary_failure_type"),
            }
            for row in sorted(
                unsolved,
                key=lambda item: _float(item.get("completion_retry_profile_generation_time")),
                reverse=True,
            )[:10]
        ],
        "unsolved_top_branch_tree": [
            {
                "short_name": row.get("short_name"),
                "status": row.get("status"),
                "branch_count": row.get("branch_count"),
                "right_censored_branch_count": row.get("right_censored_branch_count"),
                "unprocessed_child_count": row.get("unprocessed_child_count"),
                "max_branch_depth": row.get("max_branch_depth"),
                "primary_failure_type": row.get("primary_failure_type"),
            }
            for row in sorted(
                unsolved,
                key=lambda item: (
                    _int(item.get("right_censored_branch_count")),
                    _int(item.get("branch_count")),
                    _int(item.get("unprocessed_child_count")),
                ),
                reverse=True,
            )[:10]
        ],
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=ROW_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in ROW_FIELDS})


def _write_report(path: Path, summary: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    unsolved = [row for row in rows if row.get("status") != "OPTIMAL"]
    lines = [
        "# V474：V468 20 规模剩余失败分型",
        "",
        "本报告只读取已有日志和审计结果，不运行 BPC、pricing 或 RMP；不影响 official bound、certificate 或剪枝逻辑。",
        "",
        "## 总览",
        "",
        f"- 全量实例：{summary['row_count']}",
        f"- 未解实例：{summary['unsolved_count']}",
        f"- status 计数：`{summary['status_counts']}`",
        f"- primary failure type：`{summary['primary_failure_type_counts']}`",
        f"- failure tag：`{summary['failure_tag_counts']}`",
        "",
        "## 关键判断",
        "",
        "- 当前 27 个未解实例的主问题不是“root pair 正例不够”这一件事，而是 root/shallow 分支之后的深层分支树和 completion-bound proof cost 叠加。",
        "- V469 child-probe 高分但 V470 full replay 全超时，和这里的分型一致：局部 child corrected-bound/proof-cost proxy 不能直接代表完整闭环。",
        "- 后续 GAT branch score 应加入深层 branch、child ordering、completion retry/proof CPU 的反事实标签；单纯扩大 root top-k 会继续产生高分假阳性。",
        "",
        "## 未解实例分型",
        "",
        "| instance | status | primary | branch | depth | child CB retry | CB profile s | tags |",
        "|---|---:|---|---:|---:|---:|---:|---|",
    ]
    for row in unsolved:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("short_name", "")),
                    str(row.get("status", "")),
                    str(row.get("primary_failure_type", "")),
                    str(row.get("branch_count", "")),
                    str(row.get("max_branch_depth", "")),
                    str(row.get("child_completion_bound_retries", "")),
                    f"{_float(row.get('completion_retry_profile_generation_time')):.1f}",
                    str(row.get("failure_tags", "")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## 下一步",
            "",
            "1. 不把 V472/V473 直接放大全量；先补深层分支和 child-ordering 标签。",
            "2. 对 failure type 为 `branch_tree_plus_completion_tail` 的实例，生成 depth 1-4 的 limited replay/runbook，而不是继续 root top-k。",
            "3. 对 `completion_bound_proof_cost` 高的实例，单独做 final-probe/CB-tail profile 和 min-fill/cache/harvest 的精确安全优化。",
            "4. 对 `lp_bound_below_incumbent` 或宽平台节点，转 incumbent/cuts/formulation，不把更多 pricing proof 误当作可剪枝能力。",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-csv", required=True, type=Path)
    parser.add_argument("--completion-summary", required=True, type=Path)
    parser.add_argument("--branch-summary", required=True, type=Path)
    parser.add_argument("--tail-action-dir", required=True, type=Path)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, type=Path)
    parser.add_argument("--report", default=DEFAULT_REPORT, type=Path)
    args = parser.parse_args()

    rows = build_rows(
        results_csv=args.results_csv,
        completion_summary=args.completion_summary,
        branch_summary=args.branch_summary,
        tail_action_dir=args.tail_action_dir,
    )
    summary = _summary(rows)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(args.output_dir / "failure_typing_rows.csv", rows)
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(args.report, summary, rows)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
