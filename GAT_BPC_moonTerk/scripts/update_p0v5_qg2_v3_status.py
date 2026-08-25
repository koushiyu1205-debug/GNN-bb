#!/usr/bin/env python3
"""Regenerate the human-readable QG2 V3 experiment status from artifacts."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import statistics


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUN = ROOT / "runs/p0v5_qg2_v3_gat_first_20260806"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", default=str(DEFAULT_RUN))
    parser.add_argument("--output")
    args = parser.parse_args()
    run_root = Path(args.run_root).resolve()
    output = (
        Path(args.output).resolve()
        if args.output else run_root / "STATUS_ZH.md"
    )

    ranker = _optional(run_root / "training_rankers/training_report.json")
    force = _optional(run_root / "force_on_screen_v1/report.json")
    selector_folders = {
        "GAT": "arm_selector_gat_v1",
        "MLP": "arm_selector_mlp_control_v1",
        "Linear": "arm_selector_linear_control_v1",
    }
    fresh_folders = {
        "GAT": "arm_selector_fresh_heldout_v1",
        "MLP": "arm_selector_fresh_mlp_heldout_v1",
        "Linear": "arm_selector_fresh_linear_heldout_v1",
    }
    selectors = {
        name: _optional(run_root / folder / "training_report.json")
        for name, folder in selector_folders.items()
    }
    fresh = {
        name: _fresh(run_root / folder)
        for name, folder in fresh_folders.items()
    }

    lines = [
        "# P0V5 QG2 V3 GAT-first 实验状态",
        "",
        "> 本文件由 `scripts/update_p0v5_qg2_v3_status.py` 从持久化 artifact 重建；性能数字不是部署授权。",
        "",
        "## 当前结论",
        "",
        "- P0V4+V5 Exact control 未修改；Q0 始终是全部 arm 被拒绝后的唯一回退。",
        "- label-state GAT arm（QG2）已因固定 force-on screen 全面退化而 hard-veto。",
        "- 当前有效学习问题是 context-level selector 在 Q0/QD1/QB1 间选择；其收益不能归因于 QG2 label ordering。",
        "- GAT 已按约定第一个训练并第一个完成 heldout fresh-process 三重复；MLP/Linear 只作为结构对照。",
        "",
        "## Admission ranker",
        "",
    ]
    if ranker:
        metrics = ranker.get("partition_metrics") or ranker.get("metrics") or {}
        lines.extend([
            f"- contexts：`{ranker.get('context_count', 'n/a')}`；模型：`{ranker.get('model_order') or ranker.get('trained_models') or 'GAT-first'}`。",
            f"- ranker report：`{_rel(run_root / 'training_rankers/training_report.json')}`。",
        ])
        if metrics:
            lines.append(f"- metrics：`{json.dumps(metrics, ensure_ascii=False, sort_keys=True)}`。")
    else:
        lines.append("- 尚无 ranker report。")
    if force:
        overall = (force.get("summary") or {}).get("overall") or {}
        lines.extend([
            "",
            "### QG2 force-on",
            "",
            f"- context：{overall.get('context_count', 'n/a')}；beneficial：{overall.get('beneficial_count', 'n/a')}；adverse：{overall.get('adverse_count', 'n/a')}；GM：{_fmt(overall.get('observed_net_geomean_ratio'))}。",
        ])

    lines.extend([
        "",
        "## Context selector 离线对照",
        "",
        "| 模型 | train/cal/heldout | heldout 激活 | beneficial | harmful | heldout GM | scale30 GM | scale50 GM |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for name in ("GAT", "MLP", "Linear"):
        report = selectors[name]
        if not report:
            lines.append(f"| {name} | - | - | - | - | - | - | - |")
            continue
        counts = report.get("partition_counts") or {}
        heldout = (report.get("partition_reports") or {}).get("heldout") or {}
        per_scale = heldout.get("per_scale") or {}
        lines.append(
            f"| {name} | {counts.get('train', 0)}/{counts.get('calibration', 0)}/{counts.get('heldout', 0)} "
            f"| {heldout.get('activated_count', 0)} | {heldout.get('beneficial_count', 0)} "
            f"| {heldout.get('harmful_count', 0)} | {_fmt(heldout.get('net_geomean_ratio'))} "
            f"| {_fmt((per_scale.get('30') or {}).get('net_geomean_ratio'))} "
            f"| {_fmt((per_scale.get('50') or {}).get('net_geomean_ratio'))} |"
        )

    lines.extend([
        "",
        "## Fresh-process heldout",
        "",
        "| 模型 | 当前进度 | 激活 | beneficial | harmful | GM | scale30 GM | scale50 GM | safety |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for name in ("GAT", "MLP", "Linear"):
        row = fresh[name]
        if not row:
            lines.append(f"| {name} | 0/22 | - | - | - | - | - | - | - |")
            continue
        summary = row["summary"]
        overall = summary["overall"]
        lines.append(
            f"| {name} | {row['completed']}/{row['total']} "
            f"| {overall['activated_count']} | {overall['beneficial_count']} "
            f"| {overall['harmful_count']} | {_fmt(overall['net_geomean_ratio'])} "
            f"| {_fmt(summary['scale30']['net_geomean_ratio'])} "
            f"| {_fmt(summary['scale50']['net_geomean_ratio'])} "
            f"| {'PASS' if overall['all_safe'] else 'FAIL'} |"
        )

    lines.extend([
        "",
        "## 判定边界与后续",
        "",
        "1. fresh-process 结果优先于离线旧 outcome；Linear 的高激活离线结果不能直接视为运行权限。",
        "2. 先完成 MLP fresh 对照；再依据 harmful 数、GM 和动作覆盖决定是否支付 Linear fresh 成本。",
        "3. 结构胜负确定后，冻结单一 selector、阈值、gain floor、checkpoint 与 hash，再做 scale30/50 development E2E。",
        "4. development E2E 通过后才运行 scale5/10/20/30/50 full20；scale5/10/20 必须零模型调用。",
        "",
    ])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    print(output)
    return 0


def _fresh(folder: Path):
    report = _optional(folder / "report.json")
    if report:
        records = list(report.get("records") or ())
        return {
            "completed": len(records),
            "total": len(records),
            "summary": report.get("summary") or _summarize(records),
        }
    path = folder / "fresh_records.jsonl"
    if not path.exists():
        return None
    records = [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return {"completed": len(records), "total": 22, "summary": _summarize(records)}


def _summarize(records):
    def one(rows):
        ratios = [float(row.get("ratio") or 1.0) for row in rows]
        return {
            "activated_count": sum(row.get("selected_action") != "Q0" for row in rows),
            "beneficial_count": sum(bool(row.get("beneficial")) for row in rows),
            "harmful_count": sum(bool(row.get("harmful")) for row in rows),
            "net_geomean_ratio": _geomean(ratios),
            "all_safe": all(bool(row.get("safe")) for row in rows),
        }
    return {
        "overall": one(records),
        "scale30": one([row for row in records if int(row.get("scale") or 0) == 30]),
        "scale50": one([row for row in records if int(row.get("scale") or 0) == 50]),
    }


def _geomean(values):
    return 1.0 if not values else math.exp(statistics.fmean(
        math.log(max(float(value), 1.0e-12)) for value in values
    ))


def _optional(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def _fmt(value):
    return "-" if value is None else f"{float(value):.6f}"


def _rel(path: Path):
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
