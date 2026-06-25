#!/usr/bin/env python3
"""Calibrate Journey child-probe proxy rankings against full counterfactual deltas.

This script is offline and diagnostic-only. It joins
``child_probe_proxy_branch_rows.jsonl`` with ``branch_counterfactual_delta_rows.jsonl``
on the same parent context and alternative pair, then reports whether the
right-censored child-probe proxy ordering agrees with completed full replay
outcomes. It does not run BPC, pricing, RMP, or produce official bounds.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import date
import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/journey_branch_child_probe_proxy_calibration_20260624"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260624_bpc_future_journey_branch_child_probe_proxy_calibration_zh.md"
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


def _load_jsonl_from_paths(paths: Iterable[Path], filename: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        if path.is_dir():
            rows.extend(_iter_jsonl(path / filename))
            continue
        if path.name == "summary.json":
            rows.extend(_iter_jsonl(path.parent / filename))
            continue
        if path.name == filename or path.suffix == ".jsonl":
            rows.extend(_iter_jsonl(path))
    return rows


def _int(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return int(default)
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _float(value: Any, default: float | None = None) -> float | None:
    if value is None or value == "":
        return default
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    if parsed != parsed:
        return default
    return float(parsed)


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
    if row.get("pair") is not None:
        return _pair_tuple(row.get("pair"))
    if row.get("alternative_pair") is not None:
        return _pair_tuple(row.get("alternative_pair"))
    return _pair_tuple([row.get("task_i"), row.get("task_j")])


def _context_key(row: dict[str, Any]) -> tuple[str, int, int] | None:
    instance = str(row.get("instance") or "")
    node_id = _int(row.get("node_id"), -1)
    depth = _int(row.get("depth"), -1)
    if not instance or node_id < 0 or depth < 0:
        return None
    return instance, node_id, depth


def _row_key(row: dict[str, Any]) -> tuple[str, int, int, tuple[int, int]] | None:
    context = _context_key(row)
    pair = _row_pair(row)
    if context is None or pair is None:
        return None
    return context[0], context[1], context[2], pair


def _delta_labels(row: dict[str, Any]) -> dict[str, Any]:
    labels = row.get("labels")
    return labels if isinstance(labels, dict) else {}


def _full_outcome_score(row: dict[str, Any]) -> float:
    labels = _delta_labels(row)
    wall_delta = _float((row.get("deltas") or {}).get("wall_time_delta"))
    if wall_delta is None:
        wall_delta = _float(row.get("wall_time_delta"))
    exact_delta = _float((row.get("deltas") or {}).get("exact_pricing_calls_delta"), 0.0)
    label_type = str(row.get("counterfactual_label_type") or "")
    if label_type == "strong_positive":
        base = 1000.0
    elif _float(labels.get("y_counterfactual_regression"), 0.0) > 0.0:
        base = -1000.0
    elif _float(labels.get("y_counterfactual_budget_dominant_improvement"), 0.0) > 0.0:
        base = 100.0
    elif _float(labels.get("y_counterfactual_local_improved_but_whole_run_not"), 0.0) > 0.0:
        base = 10.0
    else:
        base = 0.0
    if wall_delta is not None:
        base += -float(wall_delta)
    if exact_delta is not None:
        base += -0.01 * float(exact_delta)
    return round(float(base), 9)


def _compact(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "pair": row.get("pair"),
        "proxy_score": row.get("proxy_score"),
        "full_outcome_score": row.get("full_outcome_score"),
        "counterfactual_label_type": row.get("counterfactual_label_type"),
        "wall_time_delta": row.get("wall_time_delta"),
        "alternative_wall_time": row.get("alternative_wall_time"),
    }


def build_proxy_calibration(
    proxy_inputs: list[Path],
    delta_inputs: list[Path],
    output_dir: Path,
    report: Path,
) -> dict[str, Any]:
    proxy_rows = _load_jsonl_from_paths(proxy_inputs, "child_probe_proxy_branch_rows.jsonl")
    delta_rows = _load_jsonl_from_paths(delta_inputs, "branch_counterfactual_delta_rows.jsonl")
    delta_by_key: dict[tuple[str, int, int, tuple[int, int]], dict[str, Any]] = {}
    duplicate_delta_key_count = 0
    for row in delta_rows:
        key = _row_key(row)
        if key is None:
            continue
        if key in delta_by_key:
            duplicate_delta_key_count += 1
            continue
        delta_by_key[key] = row

    calibration_rows: list[dict[str, Any]] = []
    unmatched_proxy_count = 0
    for proxy in proxy_rows:
        key = _row_key(proxy)
        if key is None:
            unmatched_proxy_count += 1
            continue
        delta = delta_by_key.get(key)
        if delta is None:
            unmatched_proxy_count += 1
            continue
        deltas = delta.get("deltas")
        deltas = deltas if isinstance(deltas, dict) else {}
        wall_delta = _float(deltas.get("wall_time_delta"))
        calibration_rows.append(
            {
                "schema_version": "journey_branch_child_probe_proxy_calibration_row_v1",
                "diagnostic_only": True,
                "runs_bpc_or_pricing": False,
                "production_ready": False,
                "certificate_effect": False,
                "official_bound_effect": False,
                "instance": key[0],
                "node_id": key[1],
                "depth": key[2],
                "pair": [key[3][0], key[3][1]],
                "proxy_score": proxy.get("proxy_score"),
                "proxy_right_censored": bool(proxy.get("right_censored")),
                "proxy_fathom_count": proxy.get("fathom_count"),
                "proxy_max_corrected_bound_gain": proxy.get("max_corrected_bound_gain"),
                "proxy_completion_bound_retry_count": proxy.get("completion_bound_retry_count"),
                "proxy_proof_cpu": proxy.get("proof_cpu"),
                "counterfactual_label_type": delta.get("counterfactual_label_type"),
                "alternative_status": delta.get("alternative_status"),
                "alternative_wall_time": delta.get("alternative_wall_time"),
                "wall_time_delta": wall_delta,
                "exact_pricing_calls_delta": _float(deltas.get("exact_pricing_calls_delta")),
                "full_outcome_score": _full_outcome_score(delta),
            }
        )

    groups: dict[tuple[str, int, int], list[dict[str, Any]]] = defaultdict(list)
    for row in calibration_rows:
        groups[(str(row["instance"]), int(row["node_id"]), int(row["depth"]))].append(row)

    context_rows: list[dict[str, Any]] = []
    discordant_pair_count = 0
    comparable_pair_count = 0
    top_match_count = 0
    label_type_counts: Counter[str] = Counter()
    for row in calibration_rows:
        label_type_counts[str(row.get("counterfactual_label_type") or "")] += 1

    for key, rows in sorted(groups.items(), key=lambda item: item[0]):
        proxy_sorted = sorted(
            rows,
            key=lambda row: (-float(_float(row.get("proxy_score"), 0.0) or 0.0), row["pair"]),
        )
        full_sorted = sorted(
            rows,
            key=lambda row: (-float(_float(row.get("full_outcome_score"), 0.0) or 0.0), row["pair"]),
        )
        top_proxy = proxy_sorted[0] if proxy_sorted else None
        top_full = full_sorted[0] if full_sorted else None
        top_match = bool(top_proxy and top_full and top_proxy.get("pair") == top_full.get("pair"))
        if top_match:
            top_match_count += 1
        for left_index, left in enumerate(rows):
            for right in rows[left_index + 1 :]:
                proxy_left = _float(left.get("proxy_score"), 0.0) or 0.0
                proxy_right = _float(right.get("proxy_score"), 0.0) or 0.0
                full_left = _float(left.get("full_outcome_score"), 0.0) or 0.0
                full_right = _float(right.get("full_outcome_score"), 0.0) or 0.0
                if proxy_left == proxy_right or full_left == full_right:
                    continue
                comparable_pair_count += 1
                if (proxy_left > proxy_right) != (full_left > full_right):
                    discordant_pair_count += 1
        context_rows.append(
            {
                "schema_version": "journey_branch_child_probe_proxy_calibration_context_v1",
                "diagnostic_only": True,
                "runs_bpc_or_pricing": False,
                "production_ready": False,
                "certificate_effect": False,
                "official_bound_effect": False,
                "instance": key[0],
                "node_id": key[1],
                "depth": key[2],
                "matched_pair_count": len(rows),
                "top_proxy": None if top_proxy is None else _compact(top_proxy),
                "top_full": None if top_full is None else _compact(top_full),
                "top_pair_match": top_match,
            }
        )

    summary = {
        "schema_version": "journey_branch_child_probe_proxy_calibration_summary_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "proxy_input_paths": [str(path) for path in proxy_inputs],
        "delta_input_paths": [str(path) for path in delta_inputs],
        "raw_proxy_row_count": len(proxy_rows),
        "raw_delta_row_count": len(delta_rows),
        "matched_pair_count": len(calibration_rows),
        "unmatched_proxy_count": int(unmatched_proxy_count),
        "duplicate_delta_key_count": int(duplicate_delta_key_count),
        "context_count": len(context_rows),
        "top_pair_match_count": int(top_match_count),
        "top_pair_mismatch_count": int(len(context_rows) - top_match_count),
        "pairwise_comparison_count": int(comparable_pair_count),
        "discordant_pair_count": int(discordant_pair_count),
        "discordant_pair_rate": 0.0
        if comparable_pair_count <= 0
        else round(float(discordant_pair_count) / float(comparable_pair_count), 9),
        "label_type_counts": dict(sorted(label_type_counts.items())),
        "sampling_navigation_ready": bool(calibration_rows),
        "ranking_training_ready": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "child_probe_proxy_calibration_rows.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in calibration_rows),
        encoding="utf-8",
    )
    (output_dir / "child_probe_proxy_calibration_context_rows.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in context_rows),
        encoding="utf-8",
    )
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    _write_report(report, summary, context_rows)
    return summary


def _write_report(report: Path, summary: dict[str, Any], context_rows: list[dict[str, Any]]) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Journey Branch Child-Probe Proxy Calibration",
        "",
        f"Date: {date.today().isoformat()}",
        "",
        "## Machine Fields",
        "",
        "```text",
    ]
    for key in [
        "raw_proxy_row_count",
        "raw_delta_row_count",
        "matched_pair_count",
        "unmatched_proxy_count",
        "duplicate_delta_key_count",
        "context_count",
        "top_pair_match_count",
        "top_pair_mismatch_count",
        "pairwise_comparison_count",
        "discordant_pair_count",
        "discordant_pair_rate",
        "label_type_counts",
        "sampling_navigation_ready",
        "ranking_training_ready",
        "production_ready",
        "certificate_effect",
        "official_bound_effect",
    ]:
        lines.append(f"{key} = {summary.get(key)}")
    lines.extend(["```", "", "## Contexts", ""])
    for row in context_rows[:20]:
        lines.append(
            "- "
            f"node={row['node_id']} depth={row['depth']} "
            f"matched={row['matched_pair_count']} "
            f"top_proxy={None if row['top_proxy'] is None else row['top_proxy']['pair']} "
            f"top_full={None if row['top_full'] is None else row['top_full']['pair']} "
            f"top_pair_match={row['top_pair_match']}"
        )
    lines.extend(["", "## Boundary", ""])
    lines.append(
        "This calibration is diagnostic-only. A child-probe proxy mismatch against full replay means the proxy should guide sampling, not production branch-score training."
    )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proxy-input", nargs="+", type=Path, required=True)
    parser.add_argument("--delta-input", nargs="+", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = build_proxy_calibration(
        list(args.proxy_input),
        list(args.delta_input),
        args.output_dir,
        args.report,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
