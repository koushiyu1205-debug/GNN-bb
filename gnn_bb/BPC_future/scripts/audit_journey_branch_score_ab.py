#!/usr/bin/env python3
"""Audit branch-score opt-in A/B runs from CSV and JSONL logs.

This script is diagnostic-only. It reads already finished solver outputs and
summarizes whether ``journey_branch_candidate_priority=branch_score`` changed
the selected Ryan-Foster branch and how wall/proof-cost metrics changed. It
does not run BPC, pricing, RMP, or produce official bounds/certificates.
"""

from __future__ import annotations

import argparse
import csv
from datetime import date
import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_branch_score_ab_audit_20260624")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_score_ab_audit_zh.md"
)


def _read_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


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


def _pair(candidate: dict[str, Any] | None) -> list[int] | None:
    if not isinstance(candidate, dict):
        return None
    if candidate.get("task_i") is None or candidate.get("task_j") is None:
        return None
    try:
        i, j = int(candidate["task_i"]), int(candidate["task_j"])
    except (TypeError, ValueError):
        return None
    return list(sorted((i, j)))


def _find_log_path(log_dir: Path, instance: str) -> Path | None:
    expected_name = f"{Path(instance).name}.jsonl"
    matches = sorted(log_dir.rglob(expected_name)) if log_dir.exists() else []
    if matches:
        return matches[0]
    suffix = str(Path(instance))
    for path in sorted(log_dir.rglob("*.jsonl")) if log_dir.exists() else []:
        text = str(path)
        if suffix in text:
            return path
    return None


def _first_branch_payload(log_path: Path | None) -> dict[str, Any]:
    if log_path is None:
        return {
            "log_path": None,
            "has_log": False,
            "priority_mode": None,
            "selected_pair": None,
            "branch_score": None,
            "branch_score_source": None,
            "branch_left": None,
            "branch_right": None,
            "branch_count": 0,
            "finish": None,
        }
    first_candidates: dict[str, Any] | None = None
    first_branch: dict[str, Any] | None = None
    finish: dict[str, Any] | None = None
    branch_count = 0
    for record in _iter_jsonl(log_path):
        if record.get("event") == "journey_branch_candidates" and first_candidates is None:
            first_candidates = record
        elif record.get("event") == "journey_branch":
            branch_count += 1
            if first_branch is None:
                first_branch = record
        elif record.get("event") == "finish":
            finish = record
    selected = first_candidates.get("selected") if first_candidates else None
    return {
        "log_path": str(log_path),
        "has_log": True,
        "priority_mode": None if first_candidates is None else first_candidates.get("priority_mode"),
        "selected_pair": _pair(selected),
        "branch_score": None if not isinstance(selected, dict) else selected.get("branch_score"),
        "branch_score_source": None if not isinstance(selected, dict) else selected.get("branch_score_source"),
        "branch_left": None if first_branch is None else first_branch.get("left"),
        "branch_right": None if first_branch is None else first_branch.get("right"),
        "branch_count": int(branch_count),
        "finish": finish,
    }


def _csv_metrics(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": row.get("status"),
        "external_timeout": str(row.get("external_timeout") or "").lower() == "true",
        "wall_time": round(_float(row.get("wall_time")), 6),
        "solving_time": round(_float(row.get("solving_time")), 6),
        "node_count": _int(row.get("node_count")),
        "rmp_solves": _int(row.get("rmp_solves")),
        "pricing_calls": _int(row.get("pricing_calls")),
        "exact_pricing_calls": _int(row.get("exact_pricing_calls")),
        "generated_sequences": _int(row.get("generated_sequences")),
        "evaluated_timed_trips": _int(row.get("evaluated_timed_trips")),
        "primal_bound": row.get("primal_bound"),
        "dual_bound": row.get("dual_bound"),
        "gap": row.get("gap"),
    }


def _delta(optin: dict[str, Any], baseline: dict[str, Any], key: str) -> float:
    return round(_float(optin.get(key)) - _float(baseline.get(key)), 6)


def _paired_rows(
    baseline_rows: list[dict[str, Any]],
    optin_rows: list[dict[str, Any]],
) -> list[tuple[str, dict[str, Any], dict[str, Any]]]:
    baseline_by_instance = {str(row.get("instance") or ""): row for row in baseline_rows}
    optin_by_instance = {str(row.get("instance") or ""): row for row in optin_rows}
    instances = sorted(set(baseline_by_instance) & set(optin_by_instance))
    return [(instance, baseline_by_instance[instance], optin_by_instance[instance]) for instance in instances]


