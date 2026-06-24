#!/usr/bin/env python3
"""Build an opt-in branch-score map from counterfactual ranking rows.

This script is offline and diagnostic-only. It reads existing
counterfactual-ranking JSONL artifacts and emits score maps that can be passed
to the solver with ``journey_branch_candidate_priority=branch_score``. It does
not run BPC, pricing, RMP, or produce official bounds/certificates.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_branch_score_map_20260624")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_score_map_zh.md"
)


@dataclass
class _ScoreAccumulator:
    score_sum: float = 0.0
    comparison_count: int = 0
    win_count: int = 0
    loss_count: int = 0
    wall_gap_sum: float = 0.0
    exact_gap_sum: float = 0.0
    instance: str = ""
    node_id: int | None = None
    depth: int | None = None
    pair: tuple[int, int] = (0, 0)


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


def _load_ranking_rows(paths: Iterable[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        if path.is_dir():
            rows.extend(_iter_jsonl(path / "counterfactual_ranking_pair_rows.jsonl"))
            continue
        if path.name == "summary.json":
            rows.extend(_iter_jsonl(path.parent / "counterfactual_ranking_pair_rows.jsonl"))
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


def _int_or_none(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _pair_tuple(value: Any) -> tuple[int, int] | None:
    if isinstance(value, str):
        pieces = [piece.strip() for piece in value.replace(";", ",").split(",") if piece.strip()]
        if len(pieces) != 2:
            return None
        try:
            i, j = int(pieces[0]), int(pieces[1])
        except ValueError:
            return None
        if i == j:
            return None
        return tuple(sorted((i, j)))
    if isinstance(value, (list, tuple)) and len(value) == 2:
        try:
            i, j = int(value[0]), int(value[1])
        except (TypeError, ValueError):
            return None
        if i == j:
            return None
        return tuple(sorted((i, j)))
    return None


def _compact_pair(row: dict[str, Any], side: str) -> tuple[int, int] | None:
    payload = row.get(side)
    if not isinstance(payload, dict):
        return None
    return _pair_tuple(payload.get("alternative_pair"))


def _score_weight(
    row: dict[str, Any],
    *,
    wall_gap_scale: float,
    exact_gap_scale: float,
    max_weight: float,
) -> float:
    wall_bonus = max(0.0, _float(row.get("wall_delta_gap"))) / max(1.0e-9, float(wall_gap_scale))
    exact_bonus = max(0.0, _float(row.get("exact_pricing_calls_gap"))) / max(1.0e-9, float(exact_gap_scale))
    return min(max(1.0, float(max_weight)), 1.0 + wall_bonus + exact_bonus)


def _score_key(
    pair: tuple[int, int],
    *,
    key_scope: str,
    node_id: int | None,
    depth: int | None,
) -> str:
    i, j = pair
    pair_text = f"{i},{j}"
    if key_scope == "node_depth" and node_id is not None and depth is not None:
        return f"node:{int(node_id)}:depth:{int(depth)}:{pair_text}"
    if key_scope == "depth" and depth is not None:
        return f"depth:{int(depth)}:{pair_text}"
    return pair_text


def _row_from_accumulator(key: str, acc: _ScoreAccumulator) -> dict[str, Any]:
    score = acc.score_sum / max(1, acc.comparison_count)
    task_i, task_j = acc.pair
    return {
        "schema_version": "journey_branch_score_row_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "key": key,
        "instance": acc.instance,
        "node_id": acc.node_id,
        "depth": acc.depth,
        "pair": [task_i, task_j],
        "task_i": task_i,
        "task_j": task_j,
        "score": round(float(score), 9),
        "branch_score": round(float(score), 9),
        "comparison_count": int(acc.comparison_count),
        "win_count": int(acc.win_count),
        "loss_count": int(acc.loss_count),
        "wall_delta_gap_sum": round(float(acc.wall_gap_sum), 9),
        "exact_pricing_calls_gap_sum": round(float(acc.exact_gap_sum), 9),
        "score_source": "counterfactual_ranking_pairs",
    }


def build_branch_score_map(
    inputs: list[Path],
    output_dir: Path,
    report: Path,
    *,
    key_scope: str = "node_depth",
    wall_gap_scale: float = 60.0,
    exact_gap_scale: float = 10.0,
    max_weight: float = 10.0,
    include_instance_contains: tuple[str, ...] = (),
    exclude_instance_contains: tuple[str, ...] = (),
) -> dict[str, Any]:
    if key_scope not in {"node_depth", "depth", "pair"}:
        raise ValueError(f"unsupported key_scope: {key_scope}")

    raw_ranking_rows = _load_ranking_rows(inputs)
    ranking_rows = [
        row
        for row in raw_ranking_rows
        if _instance_filter_accepts(
            str(row.get("instance") or ""),
            include_contains=include_instance_contains,
            exclude_contains=exclude_instance_contains,
        )
    ]
    accumulators: dict[str, _ScoreAccumulator] = {}
    skipped_rows = 0

    for row in ranking_rows:
        if row.get("official_bound_effect") not in (False, None):
            skipped_rows += 1
            continue
        better_pair = _compact_pair(row, "better")
        worse_pair = _compact_pair(row, "worse")
        if better_pair is None or worse_pair is None:
            skipped_rows += 1
            continue
        node_id = _int_or_none(row.get("node_id"))
        depth = _int_or_none(row.get("depth"))
        instance = str(row.get("instance") or "")
        weight = _score_weight(
            row,
            wall_gap_scale=wall_gap_scale,
            exact_gap_scale=exact_gap_scale,
            max_weight=max_weight,
        )
        wall_gap = max(0.0, _float(row.get("wall_delta_gap")))
        exact_gap = max(0.0, _float(row.get("exact_pricing_calls_gap")))
        for pair, sign in ((better_pair, 1.0), (worse_pair, -1.0)):
            key = _score_key(pair, key_scope=key_scope, node_id=node_id, depth=depth)
            if key not in accumulators:
                accumulators[key] = _ScoreAccumulator(
                    instance=instance,
                    node_id=node_id,
                    depth=depth,
                    pair=pair,
                )
            acc = accumulators[key]
            acc.score_sum += float(sign) * float(weight)
            acc.comparison_count += 1
            acc.wall_gap_sum += wall_gap
            acc.exact_gap_sum += exact_gap
            if sign > 0:
                acc.win_count += 1
            else:
                acc.loss_count += 1

    score_rows = [
        _row_from_accumulator(key, acc)
        for key, acc in sorted(
            accumulators.items(),
            key=lambda item: (
                item[1].instance,
                -abs(item[1].score_sum / max(1, item[1].comparison_count)),
                item[0],
            ),
        )
    ]
    score_map = {str(row["key"]): float(row["score"]) for row in score_rows}

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "journey_branch_score_rows.json").write_text(
        json.dumps(score_rows, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "journey_branch_score_rows.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in score_rows),
        encoding="utf-8",
    )
    (output_dir / "journey_branch_score_map.json").write_text(
        json.dumps(score_map, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    instance_count = len({str(row.get("instance") or "") for row in ranking_rows if row.get("instance")})
    summary = {
        "schema_version": "journey_branch_score_map_summary_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "input_paths": [str(path) for path in inputs],
        "output_dir": str(output_dir),
        "key_scope": key_scope,
        "raw_ranking_pair_row_count": len(raw_ranking_rows),
        "ranking_pair_row_count": len(ranking_rows),
        "filtered_out_row_count": len(raw_ranking_rows) - len(ranking_rows),
        "skipped_row_count": int(skipped_rows),
        "branch_score_row_count": len(score_rows),
        "branch_score_map_entry_count": len(score_map),
        "instance_count": int(instance_count),
        "wall_gap_scale": float(wall_gap_scale),
        "exact_gap_scale": float(exact_gap_scale),
        "max_weight": float(max_weight),
        "include_instance_contains": list(include_instance_contains),
        "exclude_instance_contains": list(exclude_instance_contains),
        "solver_priority_mode": "branch_score",
        "solver_score_path": str(output_dir / "journey_branch_score_rows.json"),
        "solver_score_map_path": str(output_dir / "journey_branch_score_map.json"),
        "usable_as_certificate": False,
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    _write_report(report, summary, score_rows)
    return summary


def _instance_filter_accepts(
    instance: str,
    *,
    include_contains: tuple[str, ...],
    exclude_contains: tuple[str, ...],
) -> bool:
    if include_contains and not any(token in instance for token in include_contains):
        return False
    if exclude_contains and any(token in instance for token in exclude_contains):
        return False
    return True


def _write_report(report: Path, summary: dict[str, Any], score_rows: list[dict[str, Any]]) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = [
        "# Journey Branch Score Map",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 目的",
        "",
        "把 V33 这类同 parent counterfactual ranking rows 转成 solver 的 `branch_score` opt-in 输入。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。",
        "",
        "## 机器字段",
        "",
        "```text",
    ]
    for key in [
        "ranking_pair_row_count",
        "raw_ranking_pair_row_count",
        "filtered_out_row_count",
        "branch_score_row_count",
        "branch_score_map_entry_count",
        "instance_count",
        "key_scope",
        "include_instance_contains",
        "exclude_instance_contains",
        "solver_priority_mode",
        "solver_score_path",
        "production_ready",
        "certificate_effect",
        "official_bound_effect",
    ]:
        lines.append(f"{key} = {summary.get(key)}")
    lines.extend(["```", "", "## Top Score Rows", ""])
    for row in score_rows[:12]:
        lines.append(
            "- "
            f"key={row['key']} pair={row['pair']} score={row['score']} "
            f"wins={row['win_count']} losses={row['loss_count']} "
            f"comparisons={row['comparison_count']}"
        )
    lines.extend(["", "## 使用边界", ""])
    lines.append(
        "使用方式：`journey_branch_candidate_priority=branch_score`，并把 `journey_branch_candidate_score_path` 指向 `journey_branch_score_rows.json`。"
    )
    lines.append(
        "`branch_score` 只改变 opt-in 的 Ryan-Foster pair 排序；排序范围仍由 `journey_branch_fractionality_tie_tolerance` 决定。"
    )
    lines.append(
        "它不能提供 official bound、no-negative certificate 或 fathom 依据；所有 child 最终仍必须靠 exact pricing closure。"
    )
    if summary.get("instance_count", 0) > 1:
        lines.append(
            "当前 score map 聚合了多个实例；在没有在线模型泛化验证前，不应直接作为 production 配置批量使用。"
        )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--key-scope", choices=("node_depth", "depth", "pair"), default="node_depth")
    parser.add_argument("--wall-gap-scale", type=float, default=60.0)
    parser.add_argument("--exact-gap-scale", type=float, default=10.0)
    parser.add_argument("--max-weight", type=float, default=10.0)
    parser.add_argument("--include-instance-contains", action="append", default=[])
    parser.add_argument("--exclude-instance-contains", action="append", default=[])
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = build_branch_score_map(
        list(args.paths),
        args.output_dir,
        args.report,
        key_scope=args.key_scope,
        wall_gap_scale=args.wall_gap_scale,
        exact_gap_scale=args.exact_gap_scale,
        max_weight=args.max_weight,
        include_instance_contains=tuple(args.include_instance_contains or ()),
        exclude_instance_contains=tuple(args.exclude_instance_contains or ()),
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
