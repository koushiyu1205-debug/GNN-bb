#!/usr/bin/env python3
"""Audit instance reference solutions as feasible normalized-objective incumbents."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.exact.core.objective import (  # noqa: E402
    aggregate_journey_objective_breakdown,
    flatten_objective_payload,
    objective_metadata,
)
import lunar_ice_bpc.exact.solver.journey_driver as journey_driver  # noqa: E402


DEFAULT_MANIFEST = "data/manifests/lunar_ice_sp50_real_benchmark_manifest.json"
DEFAULT_OUTPUT_DIR = "runs/objective_normalized_cost_risk_completion_full"

CSV_COLUMNS = (
    "scale",
    "instance_id",
    "status",
    "feasible_incumbent_source",
    "feasible_incumbent_objective",
    "journey_count",
    "objective_schema_version",
    "objective_mode",
    "objective_reference_cost",
    "objective_reference_risk",
    "objective_reference_completion",
    "objective_reference_makespan_metric",
    "objective_makespan_enters_pricing_objective",
    "solution_raw_operating_cost",
    "solution_raw_risk",
    "solution_raw_weighted_completion_time",
    "solution_raw_makespan",
    "solution_raw_objective_unscaled_weighted_sum",
    "solution_normalized_operating_cost",
    "solution_normalized_risk",
    "solution_normalized_weighted_completion_time",
    "solution_normalized_makespan_metric",
    "solution_normalized_objective",
    "solution_official_objective",
    "solution_makespan_enters_pricing_objective",
    "note",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--scale", type=int, default=30)
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    output_dir = _resolve(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    scale = int(args.scale)
    prefix = output_dir / f"scale{scale:03d}_reference_incumbent_audit"
    rows = []
    for instance_path in _instance_paths_for_scale(_load_manifest(_resolve(args.manifest)), scale=scale, limit=int(args.limit)):
        raw = json.loads(instance_path.read_text(encoding="utf-8"))
        data = load_lunar_ice_data(raw)
        reference = journey_driver._reference_solution_upper_bound(data)
        row = {
            "scale": scale,
            "instance_id": data.instance_id,
            "status": "REFERENCE_INCUMBENT_AVAILABLE" if reference is not None else "REFERENCE_INCUMBENT_MISSING",
            "feasible_incumbent_source": "" if reference is None else reference.source,
            "feasible_incumbent_objective": None if reference is None else float(reference.objective),
            "journey_count": 0 if reference is None else len(reference.journeys),
            "note": (
                "Reference solution is a feasible upper bound only; it is not an optimality certificate."
                if reference is not None
                else "No reconstructable feasible reference solution."
            ),
        }
        row.update(flatten_objective_payload(objective_metadata(data), prefix="objective"))
        if reference is not None:
            row.update(
                flatten_objective_payload(
                    aggregate_journey_objective_breakdown(data, reference.journeys),
                    prefix="solution",
                )
            )
        rows.append(row)

    _write_csv(prefix.with_suffix(".csv"), rows)
    prefix.with_suffix(".json").write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    prefix.with_suffix(".md").write_text(_render_report(rows, scale=scale), encoding="utf-8")
    print(f"reference incumbent audit written to {prefix.with_suffix('.md')}")
    return 0


def _load_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _instance_paths_for_scale(manifest: dict, *, scale: int, limit: int) -> tuple[Path, ...]:
    rows = [
        row
        for row in manifest.get("instances", [])
        if int(row.get("scale") or -1) == int(scale) and str(row.get("status") or "") == "accepted"
    ]
    rows = rows[: max(0, int(limit))]
    return tuple(_resolve(row["path"]) for row in rows)


def _write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _render_report(rows: list[dict], *, scale: int) -> str:
    available = [row for row in rows if row.get("status") == "REFERENCE_INCUMBENT_AVAILABLE"]
    objectives = [_float(row.get("feasible_incumbent_objective")) for row in available]
    objectives = [value for value in objectives if value is not None]
    lines = [
        f"# {scale}-scale Reference Incumbent Audit",
        "",
        "## 边界",
        "",
        "- 该审计只重建 instance `reference_solution` 对应的 feasible upper bound。",
        "- 它不是 B0 direct-DP optimality proof，也不是 BPC root/tree certificate。",
        "- makespan 仍只作为报告指标，不进入 official objective。",
        "",
        "## 汇总",
        "",
        f"- rows: {len(rows)}",
        f"- reconstructable feasible incumbents: {len(available)}/{len(rows)}",
        f"- mean objective: {_fmt(statistics.mean(objectives) if objectives else None)}",
        f"- min objective: {_fmt(min(objectives) if objectives else None)}",
        f"- max objective: {_fmt(max(objectives) if objectives else None)}",
        "",
        "## Rows",
        "",
        "| instance | status | objective | journeys | raw cost | raw risk | weighted completion | makespan |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| `{row.get('instance_id')}` | `{row.get('status')}` | {_fmt(row.get('feasible_incumbent_objective'))} | "
            f"{int(row.get('journey_count') or 0)} | {_fmt(row.get('solution_raw_operating_cost'))} | "
            f"{_fmt(row.get('solution_raw_risk'))} | {_fmt(row.get('solution_raw_weighted_completion_time'))} | "
            f"{_fmt(row.get('solution_raw_makespan'))} |"
        )
    return "\n".join(lines) + "\n"


def _float(value) -> float | None:
    if value in {None, ""}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _fmt(value) -> str:
    value = _float(value)
    if value is None:
        return ""
    return f"{value:.9g}"


def _resolve(path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else ROOT / candidate


if __name__ == "__main__":
    raise SystemExit(main())
