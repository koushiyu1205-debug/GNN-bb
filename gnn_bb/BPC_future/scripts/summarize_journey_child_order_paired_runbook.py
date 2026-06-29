#!/usr/bin/env python3
"""Summarize paired same-first/separate-first Journey child-order probes.

The paired child-order runbook forces the same Ryan-Foster branch path and
then swaps which child kind is processed first at a target branch.  This helper
joins the runbook with each probe's result CSV and JSONL events, then emits
diagnostic rows that can be used as weak child-order labels.  It never runs BPC,
pricing, RMP, or creates official bounds/certificates.
"""

from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import date
import json
from pathlib import Path
import re
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_child_order_paired_summary_20260628")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260628_bpc_future_journey_child_order_paired_summary_zh.md"
)

_RF_RE = re.compile(r"RF\((?P<i>\d+),(?P<j>\d+)\)=(?P<kind>same_vehicle|separate_vehicle)")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


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


def _read_result_row(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return dict(rows[0]) if rows else {}


def _float(value: Any, default: float | None = None) -> float | None:
    if value in (None, ""):
        return default
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    if parsed != parsed:
        return default
    return float(parsed)


def _int(value: Any, default: int = 0) -> int:
    parsed = _float(value)
    if parsed is None:
        return int(default)
    return int(parsed)


def _bool_text(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _canonical_instance(text: Any) -> str:
    value = str(text or "")
    if value.endswith(".jsonl"):
        value = value[: -len(".jsonl")]
    if value.endswith(".json.json"):
        value = value[: -len(".json")]
    return value


def _pair_key(pair: Any) -> tuple[int, int] | None:
    if not isinstance(pair, (list, tuple)) or len(pair) != 2:
        return None
    try:
        i = int(pair[0])
        j = int(pair[1])
    except (TypeError, ValueError):
        return None
    return (min(i, j), max(i, j))


def _parse_rf(text: Any) -> tuple[tuple[int, int], str] | None:
    if not isinstance(text, str):
        return None
    match = _RF_RE.search(text)
    if match is None:
        return None
    i = int(match.group("i"))
    j = int(match.group("j"))
    return (min(i, j), max(i, j)), str(match.group("kind"))


def _event_time(record: dict[str, Any], fallback: int) -> tuple[float, int]:
    return (_float(record.get("time"), float(fallback)) or float(fallback), int(fallback))


def _run_dirs(runbook_path: Path, extra_run_roots: Iterable[Path]) -> list[Path]:
    roots = [runbook_path.parent / "runs", *[Path(path) for path in extra_run_roots]]
    out: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        if not root.exists():
            continue
        candidates = [root] if (root / "results.csv").exists() else sorted(p for p in root.iterdir() if p.is_dir())
        for candidate in candidates:
            if not (candidate / "results.csv").exists():
                continue
            key = str(candidate.resolve())
            if key in seen:
                continue
            seen.add(key)
            out.append(candidate)
    return out


def _infer_run_signature(
    run_dir: Path,
    result: dict[str, Any],
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    forced: list[tuple[int, tuple[int, int], int]] = []
    branch_events: list[tuple[int, dict[str, Any]]] = []
    for index, record in enumerate(events):
        event = str(record.get("event") or "")
        if event == "journey_branch_candidates":
            pair = _pair_key(record.get("forced_pair"))
            if pair is not None:
                forced.append((_int(record.get("depth"), 0), pair, index))
        if event == "journey_branch":
            branch_events.append((index, record))
    source_depth: int | None = None
    source_pair: tuple[int, int] | None = None
    if forced:
        source_depth, source_pair, _index = max(forced, key=lambda item: (item[0], item[2]))
    if source_pair is None:
        for record_name in (run_dir.name, str(run_dir)):
            match = re.search(r"_(?P<i>\d+)_(?P<j>\d+)_", record_name)
            if match:
                source_pair = (min(int(match.group("i")), int(match.group("j"))), max(int(match.group("i")), int(match.group("j"))))
                break
    child_starts: list[tuple[tuple[float, int], str]] = []
    child_queued: list[tuple[int, str]] = []
    if source_pair is not None:
        target_parent_ids: list[int] = []
        for index, record in branch_events:
            if _pair_key(record.get("selected_pair")) == source_pair and (
                source_depth is None or _int(record.get("depth"), -1) == int(source_depth)
            ):
                target_parent_ids.append(_int(record.get("node_id"), -1))
            constraints = record.get("branch_constraints") or []
            if not isinstance(constraints, list):
                continue
            for constraint in constraints:
                parsed = _parse_rf(constraint)
                if parsed is None:
                    continue
                pair, kind = parsed
                if pair == source_pair:
                    child_starts.append((_event_time(record, index), kind))
        target_parent_id_set = {node_id for node_id in target_parent_ids if node_id >= 0}
        for index, record in enumerate(events):
            if record.get("event") != "journey_child_queued":
                continue
            if target_parent_id_set and _int(record.get("parent_node_id"), -1) not in target_parent_id_set:
                continue
            parsed = _parse_rf(record.get("constraint"))
            if parsed is None:
                continue
            pair, kind = parsed
            if pair == source_pair:
                child_queued.append((index, kind))
    child_starts.sort(key=lambda item: item[0])
    child_queued.sort(key=lambda item: item[0])
    target_child_kind = child_queued[0][1] if child_queued else child_starts[0][1] if child_starts else None
    if target_child_kind is None:
        name = run_dir.name
        if "same_vehicle" in name or name.startswith("same_"):
            target_child_kind = "same_vehicle"
        elif "separate_vehicle" in name or name.startswith("separate_"):
            target_child_kind = "separate_vehicle"
    queued_order = "/".join(dict.fromkeys(kind for _index, kind in child_queued))
    started_order = "/".join(dict.fromkeys(kind for _time, kind in child_starts))
    return {
        "instance": _canonical_instance(result.get("instance")),
        "source_depth": source_depth,
        "source_pair": list(source_pair) if source_pair is not None else None,
        "target_child_kind": target_child_kind,
        "queued_child_order": queued_order,
        "started_child_order": started_order,
        "effective_child_order": queued_order or started_order,
    }


def _summarize_run_dir(run_dir: Path, entry: dict[str, Any] | None = None) -> dict[str, Any]:
    result = _read_result_row(run_dir / "results.csv")
    events: list[dict[str, Any]] = []
    for path in sorted(run_dir.rglob("*.jsonl")):
        events.extend(_iter_jsonl(path))
    inferred = _infer_run_signature(run_dir, result, events)
    if entry is not None:
        source_pair = _pair_key(entry.get("source_pair")) or _pair_key(entry.get("forced_pair"))
        if source_pair is not None:
            inferred["source_pair"] = [int(source_pair[0]), int(source_pair[1])]
        if entry.get("source_depth") is not None:
            inferred["source_depth"] = _int(entry.get("source_depth"))
        if entry.get("target_child_kind"):
            inferred["target_child_kind"] = str(entry.get("target_child_kind"))
        if entry.get("instance"):
            inferred["instance"] = _canonical_instance(entry.get("instance"))

    pair = _pair_key(inferred.get("source_pair"))
    target_branch_seen = False
    branch_count = 0
    completion_retry_count = 0
    ordinary_retry_count = 0
    fathom_count = 0
    event_counts: Counter[str] = Counter()
    child_exact_lower_bound_count = 0
    child_inexact_lower_bound_count = 0
    if pair is not None:
        for record in events:
            event = str(record.get("event") or "")
            event_counts[event] += 1
            if event == "journey_branch":
                branch_count += 1
                selected_pair = _pair_key(record.get("selected_pair"))
                if selected_pair == pair:
                    if inferred.get("source_depth") is None or _int(record.get("depth"), -1) == int(inferred["source_depth"]):
                        target_branch_seen = True
            elif event in {
                "journey_exact_pricing_completion_bound_retry",
                "journey_exact_pricing_completion_bound_escalation_retry",
            }:
                completion_retry_count += 1
            elif event == "journey_exact_pricing_retry":
                ordinary_retry_count += 1
            elif event in {"journey_fathom", "journey_node_fathom"}:
                fathom_count += 1
            elif event == "journey_child_queued":
                if bool(record.get("lower_bound_exact")):
                    child_exact_lower_bound_count += 1
                else:
                    child_inexact_lower_bound_count += 1

    wall = _float(result.get("wall_time"), _float(result.get("solving_time")))
    gap = _float(result.get("gap"))
    return {
        "schema_version": "journey_child_order_paired_entry_v1",
        "diagnostic_only": True,
        "production_ready": False,
        "official_bound_effect": False,
        "certificate_effect": False,
        "experiment": run_dir.name,
        "run_dir": str(run_dir),
        "result_available": bool(result),
        "jsonl_event_count": len(events),
        "instance": inferred.get("instance"),
        "source_depth": inferred.get("source_depth"),
        "source_pair": inferred.get("source_pair"),
        "target_child_kind": inferred.get("target_child_kind"),
        "queued_child_order": inferred.get("queued_child_order"),
        "started_child_order": inferred.get("started_child_order"),
        "effective_child_order": inferred.get("effective_child_order"),
        "target_branch_seen": bool(target_branch_seen),
        "forced_child_order_effective": bool(
            inferred.get("target_child_kind")
            and str(inferred.get("effective_child_order") or "").split("/", 1)[0]
            == str(inferred.get("target_child_kind"))
        ),
        "status": result.get("status"),
        "wall_time": wall,
        "solving_time": _float(result.get("solving_time")),
        "gap_available": _bool_text(result.get("gap_available")),
        "gap": gap,
        "node_count": _int(result.get("node_count")),
        "columns": _int(result.get("columns")),
        "pricing_calls": _int(result.get("pricing_calls")),
        "exact_pricing_calls": _int(result.get("exact_pricing_calls")),
        "generated_sequences": _int(result.get("generated_sequences")),
        "branch_count": branch_count,
        "completion_bound_final_judge_retry_count": completion_retry_count,
        "ordinary_incomplete_no_column_retry_count": ordinary_retry_count,
        "fathom_count": fathom_count,
        "child_exact_lower_bound_count": child_exact_lower_bound_count,
        "child_inexact_lower_bound_count": child_inexact_lower_bound_count,
    }


def _entry_signature(entry: dict[str, Any]) -> tuple[str, int | None, tuple[int, int] | None, str | None]:
    return (
        _canonical_instance(entry.get("instance")),
        None if entry.get("source_depth") is None else _int(entry.get("source_depth")),
        _pair_key(entry.get("source_pair")),
        str(entry.get("target_child_kind") or "") or None,
    )


def _row_signature(row: dict[str, Any]) -> tuple[str, int | None, tuple[int, int] | None, str | None]:
    depth = row.get("source_depth")
    return (
        _canonical_instance(row.get("instance")),
        None if depth is None else _int(depth),
        _pair_key(row.get("source_pair")),
        str(row.get("target_child_kind") or "") or None,
    )


def _row_quality(row: dict[str, Any]) -> tuple[int, float]:
    score = 0
    score += 100 if bool(row.get("target_branch_seen")) else 0
    score += 50 if bool(row.get("forced_child_order_effective")) else 0
    score += 20 if bool(row.get("gap_available")) else 0
    score += 10 if bool(row.get("result_available")) else 0
    return score, float(row.get("wall_time") or 0.0)


def _paired_label(row: dict[str, Any]) -> str:
    if not bool(row.get("target_branch_seen")) or not bool(row.get("forced_child_order_effective")):
        return "invalid_unreached"
    wall_gain = float(row.get("paired_wall_time_gain") or 0.0)
    retry_gain = float(row.get("paired_completion_bound_retry_gain") or 0.0)
    gap_improvement = _float(row.get("paired_gap_improvement"), 0.0) or 0.0
    gap_bad = gap_improvement < -1.0e-9
    if (wall_gain >= 5.0 or retry_gain >= 1.0) and not gap_bad:
        return "positive_child_order_proxy"
    if wall_gain <= -5.0 or retry_gain <= -1.0 or gap_bad:
        return "hard_negative_child_order_proxy"
    return "neutral_child_order_proxy"


def summarize_child_order_paired(
    runbook_path: Path,
    output_dir: Path,
    report: Path,
    *,
    extra_run_roots: Iterable[Path] = (),
) -> dict[str, Any]:
    runbook = _read_json(runbook_path)
    entries = [entry for entry in runbook.get("entries", []) if isinstance(entry, dict)]
    candidate_rows = [_summarize_run_dir(path) for path in _run_dirs(runbook_path, extra_run_roots)]
    by_signature: dict[tuple[str, int | None, tuple[int, int] | None, str | None], list[dict[str, Any]]] = {}
    for row in candidate_rows:
        by_signature.setdefault(_row_signature(row), []).append(row)

    selected_rows: list[dict[str, Any]] = []
    for entry in entries:
        signature = _entry_signature(entry)
        candidates = by_signature.get(signature, [])
        if candidates:
            selected = max(candidates, key=_row_quality)
        else:
            selected = _summarize_run_dir(runbook_path.parent / "runs" / str(entry.get("experiment") or ""), entry)
        selected = dict(selected)
        selected.update(
            {
                "source_experiment": entry.get("experiment"),
                "pair_group_id": entry.get("pair_group_id"),
                "pair_role": entry.get("pair_role"),
                "source_first_child_kind": entry.get("source_first_child_kind"),
                "source_subtree_completion_bound_retry_count": entry.get(
                    "subtree_completion_bound_retry_count"
                ),
                "source_priority_score": entry.get("priority_score"),
            }
        )
        selected_rows.append(selected)

    rows_by_group: dict[str, list[dict[str, Any]]] = {}
    for row in selected_rows:
        rows_by_group.setdefault(str(row.get("pair_group_id") or ""), []).append(row)

    group_rows: list[dict[str, Any]] = []
    final_rows: list[dict[str, Any]] = []
    for group_id, rows in sorted(rows_by_group.items()):
        by_kind = {str(row.get("target_child_kind")): row for row in rows}
        same = by_kind.get("same_vehicle")
        separate = by_kind.get("separate_vehicle")
        if same is None or separate is None:
            final_rows.extend(rows)
            continue
        same_wall = _float(same.get("wall_time"), 0.0) or 0.0
        separate_wall = _float(separate.get("wall_time"), 0.0) or 0.0
        same_retry = _int(same.get("completion_bound_final_judge_retry_count"))
        separate_retry = _int(separate.get("completion_bound_final_judge_retry_count"))
        same_gap = _float(same.get("gap"))
        separate_gap = _float(separate.get("gap"))
        for row, other in ((same, separate), (separate, same)):
            row = dict(row)
            own_wall = _float(row.get("wall_time"), 0.0) or 0.0
            other_wall = _float(other.get("wall_time"), 0.0) or 0.0
            own_retry = _int(row.get("completion_bound_final_judge_retry_count"))
            other_retry = _int(other.get("completion_bound_final_judge_retry_count"))
            own_gap = _float(row.get("gap"))
            other_gap = _float(other.get("gap"))
            row["paired_opposite_child_kind"] = other.get("target_child_kind")
            row["paired_wall_time_gain"] = round(float(other_wall - own_wall), 6)
            row["paired_completion_bound_retry_gain"] = int(other_retry - own_retry)
            row["paired_gap_improvement"] = (
                None if own_gap is None or other_gap is None else round(float(other_gap - own_gap), 9)
            )
            row["paired_label_type"] = _paired_label(row)
            final_rows.append(row)
        separate_minus_same = round(float(separate_wall - same_wall), 6)
        group_rows.append(
            {
                "schema_version": "journey_child_order_paired_group_v1",
                "diagnostic_only": True,
                "production_ready": False,
                "official_bound_effect": False,
                "certificate_effect": False,
                "pair_group_id": group_id,
                "instance": same.get("instance") or separate.get("instance"),
                "source_depth": same.get("source_depth") if same.get("source_depth") is not None else separate.get("source_depth"),
                "source_pair": same.get("source_pair") or separate.get("source_pair"),
                "same_first_wall_time": same_wall,
                "separate_first_wall_time": separate_wall,
                "separate_minus_same_wall_time": separate_minus_same,
                "same_first_completion_bound_retry_count": same_retry,
                "separate_first_completion_bound_retry_count": separate_retry,
                "separate_minus_same_completion_bound_retry_count": int(separate_retry - same_retry),
                "same_first_gap": same_gap,
                "separate_first_gap": separate_gap,
                "same_target_branch_seen": bool(same.get("target_branch_seen")),
                "separate_target_branch_seen": bool(separate.get("target_branch_seen")),
                "same_forced_child_order_effective": bool(same.get("forced_child_order_effective")),
                "separate_forced_child_order_effective": bool(separate.get("forced_child_order_effective")),
                "preferred_child_kind": (
                    "same_vehicle"
                    if separate_minus_same > 5.0
                    else "separate_vehicle"
                    if separate_minus_same < -5.0
                    else "neutral"
                ),
            }
        )

    label_counts = Counter(str(row.get("paired_label_type") or "unpaired") for row in final_rows)
    valid_groups = [
        row
        for row in group_rows
        if bool(row.get("same_target_branch_seen"))
        and bool(row.get("separate_target_branch_seen"))
        and bool(row.get("same_forced_child_order_effective"))
        and bool(row.get("separate_forced_child_order_effective"))
    ]
    output_dir.mkdir(parents=True, exist_ok=True)
    rows_path = output_dir / "child_order_paired_rows.jsonl"
    groups_path = output_dir / "child_order_paired_group_rows.jsonl"
    rows_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in final_rows)
        + ("\n" if final_rows else ""),
        encoding="utf-8",
    )
    groups_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in group_rows)
        + ("\n" if group_rows else ""),
        encoding="utf-8",
    )
    summary = {
        "schema_version": "journey_child_order_paired_summary_v1",
        "date": date.today().isoformat(),
        "runbook_path": str(runbook_path),
        "extra_run_roots": [str(path) for path in extra_run_roots],
        "entry_count": len(entries),
        "candidate_run_count": len(candidate_rows),
        "paired_row_count": len(final_rows),
        "paired_group_count": len(group_rows),
        "valid_paired_group_count": len(valid_groups),
        "label_counts": dict(sorted(label_counts.items())),
        "rows_path": str(rows_path),
        "group_rows_path": str(groups_path),
        "report_path": str(report),
        "diagnostic_only": True,
        "production_ready": False,
        "official_bound_effect": False,
        "certificate_effect": False,
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(report, summary, group_rows)
    return summary


def _write_report(report: Path, summary: dict[str, Any], group_rows: list[dict[str, Any]]) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Journey Child Order Paired Summary",
        "",
        "该报告汇总 same-first / separate-first paired replay 的局部 proof-cost 差异；它只读已有结果和 JSONL 日志，不运行 BPC / pricing / RMP，不产生 official bound 或 certificate。",
        "",
        "## Summary",
        "",
        f"- entry_count: `{summary['entry_count']}`",
        f"- candidate_run_count: `{summary['candidate_run_count']}`",
        f"- paired_group_count: `{summary['paired_group_count']}`",
        f"- valid_paired_group_count: `{summary['valid_paired_group_count']}`",
        f"- label_counts: `{summary['label_counts']}`",
        f"- rows: `{summary['rows_path']}`",
        f"- groups: `{summary['group_rows_path']}`",
        "",
        "## Groups",
        "",
    ]
    if not group_rows:
        lines.append("- no paired groups")
    for row in group_rows:
        lines.extend(
            [
                f"### {row['pair_group_id']}",
                "",
                f"- instance: `{row.get('instance')}`",
                f"- depth / pair: `{row.get('source_depth')}` / `{row.get('source_pair')}`",
                f"- same-first wall: `{row.get('same_first_wall_time')}`",
                f"- separate-first wall: `{row.get('separate_first_wall_time')}`",
                f"- separate - same wall: `{row.get('separate_minus_same_wall_time')}`",
                f"- same / separate CB retry: `{row.get('same_first_completion_bound_retry_count')}` / `{row.get('separate_first_completion_bound_retry_count')}`",
                f"- preferred_child_kind: `{row.get('preferred_child_kind')}`",
                f"- target branch reached: `{row.get('same_target_branch_seen')}` / `{row.get('separate_target_branch_seen')}`",
                f"- forced order effective: `{row.get('same_forced_child_order_effective')}` / `{row.get('separate_forced_child_order_effective')}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Interpretation",
            "",
            "这些 rows 是 child-order 的弱监督/诊断标签。正值 wall gain 表示当前 child kind 比 opposite child kind 更快；gap improvement 只来自 solver/result 或 exact-safe 日志字段，不使用未闭合 RMP objective。",
            "",
        ]
    )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runbook", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--extra-run-root",
        type=Path,
        action="append",
        default=[],
        help="Additional root containing replacement/extra run directories with results.csv.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = summarize_child_order_paired(
        args.runbook,
        args.output_dir,
        args.report,
        extra_run_roots=args.extra_run_root,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
