#!/usr/bin/env python3
"""Replay compact single-journey pricing from saved B1 pricing history duals."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals  # noqa: E402
from lunar_ice_bpc.exact.solver.gurobi_compact import solve_highs_compact_single_journey_pricing  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", required=True)
    parser.add_argument("--rows-json")
    parser.add_argument("--rows-csv")
    parser.add_argument("--mode", default="B1B_seeded_root_CG")
    parser.add_argument("--history-round", type=int, default=-1, help="-1 means last history row.")
    parser.add_argument("--time-limit-sec", type=float, default=120.0)
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--negative-eps", type=float, default=1.0e-6)
    parser.add_argument("--mtz-connectivity", action="store_true")
    parser.add_argument("--flow-connectivity", action="store_true")
    parser.add_argument("--mtz-endpoint-order-cuts", action="store_true")
    parser.add_argument("--no-mtz-endpoint-order-cuts", action="store_true")
    parser.add_argument("--pair-adjacency-cuts", action="store_true")
    parser.add_argument("--disable-latest-service-start-slot-bound", action="store_true")
    parser.add_argument("--time-window-arc-pruning", action="store_true")
    parser.add_argument("--disable-time-window-arc-pruning", action="store_true")
    parser.add_argument("--service-start-depot-travel-lb", action="store_true")
    parser.add_argument("--task-to-depot-return-travel-lb", action="store_true")
    parser.add_argument("--pair-route-duration-lb", action="store_true")
    parser.add_argument("--sortie-slot-position-bounds", action="store_true")
    parser.add_argument("--demand-cover-cut", action="store_true")
    parser.add_argument("--single-task-energy-lb", action="store_true")
    parser.add_argument("--single-task-shadow-lb", action="store_true")
    parser.add_argument("--pair-energy-lb", action="store_true")
    parser.add_argument("--pair-energy-infeasible-cut", action="store_true")
    parser.add_argument("--pair-shadow-infeasible-cut", action="store_true")
    parser.add_argument("--triple-shadow-infeasible-cut", action="store_true")
    parser.add_argument("--triple-energy-infeasible-cut", action="store_true")
    parser.add_argument("--triple-time-window-infeasible-cut", action="store_true")
    parser.add_argument("--quad-time-window-infeasible-cut", action="store_true")
    parser.add_argument("--negative-feasibility-search", action="store_true")
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    args = parser.parse_args()

    if not args.rows_json and not args.rows_csv:
        raise SystemExit("pass --rows-json or --rows-csv")

    instance_path = _resolve(args.instance)
    raw = json.loads(instance_path.read_text(encoding="utf-8"))
    data = load_lunar_ice_data(raw)
    source_row = _load_source_row(args)
    history = _history_from_row(source_row)
    history_row = _select_history_row(history, int(args.history_round))
    dual_context = history_row.get("dual_context")
    if not isinstance(dual_context, dict):
        raise SystemExit("selected history row has no dual_context; rerun B1B with current telemetry first")

    duals = JourneyDuals(
        cover={str(key): float(value) for key, value in (dual_context.get("task_duals") or {}).items()},
        fleet_limit=float(dual_context.get("fleet_dual") or 0.0),
        cuts={str(key): float(value) for key, value in (dual_context.get("cut_duals") or {}).items()},
    )
    mtz_endpoint_order_cuts = bool(args.mtz_endpoint_order_cuts and not args.no_mtz_endpoint_order_cuts)
    time_window_arc_pruning = bool(args.time_window_arc_pruning and not args.disable_time_window_arc_pruning)
    result = solve_highs_compact_single_journey_pricing(
        data,
        duals,
        time_limit_sec=float(args.time_limit_sec),
        threads=int(args.threads),
        mip_gap=0.0,
        negative_eps=float(args.negative_eps),
        flow_connectivity=bool(args.flow_connectivity),
        mtz_connectivity=bool(args.mtz_connectivity),
        mtz_endpoint_order_cuts=mtz_endpoint_order_cuts,
        pair_adjacency_cuts=bool(args.pair_adjacency_cuts),
        latest_service_start_slot_bound=not bool(args.disable_latest_service_start_slot_bound),
        time_window_arc_pruning=time_window_arc_pruning,
        service_start_depot_travel_lb=bool(args.service_start_depot_travel_lb),
        task_to_depot_return_travel_lb=bool(args.task_to_depot_return_travel_lb),
        pair_route_duration_lb=bool(args.pair_route_duration_lb),
        sortie_slot_position_bounds=bool(args.sortie_slot_position_bounds),
        demand_cover_cut=bool(args.demand_cover_cut),
        single_task_energy_lb=bool(args.single_task_energy_lb),
        single_task_shadow_lb=bool(args.single_task_shadow_lb),
        pair_energy_lb=bool(args.pair_energy_lb),
        pair_energy_infeasible_cut=bool(args.pair_energy_infeasible_cut),
        pair_shadow_infeasible_cut=bool(args.pair_shadow_infeasible_cut),
        triple_shadow_infeasible_cut=bool(args.triple_shadow_infeasible_cut),
        triple_energy_infeasible_cut=bool(args.triple_energy_infeasible_cut),
        triple_time_window_infeasible_cut=bool(args.triple_time_window_infeasible_cut),
        quad_time_window_infeasible_cut=bool(args.quad_time_window_infeasible_cut),
        negative_feasibility_search=bool(args.negative_feasibility_search),
    )
    payload = {
        "schema_version": "lunar_ice_bpc.compact_pricing_replay.v1",
        "instance_path": str(instance_path),
        "instance_id": data.instance_id,
        "source_mode": str(source_row.get("mode") or ""),
        "source_algorithm_status": source_row.get("algorithm_status"),
        "source_certificate_scope": source_row.get("certificate_scope"),
        "source_pricing_round_count": source_row.get("pricing_round_count"),
        "source_added_column_count": source_row.get("added_column_count"),
        "selected_history_round": history_row.get("round"),
        "selected_history_pricing_state": history_row.get("pricing_state"),
        "selected_history_best_reduced_cost": history_row.get("best_reduced_cost"),
        "selected_history_dual_bound": history_row.get("dual_bound"),
        "selected_history_added_column_count": history_row.get("added_column_count"),
        "dual_context": dual_context,
        "replay_config": {
            "time_limit_sec": float(args.time_limit_sec),
            "threads": int(args.threads),
            "negative_eps": float(args.negative_eps),
            "mtz_connectivity": bool(args.mtz_connectivity),
            "flow_connectivity": bool(args.flow_connectivity),
            "mtz_endpoint_order_cuts": mtz_endpoint_order_cuts,
            "pair_adjacency_cuts": bool(args.pair_adjacency_cuts),
            "latest_service_start_slot_bound": not bool(args.disable_latest_service_start_slot_bound),
            "time_window_arc_pruning": time_window_arc_pruning,
            "service_start_depot_travel_lb": bool(args.service_start_depot_travel_lb),
            "task_to_depot_return_travel_lb": bool(args.task_to_depot_return_travel_lb),
            "pair_route_duration_lb": bool(args.pair_route_duration_lb),
            "sortie_slot_position_bounds": bool(args.sortie_slot_position_bounds),
            "demand_cover_cut": bool(args.demand_cover_cut),
            "single_task_energy_lb": bool(args.single_task_energy_lb),
            "single_task_shadow_lb": bool(args.single_task_shadow_lb),
            "pair_energy_lb": bool(args.pair_energy_lb),
            "pair_energy_infeasible_cut": bool(args.pair_energy_infeasible_cut),
            "pair_shadow_infeasible_cut": bool(args.pair_shadow_infeasible_cut),
            "triple_shadow_infeasible_cut": bool(args.triple_shadow_infeasible_cut),
            "triple_energy_infeasible_cut": bool(args.triple_energy_infeasible_cut),
            "triple_time_window_infeasible_cut": bool(args.triple_time_window_infeasible_cut),
            "quad_time_window_infeasible_cut": bool(args.quad_time_window_infeasible_cut),
            "negative_feasibility_search": bool(args.negative_feasibility_search),
        },
        "result": _json_safe_result(result),
    }

    output_json = _resolve(args.output_json)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md = _resolve(args.output_md)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(_render_markdown(payload), encoding="utf-8")
    print(f"compact pricing replay written to {output_md}")
    return 0


def _load_source_row(args) -> dict:
    rows: list[dict]
    if args.rows_json:
        payload = json.loads(_resolve(args.rows_json).read_text(encoding="utf-8"))
        if isinstance(payload, list):
            rows = payload
        elif isinstance(payload, dict) and isinstance(payload.get("rows"), list):
            rows = list(payload.get("rows") or [])
        elif isinstance(payload, dict) and (
            isinstance(payload.get("history"), list) or payload.get("pricing_history_json")
        ):
            return payload
        else:
            rows = []
    else:
        with _resolve(args.rows_csv).open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
    candidates = [row for row in rows if str(row.get("mode") or "") == str(args.mode)]
    if not candidates:
        raise SystemExit(f"no row found for mode={args.mode!r}")
    return candidates[-1]


def _history_from_row(row: dict) -> list[dict]:
    history = row.get("pricing_history_json") or row.get("history")
    if isinstance(history, list):
        return history
    if not history:
        return []
    parsed = json.loads(str(history))
    if not isinstance(parsed, list):
        raise SystemExit("pricing_history_json is not a list")
    return parsed


def _select_history_row(history: list[dict], round_index: int) -> dict:
    if not history:
        raise SystemExit("source row has empty pricing history")
    if round_index < 0:
        return history[round_index]
    for row in history:
        if int(row.get("round") or -1) == int(round_index):
            return row
    raise SystemExit(f"history round {round_index} not found")


def _json_safe_result(result: dict) -> dict:
    safe = {key: value for key, value in result.items() if key != "journeys"}
    journeys = tuple(result.get("journeys") or tuple())
    safe["journey_count"] = len(journeys)
    best = result.get("best_column")
    if best is not None:
        safe["best_column"] = best
    if journeys:
        safe["best_solution_payload"] = journeys[0].to_solution_payload(vehicle_id="compact_replay_best")
    return safe


def _render_markdown(payload: dict) -> str:
    result = payload["result"]
    config = payload["replay_config"]
    lines = [
        "# Compact Pricing Replay",
        "",
        "## Source",
        "",
        f"- instance: `{payload['instance_id']}`",
        f"- selected history round: `{payload.get('selected_history_round')}`",
        f"- source pricing state: `{payload.get('selected_history_pricing_state')}`",
        f"- source best RC: `{payload.get('selected_history_best_reduced_cost')}`",
        f"- source dual bound: `{payload.get('selected_history_dual_bound')}`",
        "",
        "## Replay Config",
        "",
        f"- time limit: `{config['time_limit_sec']}`",
        f"- negative feasibility search: `{config['negative_feasibility_search']}`",
        f"- MTZ connectivity: `{config['mtz_connectivity']}`",
        f"- flow connectivity: `{config['flow_connectivity']}`",
        f"- MTZ endpoint order cuts: `{config['mtz_endpoint_order_cuts']}`",
        f"- pair adjacency cuts: `{config['pair_adjacency_cuts']}`",
        f"- latest-service-start slot bound: `{config['latest_service_start_slot_bound']}`",
        f"- time-window arc pruning: `{config['time_window_arc_pruning']}`",
        f"- service-start depot-travel LB: `{config['service_start_depot_travel_lb']}`",
        f"- task-to-depot return-travel LB: `{config['task_to_depot_return_travel_lb']}`",
        f"- pair route-duration LB: `{config['pair_route_duration_lb']}`",
        f"- sortie slot-position bounds: `{config['sortie_slot_position_bounds']}`",
        f"- demand cover cut: `{config['demand_cover_cut']}`",
        f"- single-task energy LB: `{config['single_task_energy_lb']}`",
        f"- single-task shadow LB: `{config['single_task_shadow_lb']}`",
        f"- pair energy LB: `{config['pair_energy_lb']}`",
        f"- pair energy infeasible cut: `{config['pair_energy_infeasible_cut']}`",
        f"- pair shadow infeasible cut: `{config['pair_shadow_infeasible_cut']}`",
        f"- triple shadow infeasible cut: `{config['triple_shadow_infeasible_cut']}`",
        f"- triple energy infeasible cut: `{config['triple_energy_infeasible_cut']}`",
        f"- triple time-window infeasible cut: `{config['triple_time_window_infeasible_cut']}`",
        f"- quad time-window infeasible cut: `{config['quad_time_window_infeasible_cut']}`",
        "",
        "## Result",
        "",
        f"- status: `{result.get('status')}`",
        f"- exact status: `{result.get('exact_status')}`",
        f"- pricing state: `{result.get('pricing_state')}`",
        f"- best reduced cost: `{result.get('best_reduced_cost')}`",
        f"- dual bound: `{result.get('dual_bound')}`",
        f"- gap: `{result.get('gap')}`",
        f"- negative found: `{result.get('negative_found')}`",
        f"- can certify no-negative: `{result.get('can_certify_no_negative')}`",
        f"- MTZ endpoint order cut count: `{result.get('mtz_endpoint_order_cut_count')}`",
        f"- pair adjacency cut count: `{result.get('pair_adjacency_cut_count')}`",
        f"- latest-service-start slot bound enabled: `{result.get('latest_service_start_slot_bound_enabled')}`",
        f"- sortie slot bound source: `{result.get('sortie_slot_bound_source')}`",
        f"- time-window arc pruning enabled: `{result.get('time_window_arc_pruning_enabled')}`",
        f"- time-window impossible arc options: `{result.get('time_window_impossible_arc_option_count')}`",
        f"- service-start depot-travel LB enabled: `{result.get('service_start_depot_travel_lb_enabled')}`",
        f"- service-start depot-travel LB rows: `{result.get('service_start_depot_travel_lb_count')}`",
        f"- task-to-depot return-travel LB enabled: `{result.get('task_to_depot_return_travel_lb_enabled')}`",
        f"- task-to-depot return-travel LB rows: `{result.get('task_to_depot_return_travel_lb_count')}`",
        f"- pair route-duration LB enabled: `{result.get('pair_route_duration_lb_enabled')}`",
        f"- pair route-duration LB rows: `{result.get('pair_route_duration_lb_count')}`",
        f"- sortie slot-position bounds enabled: `{result.get('sortie_slot_position_bounds_enabled')}`",
        f"- sortie slot-position bounds rows: `{result.get('sortie_slot_position_bound_count')}`",
        f"- demand cover cut enabled: `{result.get('demand_cover_cut_enabled')}`",
        f"- demand cover cut rows: `{result.get('demand_cover_cut_count')}`",
        f"- single-task energy LB enabled: `{result.get('single_task_energy_lb_enabled')}`",
        f"- single-task energy LB rows: `{result.get('single_task_energy_lb_count')}`",
        f"- single-task shadow LB enabled: `{result.get('single_task_shadow_lb_enabled')}`",
        f"- single-task shadow LB rows: `{result.get('single_task_shadow_lb_count')}`",
        f"- pair energy LB enabled: `{result.get('pair_energy_lb_enabled')}`",
        f"- pair energy LB rows: `{result.get('pair_energy_lb_count')}`",
        f"- pair energy infeasible cut enabled: `{result.get('pair_energy_infeasible_cut_enabled')}`",
        f"- pair energy infeasible cut rows: `{result.get('pair_energy_infeasible_cut_count')}`",
        f"- pair shadow infeasible cut enabled: `{result.get('pair_shadow_infeasible_cut_enabled')}`",
        f"- pair shadow infeasible cut rows: `{result.get('pair_shadow_infeasible_cut_count')}`",
        f"- triple shadow infeasible cut enabled: `{result.get('triple_shadow_infeasible_cut_enabled')}`",
        f"- triple shadow infeasible cut rows: `{result.get('triple_shadow_infeasible_cut_count')}`",
        f"- triple energy infeasible cut enabled: `{result.get('triple_energy_infeasible_cut_enabled')}`",
        f"- triple energy infeasible cut rows: `{result.get('triple_energy_infeasible_cut_count')}`",
        f"- triple time-window infeasible cut enabled: `{result.get('triple_time_window_infeasible_cut_enabled')}`",
        f"- triple time-window infeasible cut rows: `{result.get('triple_time_window_infeasible_cut_count')}`",
        f"- quad time-window infeasible cut enabled: `{result.get('quad_time_window_infeasible_cut_enabled')}`",
        f"- quad time-window infeasible cut rows: `{result.get('quad_time_window_infeasible_cut_count')}`",
        f"- variable count: `{result.get('variable_count')}`",
        f"- constraint count: `{result.get('constraint_count')}`",
        f"- wall time: `{result.get('wall_time_sec')}`",
        "",
        "该 replay 只重放 compact pricing final-judge 子问题；只有 exact pricing optimal/no-negative 时才可作为 BPC final judge 证书的一部分。",
    ]
    return "\n".join(lines) + "\n"


def _resolve(path: str | Path) -> Path:
    raw = Path(path)
    return raw if raw.is_absolute() else ROOT / raw


if __name__ == "__main__":
    raise SystemExit(main())
