#!/usr/bin/env python3
"""Build a guarded solver A/B runbook for worker-ROI GAT candidates.

The input is the offline worker-ROI GAT + kNN/OOD decision ledger.  The output
is a command runbook for:

* 5/10 no-regression sentinels with no new worker enabled;
* 20-task explicit target-priority worker A/B for selected worker-ROI
  candidates.

This builder does not run BPC or pricing.  Generated worker commands are
opt-in probes and cannot affect certificates or official lower bounds.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

from BPC_future.scripts.build_gat_target_priority_worker_ab_runbook import (
    REQUIRED_CANDIDATE_CONTEXT_FIELDS,
    SCALE_CONFIG,
    TASK20_CONTEXT_CAPTURE_OVERRIDES,
    _batch_run_command,
    _has_certificate_effect,
    _small_instance_paths,
    _single_run_command,
    _worker_overrides,
)


DEFAULT_DECISION_RECORDS = Path(
    "BPC_future/results/gat_worker_roi_knn_ood_audit_v31_20260615/decision_records.jsonl"
)
DEFAULT_OOD_SUMMARY = Path("BPC_future/results/gat_worker_roi_knn_ood_audit_v31_20260615/summary.json")
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/20260615_bpc_future_gat_worker_roi_solver_ab_runbook_v31_zh.md"
)
DEFAULT_LOGICAL_GRAPH_ROOT = Path("BPC_future/logical_graph")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decision-records", type=Path, default=DEFAULT_DECISION_RECORDS)
    parser.add_argument("--ood-summary", type=Path, default=DEFAULT_OOD_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--logical-graph-root", type=Path, default=DEFAULT_LOGICAL_GRAPH_ROOT)
    parser.add_argument("--small-time-limit", type=float, default=60.0)
    parser.add_argument("--twenty-time-limit", type=float, default=200.0)
    parser.add_argument("--max-workers", type=int, default=4)
    parser.add_argument("--max-candidates", type=int, default=9)
    parser.add_argument("--decision-split", default="validation")
    parser.add_argument("--decision-name", default="HIGH_PRIORITY")
    parser.add_argument("--positive-label-only", action="store_true")
    parser.add_argument("--exclude-runbook-summary", action="append", default=[])
    parser.add_argument("--exclude-candidate-jsonl", action="append", default=[])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = build_runbook(
        decision_records=args.decision_records,
        ood_summary=args.ood_summary,
        output_dir=args.output_dir,
        report=args.report,
        logical_graph_root=args.logical_graph_root,
        small_time_limit=float(args.small_time_limit),
        twenty_time_limit=float(args.twenty_time_limit),
        max_workers=int(args.max_workers),
        max_candidates=int(args.max_candidates),
        decision_split=str(args.decision_split),
        decision_name=str(args.decision_name),
        positive_label_only=bool(args.positive_label_only),
        exclude_runbook_summaries=tuple(Path(path) for path in args.exclude_runbook_summary),
        exclude_candidate_jsonls=tuple(Path(path) for path in args.exclude_candidate_jsonl),
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def build_runbook(
    *,
    decision_records: Path = DEFAULT_DECISION_RECORDS,
    ood_summary: Path = DEFAULT_OOD_SUMMARY,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    logical_graph_root: Path = DEFAULT_LOGICAL_GRAPH_ROOT,
    small_time_limit: float = 60.0,
    twenty_time_limit: float = 200.0,
    max_workers: int = 4,
    max_candidates: int = 9,
    decision_split: str = "validation",
    decision_name: str = "HIGH_PRIORITY",
    positive_label_only: bool = False,
    exclude_runbook_summaries: Iterable[Path] = (),
    exclude_candidate_jsonls: Iterable[Path] = (),
) -> dict[str, Any]:
    if int(max_workers) > 4:
        raise ValueError("max_workers must be <= 4 to keep memory bounded")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    ood = json.loads(Path(ood_summary).read_text(encoding="utf-8"))
    raw_records = _read_jsonl(Path(decision_records))
    excluded_candidate_keys = _load_excluded_candidate_keys(
        exclude_runbook_summaries=exclude_runbook_summaries,
        exclude_candidate_jsonls=exclude_candidate_jsonls,
    )
    candidates = _select_candidates(
        raw_records,
        decision_split=str(decision_split),
        decision_name=str(decision_name),
        positive_label_only=bool(positive_label_only),
        excluded_candidate_keys=excluded_candidate_keys,
        max_candidates=int(max_candidates),
    )
    candidate_json = output_dir / f"selected_{str(decision_name).lower()}_candidates.json"
    candidate_json.write_text(
        json.dumps({"candidates": candidates}, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    commands: list[dict[str, Any]] = []
    small_checks: list[dict[str, Any]] = []
    for scale in (5, 10):
        instances = _small_instance_paths(Path(logical_graph_root), scale)
        profile = f"task{scale:03d}_mainline_no_regression_no_new_worker"
        command = _batch_run_command(
            config=SCALE_CONFIG[scale],
            instances=instances,
            output_dir=output_dir,
            profile=profile,
            time_limit=float(small_time_limit),
            max_workers=int(max_workers),
        )
        commands.append(
            {
                "command_type": profile,
                "description": (
                    f"Run task-{scale} no-regression sentinel. No worker, certificate, "
                    "or official-bound shortcut is enabled."
                ),
                "command": command,
            }
        )
        small_checks.append(
            {
                "task_count": scale,
                "instances": instances,
                "instance_count": len(instances),
                "results_csv": str(output_dir / profile / "results.csv"),
            }
        )

    candidate_runs: list[dict[str, Any]] = []
    for candidate in candidates:
        base_profile = f"task020_{candidate['name']}_mainline_baseline"
        worker_profile = f"task020_{candidate['name']}_worker_roi_gat_priority"
        baseline_command = _single_run_command(
            config=SCALE_CONFIG[20],
            instance=candidate["instance"],
            output_dir=output_dir,
            profile=base_profile,
            time_limit=float(twenty_time_limit),
            overrides=TASK20_CONTEXT_CAPTURE_OVERRIDES,
        )
        worker_command = _single_run_command(
            config=SCALE_CONFIG[20],
            instance=candidate["instance"],
            output_dir=output_dir,
            profile=worker_profile,
            time_limit=float(twenty_time_limit),
            overrides=(*TASK20_CONTEXT_CAPTURE_OVERRIDES, *_worker_overrides(candidate)),
        )
        commands.extend(
            [
                {
                    "command_type": base_profile,
                    "description": "Run task-20 baseline with context capture only.",
                    "command": baseline_command,
                },
                {
                    "command_type": worker_profile,
                    "description": (
                        "Run explicit opt-in worker-ROI GAT target-priority worker. "
                        "This cannot certify no-negative or set an official bound."
                    ),
                    "command": worker_command,
                },
            ]
        )
        candidate_runs.append(
            {
                **candidate,
                "baseline_csv": str(output_dir / base_profile / "results.csv"),
                "worker_csv": str(output_dir / worker_profile / "results.csv"),
            }
        )

    audit_command = " ".join(
        [
            "PYTHONDONTWRITEBYTECODE=1",
            "PYTHONPATH=.",
            "/home/kai/miniconda3/envs/ecole/bin/python",
            "BPC_future/scripts/audit_gat_worker_roi_solver_ab_results.py",
            "--runbook-summary",
            str(output_dir / "summary.json"),
            "--output-dir",
            str(output_dir / "ab_audit"),
            "--report",
            str(output_dir / "ab_audit_zh.md"),
        ]
    )
    commands.append(
        {
            "command_type": "audit_worker_roi_solver_ab_results",
            "description": "Read result CSVs after the solver commands finish.",
            "command": audit_command,
        }
    )
    checks = {
        "diagnostic_builder_only": True,
        "source_ood_candidate_ready": bool(ood.get("validation_candidate_ready")),
        "has_5_10_no_regression_commands": {5, 10}.issubset(
            {int(item["task_count"]) for item in small_checks}
        ),
        "has_selected_candidates": bool(candidates),
        "all_candidates_have_expected_context_hash": all(
            bool(item.get("expected_context_hash")) for item in candidates
        ),
        "all_candidates_have_target_sequence": all(bool(item.get("target_sequence")) for item in candidates),
        "all_candidates_have_target_arc_options": all(
            bool(item.get("target_arc_option_sequence")) for item in candidates
        ),
        "all_candidates_have_capture_pricing_kind": all(
            str(item.get("capture_pricing_kind") or "").strip()
            for item in candidates
        ),
        "all_candidates_have_full_capture_context": all(
            bool(item.get("candidate_context_complete")) for item in candidates
        ),
        "all_candidates_have_materialization_traces": all(
            _has_materialization_traces(item) for item in candidates
        ),
        "all_candidate_instances_exist": all(Path(item["instance"]).exists() for item in candidates),
        "commands_have_no_certificate_effect": not any(
            _has_certificate_effect(item["command"]) for item in commands
        ),
        "small_commands_do_not_enable_new_worker": all(
            "hidden_negative_worker_enabled=True" not in item["command"]
            for item in commands
            if item["command_type"].startswith(("task005", "task010"))
        ),
        "max_workers_bounded": int(max_workers) <= 4,
    }
    summary = {
        "schema_version": "gat_worker_roi_solver_ab_runbook_v1",
        "status": "ready",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "default_enabled": False,
        "certificate_ready": False,
        "official_bound_effect": False,
        "candidate_source": (
            "worker_roi_gat_knn_ood_"
            f"{str(decision_split).lower()}_{str(decision_name).lower()}"
            f"{'_positive_only' if positive_label_only else ''}"
        ),
        "decision_records": str(decision_records),
        "ood_summary": str(ood_summary),
        "source_ood_validation_metrics": ood.get("validation_metrics"),
        "selected_candidates_json": str(candidate_json),
        "decision_split": str(decision_split),
        "decision_name": str(decision_name),
        "positive_label_only": bool(positive_label_only),
        "excluded_candidate_key_count": len(excluded_candidate_keys),
        "exclude_runbook_summaries": [str(path) for path in exclude_runbook_summaries],
        "exclude_candidate_jsonls": [str(path) for path in exclude_candidate_jsonls],
        "max_workers": int(max_workers),
        "small_no_regression": small_checks,
        "candidate_runs": candidate_runs,
        "commands": commands,
        "candidate_policy": {
            "gat_role": "trajectory_roi_embedding_and_impact_expression",
            "knn_ood_role": "safety_shell",
            "safe_negative_action": "HIGH_PRIORITY",
            "unsafe_negative_action": "DELAY_QUEUE",
            "negative_discard_allowed": False,
            "certificate_effect": False,
            "context_policy": "expected_context_hash_plus_recovered_capture_context",
        },
        "checks": checks,
        "all_checks_pass": all(bool(value) for value in checks.values()),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(Path(report), summary)
    return summary


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _select_candidates(
    rows: list[dict[str, Any]],
    *,
    decision_split: str,
    decision_name: str,
    positive_label_only: bool,
    excluded_candidate_keys: set[str],
    max_candidates: int,
) -> list[dict[str, Any]]:
    selected = []
    seen_candidate_keys: set[str] = set()
    for row in rows:
        if row.get("decision_name") != str(decision_name):
            continue
        if str(row.get("decision_split")) != str(decision_split):
            continue
        if positive_label_only and int(row.get("label_worker_roi_positive") or 0) != 1:
            continue
        if not row.get("target_sequence") or not row.get("target_arc_option_sequence"):
            continue
        if not row.get("expected_context_hash"):
            continue
        candidate_keys = _candidate_unique_keys(row)
        if candidate_keys & excluded_candidate_keys or candidate_keys & seen_candidate_keys:
            continue
        seen_candidate_keys.update(candidate_keys)
        selected.append(row)
    selected.sort(
        key=lambda row: (
            0 if int(row.get("label_worker_roi_positive") or 0) else 1,
            -float(row.get("score") or 0.0),
            str(row.get("name") or ""),
        )
    )
    candidates: list[dict[str, Any]] = []
    for row in selected[: int(max_candidates)]:
        candidate_key = _candidate_unique_key(row)
        candidates.append(
            {
                "name": str(row.get("name") or f"worker_roi_candidate_{len(candidates):03d}"),
                "candidate_unique_key": candidate_key,
                "instance": str(row["instance"]),
                "expected_context_hash": str(row["expected_context_hash"]),
                "target_sequence": [int(value) for value in row.get("target_sequence") or []],
                "target_priority_sequence": [int(value) for value in row.get("target_sequence") or []],
                "target_arc_option_sequence": [
                    str(value) for value in row.get("target_arc_option_sequence") or []
                ],
                "target_sortie_traces": row.get("target_sortie_traces") or [],
                "capture_pricing_kind": str(row.get("capture_pricing_kind") or ""),
                "roi_class": str(row.get("roi_class") or ""),
                "worker_roi_score": float(row.get("score") or 0.0),
                "worker_roi_decision_reason": str(row.get("decision_reason") or ""),
                "worker_roi_neighbor_delay_fraction": float(
                    row.get("neighbor_delay_fraction") or 0.0
                ),
                "worker_roi_label_positive": int(row.get("label_worker_roi_positive") or 0),
                "source_decision_split": str(row.get("decision_split") or ""),
                "source_row_index": int(row.get("row_index") or 0),
                **{
                    field: str(row.get(field) or "")
                    for field in REQUIRED_CANDIDATE_CONTEXT_FIELDS
                    if field != "expected_context_hash"
                },
                "candidate_context_complete": all(
                    str(row.get(field) or "").strip()
                    for field in REQUIRED_CANDIDATE_CONTEXT_FIELDS
                ),
            }
        )
    return candidates


def _load_excluded_candidate_keys(
    *,
    exclude_runbook_summaries: Iterable[Path],
    exclude_candidate_jsonls: Iterable[Path],
) -> set[str]:
    keys: set[str] = set()
    for raw_path in exclude_runbook_summaries:
        path = Path(raw_path)
        if not path.exists():
            raise FileNotFoundError(f"exclude runbook summary not found: {path}")
        summary = json.loads(path.read_text(encoding="utf-8"))
        for candidate in summary.get("candidate_runs") or []:
            keys.update(_candidate_unique_keys(candidate))
    for raw_path in exclude_candidate_jsonls:
        path = Path(raw_path)
        if not path.exists():
            raise FileNotFoundError(f"exclude candidate jsonl not found: {path}")
        for candidate in _read_jsonl(path):
            keys.update(_candidate_unique_keys(candidate))
    return keys


def _candidate_unique_key(row: dict[str, Any]) -> str:
    keys = _candidate_unique_keys(row)
    explicit = str(row.get("roi_candidate_key") or row.get("candidate_unique_key") or "").strip()
    if explicit:
        return explicit
    return sorted(keys)[0]


def _candidate_unique_keys(row: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    for field in ("roi_candidate_key", "candidate_unique_key"):
        explicit = str(row.get(field) or "").strip()
        if explicit:
            keys.add(explicit)
    instance = str(row.get("instance") or "")
    context_hash = str(row.get("expected_context_hash") or row.get("context_hash") or "")
    sequence = [int(value) for value in row.get("target_sequence") or []]
    arc_options = [str(value) for value in row.get("target_arc_option_sequence") or []]
    if instance or context_hash or sequence or arc_options:
        keys.add(
            "|".join(
                [
                    instance,
                    context_hash,
                    ",".join(str(value) for value in sequence),
                    ",".join(arc_options),
                ]
            )
        )
    parts = {
        "instance": instance,
        "context_hash": context_hash,
        "target_sequence": sequence,
        "target_arc_option_sequence": arc_options,
        "target_sortie_traces": row.get("target_sortie_traces") or [],
    }
    keys.add(json.dumps(parts, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return keys


def _has_materialization_traces(candidate: dict[str, Any]) -> bool:
    traces = candidate.get("target_sortie_traces")
    if not isinstance(traces, list) or not traces:
        return False
    for trace in traces:
        if not isinstance(trace, dict):
            return False
        sequence = trace.get("sequence")
        arc_options = trace.get("arc_option_sequence")
        if not isinstance(sequence, list) or not sequence:
            return False
        if not isinstance(arc_options, list) or len(arc_options) != len(sequence) + 1:
            return False
        if "start_time" not in trace:
            return False
    return True


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GAT Worker ROI Solver A/B Runbook 报告",
        "",
        "日期：2026-06-15",
        "",
        "## 目的",
        "",
        "生成下一轮 solver A/B 命令：5/10 只做 no-regression sentinel，20 只对",
        "worker-ROI GAT + kNN/OOD 筛出的候选做显式 opt-in",
        "worker A/B。该脚本不运行求解器。",
        "",
        "## 机器字段",
        "",
        "```text",
        "gat_worker_roi_solver_ab_runbook = current",
        f"status = {summary['status']}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"candidate_count = {len(summary['candidate_runs'])}",
        f"decision_split = {summary['decision_split']}",
        f"decision_name = {summary['decision_name']}",
        f"positive_label_only = {str(summary['positive_label_only']).lower()}",
        f"excluded_candidate_key_count = {summary['excluded_candidate_key_count']}",
        f"exclude_candidate_jsonl_count = {len(summary.get('exclude_candidate_jsonls') or [])}",
        f"max_workers = {summary['max_workers']}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"certificate_ready = {str(summary['certificate_ready']).lower()}",
        f"official_bound_effect = {str(summary['official_bound_effect']).lower()}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## Candidate Policy",
        "",
        "```json",
        json.dumps(summary["candidate_policy"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Source OOD Metrics",
        "",
        "```json",
        json.dumps(summary["source_ood_validation_metrics"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Candidate Runs",
        "",
        "```json",
        json.dumps(summary["candidate_runs"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Commands",
        "",
    ]
    for item in summary["commands"]:
        lines.extend(
            [
                f"### {item['command_type']}",
                "",
                item["description"],
                "",
                "```bash",
                item["command"],
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## 边界",
            "",
            "- 该 runbook 不是生产开关；",
            "- 5/10 命令不启用新的 hidden-negative worker；",
            "- 20 worker 命令必须显式 opt-in；",
            "- 所有命令都不启用 sharded Pulse certificate 或 official-bound shortcut；",
            "- 未通过安全壳的 true-RC negative 只能延迟，不能永久丢弃。",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
