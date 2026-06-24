#!/usr/bin/env python3
"""Audit branch-score coverage on logged Journey branch candidates.

This script is diagnostic-only. It reads a branch-score map and existing solver
JSONL logs, then reports whether scores hit the logged Ryan-Foster candidates
and whether the best scored candidate would change the selected pair within the
same branch-candidate eligibility horizon used by the solver. It does not run
BPC, pricing, RMP, or produce official bounds/certificates.
"""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_branch_score_candidate_coverage_20260624")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260624_bpc_future_journey_branch_score_candidate_coverage_zh.md"
)


def _iter_jsonl(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if path.is_file() and path.suffix == ".jsonl":
            yield path
        elif path.is_dir():
            yield from sorted(path.rglob("*.jsonl"))


def _read_events(path: Path) -> Iterable[dict[str, Any]]:
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            yield payload


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


def _pair(candidate: Any) -> tuple[int, int] | None:
    if not isinstance(candidate, dict):
        return None
    if candidate.get("task_i") is None or candidate.get("task_j") is None:
        return None
    try:
        i, j = int(candidate["task_i"]), int(candidate["task_j"])
    except (TypeError, ValueError):
        return None
    if i == j:
        return None
    return tuple(sorted((i, j)))


def _pair_text(pair: tuple[int, int] | None) -> str | None:
    if pair is None:
        return None
    return f"{int(pair[0])},{int(pair[1])}"


def _score_lookup_keys(pair: tuple[int, int], *, node_id: int | None, depth: int | None) -> tuple[str, ...]:
    pair_text = _pair_text(pair)
    assert pair_text is not None
    keys: list[str] = []
    if node_id is not None and depth is not None:
        keys.extend(
            (
                f"node:{int(node_id)}:depth:{int(depth)}:{pair_text}",
                f"node:{int(node_id)}:depth:{int(depth)}:pair:{pair_text}",
            )
        )
    if depth is not None:
        keys.extend((f"depth:{int(depth)}:{pair_text}", f"depth:{int(depth)}:pair:{pair_text}"))
    if node_id is not None:
        keys.extend((f"node:{int(node_id)}:{pair_text}", f"node:{int(node_id)}:pair:{pair_text}"))
    keys.extend((pair_text, f"pair:{pair_text}"))
    return tuple(keys)


def _load_score_map(path: Path) -> dict[str, float]:
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    score_map: dict[str, float] = {}
    if isinstance(raw, dict):
        for key, value in raw.items():
            score = _score_value(value)
            if score is not None:
                score_map[str(key)] = score
    elif isinstance(raw, list):
        for row in raw:
            if not isinstance(row, dict):
                continue
            key = row.get("key")
            score = _score_value(row)
            if key is not None and score is not None:
                score_map[str(key)] = score
    return score_map


def _score_value(value: Any) -> float | None:
    raw = value
    if isinstance(value, dict):
        raw = value.get("branch_score", value.get("score"))
    if raw is None:
        return None
    try:
        parsed = float(raw)
    except (TypeError, ValueError):
        return None
    if parsed != parsed:
        return None
    return float(parsed)


def _candidate_score(
    candidate: dict[str, Any],
    score_map: dict[str, float],
    *,
    node_id: int | None,
    depth: int | None,
) -> tuple[float | None, str | None]:
    pair = _pair(candidate)
    if pair is None:
        return None, None
    for key in _score_lookup_keys(pair, node_id=node_id, depth=depth):
        if key in score_map:
            return float(score_map[key]), key
    return None, None


def _logged_candidates(record: dict[str, Any]) -> list[dict[str, Any]]:
    seen: set[tuple[int, int]] = set()
    candidates: list[dict[str, Any]] = []
    for key in ("priority_top", "top"):
        values = record.get(key)
        if not isinstance(values, list):
            continue
        for candidate in values:
            pair = _pair(candidate)
            if pair is None or pair in seen:
                continue
            seen.add(pair)
            candidates.append(candidate)
    return candidates


def _eligible_candidates(
    candidates: list[dict[str, Any]],
    *,
    tie_tolerance: float,
) -> list[dict[str, Any]]:
    if not candidates:
        return []
    max_frac = max(_float(candidate.get("fractionality")) for candidate in candidates)
    tolerance = max(0.0, float(tie_tolerance))
    return [
        candidate
        for candidate in candidates
        if _float(candidate.get("fractionality")) >= float(max_frac) - tolerance - 1.0e-12
    ]


def _required_tie_tolerance(max_fractionality: float | None, candidate_fractionality: Any) -> float | None:
    if max_fractionality is None:
        return None
    try:
        fractionality = float(candidate_fractionality)
    except (TypeError, ValueError):
        return None
    if fractionality != fractionality:
        return None
    return round(max(0.0, float(max_fractionality) - float(fractionality)), 9)


def _candidate_event_row(
    record: dict[str, Any],
    *,
    log_path: Path,
    score_map: dict[str, float],
    tie_tolerance_override: float | None = None,
    score_min_score: float | None = None,
) -> dict[str, Any]:
    node_id = _int(record.get("node_id"), -1)
    depth = _int(record.get("depth"), -1)
    selected = record.get("selected")
    selected_pair = _pair(selected)
    selected_score = None
    selected_score_source = None
    if isinstance(selected, dict):
        selected_score, selected_score_source = _candidate_score(
            selected,
            score_map,
            node_id=node_id,
            depth=depth,
        )
        if score_min_score is not None and selected_score is not None and float(selected_score) <= float(score_min_score):
            selected_score = None
            selected_score_source = None
    candidates = _logged_candidates(record)
    max_logged_fractionality = None
    if candidates:
        max_logged_fractionality = max(_float(candidate.get("fractionality")) for candidate in candidates)
    raw_tie_tolerance = record.get("tie_tolerance", 0.0)
    tie_tolerance = _float(raw_tie_tolerance, 0.0) if tie_tolerance_override is None else float(tie_tolerance_override)
    eligible_pairs = {
        pair
        for pair in (_pair(candidate) for candidate in _eligible_candidates(candidates, tie_tolerance=tie_tolerance))
        if pair is not None
    }
    scored_candidates: list[dict[str, Any]] = []
    eligible_scored_candidates: list[dict[str, Any]] = []
    unscored_candidates: list[dict[str, Any]] = []
    for candidate in candidates:
        score, source = _candidate_score(candidate, score_map, node_id=node_id, depth=depth)
        pair = _pair(candidate)
        if score_min_score is not None and score is not None and float(score) <= float(score_min_score):
            score = None
            source = None
        if score is None:
            if pair is not None:
                unscored_candidates.append(_compact_candidate(candidate, pair=pair))
            continue
        row = {
            "task_i": int(pair[0]) if pair else None,
            "task_j": int(pair[1]) if pair else None,
            "pair": None if pair is None else list(pair),
            "score": round(float(score), 9),
            "score_source": source,
            "fractionality": candidate.get("fractionality"),
            "required_tie_tolerance": _required_tie_tolerance(
                max_logged_fractionality,
                candidate.get("fractionality"),
            ),
            "same_mass": candidate.get("same_mass"),
        }
        scored_candidates.append(row)
        if pair in eligible_pairs:
            eligible_scored_candidates.append(row)
    scored_candidates.sort(key=lambda item: (-_float(item.get("score")), int(item["task_i"] or 0), int(item["task_j"] or 0)))
    eligible_scored_candidates.sort(
        key=lambda item: (-_float(item.get("score")), int(item["task_i"] or 0), int(item["task_j"] or 0))
    )
    best_scored = scored_candidates[0] if scored_candidates else None
    best_eligible_scored = eligible_scored_candidates[0] if eligible_scored_candidates else None
    best_pair = None if best_scored is None else tuple(best_scored["pair"])
    best_eligible_pair = None if best_eligible_scored is None else tuple(best_eligible_scored["pair"])
    best_scored_required_tie_tolerance = (
        None if best_scored is None else best_scored.get("required_tie_tolerance")
    )
    best_scored_requires_recorded_horizon_expansion = bool(
        best_scored_required_tie_tolerance is not None
        and float(best_scored_required_tie_tolerance) > _float(raw_tie_tolerance, 0.0) + 1.0e-12
    )
    best_scored_requires_effective_horizon_expansion = bool(
        best_scored_required_tie_tolerance is not None
        and float(best_scored_required_tie_tolerance) > float(tie_tolerance) + 1.0e-12
    )
    selected_pair_text = _pair_text(selected_pair)
    best_pair_text = _pair_text(best_pair)
    best_eligible_pair_text = _pair_text(best_eligible_pair)
    candidate_count = _int(record.get("candidate_count"), 0)
    logged_count = len(candidates)
    return {
        "schema_version": "journey_branch_score_candidate_coverage_row_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "log_path": str(log_path),
        "node_id": node_id,
        "depth": depth,
        "priority_mode": record.get("priority_mode"),
        "recorded_tie_tolerance": _float(raw_tie_tolerance, 0.0),
        "tie_tolerance": round(float(tie_tolerance), 9),
        "tie_tolerance_overridden": tie_tolerance_override is not None,
        "candidate_count": candidate_count,
        "eligible_count": record.get("eligible_count"),
        "max_logged_fractionality": None
        if max_logged_fractionality is None
        else round(float(max_logged_fractionality), 9),
        "eligible_logged_candidate_count": len(eligible_pairs),
        "logged_candidate_count": logged_count,
        "full_logged_candidate_coverage": bool(candidate_count > 0 and logged_count >= candidate_count),
        "selected_pair": selected_pair_text,
        "selected_fractionality": None if not isinstance(selected, dict) else selected.get("fractionality"),
        "selected_score": None if selected_score is None else round(float(selected_score), 9),
        "selected_score_source": selected_score_source,
        "scored_candidate_count": len(scored_candidates),
        "eligible_scored_candidate_count": len(eligible_scored_candidates),
        "unscored_logged_candidate_count": len(unscored_candidates),
        "selected_is_unscored": bool(selected_pair is not None and selected_score is None),
        "best_scored_pair": best_pair_text,
        "best_scored_score": None if best_scored is None else best_scored.get("score"),
        "best_scored_source": None if best_scored is None else best_scored.get("score_source"),
        "best_scored_fractionality": None if best_scored is None else best_scored.get("fractionality"),
        "best_scored_required_tie_tolerance": best_scored_required_tie_tolerance,
        "best_scored_requires_recorded_horizon_expansion": best_scored_requires_recorded_horizon_expansion,
        "best_scored_requires_effective_horizon_expansion": best_scored_requires_effective_horizon_expansion,
        "best_eligible_scored_pair": best_eligible_pair_text,
        "best_eligible_scored_score": None if best_eligible_scored is None else best_eligible_scored.get("score"),
        "best_eligible_scored_source": None if best_eligible_scored is None else best_eligible_scored.get("score_source"),
        "best_eligible_scored_fractionality": None
        if best_eligible_scored is None
        else best_eligible_scored.get("fractionality"),
        "best_eligible_scored_required_tie_tolerance": None
        if best_eligible_scored is None
        else best_eligible_scored.get("required_tie_tolerance"),
        "would_change_selected": bool(
            best_eligible_pair_text is not None and best_eligible_pair_text != selected_pair_text
        ),
        "would_change_selected_any_logged": bool(best_pair_text is not None and best_pair_text != selected_pair_text),
        "scored_candidates": scored_candidates[:12],
        "eligible_scored_candidates": eligible_scored_candidates[:12],
        "unscored_candidates": unscored_candidates[:12],
    }


def _compact_candidate(candidate: dict[str, Any], *, pair: tuple[int, int]) -> dict[str, Any]:
    return {
        "task_i": int(pair[0]),
        "task_j": int(pair[1]),
        "pair": list(pair),
        "fractionality": candidate.get("fractionality"),
        "same_mass": candidate.get("same_mass"),
        "support_count": candidate.get("support_count"),
        "pool_same_allowed": candidate.get("pool_same_allowed"),
        "pool_separate_allowed": candidate.get("pool_separate_allowed"),
        "pool_max_child_width": candidate.get("pool_max_child_width"),
        "pool_total_child_width": candidate.get("pool_total_child_width"),
        "pool_balance_gap": candidate.get("pool_balance_gap"),
    }


def build_branch_score_candidate_coverage(
    *,
    score_path: Path,
    log_paths: list[Path],
    output_dir: Path,
    report: Path,
    tie_tolerance_override: float | None = None,
    score_min_score: float | None = None,
) -> dict[str, Any]:
    score_map = _load_score_map(score_path)
    rows: list[dict[str, Any]] = []
    for log_path in _iter_jsonl(log_paths):
        for record in _read_events(log_path):
            if record.get("event") != "journey_branch_candidates":
                continue
            rows.append(
                _candidate_event_row(
                    record,
                    log_path=log_path,
                    score_map=score_map,
                    tie_tolerance_override=tie_tolerance_override,
                    score_min_score=score_min_score,
                )
            )

    required_tolerances = [
        float(row["best_scored_required_tie_tolerance"])
        for row in rows
        if row.get("best_scored_required_tie_tolerance") is not None
    ]
    summary = {
        "schema_version": "journey_branch_score_candidate_coverage_summary_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "score_path": str(score_path),
        "score_entry_count": len(score_map),
        "log_paths": [str(path) for path in log_paths],
        "output_dir": str(output_dir),
        "tie_tolerance_override": tie_tolerance_override,
        "score_min_score": score_min_score,
        "candidate_event_count": len(rows),
        "candidate_event_with_score_hit_count": sum(1 for row in rows if row["scored_candidate_count"] > 0),
        "candidate_event_with_eligible_score_hit_count": sum(
            1 for row in rows if row["eligible_scored_candidate_count"] > 0
        ),
        "candidate_event_with_selected_score_count": sum(1 for row in rows if row["selected_score"] is not None),
        "candidate_event_would_change_selected_count": sum(1 for row in rows if row["would_change_selected"]),
        "candidate_event_would_change_selected_any_logged_count": sum(
            1 for row in rows if row["would_change_selected_any_logged"]
        ),
        "candidate_event_with_best_scored_requiring_recorded_horizon_expansion_count": sum(
            1 for row in rows if row["best_scored_requires_recorded_horizon_expansion"]
        ),
        "candidate_event_with_best_scored_requiring_effective_horizon_expansion_count": sum(
            1 for row in rows if row["best_scored_requires_effective_horizon_expansion"]
        ),
        "best_scored_required_tie_tolerance_count": len(required_tolerances),
        "best_scored_required_tie_tolerance_le_0_count": sum(
            1 for value in required_tolerances if value <= 1.0e-12
        ),
        "best_scored_required_tie_tolerance_le_0_05_count": sum(
            1 for value in required_tolerances if value <= 0.05 + 1.0e-12
        ),
        "best_scored_required_tie_tolerance_le_0_1_count": sum(
            1 for value in required_tolerances if value <= 0.1 + 1.0e-12
        ),
        "best_scored_required_tie_tolerance_le_0_2_count": sum(
            1 for value in required_tolerances if value <= 0.2 + 1.0e-12
        ),
        "best_scored_required_tie_tolerance_gt_0_2_count": sum(
            1 for value in required_tolerances if value > 0.2 + 1.0e-12
        ),
        "best_scored_required_tie_tolerance_max": None
        if not required_tolerances
        else round(max(required_tolerances), 9),
        "full_logged_candidate_coverage_count": sum(1 for row in rows if row["full_logged_candidate_coverage"]),
        "scored_candidate_count_sum": sum(int(row["scored_candidate_count"]) for row in rows),
        "eligible_scored_candidate_count_sum": sum(int(row["eligible_scored_candidate_count"]) for row in rows),
        "unscored_logged_candidate_count_sum": sum(int(row["unscored_logged_candidate_count"]) for row in rows),
        "selected_unscored_count": sum(1 for row in rows if row["selected_is_unscored"]),
        "rows": rows,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "branch_score_candidate_coverage_rows.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(report, summary, rows)
    return summary


def _write_report(report: Path, summary: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Journey Branch Score Candidate Coverage",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 目的",
        "",
        "统计 branch-score map 对已有 `journey_branch_candidates` 日志的命中情况。该脚本只读 score map 和 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。",
        "",
        "## 机器字段",
        "",
        "```text",
    ]
    for key in [
        "score_entry_count",
        "tie_tolerance_override",
        "score_min_score",
        "candidate_event_count",
        "candidate_event_with_score_hit_count",
        "candidate_event_with_eligible_score_hit_count",
        "candidate_event_with_selected_score_count",
        "candidate_event_would_change_selected_count",
        "candidate_event_would_change_selected_any_logged_count",
        "candidate_event_with_best_scored_requiring_recorded_horizon_expansion_count",
        "candidate_event_with_best_scored_requiring_effective_horizon_expansion_count",
        "best_scored_required_tie_tolerance_count",
        "best_scored_required_tie_tolerance_le_0_count",
        "best_scored_required_tie_tolerance_le_0_05_count",
        "best_scored_required_tie_tolerance_le_0_1_count",
        "best_scored_required_tie_tolerance_le_0_2_count",
        "best_scored_required_tie_tolerance_gt_0_2_count",
        "best_scored_required_tie_tolerance_max",
        "full_logged_candidate_coverage_count",
        "scored_candidate_count_sum",
        "eligible_scored_candidate_count_sum",
        "unscored_logged_candidate_count_sum",
        "selected_unscored_count",
        "production_ready",
        "official_bound_effect",
    ]:
        lines.append(f"{key} = {summary.get(key)}")
    lines.extend(["```", "", "## 命中行", ""])
    hit_rows = [row for row in rows if row["scored_candidate_count"] > 0]
    for row in hit_rows[:20]:
        lines.append(
            "- "
            f"log={Path(row['log_path']).name}, node={row['node_id']}, depth={row['depth']}, "
            f"selected={row['selected_pair']}, selected_score={row['selected_score']}, "
            f"best_scored={row['best_scored_pair']}:{row['best_scored_score']}, "
            f"best_scored_required_tie_tolerance={row['best_scored_required_tie_tolerance']}, "
            f"best_eligible={row['best_eligible_scored_pair']}:{row['best_eligible_scored_score']}, "
            f"would_change={row['would_change_selected']}, "
            f"would_change_any_logged={row['would_change_selected_any_logged']}, "
            f"scored_count={row['scored_candidate_count']}/{row['logged_candidate_count']}, "
            f"eligible_scored_count={row['eligible_scored_candidate_count']}/{row['eligible_logged_candidate_count']}, "
            f"unscored_count={row['unscored_logged_candidate_count']}"
        )
    if not hit_rows:
        lines.append("- 无 score 命中。")
    lines.extend(["", "## 边界", ""])
    lines.append(
        "覆盖审计只说明 score map 是否能命中已记录候选；它不能证明 branch-score A/B 的 wall-time 收益，也不能作为 official bound 或 certificate。"
    )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--score-path", type=Path, required=True)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--override-tie-tolerance",
        type=float,
        default=None,
        help="Evaluate coverage under this candidate-horizon tolerance instead of the value recorded in logs.",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=None,
        help="Treat scores at or below this value as unscored, matching positive-only branch_score_horizon audits.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = build_branch_score_candidate_coverage(
        score_path=args.score_path,
        log_paths=list(args.paths),
        output_dir=args.output_dir,
        report=args.report,
        tie_tolerance_override=args.override_tie_tolerance,
        score_min_score=args.min_score,
    )
    print(json.dumps({key: value for key, value in summary.items() if key != "rows"}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
