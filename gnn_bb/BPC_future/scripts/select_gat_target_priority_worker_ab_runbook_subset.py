#!/usr/bin/env python3
"""Select a bounded first-tranche subset for target-priority worker A/B runs.

The selector is an offline planning helper.  It reads a candidate file already
accepted by ``build_gat_target_priority_worker_ab_runbook.py`` and writes a
smaller ``candidates.json`` for a guarded first tranche.  It never runs BPC,
pricing, RMP, workers, or certificate logic.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import json
from pathlib import Path
from typing import Any, Iterable

from BPC_future.scripts.build_gat_target_priority_worker_ab_runbook import (
    PYTHON,
    REQUIRED_CANDIDATE_CONTEXT_FIELDS,
    WORKER_METHOD_TARGET_MATERIALIZATION_FIXED,
)


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/"
    "gat_batch_impact_multibatch_intervention_plan_v15_first_tranche_20260616"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260616_bpc_future_gat_target_mode_stage3_v15_first_tranche_runbook_subset_zh.md"
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


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


def _split_csv(values: Iterable[str] | None) -> tuple[str, ...]:
    if not values:
        return tuple()
    parsed: list[str] = []
    for value in values:
        for part in str(value).split(","):
            item = part.strip()
            if item:
                parsed.append(item)
    return tuple(parsed)


def _candidate_task_count(candidate: dict[str, Any]) -> int:
    for field in ("instance_task_count", "task_count", "target_task_count"):
        value = _int_value(candidate.get(field), 0)
        if value > 0:
            return value
    text = str(candidate.get("instance") or "")
    marker = "tasks_"
    index = text.find(marker)
    while index >= 0:
        start = index + len(marker)
        chunk = ""
        while start + len(chunk) < len(text) and text[start + len(chunk)].isdigit():
            chunk += text[start + len(chunk)]
        if chunk:
            return int(chunk)
        index = text.find(marker, index + 1)
    return 0


def _context_hash(candidate: dict[str, Any]) -> str:
    return str(candidate.get("expected_context_hash") or candidate.get("context_hash") or "")


def _candidate_priority_key(candidate: dict[str, Any]) -> tuple[float, ...]:
    true_rc = _float_value(candidate.get("best_true_reduced_cost"), 0.0)
    rank = _int_value(candidate.get("context_target_rank"), 999999)
    return (
        1.0 if bool(candidate.get("opportunity_is_missed_high_roi")) else 0.0,
        1.0 if bool(candidate.get("opportunity_is_high_roi")) else 0.0,
        _float_value(candidate.get("opportunity_score")),
        max(0.0, -true_rc),
        _float_value(candidate.get("target_task_set_size")),
        -float(rank),
        1.0 if bool(candidate.get("target_task_set_new")) else 0.0,
    )


def _context_priority_key(candidates: list[dict[str, Any]]) -> tuple[float, ...]:
    best = max((_candidate_priority_key(candidate) for candidate in candidates), default=(0.0,))
    true_rc_values = [
        _float_value(candidate.get("best_true_reduced_cost"), 0.0) for candidate in candidates
    ]
    return (
        best[0],
        best[1],
        best[2],
        max((max(0.0, -value) for value in true_rc_values), default=0.0),
        float(len(candidates)),
        best[4] if len(best) > 4 else 0.0,
    )


def _candidate_allowed(
    candidate: dict[str, Any],
    *,
    task_counts: set[int] | None,
    families: set[str] | None,
) -> bool:
    if task_counts is not None and _candidate_task_count(candidate) not in task_counts:
        return False
    if families is not None:
        family = str(candidate.get("instance_family") or "").strip()
        if family not in families:
            return False
    return bool(_context_hash(candidate))


def _runbook_command(output_dir: Path, candidates_path: Path) -> str:
    parts = [
        "PYTHONDONTWRITEBYTECODE=1",
        "PYTHONPATH=.",
        PYTHON,
        "BPC_future/scripts/build_gat_target_priority_worker_ab_runbook.py",
        "--candidates-file",
        str(candidates_path),
        "--output-dir",
        str(output_dir / "worker_ab_runbook"),
        "--report",
        str(output_dir / "worker_ab_runbook.md"),
        "--worker-method",
        WORKER_METHOD_TARGET_MATERIALIZATION_FIXED,
        "--worker-batch-size",
        "1",
    ]
    return " ".join(parts)


def select_runbook_subset(
    *,
    candidates_file: Path,
    output_dir: Path,
    report: Path,
    max_contexts: int,
    max_candidates: int = 0,
    max_candidates_per_context: int = 0,
    min_candidates_per_context: int = 2,
    include_task_counts: Iterable[int] | None = None,
    families: Iterable[str] | None = None,
    exclude_context_hashes: Iterable[str] | None = None,
    require_missed_high_roi: bool = False,
) -> dict[str, Any]:
    payload = _read_json(candidates_file)
    raw_candidates = [
        dict(candidate)
        for candidate in payload.get("candidates", [])
        if isinstance(candidate, dict)
    ]
    task_counts = None
    if include_task_counts is not None:
        task_counts = {int(value) for value in include_task_counts}
    family_set = None
    if families is not None:
        family_set = {str(value).strip() for value in families if str(value).strip()}
    excluded_contexts = {
        str(value).strip()
        for value in (exclude_context_hashes or [])
        if str(value).strip()
    }

    groups: dict[str, list[dict[str, Any]]] = {}
    skipped_counts: Counter[str] = Counter()
    for candidate in raw_candidates:
        if not _candidate_allowed(candidate, task_counts=task_counts, families=family_set):
            skipped_counts["filtered_candidate"] += 1
            continue
        context_hash = _context_hash(candidate)
        if context_hash in excluded_contexts:
            skipped_counts["excluded_context"] += 1
            continue
        groups.setdefault(context_hash, []).append(candidate)

    context_records: list[dict[str, Any]] = []
    selected_candidates: list[dict[str, Any]] = []
    sorted_groups = sorted(
        groups.items(),
        key=lambda pair: (_context_priority_key(pair[1]), pair[0]),
        reverse=True,
    )
    for context_hash, context_candidates in sorted_groups:
        ordered = sorted(context_candidates, key=_candidate_priority_key, reverse=True)
        missed = any(bool(candidate.get("opportunity_is_missed_high_roi")) for candidate in ordered)
        if require_missed_high_roi and not missed:
            skipped_counts["not_missed_high_roi_context"] += 1
            continue
        if max_candidates_per_context > 0:
            ordered = ordered[: int(max_candidates_per_context)]
        if len(ordered) < max(1, int(min_candidates_per_context)):
            skipped_counts["too_few_candidates_in_context"] += 1
            continue
        if len(context_records) >= max(0, int(max_contexts)):
            skipped_counts["after_context_limit"] += len(ordered)
            continue
        remaining = 0 if max_candidates <= 0 else max(0, int(max_candidates) - len(selected_candidates))
        if max_candidates > 0 and remaining < max(1, int(min_candidates_per_context)):
            skipped_counts["after_candidate_limit"] += len(ordered)
            continue
        selected = ordered if max_candidates <= 0 else ordered[:remaining]
        if len(selected) < max(1, int(min_candidates_per_context)):
            skipped_counts["partial_context_below_min_candidates"] += 1
            continue
        selected_candidates.extend(selected)
        context_records.append(
            {
                "context_hash": context_hash,
                "candidate_count": len(selected),
                "available_candidate_count": len(context_candidates),
                "missed_high_roi": missed,
                "max_opportunity_score": max(
                    _float_value(candidate.get("opportunity_score")) for candidate in selected
                ),
                "best_true_reduced_cost": min(
                    _float_value(candidate.get("best_true_reduced_cost")) for candidate in selected
                ),
                "task_counts": sorted({_candidate_task_count(candidate) for candidate in selected}),
                "families": sorted(
                    {str(candidate.get("instance_family") or "unknown") for candidate in selected}
                ),
            }
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    candidates_path = output_dir / "candidates.json"
    runbook_command = _runbook_command(output_dir, candidates_path)
    selected_context_counts = Counter(_context_hash(candidate) for candidate in selected_candidates)
    checks = {
        "diagnostic_only": True,
        "runs_bpc_or_pricing_false": True,
        "has_candidate": bool(selected_candidates),
        "selected_context_count_within_limit": len(context_records) <= max(0, int(max_contexts)),
        "candidate_count_within_limit": max_candidates <= 0
        or len(selected_candidates) <= int(max_candidates),
        "all_selected_contexts_have_min_candidates": all(
            count >= max(1, int(min_candidates_per_context))
            for count in selected_context_counts.values()
        ),
        "all_candidates_have_expected_context_hash": all(
            bool(candidate.get("expected_context_hash")) for candidate in selected_candidates
        ),
        "all_candidates_have_full_capture_context": all(
            all(str(candidate.get(field) or "").strip() for field in REQUIRED_CANDIDATE_CONTEXT_FIELDS)
            for candidate in selected_candidates
        ),
        "all_candidates_have_target_sequences": all(
            bool(candidate.get("target_sequence")) and bool(candidate.get("target_arc_option_sequence"))
            for candidate in selected_candidates
        ),
        "all_candidates_true_rc_negative": all(
            _float_value(candidate.get("best_true_reduced_cost"), 1.0) < 0.0
            for candidate in selected_candidates
        ),
        "no_certificate_effect": all(
            candidate.get("certificate_effect") is False
            and candidate.get("official_bound_effect") is False
            for candidate in selected_candidates
        ),
        "labels_blocked_until_worker_reachability": all(
            candidate.get("training_label_allowed_before_worker_reachability") is False
            and candidate.get("requires_worker_target_causal_match") is True
            for candidate in selected_candidates
        ),
    }
    summary = {
        "schema_version": "gat_target_priority_worker_ab_runbook_subset_v1",
        "status": "ready" if selected_candidates else "no_candidates",
        "report_date": date.today().isoformat(),
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "default_enabled": False,
        "certificate_ready": False,
        "official_bound_effect": False,
        "source_candidates_file": str(candidates_file),
        "source_candidate_count": len(raw_candidates),
        "eligible_context_count": len(groups),
        "selected_context_count": len(context_records),
        "candidate_count": len(selected_candidates),
        "max_contexts": max(0, int(max_contexts)),
        "max_candidates": max(0, int(max_candidates)),
        "max_candidates_per_context": max(0, int(max_candidates_per_context)),
        "min_candidates_per_context": max(1, int(min_candidates_per_context)),
        "include_task_counts": []
        if include_task_counts is None
        else [int(value) for value in include_task_counts],
        "families": [] if families is None else sorted(family_set or []),
        "exclude_context_hashes": sorted(excluded_contexts),
        "require_missed_high_roi": bool(require_missed_high_roi),
        "candidate_task_count_counts": {
            str(key): value
            for key, value in sorted(
                Counter(_candidate_task_count(candidate) for candidate in selected_candidates).items()
            )
        },
        "candidate_family_counts": dict(
            sorted(
                Counter(
                    str(candidate.get("instance_family") or "unknown")
                    for candidate in selected_candidates
                ).items()
            )
        ),
        "candidate_context_counts": dict(sorted(selected_context_counts.items())),
        "contexts": context_records,
        "output_candidates_json": str(candidates_path),
        "output_runbook_command_txt": str(output_dir / "runbook_command.txt"),
        "runbook_command": runbook_command,
        "skipped_counts": dict(sorted(skipped_counts.items())),
        "checks": checks,
        "all_checks_pass": all(bool(value) for value in checks.values()),
    }
    candidates_path.write_text(
        json.dumps({"candidates": selected_candidates}, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "runbook_command.txt").write_text(runbook_command + "\n", encoding="utf-8")
    _write_report(report, summary)
    return summary


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GAT Target-Priority Worker A/B 首批子集报告",
        "",
        f"日期：{summary['report_date']}",
        "",
        "## 目的",
        "",
        "missed high-ROI 的分数差距已经显示这不是简单阈值问题。这里从完整",
        " multi-batch intervention candidates 中筛出一个可控首批子集，先验证",
        " fixed target materialization worker 是否能在同一 RMP context 命中目标并产生",
        "可用于下一轮数据闭环的 same-context A/B 标签。",
        "",
        "该脚本只生成子集和 runbook 生成命令，不运行 BPC / pricing / RMP / worker，",
        "不改变 admission，也不参与 certificate。",
        "",
        "## 机器字段",
        "",
        "```text",
        "gat_target_priority_worker_ab_runbook_subset = current",
        f"status = {summary['status']}",
        f"source_candidate_count = {summary['source_candidate_count']}",
        f"eligible_context_count = {summary['eligible_context_count']}",
        f"selected_context_count = {summary['selected_context_count']}",
        f"candidate_count = {summary['candidate_count']}",
        f"max_contexts = {summary['max_contexts']}",
        f"min_candidates_per_context = {summary['min_candidates_per_context']}",
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
                "selected_context_count": summary["selected_context_count"],
                "candidate_task_count_counts": summary["candidate_task_count_counts"],
                "candidate_family_counts": summary["candidate_family_counts"],
                "candidate_context_counts": summary["candidate_context_counts"],
                "exclude_context_hashes": summary["exclude_context_hashes"],
                "skipped_counts": summary["skipped_counts"],
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
        "```json",
        json.dumps(summary["contexts"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## 下一步命令",
        "",
        "先生成首批 guarded worker A/B runbook；实际运行仍需显式执行生成的命令：",
        "",
        "```bash",
        summary["runbook_command"],
        "```",
        "",
        "## 边界",
        "",
        "- 子集只用于控制首批 A/B 运行规模；不是最终 Stage 4/Stage 5 结论；",
        "- worker 跑完前不能把这些候选写成训练标签；",
        "- true-RC negative 仍可能拖慢 RMP，失败样本进入 DELAY_QUEUE/诊断，不可永久丢弃；",
        "- 最终 no-negative certificate 只能由当前 branch/cut/dual 下的 exact pricing closure 给出。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates-file", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--max-contexts", type=int, default=3)
    parser.add_argument("--max-candidates", type=int, default=0)
    parser.add_argument("--max-candidates-per-context", type=int, default=0)
    parser.add_argument("--min-candidates-per-context", type=int, default=2)
    parser.add_argument("--include-task-counts", nargs="*", type=int, default=None)
    parser.add_argument(
        "--family",
        action="append",
        default=None,
        help="Allowed instance family; may be repeated or comma-separated.",
    )
    parser.add_argument(
        "--exclude-context-hash",
        action="append",
        default=None,
        help="Context hash to skip; may be repeated or comma-separated.",
    )
    parser.add_argument("--require-missed-high-roi", action="store_true")
    args = parser.parse_args(argv)
    summary = select_runbook_subset(
        candidates_file=args.candidates_file,
        output_dir=args.output_dir,
        report=args.report,
        max_contexts=max(0, int(args.max_contexts)),
        max_candidates=max(0, int(args.max_candidates)),
        max_candidates_per_context=max(0, int(args.max_candidates_per_context)),
        min_candidates_per_context=max(1, int(args.min_candidates_per_context)),
        include_task_counts=args.include_task_counts,
        families=_split_csv(args.family) or None,
        exclude_context_hashes=_split_csv(args.exclude_context_hash) or None,
        require_missed_high_roi=bool(args.require_missed_high_roi),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
