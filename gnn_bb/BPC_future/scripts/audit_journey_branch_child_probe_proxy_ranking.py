#!/usr/bin/env python3
"""Build proxy branch-ranking rows from Journey child-probe audit rows.

The script is offline and diagnostic-only. It reads ``child_probe_rows.jsonl``
artifacts, groups children back into branch-pair probes, and compares pairs
within the same source parent context.  The output is intentionally marked as
right-censored proxy data; it is for sampling navigation and model diagnostics,
not for certificates, pruning, official bounds, or production score-map opt-in.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import date
import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_branch_child_probe_proxy_ranking_20260624")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260624_bpc_future_journey_branch_child_probe_proxy_ranking_zh.md"
)


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            yield payload


def _load_child_probe_rows(paths: Iterable[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        if path.is_dir():
            rows.extend(_iter_jsonl(path / "child_probe_rows.jsonl"))
            continue
        if path.name == "summary.json":
            rows.extend(_iter_jsonl(path.parent / "child_probe_rows.jsonl"))
            continue
        if path.name == "child_probe_rows.jsonl" or path.suffix == ".jsonl":
            rows.extend(_iter_jsonl(path))
    return rows


def _float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return float(default)
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float(default)
    if parsed != parsed:
        return float(default)
    return float(parsed)


def _int(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return int(default)
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _pair_tuple(value: Any) -> tuple[int, int] | None:
    if isinstance(value, str):
        pieces = [piece.strip() for piece in value.replace(";", ",").split(",") if piece.strip()]
        if len(pieces) != 2:
            return None
        try:
            i, j = int(pieces[0]), int(pieces[1])
        except ValueError:
            return None
    elif isinstance(value, (list, tuple)) and len(value) == 2:
        try:
            i, j = int(value[0]), int(value[1])
        except (TypeError, ValueError):
            return None
    else:
        return None
    if i == j:
        return None
    return tuple(sorted((i, j)))


def _row_pair(row: dict[str, Any]) -> tuple[int, int] | None:
    return _pair_tuple([row.get("task_i"), row.get("task_j")])


def _canonical_instance_from_log(log_file: Any) -> str:
    text = str(log_file or "")
    marker = "BPC_future/logical_graph/"
    if marker in text:
        instance = marker + text.split(marker, 1)[1]
        if instance.endswith(".jsonl"):
            instance = instance[: -len(".jsonl")]
        return instance
    return text


def _branch_group_key(row: dict[str, Any]) -> tuple[str, int, int, tuple[int, int]] | None:
    pair = _row_pair(row)
    if pair is None:
        return None
    return (
        _canonical_instance_from_log(row.get("log_file")),
        _int(row.get("branch_node_id"), -1),
        _int(row.get("branch_depth"), -1),
        pair,
    )


def _context_key(branch_row: dict[str, Any]) -> tuple[str, int, int]:
    return (
        str(branch_row.get("instance") or ""),
        _int(branch_row.get("node_id"), -1),
        _int(branch_row.get("depth"), -1),
    )


def _proxy_score(
    row: dict[str, Any],
    *,
    complete_bonus: float,
    right_censored_penalty: float,
    unstarted_child_penalty: float,
    fathom_bonus: float,
    corrected_gain_scale: float,
    corrected_gain_cap: float,
    completion_retry_penalty: float,
    proof_cpu_scale: float,
    negative_pricing_penalty: float,
) -> float:
    score = 0.0
    if bool(row.get("label_observation_complete")):
        score += float(complete_bonus)
    if bool(row.get("right_censored")):
        score -= float(right_censored_penalty)
    score -= float(unstarted_child_penalty) * _float(row.get("unstarted_child_count"))
    score += float(fathom_bonus) * _float(row.get("fathom_count"))
    corrected_gain = min(max(0.0, _float(row.get("max_corrected_bound_gain"))), float(corrected_gain_cap))
    score += corrected_gain / max(1.0e-9, float(corrected_gain_scale))
    score -= float(completion_retry_penalty) * _float(row.get("completion_bound_retry_count"))
    score -= _float(row.get("proof_cpu")) / max(1.0e-9, float(proof_cpu_scale))
    score -= float(negative_pricing_penalty) * _float(row.get("negative_pricing_event_count"))
    return float(score)


def _promotion_blocked_reasons(
    row: dict[str, Any],
    *,
    min_promotion_proxy_score: float | None,
    min_promotion_fathom_count: float | None,
    min_promotion_corrected_bound_gain: float | None,
    max_promotion_completion_bound_retry_count: float | None,
    max_promotion_negative_pricing_event_count: float | None,
    require_promotion_complete_label: bool,
) -> list[str]:
    reasons: list[str] = []
    if (
        min_promotion_proxy_score is not None
        and _float(row.get("proxy_score"), default=float("-inf"))
        < float(min_promotion_proxy_score)
    ):
        reasons.append("proxy_score_below_promotion_threshold")
    if (
        min_promotion_fathom_count is not None
        and _float(row.get("fathom_count")) < float(min_promotion_fathom_count)
    ):
        reasons.append("fathom_count_below_promotion_threshold")
    if (
        min_promotion_corrected_bound_gain is not None
        and _float(row.get("max_corrected_bound_gain"))
        < float(min_promotion_corrected_bound_gain)
    ):
        reasons.append("corrected_bound_gain_below_promotion_threshold")
    if (
        max_promotion_completion_bound_retry_count is not None
        and _float(row.get("completion_bound_retry_count"))
        > float(max_promotion_completion_bound_retry_count)
    ):
        reasons.append("completion_bound_retry_above_promotion_threshold")
    if (
        max_promotion_negative_pricing_event_count is not None
        and _float(row.get("negative_pricing_event_count"))
        > float(max_promotion_negative_pricing_event_count)
    ):
        reasons.append("negative_pricing_above_promotion_threshold")
    if require_promotion_complete_label and not bool(row.get("label_observation_complete")):
        reasons.append("label_observation_incomplete")
    return reasons


def _build_branch_rows(
    child_rows: list[dict[str, Any]],
    *,
    complete_bonus: float,
    right_censored_penalty: float,
    unstarted_child_penalty: float,
    fathom_bonus: float,
    corrected_gain_scale: float,
    corrected_gain_cap: float,
    completion_retry_penalty: float,
    proof_cpu_scale: float,
    negative_pricing_penalty: float,
    min_promotion_proxy_score: float | None,
    min_promotion_fathom_count: float | None,
    min_promotion_corrected_bound_gain: float | None,
    max_promotion_completion_bound_retry_count: float | None,
    max_promotion_negative_pricing_event_count: float | None,
    require_promotion_complete_label: bool,
) -> tuple[list[dict[str, Any]], int]:
    grouped: dict[tuple[str, int, int, tuple[int, int]], list[dict[str, Any]]] = defaultdict(list)
    skipped = 0
    for row in child_rows:
        key = _branch_group_key(row)
        if key is None:
            skipped += 1
            continue
        grouped[key].append(row)

    branch_rows: list[dict[str, Any]] = []
    for (instance, node_id, depth, pair), children in sorted(grouped.items()):
        labels = [child.get("child_labels") for child in children if isinstance(child.get("child_labels"), dict)]
        child_count = len(children)
        started_count = sum(1 for child in children if bool(child.get("child_started")))
        label_complete = bool(children) and all(bool(child.get("label_observation_complete")) for child in children)
        right_censored = any(bool(child.get("right_censored")) for child in children)
        run_statuses = sorted({str(child.get("run_status") or "") for child in children})
        proof_cpu = sum(_float(label.get("child_proof_cpu")) for label in labels)
        retries = sum(_float(label.get("child_completion_bound_retry_count")) for label in labels)
        exact_events = sum(_float(label.get("child_exact_pricing_event_count")) for label in labels)
        negative_events = sum(_float(label.get("child_negative_pricing_event_count")) for label in labels)
        fathom_count = sum(_float(label.get("child_fathomed")) for label in labels)
        max_corrected_gain = max(
            (_float(label.get("child_max_corrected_bound_gain")) for label in labels),
            default=0.0,
        )
        row = {
            "schema_version": "journey_branch_child_probe_proxy_branch_row_v1",
            "diagnostic_only": True,
            "runs_bpc_or_pricing": False,
            "production_ready": False,
            "certificate_effect": False,
            "official_bound_effect": False,
            "instance": instance,
            "node_id": int(node_id),
            "depth": int(depth),
            "pair": [int(pair[0]), int(pair[1])],
            "task_i": int(pair[0]),
            "task_j": int(pair[1]),
            "child_count": int(child_count),
            "started_child_count": int(started_count),
            "unstarted_child_count": int(max(0, child_count - started_count)),
            "label_observation_complete": bool(label_complete),
            "right_censored": bool(right_censored),
            "run_statuses": run_statuses,
            "proof_cpu": round(float(proof_cpu), 9),
            "completion_bound_retry_count": round(float(retries), 9),
            "exact_pricing_event_count": round(float(exact_events), 9),
            "negative_pricing_event_count": round(float(negative_events), 9),
            "fathom_count": round(float(fathom_count), 9),
            "max_corrected_bound_gain": round(float(max_corrected_gain), 9),
        }
        row["proxy_score"] = round(
            _proxy_score(
                row,
                complete_bonus=complete_bonus,
                right_censored_penalty=right_censored_penalty,
                unstarted_child_penalty=unstarted_child_penalty,
                fathom_bonus=fathom_bonus,
                corrected_gain_scale=corrected_gain_scale,
                corrected_gain_cap=corrected_gain_cap,
                completion_retry_penalty=completion_retry_penalty,
                proof_cpu_scale=proof_cpu_scale,
                negative_pricing_penalty=negative_pricing_penalty,
            ),
            9,
        )
        blocked_reasons = _promotion_blocked_reasons(
            row,
            min_promotion_proxy_score=min_promotion_proxy_score,
            min_promotion_fathom_count=min_promotion_fathom_count,
            min_promotion_corrected_bound_gain=min_promotion_corrected_bound_gain,
            max_promotion_completion_bound_retry_count=max_promotion_completion_bound_retry_count,
            max_promotion_negative_pricing_event_count=max_promotion_negative_pricing_event_count,
            require_promotion_complete_label=require_promotion_complete_label,
        )
        row["promotion_ready"] = not blocked_reasons
        row["promotion_blocked_reasons"] = blocked_reasons
        branch_rows.append(row)
    return branch_rows, skipped


def _compact_branch(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "alternative_pair": row.get("pair"),
        "proxy_score": row.get("proxy_score"),
        "right_censored": row.get("right_censored"),
        "label_observation_complete": row.get("label_observation_complete"),
        "fathom_count": row.get("fathom_count"),
        "max_corrected_bound_gain": row.get("max_corrected_bound_gain"),
        "completion_bound_retry_count": row.get("completion_bound_retry_count"),
        "proof_cpu": row.get("proof_cpu"),
        "negative_pricing_event_count": row.get("negative_pricing_event_count"),
        "exact_pricing_event_count": row.get("exact_pricing_event_count"),
        "child_count": row.get("child_count"),
        "started_child_count": row.get("started_child_count"),
        "promotion_ready": row.get("promotion_ready"),
        "promotion_blocked_reasons": row.get("promotion_blocked_reasons"),
    }


def _preference_reason(better: dict[str, Any], worse: dict[str, Any]) -> str:
    if _float(better.get("fathom_count")) > _float(worse.get("fathom_count")):
        return "child_fathom_then_proxy_score"
    if _float(better.get("max_corrected_bound_gain")) > _float(worse.get("max_corrected_bound_gain")):
        return "corrected_gain_then_proxy_score"
    return "child_probe_proxy_score"


def build_proxy_ranking(
    inputs: list[Path],
    output_dir: Path,
    report: Path,
    *,
    min_proxy_score_gap: float = 0.05,
    min_started_child_count: int = 1,
    complete_bonus: float = 5.0,
    right_censored_penalty: float = 8.0,
    unstarted_child_penalty: float = 1.0,
    fathom_bonus: float = 1.0,
    corrected_gain_scale: float = 5.0,
    corrected_gain_cap: float = 25.0,
    completion_retry_penalty: float = 0.1,
    proof_cpu_scale: float = 120.0,
    negative_pricing_penalty: float = 0.0,
    min_promotion_proxy_score: float | None = 0.0,
    min_promotion_fathom_count: float | None = None,
    min_promotion_corrected_bound_gain: float | None = None,
    max_promotion_completion_bound_retry_count: float | None = None,
    max_promotion_negative_pricing_event_count: float | None = None,
    require_promotion_complete_label: bool = False,
) -> dict[str, Any]:
    child_rows = _load_child_probe_rows(inputs)
    branch_rows, skipped_child_rows = _build_branch_rows(
        child_rows,
        complete_bonus=complete_bonus,
        right_censored_penalty=right_censored_penalty,
        unstarted_child_penalty=unstarted_child_penalty,
        fathom_bonus=fathom_bonus,
        corrected_gain_scale=corrected_gain_scale,
        corrected_gain_cap=corrected_gain_cap,
        completion_retry_penalty=completion_retry_penalty,
        proof_cpu_scale=proof_cpu_scale,
        negative_pricing_penalty=negative_pricing_penalty,
        min_promotion_proxy_score=min_promotion_proxy_score,
        min_promotion_fathom_count=min_promotion_fathom_count,
        min_promotion_corrected_bound_gain=min_promotion_corrected_bound_gain,
        max_promotion_completion_bound_retry_count=max_promotion_completion_bound_retry_count,
        max_promotion_negative_pricing_event_count=max_promotion_negative_pricing_event_count,
        require_promotion_complete_label=require_promotion_complete_label,
    )

    filtered_branch_rows = [
        row for row in branch_rows if _int(row.get("started_child_count"), 0) >= int(min_started_child_count)
    ]

    groups: dict[tuple[str, int, int], list[dict[str, Any]]] = defaultdict(list)
    for row in filtered_branch_rows:
        groups[_context_key(row)].append(row)

    context_rows: list[dict[str, Any]] = []
    ranking_rows: list[dict[str, Any]] = []
    context_counts: Counter[str] = Counter()
    promotion_blocked_reason_counts: Counter[str] = Counter()
    for row in filtered_branch_rows:
        for reason in row.get("promotion_blocked_reasons") or []:
            promotion_blocked_reason_counts[str(reason)] += 1
    for key, group in sorted(groups.items(), key=lambda item: item[0]):
        sorted_group = sorted(group, key=lambda row: (-_float(row.get("proxy_score")), row.get("pair")))
        if len(sorted_group) < 2:
            context_counts["single_pair_context"] += 1
        elif any(not bool(row.get("right_censored")) for row in sorted_group):
            context_counts["has_uncensored_pair_context"] += 1
        else:
            context_counts["all_right_censored_context"] += 1
        best = sorted_group[0]
        worst = sorted_group[-1]
        spread = _float(best.get("proxy_score")) - _float(worst.get("proxy_score"))
        context_rows.append(
            {
                "schema_version": "journey_branch_child_probe_proxy_context_summary_v1",
                "diagnostic_only": True,
                "runs_bpc_or_pricing": False,
                "production_ready": False,
                "certificate_effect": False,
                "official_bound_effect": False,
                "instance": key[0],
                "node_id": key[1],
                "depth": key[2],
                "alternative_count": len(sorted_group),
                "right_censored_pair_count": sum(1 for row in sorted_group if bool(row.get("right_censored"))),
                "complete_pair_count": sum(
                    1 for row in sorted_group if bool(row.get("label_observation_complete"))
                ),
                "best": _compact_branch(best),
                "worst": _compact_branch(worst),
                "proxy_score_spread": round(float(spread), 9),
                "ranking_pair_possible_count": max(0, len(sorted_group) * (len(sorted_group) - 1) // 2),
            }
        )
        for left_index, left in enumerate(sorted_group):
            for right in sorted_group[left_index + 1 :]:
                gap = _float(left.get("proxy_score")) - _float(right.get("proxy_score"))
                if gap < float(min_proxy_score_gap):
                    continue
                ranking_rows.append(
                    {
                        "schema_version": "journey_branch_child_probe_proxy_ranking_pair_v1",
                        "diagnostic_only": True,
                        "runs_bpc_or_pricing": False,
                        "production_ready": False,
                        "certificate_effect": False,
                        "official_bound_effect": False,
                        "proxy_only": True,
                        "right_censored_proxy": bool(left.get("right_censored"))
                        or bool(right.get("right_censored")),
                        "instance": key[0],
                        "node_id": key[1],
                        "depth": key[2],
                        "preference_reason": _preference_reason(left, right),
                        "better": _compact_branch(left),
                        "worse": _compact_branch(right),
                        "proxy_score_gap": round(float(gap), 9),
                        "corrected_bound_gain_gap": round(
                            _float(left.get("max_corrected_bound_gain"))
                            - _float(right.get("max_corrected_bound_gain")),
                            9,
                        ),
                        "proof_cpu_gap": round(
                            _float(right.get("proof_cpu")) - _float(left.get("proof_cpu")),
                            9,
                        ),
                    }
                )

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "child_probe_proxy_branch_rows.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in branch_rows),
        encoding="utf-8",
    )
    (output_dir / "child_probe_proxy_context_rows.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in context_rows),
        encoding="utf-8",
    )
    (output_dir / "child_probe_proxy_ranking_pair_rows.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in ranking_rows),
        encoding="utf-8",
    )

    summary = {
        "schema_version": "journey_branch_child_probe_proxy_ranking_summary_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "input_paths": [str(path) for path in inputs],
        "output_dir": str(output_dir),
        "raw_child_probe_row_count": len(child_rows),
        "skipped_child_probe_row_count": int(skipped_child_rows),
        "raw_proxy_branch_row_count": len(branch_rows),
        "proxy_branch_row_count": len(filtered_branch_rows),
        "filtered_out_proxy_branch_row_count": len(branch_rows) - len(filtered_branch_rows),
        "proxy_context_count": len(context_rows),
        "proxy_ranking_pair_count": len(ranking_rows),
        "right_censored_proxy_ranking_pair_count": sum(
            1 for row in ranking_rows if bool(row.get("right_censored_proxy"))
        ),
        "min_proxy_score_gap": float(min_proxy_score_gap),
        "min_started_child_count": int(min_started_child_count),
        "context_counts": dict(sorted(context_counts.items())),
        "complete_bonus": float(complete_bonus),
        "right_censored_penalty": float(right_censored_penalty),
        "unstarted_child_penalty": float(unstarted_child_penalty),
        "fathom_bonus": float(fathom_bonus),
        "corrected_gain_scale": float(corrected_gain_scale),
        "corrected_gain_cap": float(corrected_gain_cap),
        "completion_retry_penalty": float(completion_retry_penalty),
        "proof_cpu_scale": float(proof_cpu_scale),
        "negative_pricing_penalty": float(negative_pricing_penalty),
        "min_promotion_proxy_score": min_promotion_proxy_score,
        "min_promotion_fathom_count": min_promotion_fathom_count,
        "min_promotion_corrected_bound_gain": min_promotion_corrected_bound_gain,
        "max_promotion_completion_bound_retry_count": max_promotion_completion_bound_retry_count,
        "max_promotion_negative_pricing_event_count": max_promotion_negative_pricing_event_count,
        "require_promotion_complete_label": bool(require_promotion_complete_label),
        "promotion_ready_branch_count": sum(
            1 for row in filtered_branch_rows if bool(row.get("promotion_ready"))
        ),
        "promotion_blocked_branch_count": sum(
            1 for row in filtered_branch_rows if not bool(row.get("promotion_ready"))
        ),
        "promotion_blocked_reason_counts": dict(sorted(promotion_blocked_reason_counts.items())),
        "ranking_training_ready": False,
        "sampling_navigation_ready": bool(ranking_rows),
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    _write_report(report, summary, context_rows, ranking_rows)
    return summary


def _write_report(
    report: Path,
    summary: dict[str, Any],
    context_rows: list[dict[str, Any]],
    ranking_rows: list[dict[str, Any]],
) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = [
        "# Journey Branch Child-Probe Proxy Ranking",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 目的",
        "",
        "把同一 parent context 下的 child-probe proof-cost proxy 转成相对排序，用于采样导航和模型诊断。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。",
        "",
        "## 机器字段",
        "",
        "```text",
    ]
    for key in [
        "raw_child_probe_row_count",
        "raw_proxy_branch_row_count",
        "proxy_branch_row_count",
        "filtered_out_proxy_branch_row_count",
        "proxy_context_count",
        "proxy_ranking_pair_count",
        "right_censored_proxy_ranking_pair_count",
        "min_proxy_score_gap",
        "min_started_child_count",
        "context_counts",
        "min_promotion_proxy_score",
        "min_promotion_fathom_count",
        "min_promotion_corrected_bound_gain",
        "max_promotion_completion_bound_retry_count",
        "max_promotion_negative_pricing_event_count",
        "require_promotion_complete_label",
        "promotion_ready_branch_count",
        "promotion_blocked_branch_count",
        "promotion_blocked_reason_counts",
        "sampling_navigation_ready",
        "ranking_training_ready",
        "production_ready",
        "certificate_effect",
        "official_bound_effect",
    ]:
        lines.append(f"{key} = {summary.get(key)}")
    lines.extend(["```", "", "## 关键 Context", ""])
    for row in context_rows[:12]:
        lines.append(
            "- "
            f"node={row['node_id']} depth={row['depth']} alts={row['alternative_count']} "
            f"spread={row['proxy_score_spread']} "
            f"best={row['best']['alternative_pair']} score={row['best']['proxy_score']} "
            f"promote={row['best']['promotion_ready']} "
            f"worst={row['worst']['alternative_pair']} score={row['worst']['proxy_score']}"
        )
    lines.extend(["", "## Top Proxy Ranking Pairs", ""])
    for row in sorted(ranking_rows, key=lambda item: float(item.get("proxy_score_gap") or 0.0), reverse=True)[:12]:
        lines.append(
            "- "
            f"node={row['node_id']} depth={row['depth']} "
            f"better={row['better']['alternative_pair']} "
            f"worse={row['worse']['alternative_pair']} "
            f"gap={row['proxy_score_gap']} reason={row['preference_reason']} "
            f"right_censored={row['right_censored_proxy']} "
            f"better_promote={row['better']['promotion_ready']}"
        )
    lines.extend(["", "## 使用边界", ""])
    lines.append(
        "这些 rows 是 right-censored proxy，不是 full replay / timeout-resolved 标签；只能用于决定下一批 longer probe / replay 优先级。"
    )
    lines.append(
        "它们不能作为剪枝依据、no-negative certificate、official bound、exact pricing 替代品，也不应直接接入生产 branch score map。"
    )
    if not ranking_rows:
        lines.append("当前没有形成 proxy ranking pair，需要补同 parent alternatives。")
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--min-proxy-score-gap", type=float, default=0.05)
    parser.add_argument(
        "--min-started-child-count",
        type=int,
        default=1,
        help="Drop branch-level probes whose children never started; default keeps rows with at least one started child.",
    )
    parser.add_argument("--complete-bonus", type=float, default=5.0)
    parser.add_argument("--right-censored-penalty", type=float, default=8.0)
    parser.add_argument("--unstarted-child-penalty", type=float, default=1.0)
    parser.add_argument("--fathom-bonus", type=float, default=1.0)
    parser.add_argument("--corrected-gain-scale", type=float, default=5.0)
    parser.add_argument("--corrected-gain-cap", type=float, default=25.0)
    parser.add_argument("--completion-retry-penalty", type=float, default=0.1)
    parser.add_argument("--proof-cpu-scale", type=float, default=120.0)
    parser.add_argument("--negative-pricing-penalty", type=float, default=0.0)
    parser.add_argument("--min-promotion-proxy-score", type=float, default=0.0)
    parser.add_argument("--min-promotion-fathom-count", type=float, default=None)
    parser.add_argument("--min-promotion-corrected-bound-gain", type=float, default=None)
    parser.add_argument("--max-promotion-completion-bound-retry-count", type=float, default=None)
    parser.add_argument("--max-promotion-negative-pricing-event-count", type=float, default=None)
    parser.add_argument("--require-promotion-complete-label", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = build_proxy_ranking(
        list(args.paths),
        args.output_dir,
        args.report,
        min_proxy_score_gap=args.min_proxy_score_gap,
        min_started_child_count=args.min_started_child_count,
        complete_bonus=args.complete_bonus,
        right_censored_penalty=args.right_censored_penalty,
        unstarted_child_penalty=args.unstarted_child_penalty,
        fathom_bonus=args.fathom_bonus,
        corrected_gain_scale=args.corrected_gain_scale,
        corrected_gain_cap=args.corrected_gain_cap,
        completion_retry_penalty=args.completion_retry_penalty,
        proof_cpu_scale=args.proof_cpu_scale,
        negative_pricing_penalty=args.negative_pricing_penalty,
        min_promotion_proxy_score=args.min_promotion_proxy_score,
        min_promotion_fathom_count=args.min_promotion_fathom_count,
        min_promotion_corrected_bound_gain=args.min_promotion_corrected_bound_gain,
        max_promotion_completion_bound_retry_count=args.max_promotion_completion_bound_retry_count,
        max_promotion_negative_pricing_event_count=args.max_promotion_negative_pricing_event_count,
        require_promotion_complete_label=args.require_promotion_complete_label,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
