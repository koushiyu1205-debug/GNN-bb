#!/usr/bin/env python3
"""Summarize dynamic subset-row cut audit logs.

This helper is read-only. It inspects ``journey_cut_separation`` and
``journey_cut_added`` events and reports cut activity, top violated candidates,
and repeated task hubs. It does not run BPC/pricing/RMP and does not create
official bounds or certificates.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import date
import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_dynamic_src_audit_summary_20260628")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260628_bpc_future_journey_dynamic_src_audit_summary_zh.md"
)


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            yield payload


def _run_name_from_log(log_root: Path, path: Path) -> str:
    try:
        rel = path.relative_to(log_root)
    except ValueError:
        rel = path
    text = str(rel)
    if "/logs/" in text:
        return text.split("/logs/", 1)[0]
    parts = rel.parts
    if parts and parts[0] != "BPC_future":
        return parts[0]
    instance_name = path.name
    if instance_name.endswith(".jsonl"):
        instance_name = instance_name[: -len(".jsonl")]
    if instance_name.endswith(".json"):
        instance_name = instance_name[: -len(".json")]
    return f"{log_root.parent.name}::{instance_name}"


def summarize_dynamic_src(log_roots: list[Path], output_dir: Path, report: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    task_hub_counter: Counter[int] = Counter()
    route_region_task_hub_counter: Counter[int] = Counter()
    route_region_pair_hub_counter: Counter[tuple[int, int]] = Counter()
    run_task_counter: dict[str, Counter[int]] = defaultdict(Counter)
    run_route_region_task_counter: dict[str, Counter[int]] = defaultdict(Counter)
    run_route_region_pair_counter: dict[str, Counter[tuple[int, int]]] = defaultdict(Counter)
    run_rows: dict[str, dict[str, Any]] = {}

    for log_root in log_roots:
        paths = sorted(path for path in log_root.rglob("*.jsonl") if path.is_file())
        for path in paths:
            run_name = _run_name_from_log(log_root, path)
            bucket = run_rows.setdefault(
                run_name,
                {
                    "schema_version": "journey_dynamic_src_audit_run_v1",
                    "run": run_name,
                    "log_root": str(log_root),
                    "log_file_count": 0,
                    "separation_count": 0,
                    "cut_added_count": 0,
                    "total_generated": 0,
                    "total_route_region_guided_generated": 0,
                    "total_route_region_guided_violated": 0,
                    "total_violated": 0,
                    "total_added_from_separation": 0,
                    "max_best_violation": 0.0,
                    "max_active_cuts": 0,
                    "cut_gate_pass_count": 0,
                    "cut_gate_block_count": 0,
                    "route_region_event_count": 0,
                    "cut_dual_diagnostic_count": 0,
                    "cut_dual_nonzero_event_count": 0,
                    "max_nonzero_cut_dual_count": 0,
                    "max_subset_row_nonzero_dual_count": 0,
                    "max_binding_nonzero_cut_count": 0,
                    "max_cut_dual_abs_sum": 0.0,
                    "max_cut_dual_objective_abs_contribution": 0.0,
                    "top_cut_dual_rows": [],
                    "by_depth": {},
                    "top_candidates": [],
                },
            )
            bucket["log_file_count"] += 1
            for record in _iter_jsonl(path):
                event = record.get("event")
                if event == "journey_cut_added":
                    bucket["cut_added_count"] += 1
                    for task in record.get("tasks") or []:
                        task_int = int(task)
                        task_hub_counter[task_int] += 1
                        run_task_counter[run_name][task_int] += 1
                    continue
                if event == "journey_cut_dual_diagnostics":
                    nonzero = int(record.get("nonzero_cut_dual_count") or 0)
                    subset_nonzero = int(record.get("subset_row_nonzero_dual_count") or 0)
                    binding_nonzero = int(record.get("binding_nonzero_cut_count") or 0)
                    cut_abs_sum = float(record.get("cut_dual_abs_sum") or 0.0)
                    contribution = float(record.get("cut_dual_objective_contribution") or 0.0)
                    bucket["cut_dual_diagnostic_count"] += 1
                    if nonzero > 0:
                        bucket["cut_dual_nonzero_event_count"] += 1
                    bucket["max_nonzero_cut_dual_count"] = max(
                        int(bucket["max_nonzero_cut_dual_count"]),
                        nonzero,
                    )
                    bucket["max_subset_row_nonzero_dual_count"] = max(
                        int(bucket["max_subset_row_nonzero_dual_count"]),
                        subset_nonzero,
                    )
                    bucket["max_binding_nonzero_cut_count"] = max(
                        int(bucket["max_binding_nonzero_cut_count"]),
                        binding_nonzero,
                    )
                    bucket["max_cut_dual_abs_sum"] = max(
                        float(bucket["max_cut_dual_abs_sum"]),
                        cut_abs_sum,
                    )
                    bucket["max_cut_dual_objective_abs_contribution"] = max(
                        float(bucket["max_cut_dual_objective_abs_contribution"]),
                        abs(contribution),
                    )
                    for cut_row in record.get("top_cuts") or []:
                        abs_dual = float(cut_row.get("abs_dual") or 0.0)
                        if abs_dual <= 0.0:
                            continue
                        bucket["top_cut_dual_rows"].append(
                            {
                                "run": run_name,
                                "node_id": record.get("node_id"),
                                "depth": record.get("depth"),
                                "cg_iter": record.get("cg_iter"),
                                "cut_index": cut_row.get("cut_index"),
                                "kind": cut_row.get("kind"),
                                "tasks": cut_row.get("tasks"),
                                "k": cut_row.get("k"),
                                "rhs": cut_row.get("rhs"),
                                "activity": cut_row.get("activity"),
                                "sense_slack": cut_row.get("sense_slack"),
                                "dual": cut_row.get("dual"),
                                "abs_dual": abs_dual,
                                "binding": cut_row.get("binding"),
                            }
                        )
                    continue
                if event != "journey_cut_separation":
                    continue
                depth = int(record.get("depth") or 0)
                depth_key = str(depth)
                by_depth = bucket["by_depth"].setdefault(
                    depth_key,
                    {
                        "separation_count": 0,
                        "violated": 0,
                        "added": 0,
                        "max_best_violation": 0.0,
                    },
                )
                violated = int(record.get("violated") or 0)
                added = int(record.get("added") or 0)
                best_violation = float(record.get("best_violation") or 0.0)
                bucket["separation_count"] += 1
                bucket["total_generated"] += int(record.get("generated") or 0)
                bucket["total_route_region_guided_generated"] += int(
                    record.get("route_region_guided_generated") or 0
                )
                bucket["total_route_region_guided_violated"] += int(
                    record.get("route_region_guided_violated") or 0
                )
                bucket["total_violated"] += violated
                bucket["total_added_from_separation"] += added
                bucket["max_best_violation"] = max(float(bucket["max_best_violation"]), best_violation)
                bucket["max_active_cuts"] = max(int(bucket["max_active_cuts"]), int(record.get("active_cuts") or 0))
                if bool(record.get("cut_gate_enabled")):
                    if bool(record.get("cut_gate_passed")):
                        bucket["cut_gate_pass_count"] += 1
                    else:
                        bucket["cut_gate_block_count"] += 1
                if bool(record.get("route_region_audit_enabled", False)):
                    bucket["route_region_event_count"] += 1
                    for hub in record.get("route_region_top_task_hubs") or []:
                        task = int(hub.get("task"))
                        weight = float(hub.get("weighted_violation") or 0.0)
                        route_region_task_hub_counter[task] += weight
                        run_route_region_task_counter[run_name][task] += weight
                    for hub in record.get("route_region_top_pair_hubs") or []:
                        tasks = tuple(int(task) for task in hub.get("tasks") or [])
                        if len(tasks) != 2:
                            continue
                        pair = tuple(sorted(tasks))
                        weight = float(hub.get("weighted_violation") or 0.0)
                        route_region_pair_hub_counter[pair] += weight
                        run_route_region_pair_counter[run_name][pair] += weight
                by_depth["separation_count"] += 1
                by_depth["violated"] += violated
                by_depth["added"] += added
                by_depth["max_best_violation"] = max(float(by_depth["max_best_violation"]), best_violation)
                for rank, candidate in enumerate(record.get("top_candidates") or [], start=1):
                    tasks = tuple(int(task) for task in candidate.get("tasks") or [])
                    candidate_row = {
                        "schema_version": "journey_dynamic_src_candidate_v1",
                        "run": run_name,
                        "node_id": record.get("node_id"),
                        "depth": depth,
                        "cg_iter": record.get("cg_iter"),
                        "rank": rank,
                        "tasks": list(tasks),
                        "k": candidate.get("k"),
                        "rhs": candidate.get("rhs"),
                        "violation": candidate.get("violation"),
                        "compactness": candidate.get("compactness"),
                        "candidate_source": candidate.get("candidate_source"),
                        "activity": candidate.get("activity"),
                        "active_overlap_journey_count": candidate.get("active_overlap_journey_count"),
                        "active_overlap_task_set_count": candidate.get("active_overlap_task_set_count"),
                        "active_overlap_route_signature_count": candidate.get(
                            "active_overlap_route_signature_count"
                        ),
                        "active_overlap_max_value": candidate.get("active_overlap_max_value"),
                        "active_overlap_top_task_hubs": candidate.get("active_overlap_top_task_hubs"),
                        "active_overlap_top_task_sets": candidate.get("active_overlap_top_task_sets"),
                        "added_in_separation": added,
                        "cut_gate_passed": record.get("cut_gate_passed"),
                        "cut_gate_reason": record.get("cut_gate_reason"),
                    }
                    candidate_rows.append(candidate_row)
                    if len(bucket["top_candidates"]) < 20:
                        bucket["top_candidates"].append(candidate_row)
                    for task in tasks:
                        task_hub_counter[task] += 1
                        run_task_counter[run_name][task] += 1

    for run_name, row in sorted(run_rows.items()):
        hubs = run_task_counter[run_name].most_common(20)
        row["task_hubs"] = [{"task": int(task), "count": int(count)} for task, count in hubs]
        row["route_region_task_hubs"] = [
            {"task": int(task), "weighted_violation": round(float(weight), 9)}
            for task, weight in run_route_region_task_counter[run_name].most_common(20)
        ]
        row["route_region_pair_hubs"] = [
            {"tasks": list(pair), "weighted_violation": round(float(weight), 9)}
            for pair, weight in run_route_region_pair_counter[run_name].most_common(20)
        ]
        row["top_cut_dual_rows"] = sorted(
            row.get("top_cut_dual_rows") or [],
            key=lambda item: (-float(item.get("abs_dual") or 0.0), int(item.get("node_id") or 0), int(item.get("cg_iter") or 0)),
        )[:20]
        rows.append(row)

    summary = {
        "schema_version": "journey_dynamic_src_audit_summary_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "log_roots": [str(path) for path in log_roots],
        "run_count": len(rows),
        "candidate_row_count": len(candidate_rows),
        "cut_dual_diagnostic_count": sum(int(row.get("cut_dual_diagnostic_count") or 0) for row in rows),
        "cut_dual_nonzero_event_count": sum(int(row.get("cut_dual_nonzero_event_count") or 0) for row in rows),
        "max_nonzero_cut_dual_count": max((int(row.get("max_nonzero_cut_dual_count") or 0) for row in rows), default=0),
        "max_subset_row_nonzero_dual_count": max(
            (int(row.get("max_subset_row_nonzero_dual_count") or 0) for row in rows),
            default=0,
        ),
        "max_binding_nonzero_cut_count": max(
            (int(row.get("max_binding_nonzero_cut_count") or 0) for row in rows),
            default=0,
        ),
        "max_cut_dual_abs_sum": max((float(row.get("max_cut_dual_abs_sum") or 0.0) for row in rows), default=0.0),
        "max_cut_dual_objective_abs_contribution": max(
            (float(row.get("max_cut_dual_objective_abs_contribution") or 0.0) for row in rows),
            default=0.0,
        ),
        "global_task_hubs": [
            {"task": int(task), "count": int(count)}
            for task, count in task_hub_counter.most_common(30)
        ],
        "global_route_region_task_hubs": [
            {"task": int(task), "weighted_violation": round(float(weight), 9)}
            for task, weight in route_region_task_hub_counter.most_common(30)
        ],
        "global_route_region_pair_hubs": [
            {"tasks": list(pair), "weighted_violation": round(float(weight), 9)}
            for pair, weight in route_region_pair_hub_counter.most_common(30)
        ],
        "runs": rows,
    }
    write_outputs(summary, rows, candidate_rows, output_dir, report)
    return summary


def write_outputs(
    summary: dict[str, Any],
    rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    output_dir: Path,
    report: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "run_rows.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    (output_dir / "candidate_rows.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in candidate_rows),
        encoding="utf-8",
    )
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(_render_report(summary), encoding="utf-8")


def _render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Journey Dynamic SRC Audit Summary",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## Boundary",
        "",
        "This report summarizes existing dynamic SRC logs only. It does not run BPC / pricing / RMP and does not create official bounds or certificates.",
        "",
        "## Summary",
        "",
        "```text",
        f"run_count = {summary.get('run_count')}",
        f"candidate_row_count = {summary.get('candidate_row_count')}",
        f"cut_dual_diagnostic_count = {summary.get('cut_dual_diagnostic_count', 0)}",
        f"cut_dual_nonzero_event_count = {summary.get('cut_dual_nonzero_event_count', 0)}",
        f"max_nonzero_cut_dual_count = {summary.get('max_nonzero_cut_dual_count', 0)}",
        f"max_subset_row_nonzero_dual_count = {summary.get('max_subset_row_nonzero_dual_count', 0)}",
        f"max_binding_nonzero_cut_count = {summary.get('max_binding_nonzero_cut_count', 0)}",
        f"max_cut_dual_abs_sum = {summary.get('max_cut_dual_abs_sum', 0.0)}",
        f"global_task_hubs = {summary.get('global_task_hubs')[:10]}",
        f"global_route_region_task_hubs = {summary.get('global_route_region_task_hubs', [])[:10]}",
        f"global_route_region_pair_hubs = {summary.get('global_route_region_pair_hubs', [])[:10]}",
        "production_ready = false",
        "certificate_effect = false",
        "official_bound_effect = false",
        "```",
        "",
        "## Runs",
        "",
    ]
    for row in summary.get("runs", [])[:50]:
        lines.extend(
            [
                f"- `{row.get('run')}`",
                f"  separations={row.get('separation_count')}, violated={row.get('total_violated')}, added={row.get('cut_added_count')}, max_best_violation={row.get('max_best_violation')}, max_active_cuts={row.get('max_active_cuts')}",
                f"  route_region_guided generated/violated={row.get('total_route_region_guided_generated', 0)}/{row.get('total_route_region_guided_violated', 0)}",
                f"  cut_dual_diag nonzero_events={row.get('cut_dual_nonzero_event_count', 0)}/{row.get('cut_dual_diagnostic_count', 0)}, max_nonzero={row.get('max_nonzero_cut_dual_count', 0)}, max_subset_nonzero={row.get('max_subset_row_nonzero_dual_count', 0)}, max_binding_nonzero={row.get('max_binding_nonzero_cut_count', 0)}, max_abs_sum={row.get('max_cut_dual_abs_sum', 0.0)}",
                f"  gate pass/block={row.get('cut_gate_pass_count')}/{row.get('cut_gate_block_count')}",
                f"  task_hubs={row.get('task_hubs')[:8]}",
                f"  route_region_events={row.get('route_region_event_count')}, route_region_task_hubs={row.get('route_region_task_hubs', [])[:8]}",
            ]
        )
    return "\n".join(lines) + "\n"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log-root", type=Path, action="append", required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = summarize_dynamic_src(args.log_root, args.output_dir, args.report)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
