#!/usr/bin/env python3
"""Audit whether child-probe branch rows are enough for offline training.

This script is diagnostic-only. It reads
``child_probe_proxy_branch_rows.jsonl`` files produced by
``audit_journey_branch_child_probe_proxy_ranking.py`` and reports whether the
proxy/proof-cost data is large enough to start branch/proof-head training.

The readiness levels here are intentionally weaker than strict full-replay
readiness. They are suitable for offline ranking/model-shape training and
sampling navigation only; they are not production opt-in gates, official
bounds, certificates, or pruning evidence.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_branch_probe_training_readiness_20260625")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260625_bpc_future_journey_branch_probe_training_readiness_zh.md"
)
ROW_FILENAME = "child_probe_proxy_branch_rows.jsonl"


PROBE_DEBUG_REQUIREMENTS = {
    "probe_branch_row_min": 100,
    "probe_positive_min": 10,
    "probe_hard_negative_min": 10,
    "probe_positive_context_min": 2,
    "probe_hard_negative_context_min": 2,
    "probe_instance_min": 3,
}

PROBE_SANITY_REQUIREMENTS = {
    "probe_branch_row_min": 500,
    "probe_positive_min": 30,
    "probe_hard_negative_min": 30,
    "probe_positive_context_min": 6,
    "probe_hard_negative_context_min": 6,
    "probe_instance_min": 8,
    "probe_time_window_family_min": 2,
}

PROBE_SERIOUS_REQUIREMENTS = {
    "probe_branch_row_min": 1000,
    "probe_positive_min": 50,
    "probe_hard_negative_min": 50,
    "probe_positive_context_min": 10,
    "probe_hard_negative_context_min": 10,
    "probe_instance_min": 12,
    "probe_time_window_family_min": 3,
}


def _float(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return float(default)
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float(default)
    if parsed != parsed:
        return float(default)
    return float(parsed)


def _int(value: Any, default: int = 0) -> int:
    if value in (None, ""):
        return int(default)
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _row_file(path: Path) -> Path:
    if path.is_dir():
        return path / ROW_FILENAME
    if path.name == "summary.json":
        return path.parent / ROW_FILENAME
    return path


def _load_rows(paths: Iterable[Path]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    resolved: list[str] = []
    for path in paths:
        row_path = _row_file(path)
        resolved.append(str(row_path))
        rows.extend(_read_jsonl(row_path))
    return rows, resolved


def _time_window_family(value: Any) -> str:
    text = str(value or "")
    for token in ("greedy-anchor", "random-wave", "sector-wave"):
        if token in text:
            return token
    return ""


def _pair_text(value: Any) -> str:
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return f"{value[0]}-{value[1]}"
    return str(value or "")


def _context_key(row: dict[str, Any]) -> str:
    return "|".join(
        [
            str(row.get("instance") or ""),
            str(row.get("node_id") if row.get("node_id") is not None else ""),
            str(row.get("depth") if row.get("depth") is not None else ""),
            _pair_text(row.get("pair")),
        ]
    )


def _hard_negative_reasons(
    row: dict[str, Any],
    *,
    max_hard_negative_proxy_score: float,
    min_hard_negative_completion_retry_count: float,
    min_hard_negative_negative_pricing_event_count: float,
) -> list[str]:
    reasons: list[str] = []
    if _float(row.get("proxy_score")) <= float(max_hard_negative_proxy_score):
        reasons.append("low_proxy_score")
    if bool(row.get("right_censored")):
        reasons.append("right_censored_probe")
    if _int(row.get("unstarted_child_count")) > 0:
        reasons.append("unstarted_child")
    if _float(row.get("completion_bound_retry_count")) >= float(
        min_hard_negative_completion_retry_count
    ):
        reasons.append("completion_bound_retry")
    if _float(row.get("negative_pricing_event_count")) >= float(
        min_hard_negative_negative_pricing_event_count
    ):
        reasons.append("negative_pricing_event")
    return reasons


def _normalized_row(
    row: dict[str, Any],
    *,
    min_started_child_count: int,
    min_probe_positive_proxy_score: float,
    max_hard_negative_proxy_score: float,
    min_hard_negative_completion_retry_count: float,
    min_hard_negative_negative_pricing_event_count: float,
) -> dict[str, Any]:
    started_child_count = _int(row.get("started_child_count"))
    promotion_ready = bool(row.get("promotion_ready"))
    positive = bool(
        started_child_count >= int(min_started_child_count)
        and promotion_ready
        and _float(row.get("proxy_score")) >= float(min_probe_positive_proxy_score)
    )
    hard_negative_reasons = _hard_negative_reasons(
        row,
        max_hard_negative_proxy_score=max_hard_negative_proxy_score,
        min_hard_negative_completion_retry_count=min_hard_negative_completion_retry_count,
        min_hard_negative_negative_pricing_event_count=min_hard_negative_negative_pricing_event_count,
    )
    hard_negative = bool(
        not positive
        and started_child_count >= int(min_started_child_count)
        and hard_negative_reasons
    )
    return {
        "schema_version": "journey_branch_probe_training_readiness_row_v1",
        "diagnostic_only": True,
        "proxy_only": True,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "instance": row.get("instance"),
        "time_window_family": _time_window_family(row.get("instance")),
        "context_key": _context_key(row),
        "node_id": row.get("node_id"),
        "depth": row.get("depth"),
        "pair": row.get("pair"),
        "proxy_score": _float(row.get("proxy_score")),
        "promotion_ready": promotion_ready,
        "promotion_blocked_reasons": row.get("promotion_blocked_reasons") or [],
        "probe_positive": positive,
        "strict_uncensored_probe_positive": bool(
            positive
            and bool(row.get("label_observation_complete"))
            and not bool(row.get("right_censored"))
        ),
        "probe_hard_negative": hard_negative,
        "probe_hard_negative_reasons": hard_negative_reasons,
        "label_observation_complete": bool(row.get("label_observation_complete")),
        "right_censored": bool(row.get("right_censored")),
        "child_count": _int(row.get("child_count")),
        "started_child_count": started_child_count,
        "unstarted_child_count": _int(row.get("unstarted_child_count")),
        "fathom_count": _float(row.get("fathom_count")),
        "max_corrected_bound_gain": _float(row.get("max_corrected_bound_gain")),
        "completion_bound_retry_count": _float(row.get("completion_bound_retry_count")),
        "negative_pricing_event_count": _float(row.get("negative_pricing_event_count")),
        "exact_pricing_event_count": _float(row.get("exact_pricing_event_count")),
        "proof_cpu": _float(row.get("proof_cpu")),
    }


def _count_distinct(rows: Iterable[dict[str, Any]], key: str) -> int:
    if key == "context":
        return len({str(row.get("context_key") or "") for row in rows if row.get("context_key")})
    if key == "instance":
        return len({str(row.get("instance") or "") for row in rows if row.get("instance")})
    if key == "family":
        return len({str(row.get("time_window_family") or "") for row in rows if row.get("time_window_family")})
    raise ValueError(f"unsupported distinct key: {key}")


def _missing(requirements: dict[str, int], actuals: dict[str, int]) -> dict[str, int]:
    return {
        key: max(0, int(required) - int(actuals.get(key, 0)))
        for key, required in requirements.items()
    }


def _ready(requirements: dict[str, int], actuals: dict[str, int]) -> bool:
    return all(int(actuals.get(key, 0)) >= int(required) for key, required in requirements.items())


def build_probe_training_readiness(
    inputs: list[Path],
    output_dir: Path,
    report: Path,
    *,
    min_started_child_count: int = 1,
    min_probe_positive_proxy_score: float = 0.0,
    max_hard_negative_proxy_score: float = -1.0,
    min_hard_negative_completion_retry_count: float = 1.0,
    min_hard_negative_negative_pricing_event_count: float = 1.0,
) -> dict[str, Any]:
    rows, resolved_inputs = _load_rows(inputs)
    normalized_rows = [
        _normalized_row(
            row,
            min_started_child_count=min_started_child_count,
            min_probe_positive_proxy_score=min_probe_positive_proxy_score,
            max_hard_negative_proxy_score=max_hard_negative_proxy_score,
            min_hard_negative_completion_retry_count=min_hard_negative_completion_retry_count,
            min_hard_negative_negative_pricing_event_count=(
                min_hard_negative_negative_pricing_event_count
            ),
        )
        for row in rows
    ]
    positive_rows = [row for row in normalized_rows if row["probe_positive"]]
    hard_negative_rows = [row for row in normalized_rows if row["probe_hard_negative"]]
    strict_positive_rows = [
        row for row in normalized_rows if row["strict_uncensored_probe_positive"]
    ]
    reason_counts: Counter[str] = Counter()
    for row in hard_negative_rows:
        for reason in row["probe_hard_negative_reasons"]:
            reason_counts[str(reason)] += 1
    actuals = {
        "probe_branch_row_min": len(normalized_rows),
        "probe_positive_min": len(positive_rows),
        "probe_hard_negative_min": len(hard_negative_rows),
        "probe_positive_context_min": _count_distinct(positive_rows, "context"),
        "probe_hard_negative_context_min": _count_distinct(hard_negative_rows, "context"),
        "probe_instance_min": _count_distinct(normalized_rows, "instance"),
        "probe_time_window_family_min": _count_distinct(normalized_rows, "family"),
    }
    remaining_debug = _missing(PROBE_DEBUG_REQUIREMENTS, actuals)
    remaining_sanity = _missing(PROBE_SANITY_REQUIREMENTS, actuals)
    remaining_serious = _missing(PROBE_SERIOUS_REQUIREMENTS, actuals)
    family_counts = Counter(str(row.get("time_window_family") or "") for row in normalized_rows)
    summary = {
        "schema_version": "journey_branch_probe_training_readiness_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "official_bound_effect": False,
        "certificate_effect": False,
        "proxy_only": True,
        "production_ready": False,
        "optin_training_ready": False,
        "input_paths": [str(path) for path in inputs],
        "resolved_row_paths": resolved_inputs,
        "output_dir": str(output_dir),
        "row_count": len(normalized_rows),
        "probe_positive_count": len(positive_rows),
        "strict_uncensored_probe_positive_count": len(strict_positive_rows),
        "probe_hard_negative_count": len(hard_negative_rows),
        "probe_positive_context_count": _count_distinct(positive_rows, "context"),
        "probe_hard_negative_context_count": _count_distinct(hard_negative_rows, "context"),
        "probe_instance_count": _count_distinct(normalized_rows, "instance"),
        "probe_time_window_family_count": _count_distinct(normalized_rows, "family"),
        "family_counts": dict(sorted(family_counts.items())),
        "probe_hard_negative_reason_counts": dict(sorted(reason_counts.items())),
        "min_started_child_count": int(min_started_child_count),
        "min_probe_positive_proxy_score": float(min_probe_positive_proxy_score),
        "max_hard_negative_proxy_score": float(max_hard_negative_proxy_score),
        "min_hard_negative_completion_retry_count": float(
            min_hard_negative_completion_retry_count
        ),
        "min_hard_negative_negative_pricing_event_count": float(
            min_hard_negative_negative_pricing_event_count
        ),
        "probe_debug_training_requirements": PROBE_DEBUG_REQUIREMENTS,
        "probe_sanity_training_requirements": PROBE_SANITY_REQUIREMENTS,
        "probe_serious_training_requirements": PROBE_SERIOUS_REQUIREMENTS,
        "probe_training_readiness_actuals": actuals,
        "probe_debug_training_ready": _ready(PROBE_DEBUG_REQUIREMENTS, actuals),
        "probe_sanity_training_ready": _ready(PROBE_SANITY_REQUIREMENTS, actuals),
        "probe_serious_training_ready": _ready(PROBE_SERIOUS_REQUIREMENTS, actuals),
        "remaining_for_probe_debug_training": remaining_debug,
        "remaining_for_probe_sanity_training": remaining_sanity,
        "remaining_for_probe_serious_training": remaining_serious,
        "missing_for_probe_debug_training": remaining_debug,
        "missing_for_probe_sanity_training": remaining_sanity,
        "missing_for_probe_serious_training": remaining_serious,
        "rows": normalized_rows,
    }
    write_outputs(summary, output_dir, report)
    return summary


def write_outputs(summary: dict[str, Any], output_dir: Path, report: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = list(summary.get("rows", []))
    summary_without_rows = dict(summary)
    summary_without_rows.pop("rows", None)
    (output_dir / "summary.json").write_text(
        json.dumps(summary_without_rows, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "branch_probe_training_readiness_rows.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    _write_report(report, summary_without_rows)


def _format_missing(missing: dict[str, int]) -> str:
    nonzero = {key: value for key, value in missing.items() if value > 0}
    if not nonzero:
        return "{}"
    return str(nonzero)


def _write_report(report: Path, summary: dict[str, Any]) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Journey Branch Probe Training Readiness Audit",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 目的",
        "",
        "汇总 child-probe / proof-cost proxy rows，判断是否足够先启动离线 branch/proof-head 训练。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不改变 official bound 或 certificate。",
        "",
        "## 机器字段",
        "",
        "```text",
    ]
    for key in [
        "row_count",
        "probe_positive_count",
        "strict_uncensored_probe_positive_count",
        "probe_hard_negative_count",
        "probe_positive_context_count",
        "probe_hard_negative_context_count",
        "probe_instance_count",
        "probe_time_window_family_count",
        "family_counts",
        "probe_hard_negative_reason_counts",
        "min_started_child_count",
        "min_probe_positive_proxy_score",
        "max_hard_negative_proxy_score",
        "probe_debug_training_ready",
        "probe_sanity_training_ready",
        "probe_serious_training_ready",
        "probe_debug_training_requirements",
        "probe_sanity_training_requirements",
        "probe_serious_training_requirements",
        "remaining_for_probe_debug_training",
        "remaining_for_probe_sanity_training",
        "remaining_for_probe_serious_training",
        "runs_bpc_or_pricing",
        "official_bound_effect",
        "certificate_effect",
        "proxy_only",
        "production_ready",
        "optin_training_ready",
    ]:
        value = summary.get(key)
        if key.startswith("remaining_for"):
            value = _format_missing(value)
        lines.append(f"{key} = {value}")
    lines.extend(
        [
            "```",
            "",
            "## 解释",
            "",
            "- `probe_positive` 来自 child-probe proxy 的 promotion-ready 分支行；它可以训练排序/调度头，但不等价于整局 target-200 strong positive。",
            "- `probe_hard_negative` 是带有明显 proxy 失败信号的分支行，例如低 proxy score、右删失、completion-bound retry、negative pricing event 或 child 未启动。",
            "- `probe_debug_training_ready=true` 只表示可以先跑离线数据加载、loss、checkpoint 和排序 sanity，不允许 production opt-in。",
            "- `probe_sanity_training_ready=true` 接近“可以开始一次像样的 probe 级离线训练”；production/opt-in 仍必须回到 strict full-replay 与 target-200 readiness。",
            "",
            "## 当前判断",
            "",
        ]
    )
    if summary["probe_debug_training_ready"]:
        lines.append("probe 级数据已经足够启动一次离线 debug 训练。")
    else:
        lines.append("probe 级数据连 debug 训练都偏薄，应继续补 top200 child-probe contexts。")
    if summary["probe_sanity_training_ready"]:
        lines.append("probe 级数据已经接近可以训练一个非上线 branch/proof head。")
    else:
        lines.append("probe 级数据还不足以支撑稳定试训，主要缺口见 remaining_for_probe_sanity_training。")
    lines.append(
        "无论 readiness 是否为 true，这份审计都不授权把 proxy score map 接入 production opt-in。"
    )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--min-started-child-count", type=int, default=1)
    parser.add_argument("--min-probe-positive-proxy-score", type=float, default=0.0)
    parser.add_argument("--max-hard-negative-proxy-score", type=float, default=-1.0)
    parser.add_argument("--min-hard-negative-completion-retry-count", type=float, default=1.0)
    parser.add_argument("--min-hard-negative-negative-pricing-event-count", type=float, default=1.0)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = build_probe_training_readiness(
        list(args.inputs),
        args.output_dir,
        args.report,
        min_started_child_count=args.min_started_child_count,
        min_probe_positive_proxy_score=args.min_probe_positive_proxy_score,
        max_hard_negative_proxy_score=args.max_hard_negative_proxy_score,
        min_hard_negative_completion_retry_count=args.min_hard_negative_completion_retry_count,
        min_hard_negative_negative_pricing_event_count=(
            args.min_hard_negative_negative_pricing_event_count
        ),
    )
    printable = {key: value for key, value in summary.items() if key != "rows"}
    print(json.dumps(printable, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
