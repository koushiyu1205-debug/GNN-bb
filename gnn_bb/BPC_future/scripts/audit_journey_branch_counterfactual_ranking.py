#!/usr/bin/env python3
"""Build branch-ranking diagnostics from counterfactual delta rows.

This script is offline and diagnostic-only. It reads counterfactual delta JSONL
artifacts and emits same-parent ranking pairs for branch-impact training. It
does not run BPC, pricing, RMP, or produce official bounds/certificates.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import date
import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_branch_counterfactual_ranking_20260624")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260624_bpc_future_journey_branch_counterfactual_ranking_zh.md"
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


def _load_rows(paths: Iterable[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        if path.is_dir():
            rows.extend(_iter_jsonl(path / "branch_counterfactual_delta_rows.jsonl"))
            continue
        if path.name == "summary.json":
            rows.extend(_iter_jsonl(path.parent / "branch_counterfactual_delta_rows.jsonl"))
            continue
        if path.suffix == ".jsonl":
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


def _pair_text(value: Any) -> str:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        return "?,?"
    return f"{_int(value[0])},{_int(value[1])}"


def _context_key(row: dict[str, Any]) -> tuple[str, int, int, str]:
    return (
        str(row.get("instance") or ""),
        _int(row.get("node_id"), -1),
        _int(row.get("depth"), -1),
        _pair_text(row.get("baseline_pair")),
    )


def _time_window_family(value: Any) -> str:
    text = str(value or "")
    for token in ("greedy-anchor", "random-wave", "sector-wave"):
        if token in text:
            return token
    return ""


def _metric(row: dict[str, Any], name: str) -> float:
    deltas = row.get("deltas")
    if not isinstance(deltas, dict):
        return 0.0
    return _float(deltas.get(name))


def _label(row: dict[str, Any], name: str) -> float:
    labels = row.get("labels")
    if not isinstance(labels, dict):
        return 0.0
    return _float(labels.get(name))


def _entry_id(row: dict[str, Any]) -> str:
    experiment = str(row.get("experiment") or "")
    return experiment[:2] if experiment[:2].isdigit() else experiment


def _ranking_preference(
    left: dict[str, Any],
    right: dict[str, Any],
    *,
    min_wall_gap: float,
    min_exact_pricing_gap: int,
) -> tuple[dict[str, Any], dict[str, Any], str] | None:
    left_wall = _metric(left, "wall_time_delta")
    right_wall = _metric(right, "wall_time_delta")
    wall_gap = abs(left_wall - right_wall)
    if wall_gap >= float(min_wall_gap):
        if left_wall < right_wall:
            return left, right, "wall_time_delta"
        return right, left, "wall_time_delta"

    left_exact = _metric(left, "exact_pricing_calls_delta")
    right_exact = _metric(right, "exact_pricing_calls_delta")
    exact_gap = abs(left_exact - right_exact)
    if exact_gap >= float(min_exact_pricing_gap):
        if left_exact < right_exact:
            return left, right, "exact_pricing_calls_delta"
        return right, left, "exact_pricing_calls_delta"
    return None


def _compact_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "experiment": row.get("experiment"),
        "entry_id": _entry_id(row),
        "alternative_pair": row.get("alternative_pair"),
        "wall_time_delta": round(_metric(row, "wall_time_delta"), 9),
        "exact_pricing_calls_delta": round(_metric(row, "exact_pricing_calls_delta"), 9),
        "node_count_delta": round(_metric(row, "node_count_delta"), 9),
        "pricing_calls_delta": round(_metric(row, "pricing_calls_delta"), 9),
        "child_negative_pricing_events_delta": round(
            _metric(row, "child_negative_pricing_events_delta"), 9
        ),
        "y_counterfactual_wall_improved": _label(row, "y_counterfactual_wall_improved"),
        "y_counterfactual_proof_cost_improved": _label(
            row, "y_counterfactual_proof_cost_improved"
        ),
        "y_counterfactual_regression": _label(row, "y_counterfactual_regression"),
    }


def _is_strong_positive(row: dict[str, Any]) -> bool:
    if str(row.get("counterfactual_label_type") or "") == "strong_positive":
        return True
    return bool(
        _label(row, "y_counterfactual_wall_improved") > 0
        or _label(row, "y_counterfactual_timeout_resolved") > 0
    )


def _matches_holdout_filter(row: dict[str, Any], holdout_instance_contains: tuple[str, ...]) -> bool:
    if not holdout_instance_contains:
        return False
    instance = str(row.get("instance") or "")
    return any(token and token in instance for token in holdout_instance_contains)


def _has_positive_holdout(
    row: dict[str, Any],
    holdout_instance_contains: tuple[str, ...] = (),
) -> bool:
    if not _is_strong_positive(row):
        return False
    baseline_raw = row.get("baseline_raw_row") if isinstance(row.get("baseline_raw_row"), dict) else {}
    alt_raw = row.get("alternative_raw_row") if isinstance(row.get("alternative_raw_row"), dict) else {}
    return bool(
        row.get("holdout_context")
        or row.get("is_holdout")
        or row.get("positive_holdout_context")
        or baseline_raw.get("holdout_context")
        or baseline_raw.get("is_holdout")
        or alt_raw.get("holdout_context")
        or alt_raw.get("is_holdout")
        or alt_raw.get("positive_holdout_context")
        or _matches_holdout_filter(row, holdout_instance_contains)
    )


def build_ranking_audit(
    inputs: list[Path],
    output_dir: Path,
    report: Path,
    *,
    min_wall_gap: float = 1.0,
    min_exact_pricing_gap: int = 1,
    positive_holdout_instance_contains: tuple[str, ...] = (),
) -> dict[str, Any]:
    rows = _load_rows(inputs)
    groups: dict[tuple[str, int, int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("alternative_forced_pair_matched") is False:
            continue
        groups[_context_key(row)].append(row)

    context_rows: list[dict[str, Any]] = []
    ranking_rows: list[dict[str, Any]] = []
    proxy_counter: Counter[str] = Counter()
    label_counter: Counter[str] = Counter()
    context_counter: Counter[str] = Counter()
    positive_context_keys: set[tuple[str, int, int, str]] = set()

    for row in rows:
        if _label(row, "y_counterfactual_wall_improved") > 0:
            label_counter["wall_improved"] += 1
        if _label(row, "y_counterfactual_proof_cost_improved") > 0:
            label_counter["proof_cost_improved"] += 1
        if _label(row, "y_counterfactual_regression") > 0:
            label_counter["regression"] += 1
        if (
            _metric(row, "child_negative_pricing_events_delta") < 0
            and _label(row, "y_counterfactual_regression") > 0
        ):
            proxy_counter["fewer_child_negative_but_regressed"] += 1
        if (
            _metric(row, "child_negative_pricing_events_delta") > 0
            and _label(row, "y_counterfactual_wall_improved") > 0
        ):
            proxy_counter["more_child_negative_but_wall_improved"] += 1
        if _is_strong_positive(row):
            positive_context_keys.add(_context_key(row))

    for key, group in sorted(groups.items(), key=lambda item: item[0]):
        sorted_group = sorted(group, key=lambda row: (_metric(row, "wall_time_delta"), _entry_id(row)))
        best = sorted_group[0]
        worst = sorted_group[-1]
        wall_spread = _metric(worst, "wall_time_delta") - _metric(best, "wall_time_delta")
        row = {
            "schema_version": "journey_branch_counterfactual_context_summary_v1",
            "diagnostic_only": True,
            "runs_bpc_or_pricing": False,
            "production_ready": False,
            "certificate_effect": False,
            "official_bound_effect": False,
            "instance": key[0],
            "node_id": key[1],
            "depth": key[2],
            "baseline_pair": key[3],
            "alternative_count": len(group),
            "wall_improved_count": sum(
                1 for item in group if _label(item, "y_counterfactual_wall_improved") > 0
            ),
            "proof_cost_improved_count": sum(
                1 for item in group if _label(item, "y_counterfactual_proof_cost_improved") > 0
            ),
            "regression_count": sum(
                1 for item in group if _label(item, "y_counterfactual_regression") > 0
            ),
            "best": _compact_row(best),
            "worst": _compact_row(worst),
            "wall_delta_spread": round(wall_spread, 9),
        }
        context_rows.append(row)
        if row["wall_improved_count"] and row["regression_count"]:
            context_counter["mixed_positive_negative_context"] += 1
        elif row["wall_improved_count"]:
            context_counter["positive_only_context"] += 1
        elif row["regression_count"]:
            context_counter["regression_only_context"] += 1
        else:
            context_counter["neutral_only_context"] += 1

        for left_index, left in enumerate(group):
            for right in group[left_index + 1 :]:
                preference = _ranking_preference(
                    left,
                    right,
                    min_wall_gap=min_wall_gap,
                    min_exact_pricing_gap=min_exact_pricing_gap,
                )
                if preference is None:
                    continue
                better, worse, reason = preference
                ranking_rows.append(
                    {
                        "schema_version": "journey_branch_counterfactual_ranking_pair_v1",
                        "diagnostic_only": True,
                        "runs_bpc_or_pricing": False,
                        "production_ready": False,
                        "certificate_effect": False,
                        "official_bound_effect": False,
                        "instance": key[0],
                        "node_id": key[1],
                        "depth": key[2],
                        "baseline_pair": key[3],
                        "preference_reason": reason,
                        "better": _compact_row(better),
                        "worse": _compact_row(worse),
                        "wall_delta_gap": round(
                            _metric(worse, "wall_time_delta") - _metric(better, "wall_time_delta"),
                            9,
                        ),
                        "exact_pricing_calls_gap": round(
                            _metric(worse, "exact_pricing_calls_delta")
                            - _metric(better, "exact_pricing_calls_delta"),
                            9,
                        ),
                    }
                )

    output_dir.mkdir(parents=True, exist_ok=True)
    context_path = output_dir / "counterfactual_context_summary_rows.jsonl"
    context_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in context_rows),
        encoding="utf-8",
    )
    ranking_path = output_dir / "counterfactual_ranking_pair_rows.jsonl"
    ranking_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in ranking_rows),
        encoding="utf-8",
    )
    strong_positive_rows = [row for row in rows if _is_strong_positive(row)]
    strong_positive_count = len(strong_positive_rows)
    strong_positive_context_count = len(positive_context_keys)
    strong_positive_instance_count = len(
        {str(row.get("instance") or "") for row in strong_positive_rows}
    )
    strong_positive_time_window_family_count = len(
        {
            family
            for family in (
                _time_window_family(row.get("instance")) for row in strong_positive_rows
            )
            if family
        }
    )
    regression_count = int(label_counter.get("regression", 0))
    positive_holdout_context_keys = {
        _context_key(row)
        for row in rows
        if _has_positive_holdout(row, positive_holdout_instance_contains)
    }
    positive_holdout_context_count = len(positive_holdout_context_keys)
    holdout_strong_positive_count = sum(
        1
        for row in strong_positive_rows
        if _context_key(row) in positive_holdout_context_keys
    )
    training_strong_positive_rows = [
        row for row in strong_positive_rows if _context_key(row) not in positive_holdout_context_keys
    ]
    training_strong_positive_count = len(training_strong_positive_rows)
    training_strong_positive_context_count = len(
        {_context_key(row) for row in training_strong_positive_rows}
    )
    training_strong_positive_instance_count = len(
        {str(row.get("instance") or "") for row in training_strong_positive_rows}
    )
    training_strong_positive_time_window_family_count = len(
        {
            family
            for family in (
                _time_window_family(row.get("instance"))
                for row in training_strong_positive_rows
            )
            if family
        }
    )
    training_regression_count = regression_count
    strict_training_requirements = {
        "strong_positive_min": 5,
        "distinct_parent_context_min": 3,
        "distinct_instance_min": 3,
        "distinct_time_window_family_min": 2,
        "regression_at_least_positive": True,
        "positive_holdout_context_min": 1,
    }
    minimal_ranking_signal_ready = bool(ranking_rows)
    strict_ranking_training_ready = bool(
        minimal_ranking_signal_ready
        and strong_positive_count >= strict_training_requirements["strong_positive_min"]
        and strong_positive_context_count
        >= strict_training_requirements["distinct_parent_context_min"]
        and strong_positive_instance_count
        >= strict_training_requirements["distinct_instance_min"]
        and strong_positive_time_window_family_count
        >= strict_training_requirements["distinct_time_window_family_min"]
        and regression_count >= strong_positive_count
        and positive_holdout_context_count
        >= strict_training_requirements["positive_holdout_context_min"]
    )

    summary = {
        "schema_version": "journey_branch_counterfactual_ranking_audit_v2",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "input_paths": [str(path) for path in inputs],
        "output_dir": str(output_dir),
        "counterfactual_row_count": len(rows),
        "context_count": len(context_rows),
        "ranking_pair_count": len(ranking_rows),
        "min_wall_gap": float(min_wall_gap),
        "min_exact_pricing_gap": int(min_exact_pricing_gap),
        "label_counts": dict(sorted(label_counter.items())),
        "context_counts": dict(sorted(context_counter.items())),
        "proxy_contradiction_counts": dict(sorted(proxy_counter.items())),
        "minimal_ranking_signal_ready": minimal_ranking_signal_ready,
        "strict_ranking_training_requirements": strict_training_requirements,
        "strong_positive_count": strong_positive_count,
        "strong_positive_context_count": strong_positive_context_count,
        "strong_positive_instance_count": strong_positive_instance_count,
        "strong_positive_time_window_family_count": (
            strong_positive_time_window_family_count
        ),
        "positive_holdout_instance_contains": list(positive_holdout_instance_contains),
        "positive_holdout_context_count": positive_holdout_context_count,
        "holdout_strong_positive_count": holdout_strong_positive_count,
        "training_strong_positive_count": training_strong_positive_count,
        "training_strong_positive_context_count": (
            training_strong_positive_context_count
        ),
        "training_strong_positive_instance_count": (
            training_strong_positive_instance_count
        ),
        "training_strong_positive_time_window_family_count": (
            training_strong_positive_time_window_family_count
        ),
        "training_regression_count": training_regression_count,
        "training_regression_at_least_positive": (
            training_regression_count >= training_strong_positive_count
        ),
        "strict_ranking_training_ready": strict_ranking_training_ready,
        "ranking_training_ready": strict_ranking_training_ready,
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
        "# Journey Branch Counterfactual Ranking Audit",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 目的",
        "",
        "把同一 parent context 下的 branch alternative delta 转成排序对，并统计局部 proxy 是否误导。该脚本只读既有 delta JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。",
        "",
        "## 机器字段",
        "",
        "```text",
    ]
    for key in [
        "counterfactual_row_count",
        "context_count",
        "ranking_pair_count",
        "label_counts",
        "context_counts",
        "proxy_contradiction_counts",
        "minimal_ranking_signal_ready",
        "strict_ranking_training_ready",
        "strong_positive_count",
        "strong_positive_context_count",
        "strong_positive_instance_count",
        "strong_positive_time_window_family_count",
        "positive_holdout_instance_contains",
        "positive_holdout_context_count",
        "holdout_strong_positive_count",
        "training_strong_positive_count",
        "training_strong_positive_context_count",
        "training_strong_positive_instance_count",
        "training_strong_positive_time_window_family_count",
        "training_regression_count",
        "training_regression_at_least_positive",
        "ranking_training_ready",
        "production_ready",
        "certificate_effect",
        "official_bound_effect",
    ]:
        lines.append(f"{key} = {summary.get(key)}")
    lines.extend(["```", "", "## 关键 context", ""])
    for row in context_rows[:10]:
        lines.append(
            "- "
            f"node={row['node_id']} depth={row['depth']} baseline=[{row['baseline_pair']}], "
            f"alts={row['alternative_count']}, spread={row['wall_delta_spread']}, "
            f"best={row['best']['entry_id']} {row['best']['alternative_pair']} "
            f"wall_delta={row['best']['wall_time_delta']}, "
            f"worst={row['worst']['entry_id']} {row['worst']['alternative_pair']} "
            f"wall_delta={row['worst']['wall_time_delta']}"
        )
    lines.extend(["", "## 判断", ""])
    lines.append(
        "这些 ranking pair 只能训练或评估 branch-impact 排序；不能作为剪枝依据、no-negative certificate、official bound 或 exact pricing 替代品。"
    )
    if summary.get("proxy_contradiction_counts"):
        lines.append(
            "proxy_contradiction_counts 非空说明 child negative count / pool proxy 不能直接当排序标签。"
        )
    if not ranking_rows:
        lines.append("当前没有形成有效排序对，需要继续补同 parent alternatives。")
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--min-wall-gap", type=float, default=1.0)
    parser.add_argument("--min-exact-pricing-gap", type=int, default=1)
    parser.add_argument(
        "--positive-holdout-instance-contains",
        action="append",
        default=[],
        help=(
            "Mark strong-positive rows whose instance path contains this token as "
            "positive holdout context for offline readiness diagnostics. May be repeated."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = build_ranking_audit(
        list(args.paths),
        args.output_dir,
        args.report,
        min_wall_gap=args.min_wall_gap,
        min_exact_pricing_gap=args.min_exact_pricing_gap,
        positive_holdout_instance_contains=tuple(args.positive_holdout_instance_contains),
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
