#!/usr/bin/env python3
"""Build an audit-only runbook for collecting Journey branch-tail positives."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_branch_tail_positive_runbook_20260623")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260623_bpc_future_journey_branch_tail_positive_runbook_zh.md"
)
DEFAULT_CONFIG = Path("BPC_future/configs/moon_trek_20_smoke.yaml")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _instance_from_log_file(log_file: Any) -> str | None:
    text = str(log_file or "")
    marker = "/logs/"
    if marker not in text:
        return None
    instance = text.split(marker, 1)[1]
    if instance.endswith(".jsonl"):
        instance = instance[: -len(".jsonl")]
    return instance or None


def _safe_slug(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("_")
    return slug[:160] or "instance"


def _unique_root_pairs(rows: Iterable[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen: set[tuple[str, int, int]] = set()
    for row in rows:
        if str(row.get("source_type") or "") != "branch_impact":
            continue
        if int(row.get("depth") or 0) != 0:
            continue
        instance = _instance_from_log_file(row.get("log_file"))
        if instance is None:
            continue
        task_i = row.get("task_i")
        task_j = row.get("task_j")
        if task_i is None or task_j is None:
            continue
        pair = tuple(sorted((int(task_i), int(task_j))))
        key = (instance, pair[0], pair[1])
        if key in seen:
            continue
        seen.add(key)
        selected.append({**row, "instance": instance, "task_i": pair[0], "task_j": pair[1]})
        if len(selected) >= int(limit):
            break
    return selected


def build_runbook(
    positive_gap_summary: Path,
    output_dir: Path,
    report: Path,
    *,
    config: Path = DEFAULT_CONFIG,
    time_limit: int = 200,
    limit: int = 8,
) -> dict[str, Any]:
    summary = _read_json(positive_gap_summary)
    rows = summary.get("near_positive_rows")
    if not isinstance(rows, list):
        rows = []
    root_rows = _unique_root_pairs((row for row in rows if isinstance(row, dict)), limit)
    run_root = output_dir / "runs"
    entries: list[dict[str, Any]] = []
    for index, row in enumerate(root_rows, start=1):
        instance = str(row["instance"])
        task_i = int(row["task_i"])
        task_j = int(row["task_j"])
        experiment = f"{index:02d}_force_pair_{task_i}_{task_j}_{_safe_slug(Path(instance).stem)}"
        result_dir = run_root / experiment
        command = [
            "/home/kai/miniconda3/bin/python",
            "BPC_future/scripts/run_bpc_future_external_timeout_batch.py",
            "--config",
            str(config),
            "--instances",
            instance,
            "--time-limit",
            str(int(time_limit)),
            "--results-csv",
            str(result_dir / "results.csv"),
            "--log-dir",
            str(result_dir / "logs"),
            "--solution-dir",
            str(result_dir / "solutions"),
            "--run-log-dir",
            str(result_dir / "run_logs"),
            "--python",
            "/home/kai/miniconda3/bin/python",
            "--timeout-kill-after",
            "30s",
            "--max-workers",
            "1",
            "--quiet",
            "--set",
            "journey_early_branching_enabled=True",
            "--set",
            "journey_early_branching_min_cg_iter=56",
            "--set",
            "journey_early_branching_child_min_cg_iter=3",
            "--set",
            "journey_early_branching_max_depth=1",
            "--set",
            "journey_child_priority_by_width_enabled=True",
            "--set",
            "journey_early_branching_after_incomplete_no_column_enabled=True",
            "--set",
            "journey_early_branching_after_incomplete_no_column_min_remaining=20.0",
            "--set",
            "journey_branch_fractionality_tie_tolerance=0.05",
            "--set",
            f"journey_branch_candidate_priority=force_pair:{task_i},{task_j}",
            "--set",
            "journey_branch_candidate_log_top_n=12",
        ]
        entries.append(
            {
                "experiment": experiment,
                "instance": instance,
                "forced_pair": [task_i, task_j],
                "source_log_file": row.get("log_file"),
                "source_tail_class": row.get("tail_class"),
                "source_tail_badness_score": row.get("tail_badness_score"),
                "source_child_negative_pricing_events": row.get("y_child_negative_pricing_events"),
                "command": command,
                "shell_command": " ".join(command),
                "expected_label_source": "rerun_then_audit_branch_impact",
            }
        )
    runbook = {
        "schema_version": "journey_branch_tail_positive_runbook_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "stage4_candidate_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "base_sample_strategy": "extend_existing_5000_with_branch_tail_interventions",
        "positive_gap_summary": str(positive_gap_summary),
        "config": str(config),
        "time_limit": int(time_limit),
        "candidate_source": "root_level_near_positive_rows",
        "entry_count": len(entries),
        "entries": entries,
        "notes": (
            "These commands are opt-in positive collection probes.  They force a "
            "legal fractional Ryan-Foster pair if present, but exact pricing and "
            "certificate semantics remain unchanged.  Non-root parent-context "
            "A/B requires ancestor-path binding and is intentionally not included "
            "in this first tranche."
        ),
    }
    write_outputs(runbook, output_dir, report)
    return runbook


def write_outputs(runbook: dict[str, Any], output_dir: Path, report: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "runbook.json").write_text(
        json.dumps(runbook, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "commands.sh").write_text(
        "\n".join(entry["shell_command"] for entry in runbook.get("entries", [])) + "\n",
        encoding="utf-8",
    )
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(_render_report(runbook, output_dir), encoding="utf-8")


def _render_report(runbook: dict[str, Any], output_dir: Path) -> str:
    lines = [
        "# Journey Branch-Tail Positive Collection Runbook",
        "",
        "日期：2026-06-23",
        "",
        "## 目的",
        "",
        "在已有 5000 个 Stage 3 样本基础上追加 branch-tail intervention 样本，而不是重新生成全部样本。runbook 只生成 opt-in 命令，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "journey_branch_tail_positive_runbook = current",
        f"output_dir = {output_dir}",
        f"entry_count = {runbook.get('entry_count')}",
        f"base_sample_strategy = {runbook.get('base_sample_strategy')}",
        f"candidate_source = {runbook.get('candidate_source')}",
        "production_ready = false",
        "stage4_candidate_ready = false",
        "certificate_effect = false",
        "official_bound_effect = false",
        "```",
        "",
        "## 条目",
        "",
    ]
    for entry in runbook.get("entries", []):
        lines.extend(
            [
                f"### {entry['experiment']}",
                "",
                "```text",
                f"instance = {entry['instance']}",
                f"forced_pair = {entry['forced_pair']}",
                f"source_tail_class = {entry.get('source_tail_class')}",
                f"source_tail_badness_score = {entry.get('source_tail_badness_score')}",
                "```",
                "",
                "```bash",
                entry["shell_command"],
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## 边界",
            "",
            "这些命令只改变 Ryan-Foster 候选选择顺序；如果 forced pair 不是当前合法 fractional candidate，会回退到默认 fractionality 选择。最终 no-negative closure 仍只来自 exact pricing。",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("positive_gap_summary", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--time-limit", type=int, default=200)
    parser.add_argument("--limit", type=int, default=8)
    args = parser.parse_args()

    runbook = build_runbook(
        args.positive_gap_summary,
        args.output_dir,
        args.report,
        config=args.config,
        time_limit=args.time_limit,
        limit=args.limit,
    )
    print(json.dumps(runbook, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
