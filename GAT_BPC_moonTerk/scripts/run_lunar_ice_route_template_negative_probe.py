"""Run exact-safe route-template negative-column probes for lunar-ice pricing."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.core.journey import journey_column_from_solution_payload
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals, manual_journey_reduced_cost
from lunar_ice_bpc.exact.pricing.journey_pricing import price_direct_journey_columns_incremental
from lunar_ice_bpc.io.instance_io import read_json


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-json", required=True, type=Path)
    parser.add_argument("--active-pool-json", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--history-round", type=int, default=-1)
    parser.add_argument("--max-direct-tasks", type=int, default=8)
    parser.add_argument("--max-active-seeds", type=int, default=120)
    parser.add_argument("--max-candidate-sets", type=int, default=160)
    parser.add_argument("--time-limit-sec", type=float, default=60.0)
    parser.add_argument("--negative-eps", type=float, default=1.0e-6)
    args = parser.parse_args()

    source = _read_json(args.source_json)
    active_source = _read_json(args.active_pool_json) if args.active_pool_json else source
    instance_path = Path(str(source.get("instance_path") or active_source.get("instance_path") or ""))
    if not instance_path.exists():
        raise SystemExit(f"instance_path not found in source JSON: {instance_path}")

    data = load_lunar_ice_data(read_json(instance_path))
    dual_context = _select_dual_context(source, history_round=int(args.history_round))
    duals = JourneyDuals(
        cover={str(task_id): float(value) for task_id, value in (dual_context.get("task_duals") or {}).items()},
        fleet_limit=float(dual_context.get("fleet_dual") or 0.0),
        cuts={str(cut_id): float(value) for cut_id, value in (dual_context.get("cut_duals") or {}).items()},
    )
    seed_rows = _active_pool_seed_task_sets(
        data,
        active_source.get("active_columns") or (),
        duals=duals,
        max_direct_tasks=int(args.max_direct_tasks),
        max_active_seeds=int(args.max_active_seeds),
    )
    pricing_payload, columns = price_direct_journey_columns_incremental(
        data,
        duals,
        negative_eps=float(args.negative_eps),
        max_direct_tasks=int(args.max_direct_tasks),
        seed_task_sets=seed_rows,
        max_candidate_sets=int(args.max_candidate_sets),
        wall_time_limit_sec=float(args.time_limit_sec),
        stop_at_first_negative=True,
    )
    negative_payloads = [
        {
            "reduced_cost": manual_journey_reduced_cost(column, duals),
            "task_count": len(column.task_set),
            "tasks": sorted(column.task_set),
            "objective": column.objective,
            "sortie_count": len(column.sorties),
            "solution_payload": column.to_solution_payload(vehicle_id=f"route_template_negative_{index + 1:03d}"),
        }
        for index, column in enumerate(columns)
        if manual_journey_reduced_cost(column, duals) < -abs(float(args.negative_eps))
    ]
    compact_reference = _compact_reference_payload(source)
    result = {
        "schema_version": "lunar_ice_bpc.route_template_negative_probe.v1",
        "source_json": str(args.source_json),
        "active_pool_json": str(args.active_pool_json or args.source_json),
        "instance_path": str(instance_path),
        "instance_id": data.instance_id,
        "config": {
            "max_direct_tasks": int(args.max_direct_tasks),
            "max_active_seeds": int(args.max_active_seeds),
            "max_candidate_sets": int(args.max_candidate_sets),
            "time_limit_sec": float(args.time_limit_sec),
            "negative_eps": float(args.negative_eps),
            "history_round": int(args.history_round),
        },
        "dual_context": dual_context,
        "active_seed_count": len(seed_rows),
        "active_seed_task_sets": [list(row) for row in seed_rows],
        "pricing": pricing_payload,
        "negative_columns": negative_payloads,
        "compact_reference": compact_reference,
        "speedup_vs_compact_reference": _speedup_payload(pricing_payload, compact_reference),
        "certificate_boundary": (
            "Negative columns are true-dual audited and exact-safe to add. "
            "This probe never certifies no-negative because selected task sets are not full-space coverage."
        ),
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_json = args.output_dir / "route_template_negative_probe.json"
    report_md = args.output_dir / "route_template_negative_probe_zh.md"
    output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    report_md.write_text(_build_report(result), encoding="utf-8")
    print(f"route-template negative probe written to {output_json}")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _select_dual_context(payload: dict, *, history_round: int) -> dict:
    if isinstance(payload.get("dual_context"), dict):
        return dict(payload["dual_context"])
    history = payload.get("history") or ()
    if history:
        index = int(history_round)
        if index < 0:
            row = history[index]
        else:
            row = history[max(0, index - 1)]
        if isinstance(row.get("dual_context"), dict):
            return dict(row["dual_context"])
    result = payload.get("result")
    if isinstance(result, dict) and isinstance(result.get("dual_context"), dict):
        return dict(result["dual_context"])
    raise ValueError("source JSON does not contain a usable dual_context")


def _active_pool_seed_task_sets(
    data,
    active_columns: Iterable[dict],
    *,
    duals: JourneyDuals,
    max_direct_tasks: int,
    max_active_seeds: int,
) -> tuple[tuple[str, ...], ...]:
    scored: list[tuple[float, tuple[str, ...]]] = []
    seen: set[tuple[str, ...]] = set()
    for payload in active_columns:
        if not isinstance(payload, dict):
            continue
        try:
            column = journey_column_from_solution_payload(data, payload)
        except Exception:
            continue
        task_set = tuple(sorted(column.task_set))
        if not task_set or len(task_set) > int(max_direct_tasks) or task_set in seen:
            continue
        seen.add(task_set)
        score = (
            sum(float(duals.cover.get(task_id, 0.0)) for task_id in task_set)
            - float(column.objective)
            - float(duals.fleet_limit)
        )
        scored.append((score, task_set))
    scored.sort(key=lambda item: (-item[0], len(item[1]), item[1]))
    return tuple(task_set for _, task_set in scored[: max(0, int(max_active_seeds))])


def _compact_reference_payload(source: dict) -> dict:
    result = source.get("result") if isinstance(source.get("result"), dict) else None
    if result is not None:
        return {
            "source": "result",
            "wall_time_sec": result.get("wall_time_sec"),
            "best_reduced_cost": result.get("best_reduced_cost"),
            "dual_bound": result.get("dual_bound"),
            "pricing_state": result.get("pricing_state"),
            "algorithm_status": result.get("algorithm_status") or result.get("status"),
        }
    final_judge = source.get("final_judge") if isinstance(source.get("final_judge"), dict) else None
    if final_judge is not None:
        return {
            "source": "final_judge",
            "wall_time_sec": final_judge.get("wall_time_sec"),
            "best_reduced_cost": final_judge.get("best_reduced_cost"),
            "dual_bound": final_judge.get("dual_bound"),
            "pricing_state": final_judge.get("pricing_state"),
            "algorithm_status": final_judge.get("algorithm_status") or final_judge.get("status"),
        }
    history = source.get("history") or ()
    if history:
        row = history[-1]
        return {
            "source": "history_last",
            "wall_time_sec": row.get("final_judge_wall_time"),
            "best_reduced_cost": row.get("best_reduced_cost"),
            "dual_bound": row.get("dual_bound"),
            "pricing_state": row.get("pricing_state"),
            "algorithm_status": row.get("final_judge_status"),
        }
    return {"source": "none"}


def _speedup_payload(pricing: dict, compact: dict) -> dict:
    route_wall = _float_or_none(pricing.get("wall_time_sec"))
    compact_wall = _float_or_none(compact.get("wall_time_sec"))
    if route_wall is None or compact_wall is None or route_wall <= 0.0:
        return {"available": False}
    return {
        "available": True,
        "route_template_wall_time_sec": round(route_wall, 6),
        "compact_reference_wall_time_sec": round(compact_wall, 6),
        "saved_wall_time_sec": round(compact_wall - route_wall, 6),
        "speedup_factor": round(compact_wall / route_wall, 6),
    }


def _float_or_none(value) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _build_report(result: dict) -> str:
    pricing = result["pricing"]
    speedup = result["speedup_vs_compact_reference"]
    negative_columns = result["negative_columns"]
    lines = [
        "# Route-template Negative Probe",
        "",
        "## Boundary",
        "",
        "- This is an exact-safe negative-column discovery probe.",
        "- It does not certify no-negative and never upgrades BPC status.",
        "- Returned negative columns are manually reduced-cost audited under the current true dual.",
        "",
        "## Result",
        "",
        f"- instance: `{result['instance_id']}`",
        f"- status: `{pricing.get('status')}`",
        f"- wall time: `{pricing.get('wall_time_sec')}` s",
        f"- best reduced cost: `{pricing.get('best_reduced_cost')}`",
        f"- negative columns: `{len(negative_columns)}`",
        f"- active seeds: `{result.get('active_seed_count')}`",
        f"- candidate rounds: `{pricing.get('candidate_round_count')}`",
        f"- sortie attempts: `{pricing.get('sortie_attempt_count')}`",
        f"- feasible route templates: `{pricing.get('feasible_sortie_template_count')}`",
        f"- pareto labels: `{pricing.get('pareto_label_count')}`",
        "",
        "## Compact Reference",
        "",
        f"- source: `{result['compact_reference'].get('source')}`",
        f"- wall time: `{result['compact_reference'].get('wall_time_sec')}` s",
        f"- best reduced cost: `{result['compact_reference'].get('best_reduced_cost')}`",
        f"- pricing state: `{result['compact_reference'].get('pricing_state')}`",
        "",
        "## Speed",
        "",
    ]
    if speedup.get("available"):
        lines.extend(
            [
                f"- saved wall time: `{speedup.get('saved_wall_time_sec')}` s",
                f"- speedup factor: `{speedup.get('speedup_factor')}x`",
            ]
        )
    else:
        lines.append("- speedup unavailable: missing comparable wall times.")
    lines.extend(["", "## Negative Columns", ""])
    if not negative_columns:
        lines.append("- none")
    for row in negative_columns:
        lines.append(
            f"- rc `{row['reduced_cost']}` | tasks `{row['task_count']}` | sorties `{row['sortie_count']}` | "
            f"{', '.join(row['tasks'])}"
        )
    lines.extend(["", "## Certificate Boundary", "", result["certificate_boundary"], ""])
    return "\n".join(lines)


if __name__ == "__main__":
    main()