def build_branch_score_ab_audit(
    *,
    baseline_csv: Path,
    optin_csv: Path,
    baseline_log_dir: Path,
    optin_log_dir: Path,
    output_dir: Path,
    report: Path,
) -> dict[str, Any]:
    baseline_rows = _read_csv(baseline_csv)
    optin_rows = _read_csv(optin_csv)
    rows: list[dict[str, Any]] = []
    for instance, baseline_row, optin_row in _paired_rows(baseline_rows, optin_rows):
        baseline_log = _first_branch_payload(_find_log_path(baseline_log_dir, instance))
        optin_log = _first_branch_payload(_find_log_path(optin_log_dir, instance))
        baseline_metrics = _csv_metrics(baseline_row)
        optin_metrics = _csv_metrics(optin_row)
        row = {
            "schema_version": "journey_branch_score_ab_row_v1",
            "diagnostic_only": True,
            "runs_bpc_or_pricing": False,
            "production_ready": False,
            "certificate_effect": False,
            "official_bound_effect": False,
            "instance": instance,
            "baseline": {**baseline_metrics, **baseline_log},
            "optin": {**optin_metrics, **optin_log},
            "selected_pair_changed": baseline_log.get("selected_pair") != optin_log.get("selected_pair"),
            "branch_score_used": optin_log.get("branch_score") is not None,
            "both_optimal": baseline_metrics.get("status") == "OPTIMAL"
            and optin_metrics.get("status") == "OPTIMAL",
            "deltas": {
                key: _delta(optin_metrics, baseline_metrics, key)
                for key in [
                    "wall_time",
                    "solving_time",
                    "node_count",
                    "rmp_solves",
                    "pricing_calls",
                    "exact_pricing_calls",
                    "generated_sequences",
                    "evaluated_timed_trips",
                ]
            },
        }
        rows.append(row)

    improved = [row for row in rows if _float(row["deltas"].get("wall_time")) < 0.0]
    regressed = [row for row in rows if _float(row["deltas"].get("wall_time")) > 0.0]
    summary = {
        "schema_version": "journey_branch_score_ab_audit_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "baseline_csv": str(baseline_csv),
        "optin_csv": str(optin_csv),
        "baseline_log_dir": str(baseline_log_dir),
        "optin_log_dir": str(optin_log_dir),
        "output_dir": str(output_dir),
        "paired_instance_count": len(rows),
        "both_optimal_count": sum(1 for row in rows if row["both_optimal"]),
        "selected_pair_changed_count": sum(1 for row in rows if row["selected_pair_changed"]),
        "branch_score_used_count": sum(1 for row in rows if row["branch_score_used"]),
        "wall_improved_count": len(improved),
        "wall_regressed_count": len(regressed),
        "wall_time_delta_sum": round(sum(_float(row["deltas"].get("wall_time")) for row in rows), 6),
        "exact_pricing_calls_delta_sum": round(
            sum(_float(row["deltas"].get("exact_pricing_calls")) for row in rows),
            6,
        ),
        "node_count_delta_sum": round(sum(_float(row["deltas"].get("node_count")) for row in rows), 6),
        "rows": rows,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "branch_score_ab_rows.jsonl").write_text(
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
        "# Journey Branch Score A/B Audit",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 目的",
        "",
        "汇总 branch-score opt-in A/B 的实际分支选择和 proof-cost 差异。该脚本只读已完成的 CSV / JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。",
        "",
        "## 机器字段",
        "",
        "```text",
    ]
    for key in [
        "paired_instance_count",
        "both_optimal_count",
        "selected_pair_changed_count",
        "branch_score_used_count",
        "wall_improved_count",
        "wall_regressed_count",
        "wall_time_delta_sum",
        "exact_pricing_calls_delta_sum",
        "node_count_delta_sum",
        "production_ready",
        "official_bound_effect",
    ]:
        lines.append(f"{key} = {summary.get(key)}")
    lines.extend(["```", "", "## Rows", ""])
    for row in rows:
        baseline = row["baseline"]
        optin = row["optin"]
        deltas = row["deltas"]
        lines.append(
            "- "
            f"instance={Path(str(row['instance'])).name}, "
            f"baseline_selected={baseline.get('selected_pair')}, "
            f"optin_selected={optin.get('selected_pair')}, "
            f"score={optin.get('branch_score')}, "
            f"source={optin.get('branch_score_source')}, "
            f"wall_delta={deltas.get('wall_time')}, "
            f"exact_delta={deltas.get('exact_pricing_calls')}, "
            f"node_delta={deltas.get('node_count')}"
        )
    lines.extend(["", "## 边界", ""])
    lines.append(
        "该审计只证明 opt-in 调度和已完成 run 的差异；不能作为 random-TW 全量加速、production GAT 泛化或 official certificate 证据。"
    )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-csv", type=Path, required=True)
    parser.add_argument("--optin-csv", type=Path, required=True)
    parser.add_argument("--baseline-log-dir", type=Path, required=True)
    parser.add_argument("--optin-log-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = build_branch_score_ab_audit(
        baseline_csv=args.baseline_csv,
        optin_csv=args.optin_csv,
        baseline_log_dir=args.baseline_log_dir,
        optin_log_dir=args.optin_log_dir,
        output_dir=args.output_dir,
        report=args.report,
    )
    print(json.dumps({key: value for key, value in summary.items() if key != "rows"}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
