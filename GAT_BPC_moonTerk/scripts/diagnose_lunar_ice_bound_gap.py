#!/usr/bin/env python3
"""Diagnose lower-bound strength for normalized lunar-ice objectives."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.exact.core.objective import (  # noqa: E402
    OBJECTIVE_MODE,
    OBJECTIVE_SCHEMA_VERSION,
    objective_references,
    operating_cost_value,
    service_risk_value,
)
from lunar_ice_bpc.exact.solver.lower_bounds import compute_analytic_lower_bound  # noqa: E402
import lunar_ice_bpc.exact.solver.journey_driver as journey_driver  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", required=True)
    parser.add_argument("--compact-csv", action="append", default=[])
    parser.add_argument("--output-md", required=True)
    parser.add_argument("--output-json")
    args = parser.parse_args()

    instance_path = _resolve(args.instance)
    instance = json.loads(instance_path.read_text(encoding="utf-8"))
    data = load_lunar_ice_data(instance)
    payload = build_bound_gap_diagnostic(
        data,
        compact_csv_paths=tuple(_resolve(path) for path in args.compact_csv),
    )
    payload["instance_path"] = str(instance_path)

    output_md = _resolve(args.output_md)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(render_markdown(payload), encoding="utf-8")

    if args.output_json:
        output_json = _resolve(args.output_json)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"bound gap diagnostic written to {output_md}")
    return 0


def build_bound_gap_diagnostic(data, *, compact_csv_paths: tuple[Path, ...]) -> dict:
    refs = objective_references(data)
    full_mask = journey_driver._full_task_mask(data)
    reference = journey_driver._reference_solution_upper_bound(data)
    reference_objective = None if reference is None else float(reference.objective)
    task_visit = _task_visit_lower_bound_payload(data)
    return_path = _return_path_lower_bound_payload(data)
    endpoint_path = _endpoint_path_lower_bound_payload(data)
    outgoing_task_visit = _outgoing_task_visit_lower_bound_payload(data)
    start_path = _start_path_lower_bound_payload(data)
    inbound_tail_bound = round(float(task_visit["function_value"]) + float(endpoint_path["function_value"]), 9)
    outgoing_tail_bound = round(
        float(outgoing_task_visit["function_value"]) + float(start_path["function_value"]),
        9,
    )
    future_tail = _future_tail_lower_bound_payload(
        data,
        inbound_tail_bound=inbound_tail_bound,
        outgoing_tail_bound=outgoing_tail_bound,
    )
    direct_pruning_bound = float(future_tail["function_value"])
    analytic = compute_analytic_lower_bound(data).to_payload()
    compact_rows = _compact_bound_rows(data.instance_id, compact_csv_paths)

    bounds = [
        {
            "name": "analytic_relaxation",
            "bound": _float_or_none(analytic.get("bound")),
            "source": analytic.get("status"),
            "note": analytic.get("note"),
        },
        {
            "name": "task_visit_lower_bound",
            "bound": float(task_visit["objective"]),
            "source": "service_plus_min_inbound_path_metrics",
            "note": (
                "Safe per-task bound used by direct-DP pruning; it relaxes routing order, return, "
                "fleet coupling, capacity interactions, and recharge sequencing."
            ),
        },
        {
            "name": "direct_dp_root_pruning_bound",
            "bound": direct_pruning_bound,
            "source": "max(inbound_tail_bound,outgoing_tail_bound)",
            "note": (
                "Current direct-DP pruning bound at root; it takes the stronger of a safe inbound "
                "task-visit formulation and a safe outgoing task-visit formulation."
            ),
        },
    ]
    for row in compact_rows:
        bounds.append(
            {
                "name": f"compact_product_bound:{row['source_name']}",
                "bound": row.get("bound"),
                "source": "HiGHS compact product LP/MIP dual bound",
                "note": (
                    "Product-oracle diagnostic bound; useful for scale diagnosis but not a BPC tree certificate."
                ),
            }
        )

    for row in bounds:
        row["ratio_to_reference_upper_bound"] = _ratio(row.get("bound"), reference_objective)
        row["gap_vs_reference_upper_bound"] = _gap(reference_objective, row.get("bound"))

    return {
        "schema_version": "lunar_ice_bpc.bound_gap_diagnostic.v1",
        "objective_schema_version": OBJECTIVE_SCHEMA_VERSION,
        "objective_mode": OBJECTIVE_MODE,
        "instance_id": data.instance_id,
        "scale": int(data.scale),
        "task_count": len(data.task_ids),
        "reference_upper_bound": reference_objective,
        "reference_upper_bound_source": "" if reference is None else reference.source,
        "objective_references": refs.to_payload(),
        "task_visit_lower_bound": task_visit,
        "return_path_lower_bound": return_path,
        "endpoint_path_lower_bound": endpoint_path,
        "outgoing_task_visit_lower_bound": outgoing_task_visit,
        "start_path_lower_bound": start_path,
        "future_tail_lower_bound": future_tail,
        "analytic_lower_bound": analytic,
        "compact_bound_rows": compact_rows,
        "bounds": bounds,
    }


def _task_visit_lower_bound_payload(data) -> dict:
    refs = objective_references(data)
    min_inbound = journey_driver._min_inbound_path_metric_by_task(data)
    raw_cost = 0.0
    raw_risk = 0.0
    raw_completion = 0.0
    per_task = []
    for index, task_id in enumerate(data.task_ids):
        task = data.tasks[task_id]
        min_distance, min_energy, min_risk = min_inbound[str(task_id)]
        completion = float(task.science_weight) * (max(0.0, float(task.ready_time)) + float(task.service_time))
        cost = operating_cost_value(
            service_cost=float(task.service_cost),
            distance_km=float(min_distance),
            energy_proxy=float(task.service_energy) + float(min_energy),
        )
        risk = service_risk_value(task) + float(min_risk)
        raw_cost += cost
        raw_risk += risk
        raw_completion += completion
        per_task.append(
            {
                "index": index,
                "task_id": str(task_id),
                "cost": round(cost, 9),
                "risk": round(risk, 9),
                "weighted_completion": round(completion, 9),
                "min_inbound_distance": round(float(min_distance), 9),
                "min_inbound_energy": round(float(min_energy), 9),
                "min_inbound_risk": round(float(min_risk), 9),
            }
        )
    normalized_cost = raw_cost / refs.reference_cost
    normalized_risk = raw_risk / refs.reference_risk
    normalized_completion = raw_completion / refs.reference_completion
    objective = normalized_cost + normalized_risk + 0.4 * normalized_completion
    full_mask = journey_driver._full_task_mask(data)
    fn_value = journey_driver._remaining_task_visit_lower_bound_fn(data)(full_mask)
    return {
        "raw_operating_cost": round(raw_cost, 9),
        "raw_risk": round(raw_risk, 9),
        "raw_weighted_completion_time": round(raw_completion, 9),
        "normalized_operating_cost": round(normalized_cost, 9),
        "normalized_risk": round(normalized_risk, 9),
        "normalized_weighted_completion_time": round(normalized_completion, 9),
        "weighted_normalized_completion": round(0.4 * normalized_completion, 9),
        "objective": round(objective, 9),
        "function_value": round(float(fn_value), 9),
        "per_task_count": len(per_task),
        "largest_task_terms": sorted(
            per_task,
            key=lambda row: row["cost"] + row["risk"] + 0.4 * row["weighted_completion"],
            reverse=True,
        )[:5],
    }


def _return_path_lower_bound_payload(data) -> dict:
    full_mask = journey_driver._full_task_mask(data)
    fn_value = journey_driver._remaining_return_path_lower_bound_fn(data)(full_mask)
    return {
        "function_value": round(float(fn_value), 9),
        "scope": "at_least_one_return_to_depot_path",
    }


def _endpoint_path_lower_bound_payload(data) -> dict:
    full_mask = journey_driver._full_task_mask(data)
    fn_value = journey_driver._remaining_endpoint_path_lower_bound_fn(data)(full_mask)
    return {
        "function_value": round(float(fn_value), 9),
        "scope": "minimum_future_sortie_starts_and_returns",
    }


def _outgoing_task_visit_lower_bound_payload(data) -> dict:
    full_mask = journey_driver._full_task_mask(data)
    fn_value = journey_driver._remaining_outgoing_task_visit_lower_bound_fn(data)(full_mask)
    return {
        "function_value": round(float(fn_value), 9),
        "scope": "service_plus_min_outgoing_path_metrics",
    }


def _start_path_lower_bound_payload(data) -> dict:
    full_mask = journey_driver._full_task_mask(data)
    fn_value = journey_driver._remaining_start_path_lower_bound_fn(data)(full_mask)
    return {
        "function_value": round(float(fn_value), 9),
        "scope": "minimum_future_sortie_depot_starts",
    }


def _future_tail_lower_bound_payload(data, *, inbound_tail_bound: float, outgoing_tail_bound: float) -> dict:
    full_mask = journey_driver._full_task_mask(data)
    fn_value = journey_driver._remaining_future_sortie_tail_lower_bound_fn(data)(full_mask, 0.0)
    return {
        "function_value": round(float(fn_value), 9),
        "inbound_tail_bound": round(float(inbound_tail_bound), 9),
        "outgoing_tail_bound": round(float(outgoing_tail_bound), 9),
        "scope": "max_of_safe_inbound_and_outgoing_future_sortie_tail_bounds",
    }


def _compact_bound_rows(instance_id: str, paths: tuple[Path, ...]) -> list[dict]:
    rows = []
    for path in paths:
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                if str(row.get("instance_id") or "") != str(instance_id):
                    continue
                bound = _float_or_none(row.get("bound") or row.get("solver_info_mip_dual_bound"))
                objective = _float_or_none(row.get("objective") or row.get("model_objective"))
                rows.append(
                    {
                        "source_name": path.parent.name or path.stem,
                        "path": str(path),
                        "algorithm_status": row.get("algorithm_status"),
                        "certificate_scope": row.get("certificate_scope"),
                        "has_feasible_incumbent": row.get("has_feasible_incumbent"),
                        "objective": objective,
                        "bound": bound,
                        "gap": _float_or_none(row.get("gap") or row.get("solver_info_mip_gap")),
                        "simplex_iteration_count": _float_or_none(row.get("solver_info_simplex_iteration_count")),
                        "mip_node_count": _float_or_none(row.get("solver_info_mip_node_count")),
                    }
                )
                break
    return rows


def render_markdown(payload: dict) -> str:
    lines = [
        "# 30-scale Bound Gap Diagnostic",
        "",
        "## 边界",
        "",
        "- 该诊断不求解实例，只汇总已有上界/下界强度。",
        "- compact product bound 是 product-oracle 诊断下界，不是 BPC tree certificate。",
        "- makespan 仍只作为报告指标；下表所有目标值均使用 normalized additive official objective。",
        "",
        "## 实例",
        "",
        f"- instance: `{payload['instance_id']}`",
        f"- scale: `{payload['scale']}`",
        f"- task count: `{payload['task_count']}`",
        f"- reference upper bound: `{_fmt(payload.get('reference_upper_bound'))}`",
        f"- reference upper bound source: `{payload.get('reference_upper_bound_source') or ''}`",
        "",
        "## 下界对比",
        "",
        "| bound | value | ratio to ref UB | gap vs ref UB | note |",
        "|---|---:|---:|---:|---|",
    ]
    for row in payload["bounds"]:
        lines.append(
            f"| `{row['name']}` | {_fmt(row.get('bound'))} | {_fmt(row.get('ratio_to_reference_upper_bound'))} | "
            f"{_fmt(row.get('gap_vs_reference_upper_bound'))} | {row.get('note') or ''} |"
        )
    task_visit = payload["task_visit_lower_bound"]
    return_path = payload["return_path_lower_bound"]
    endpoint_path = payload["endpoint_path_lower_bound"]
    outgoing_task_visit = payload["outgoing_task_visit_lower_bound"]
    start_path = payload["start_path_lower_bound"]
    future_tail = payload["future_tail_lower_bound"]
    direct_root = float(future_tail["function_value"])
    lines.extend(
        [
            "",
            "## Task-Visit Lower Bound 分解",
            "",
            "| term | raw | normalized contribution |",
            "|---|---:|---:|",
            f"| operating cost | {_fmt(task_visit['raw_operating_cost'])} | {_fmt(task_visit['normalized_operating_cost'])} |",
            f"| risk | {_fmt(task_visit['raw_risk'])} | {_fmt(task_visit['normalized_risk'])} |",
            f"| weighted completion | {_fmt(task_visit['raw_weighted_completion_time'])} | {_fmt(task_visit['weighted_normalized_completion'])} |",
            f"| total |  | {_fmt(task_visit['objective'])} |",
            f"| one return path |  | {_fmt(return_path['function_value'])} |",
            f"| endpoint path lower bound |  | {_fmt(endpoint_path['function_value'])} |",
            f"| inbound tail bound |  | {_fmt(future_tail['inbound_tail_bound'])} |",
            f"| outgoing task-visit lower bound |  | {_fmt(outgoing_task_visit['function_value'])} |",
            f"| start path lower bound |  | {_fmt(start_path['function_value'])} |",
            f"| outgoing tail bound |  | {_fmt(future_tail['outgoing_tail_bound'])} |",
            f"| direct-DP root pruning bound |  | {_fmt(direct_root)} |",
            "",
            "## 解释",
            "",
            "- direct-DP root pruning bound 对该实例仍偏弱：只达到 repaired reference upper bound 的约 "
            f"{_fmt(_percent(direct_root, payload.get('reference_upper_bound')))}%。",
            "- compact product dual bound 明显强于 task-visit bound，但它仍不是 BPC certificate，且已有 probe 没有闭合 product model。",
            "- 下一步更有价值的 exact-safe 方向是更强的 relaxation/certificate path，而不是继续做局部 dominance 微调。",
        ]
    )
    return "\n".join(lines) + "\n"


def _ratio(value, denominator) -> float | None:
    value = _float_or_none(value)
    denominator = _float_or_none(denominator)
    if value is None or denominator is None or abs(denominator) <= 1.0e-12:
        return None
    return round(value / denominator, 9)


def _gap(incumbent, lower_bound) -> float | None:
    incumbent = _float_or_none(incumbent)
    lower_bound = _float_or_none(lower_bound)
    if incumbent is None or lower_bound is None or abs(incumbent) <= 1.0e-12:
        return None
    return round(max(0.0, incumbent - lower_bound) / abs(incumbent), 9)


def _percent(value, denominator) -> float | None:
    ratio = _ratio(value, denominator)
    return None if ratio is None else round(100.0 * ratio, 2)


def _fmt(value) -> str:
    value = _float_or_none(value)
    if value is None:
        return ""
    return f"{value:.9g}"


def _float_or_none(value) -> float | None:
    if value in {None, ""}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _resolve(path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else ROOT / candidate


if __name__ == "__main__":
    raise SystemExit(main())
