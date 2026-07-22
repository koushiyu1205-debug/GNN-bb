#!/usr/bin/env python3
"""Run read-only Live SRI separation over frozen no-cut tree snapshots."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from lunar_ice_bpc.exact.bpc.cuts.live_sri import separate_live_sri


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    baseline_dir = args.baseline_dir.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    snapshots = sorted(
        path
        for scale in (20, 30)
        for path in (baseline_dir / "rows" / f"scale_{scale:03d}").glob(
            "**/tree_closure_results/tree_closure_001.json"
        )
    )
    rows: list[dict] = []
    for path in snapshots:
        tree = json.loads(path.read_text(encoding="utf-8"))
        scale = int(tree["task_count"])
        for node in tree.get("nodes", []) or []:
            depth = int(node.get("depth") or 0)
            primal = tuple(node.get("primal_columns", []) or [])
            task_ids = tuple(
                sorted(
                    {
                        str(task_id)
                        for primal_row in primal
                        for task_id in primal_row.get("tasks", []) or []
                    }
                )
            )
            if len(task_ids) != scale or not primal:
                rows.append(
                    {
                        "scale": scale,
                        "instance_id": tree.get("instance_id"),
                        "node_id": node.get("node_id"),
                        "depth": depth,
                        "snapshot_kind": "root" if depth == 0 else "branch",
                        "evaluable": False,
                        "reason": "serialized_primal_does_not_cover_all_tasks",
                    }
                )
                continue
            subset_sizes = (3, 5) if depth == 0 else (3,)
            result = separate_live_sri(
                task_ids,
                primal,
                subset_sizes=subset_sizes,
                selection_capacity=16,
            )
            payload = result.to_payload()
            support = [
                int(candidate["support_column_count"])
                for candidate in payload["selected"]
            ]
            rows.append(
                {
                    "scale": scale,
                    "instance_id": tree.get("instance_id"),
                    "node_id": node.get("node_id"),
                    "depth": depth,
                    "snapshot_kind": "root" if depth == 0 else "branch",
                    "node_status": node.get("node_status"),
                    "primal_integral": bool(node.get("primal_integral")),
                    "evaluable": True,
                    "subset_sizes": list(subset_sizes),
                    "primal_column_count": len(primal),
                    "enumerated_candidate_count": result.enumerated_candidate_count,
                    "full_enumeration_completed": result.full_enumeration_completed,
                    "violated_candidate_count": result.violated_candidate_count,
                    "selected_candidate_count": len(result.selected),
                    "unselected_violated_count": result.unselected_violated_count,
                    "max_violation": result.max_violation,
                    "max_selected_support": max(support, default=0),
                    "selected": payload["selected"],
                    "restricted_rmp_bound_movement": None,
                    "restricted_rmp_bound_movement_evaluable": False,
                    "restricted_rmp_bound_movement_reason": (
                        "Frozen tree JSON retains primal lambdas but not every active JourneyColumn object; "
                        "the diagnostic is separation-only and does not mutate or re-solve the frozen RMP."
                    ),
                    "source_tree_json": str(path.relative_to(baseline_dir)),
                }
            )

    summary = build_summary(rows, baseline_dir=baseline_dir)
    (output_dir / "readiness_rows.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "readiness_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_csv(output_dir / "readiness_rows.csv", rows)
    (output_dir / "readiness_report_zh.md").write_text(
        render_report(summary),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def build_summary(rows: list[dict], *, baseline_dir: Path) -> dict:
    by_scale: dict[str, dict] = {}
    for scale in (20, 30):
        scale_rows = [row for row in rows if row.get("scale") == scale and row.get("evaluable")]
        root_rows = [row for row in scale_rows if row["snapshot_kind"] == "root"]
        branch_rows = [
            row
            for row in scale_rows
            if row["snapshot_kind"] == "branch" and not row.get("primal_integral")
        ]
        violated_branches = [row for row in branch_rows if row["violated_candidate_count"] > 0]
        violated_branch_instances = sorted(
            {str(row["instance_id"]) for row in violated_branches}
        )
        by_scale[str(scale)] = {
            "root_snapshot_count": len(root_rows),
            "root_full_enumeration_count": sum(
                bool(row["full_enumeration_completed"]) for row in root_rows
            ),
            "root_with_violated_sri_count": sum(
                row["violated_candidate_count"] > 0 for row in root_rows
            ),
            "root_total_violated_candidate_count": sum(
                int(row["violated_candidate_count"]) for row in root_rows
            ),
            "root_max_violation": max(
                (float(row["max_violation"]) for row in root_rows if row["max_violation"] is not None),
                default=None,
            ),
            "fractional_branch_snapshot_count": len(branch_rows),
            "fractional_branch_with_violated_sri_count": len(violated_branches),
            "fractional_branch_violation_rate": (
                len(violated_branches) / len(branch_rows) if branch_rows else 0.0
            ),
            "branch_instances_with_violated_sri": violated_branch_instances,
            "branch_instance_violation_count": len(violated_branch_instances),
        }
    combined_branches = [
        row
        for row in rows
        if row.get("evaluable")
        and row.get("snapshot_kind") == "branch"
        and not row.get("primal_integral")
    ]
    combined_violated = [
        row for row in combined_branches if int(row.get("violated_candidate_count") or 0) > 0
    ]
    hard_instances = sorted({str(row["instance_id"]) for row in combined_violated})
    p2_gate = bool(
        len(hard_instances) >= 3
        and combined_branches
        and len(combined_violated) / len(combined_branches) >= 0.20
    )
    any_signal = any(
        details["root_with_violated_sri_count"]
        or details["fractional_branch_with_violated_sri_count"]
        for details in by_scale.values()
    )
    return {
        "schema_version": "lunar_ice_bpc.live_sri_readiness.v1",
        "baseline_dir": str(baseline_dir),
        "snapshot_count": len(rows),
        "evaluable_snapshot_count": sum(bool(row.get("evaluable")) for row in rows),
        "scale_summary": by_scale,
        "p2_branch_gate": {
            "required_hard_instance_count": 3,
            "denominator_hard_instance_target": 5,
            "required_fractional_branch_violation_rate": 0.20,
            "observed_hard_instances_with_violation": hard_instances,
            "observed_hard_instance_count": len(hard_instances),
            "observed_fractional_branch_snapshot_count": len(combined_branches),
            "observed_violated_fractional_branch_snapshot_count": len(combined_violated),
            "observed_fractional_branch_violation_rate": (
                len(combined_violated) / len(combined_branches) if combined_branches else 0.0
            ),
            "passed": p2_gate,
        },
        "stable_sri_signal_observed": any_signal,
        "recommendation": (
            "RUN_P0_P1_ROOT_ONLY_PILOT" if any_signal else "STOP_LIVE_V1_KEEP_NO_CUT_DEFAULT"
        ),
        "mutates_solver": False,
        "official_bound_effect": "none",
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    keys = [
        "scale",
        "instance_id",
        "node_id",
        "depth",
        "snapshot_kind",
        "node_status",
        "primal_integral",
        "evaluable",
        "enumerated_candidate_count",
        "full_enumeration_completed",
        "violated_candidate_count",
        "selected_candidate_count",
        "unselected_violated_count",
        "max_violation",
        "max_selected_support",
        "source_tree_json",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in keys})


def render_report(summary: dict) -> str:
    lines = [
        "# Native Live SRI V1 Readiness 诊断报告",
        "",
        "本报告只读取冻结 no-cut BPC 树中的 RMP primal snapshot；不添加 cut、不重求解 RMP，",
        "因此不会改变任何正式 lower bound 或 exact certificate。",
        "",
    ]
    for scale, row in summary["scale_summary"].items():
        lines.extend(
            [
                f"## {scale} 规模",
                "",
                f"- root：{row['root_with_violated_sri_count']}/{row['root_snapshot_count']} 存在 violated SRI；最大 violation={row['root_max_violation']}。",
                f"- fractional branch：{row['fractional_branch_with_violated_sri_count']}/{row['fractional_branch_snapshot_count']} 存在 violated SRI，比例={row['fractional_branch_violation_rate']:.2%}。",
                "",
            ]
        )
    gate = summary["p2_branch_gate"]
    lines.extend(
        [
            "## 决策",
            "",
            f"- 稳定 SRI signal：{summary['stable_sri_signal_observed']}。",
            f"- P2 branch gate：{gate['passed']}（branch violation rate={gate['observed_fractional_branch_violation_rate']:.2%}）。",
            f"- 建议：`{summary['recommendation']}`。",
            "",
            "受冻结 JSON 内容限制，restricted-RMP bound movement 在本轮不可重建；该指标必须由后续 fresh P0/P1 root-only pilot 在完整 JourneyColumn 状态上测量。",
            "",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
