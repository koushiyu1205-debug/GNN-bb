#!/usr/bin/env python3
"""中文摘要：本脚本运行 clean BPC 长时间消融实验，用同一实例和 seed 对比 task-vehicle linking 与 schedule-cap cut 的贡献。"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bpc.data import load_bpc_data
from bpc.solver import BPCResult, solve_bpc_clean
from gnn_bb.baseline.config import load_config
from gnn_bb.data.io_utils import ensure_dir


VARIANTS: dict[str, dict[str, bool]] = {
    "no_link_no_schedcap": {
        "task_vehicle_linking_enabled": False,
        "schedule_capacity_cuts_enabled": False,
    },
    "link_only": {
        "task_vehicle_linking_enabled": True,
        "schedule_capacity_cuts_enabled": False,
    },
    "schedcap_only": {
        "task_vehicle_linking_enabled": False,
        "schedule_capacity_cuts_enabled": True,
    },
    "link_schedcap": {
        "task_vehicle_linking_enabled": True,
        "schedule_capacity_cuts_enabled": True,
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行 clean BPC linking / schedule-cap long-run ablation。")
    parser.add_argument("--config", default="configs/bpc_ablation.yaml")
    parser.add_argument("--base-config", help="覆盖 ablation 配置中的 base_config")
    parser.add_argument("--instances", nargs="*", help="覆盖配置中的实例列表")
    parser.add_argument("--variants", nargs="*", choices=sorted(VARIANTS), help="覆盖配置中的 variant 列表")
    parser.add_argument("--time-limit", type=float, help="覆盖每个 variant 的时间限制")
    parser.add_argument("--max-nodes", type=int, help="覆盖最大处理节点数")
    parser.add_argument("--run-id", help="输出目录 run id；默认使用当前时间戳")
    parser.add_argument("--results-csv", help="汇总 CSV 路径；默认写到 results/ablation/<run_id>/summary.csv")
    parser.add_argument("--quiet", action="store_true", help="关闭 clean BPC 控制台进度")
    return parser.parse_args()


def _append_row(path: Path, row: dict[str, Any], fieldnames: list[str]) -> None:
    ensure_dir(path.parent)
    write_header = not path.exists() or path.stat().st_size == 0
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow(row)
        handle.flush()


def _bool_config(config: dict[str, Any], key: str, default: bool) -> bool:
    return bool(config.get(key, default))


def _int_tuple_config(config: dict[str, Any], name: str, default: tuple[int, ...]) -> tuple[int, ...]:
    value = config.get(name, default)
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("[") and text.endswith("]"):
            text = text[1:-1]
        items = [item.strip() for item in text.split(",") if item.strip()]
    elif isinstance(value, (list, tuple)):
        items = list(value)
    else:
        items = [value]
    parsed = tuple(sorted({int(item) for item in items if int(item) >= 2}))
    return parsed or tuple(default)


def _solve_one(
    *,
    data,
    base: dict[str, Any],
    variant: str,
    overrides: dict[str, bool],
    run_root: Path,
    time_limit: float,
    max_nodes: int,
    quiet: bool,
) -> BPCResult:
    log_path = run_root / "logs" / variant / f"{data.name}.jsonl"
    solution_path = run_root / "solutions" / variant / f"solution_{data.name}.json"
    print(
        f"开始 ablation: variant={variant}, instance={data.name}, "
        f"task_vehicle_linking={overrides['task_vehicle_linking_enabled']}, "
        f"schedule_cap={overrides['schedule_capacity_cuts_enabled']}, "
        f"time_limit={time_limit:g}s, log={log_path}",
        flush=True,
    )
    return solve_bpc_clean(
        data,
        time_limit=time_limit,
        max_nodes=max_nodes,
        pricing_eps=float(base.get("pricing_eps", 1.0e-6)),
        integer_tol=float(base.get("integer_tol", 1.0e-6)),
        max_routes_per_pricing=int(base.get("max_routes_per_pricing", 200)),
        max_labels_per_pricing=int(base.get("max_labels_per_pricing", 0) or 0),
        root_max_routes_per_pricing=int(base.get("root_max_routes_per_pricing", 0) or 0),
        heuristic_pricing_enabled=bool(base.get("heuristic_pricing_enabled", False)),
        heuristic_pricing_max_labels=int(base.get("heuristic_pricing_max_labels", 100000)),
        heuristic_pricing_routes_per_round=int(base.get("heuristic_pricing_routes_per_round", 500)),
        heuristic_pricing_selection_mode=str(base.get("heuristic_pricing_selection_mode", "diverse")),
        exact_pricing_selection_mode=str(base.get("exact_pricing_selection_mode", "reduced_cost")),
        branch_node_heuristic_boost_enabled=bool(base.get("branch_node_heuristic_boost_enabled", False)),
        branch_node_heuristic_boost_max_labels=int(base.get("branch_node_heuristic_boost_max_labels", 800000)),
        branch_node_heuristic_boost_routes_per_round=int(base.get("branch_node_heuristic_boost_routes_per_round", 1000)),
        branch_node_heuristic_boost_min_depth=int(base.get("branch_node_heuristic_boost_min_depth", 1)),
        exact_pricing_dominance_enabled=bool(
            base.get("exact_pricing_dominance_enabled", base.get("exact_pricing_enable_dominance", False))
        ),
        pricing_completion_bound_enabled=_bool_config(base, "pricing_completion_bound_enabled", False),
        ng_dssr_pricing_enabled=_bool_config(base, "ng_dssr_pricing_enabled", False),
        ng_dssr_memory_size=int(base.get("ng_dssr_memory_size", 6)),
        exact_dssr_pricing_enabled=_bool_config(base, "exact_dssr_pricing_enabled", False),
        exact_dssr_initial_memory_size=int(base.get("exact_dssr_initial_memory_size", 6)),
        exact_dssr_max_iterations=int(base.get("exact_dssr_max_iterations", 4)),
        exact_dssr_max_labels=int(base.get("exact_dssr_max_labels", 0)),
        route_enumeration_enabled=_bool_config(base, "route_enumeration_enabled", False),
        route_enumeration_rc_threshold=float(base.get("route_enumeration_rc_threshold", 0.0)),
        route_enumeration_max_routes=int(base.get("route_enumeration_max_routes", 0)),
        restricted_master_heuristic_enabled=bool(base.get("restricted_master_heuristic_enabled", False)),
        restricted_master_time_limit=float(base.get("restricted_master_time_limit", 20.0)),
        restricted_master_max_routes=int(base.get("restricted_master_max_routes", 4000)),
        restricted_master_max_calls=int(base.get("restricted_master_max_calls", 20)),
        restricted_master_max_depth=int(base.get("restricted_master_max_depth", 3)),
        restricted_master_schedule_aware=bool(base.get("restricted_master_schedule_aware", True)),
        restricted_master_max_no_good_rounds=int(base.get("restricted_master_max_no_good_rounds", 20)),
        restricted_master_route_pack_conflict_max_events=int(
            base.get("restricted_master_route_pack_conflict_max_events", 2)
        ),
        rmp_params=dict(base.get("rmp_params", {})),
        log_path=log_path,
        solution_path=solution_path,
        seed=int(base["random_seed"]) if base.get("random_seed") is not None else None,
        quiet=bool(quiet or base.get("log_level", "progress") == "quiet"),
        branching_strategy=str(base.get("branching_strategy", "3pb")),
        three_pb_pseudocost_candidates=int(base.get("three_pb_pseudocost_candidates", 6)),
        three_pb_fractional_candidates=int(base.get("three_pb_fractional_candidates", 6)),
        three_pb_lp_candidates=int(base.get("three_pb_lp_candidates", 3)),
        three_pb_heuristic_cg_iterations=int(base.get("three_pb_heuristic_cg_iterations", 3)),
        three_pb_heuristic_routes_per_iter=int(base.get("three_pb_heuristic_routes_per_iter", 50)),
        three_pb_heuristic_max_labels=int(base.get("three_pb_heuristic_max_labels", 800)),
        three_pb_candidate_budget_enabled=_bool_config(base, "three_pb_candidate_budget_enabled", False),
        three_pb_root_pseudocost_candidates=int(base.get("three_pb_root_pseudocost_candidates", 6)),
        three_pb_root_fractional_candidates=int(base.get("three_pb_root_fractional_candidates", 6)),
        three_pb_root_lp_candidates=int(base.get("three_pb_root_lp_candidates", 3)),
        three_pb_nonroot_pseudocost_candidates=int(base.get("three_pb_nonroot_pseudocost_candidates", 4)),
        three_pb_nonroot_fractional_candidates=int(base.get("three_pb_nonroot_fractional_candidates", 4)),
        three_pb_nonroot_lp_candidates=int(base.get("three_pb_nonroot_lp_candidates", 2)),
        three_pb_deep_depth=int(base.get("three_pb_deep_depth", 3)),
        three_pb_deep_pseudocost_candidates=int(base.get("three_pb_deep_pseudocost_candidates", 3)),
        three_pb_deep_fractional_candidates=int(base.get("three_pb_deep_fractional_candidates", 3)),
        three_pb_deep_lp_candidates=int(base.get("three_pb_deep_lp_candidates", 1)),
        task_vehicle_linking_enabled=overrides["task_vehicle_linking_enabled"],
        robust_capacity_cuts_enabled=_bool_config(base, "robust_capacity_cuts_enabled", True),
        robust_capacity_cut_max_depth=int(base.get("robust_capacity_cut_max_depth", 0)),
        robust_capacity_cut_max_subset_size=int(base.get("robust_capacity_cut_max_subset_size", 5)),
        robust_capacity_cut_max_per_round=int(base.get("robust_capacity_cut_max_per_round", 20)),
        robust_capacity_cut_min_violation=float(base.get("robust_capacity_cut_min_violation", 1.0e-5)),
        robust_capacity_cut_max_rounds_per_node=int(base.get("robust_capacity_cut_max_rounds_per_node", 3)),
        resource_lower_bound_cuts_enabled=_bool_config(base, "resource_lower_bound_cuts_enabled", True),
        resource_cut_max_depth=int(base.get("resource_cut_max_depth", 0)),
        resource_cut_max_subset_size=int(base.get("resource_cut_max_subset_size", 6)),
        resource_cut_max_per_round=int(base.get("resource_cut_max_per_round", 20)),
        resource_cut_min_violation=float(base.get("resource_cut_min_violation", 1.0e-5)),
        resource_cut_max_rounds_per_node=int(base.get("resource_cut_max_rounds_per_node", 3)),
        subset_row_cuts_enabled=_bool_config(base, "subset_row_cuts_enabled", True),
        subset_row_cut_max_depth=int(base.get("subset_row_cut_max_depth", 0)),
        subset_row_cut_max_subset_size=int(base.get("subset_row_cut_max_subset_size", 8)),
        subset_row_cut_max_per_round=int(base.get("subset_row_cut_max_per_round", 20)),
        subset_row_cut_min_violation=float(base.get("subset_row_cut_min_violation", 1.0e-5)),
        subset_row_cut_max_rounds_per_node=int(base.get("subset_row_cut_max_rounds_per_node", 3)),
        subset_row_candidate_top_routes=int(base.get("subset_row_candidate_top_routes", 80)),
        subset_row_candidate_max_sets=int(base.get("subset_row_candidate_max_sets", 500)),
        subset_row_k_values=_int_tuple_config(base, "subset_row_k_values", (2, 3)),
        lm_rank1_cuts_enabled=_bool_config(base, "lm_rank1_cuts_enabled", True),
        lm_rank1_cut_max_depth=int(base.get("lm_rank1_cut_max_depth", 0)),
        lm_rank1_cut_max_subset_size=int(base.get("lm_rank1_cut_max_subset_size", 8)),
        lm_rank1_cut_max_per_round=int(base.get("lm_rank1_cut_max_per_round", 20)),
        lm_rank1_cut_min_violation=float(base.get("lm_rank1_cut_min_violation", 1.0e-5)),
        lm_rank1_cut_max_rounds_per_node=int(base.get("lm_rank1_cut_max_rounds_per_node", 3)),
        lm_rank1_candidate_top_routes=int(base.get("lm_rank1_candidate_top_routes", 100)),
        lm_rank1_candidate_max_sets=int(base.get("lm_rank1_candidate_max_sets", 700)),
        lm_rank1_denominators=_int_tuple_config(base, "lm_rank1_denominators", (3, 4)),
        lm_rank1_memory_size=int(base.get("lm_rank1_memory_size", 4)),
        lm_rank1_max_patterns_per_set=int(base.get("lm_rank1_max_patterns_per_set", 12)),
        schedule_subset_cost_cuts_enabled=_bool_config(base, "schedule_subset_cost_cuts_enabled", False),
        schedule_subset_cost_cut_max_depth=int(base.get("schedule_subset_cost_cut_max_depth", 0)),
        schedule_subset_cost_cut_max_subset_size=int(base.get("schedule_subset_cost_cut_max_subset_size", 8)),
        schedule_subset_cost_cut_max_per_round=int(base.get("schedule_subset_cost_cut_max_per_round", 10)),
        schedule_subset_cost_cut_min_violation=float(base.get("schedule_subset_cost_cut_min_violation", 1.0e-4)),
        schedule_subset_cost_cut_max_rounds_per_node=int(base.get("schedule_subset_cost_cut_max_rounds_per_node", 2)),
        schedule_subset_cost_oracle_max_states=int(base.get("schedule_subset_cost_oracle_max_states", 200000)),
        schedule_subset_cost_candidate_top_tasks=int(base.get("schedule_subset_cost_candidate_top_tasks", 12)),
        schedule_subset_cost_candidate_max_combinations=int(base.get("schedule_subset_cost_candidate_max_combinations", 200)),
        schedule_subset_cost_route_union_top_routes=int(base.get("schedule_subset_cost_route_union_top_routes", 10)),
        schedule_subset_cost_route_union_max_routes=int(base.get("schedule_subset_cost_route_union_max_routes", 4)),
        schedule_capacity_cuts_enabled=overrides["schedule_capacity_cuts_enabled"],
        schedule_capacity_separation_enabled=_bool_config(base, "schedule_capacity_separation_enabled", False),
        schedule_capacity_cut_max_depth=int(base.get("schedule_capacity_cut_max_depth", 0)),
        schedule_capacity_cut_max_subset_size=int(base.get("schedule_capacity_cut_max_subset_size", 10)),
        schedule_capacity_cut_max_per_round=int(base.get("schedule_capacity_cut_max_per_round", 20)),
        schedule_capacity_cut_min_violation=float(base.get("schedule_capacity_cut_min_violation", 1.0e-5)),
        schedule_capacity_cut_max_rounds_per_node=int(base.get("schedule_capacity_cut_max_rounds_per_node", 3)),
        schedule_capacity_oracle_max_states=int(base.get("schedule_capacity_oracle_max_states", 200000)),
        schedule_capacity_candidate_top_tasks=int(base.get("schedule_capacity_candidate_top_tasks", 12)),
        schedule_capacity_candidate_max_combinations=int(base.get("schedule_capacity_candidate_max_combinations", 300)),
        schedule_capacity_route_union_top_routes=int(base.get("schedule_capacity_route_union_top_routes", 8)),
        schedule_capacity_route_union_max_routes=int(base.get("schedule_capacity_route_union_max_routes", 4)),
        schedule_incompatibility_cuts_enabled=_bool_config(base, "schedule_incompatibility_cuts_enabled", True),
        schedule_incompatibility_cut_max_depth=int(base.get("schedule_incompatibility_cut_max_depth", 2)),
        schedule_incompatibility_cut_max_rounds_per_node=int(base.get("schedule_incompatibility_cut_max_rounds_per_node", 2)),
        schedule_incompatibility_cut_max_support_routes=int(base.get("schedule_incompatibility_cut_max_support_routes", 80)),
        schedule_incompatibility_cut_max_per_round=int(base.get("schedule_incompatibility_cut_max_per_round", 10)),
        schedule_incompatibility_cut_min_violation=float(base.get("schedule_incompatibility_cut_min_violation", 5.0e-2)),
        schedule_incompatibility_clique_min_size=int(base.get("schedule_incompatibility_clique_min_size", 3)),
        schedule_incompatibility_clique_seed_count=int(base.get("schedule_incompatibility_clique_seed_count", 24)),
        route_set_schedule_packing_cuts_enabled=_bool_config(base, "route_set_schedule_packing_cuts_enabled", True),
        route_set_schedule_packing_cut_max_depth=int(base.get("route_set_schedule_packing_cut_max_depth", 2)),
        route_set_schedule_packing_cut_max_rounds_per_node=int(base.get("route_set_schedule_packing_cut_max_rounds_per_node", 2)),
        route_set_schedule_packing_cut_max_support_routes=int(base.get("route_set_schedule_packing_cut_max_support_routes", 40)),
        route_set_schedule_packing_cut_max_routes=int(base.get("route_set_schedule_packing_cut_max_routes", 16)),
        route_set_schedule_packing_cut_max_per_round=int(base.get("route_set_schedule_packing_cut_max_per_round", 5)),
        route_set_schedule_packing_cut_min_violation=float(base.get("route_set_schedule_packing_cut_min_violation", 5.0e-2)),
        route_set_schedule_packing_oracle_max_states=int(base.get("route_set_schedule_packing_oracle_max_states", 200000)),
        fleet_lower_bound_cuts_enabled=_bool_config(base, "fleet_lower_bound_cuts_enabled", False),
        fleet_lower_bound_oracle_max_states=int(base.get("fleet_lower_bound_oracle_max_states", 500000)),
        schedule_pack_diagnostic_enabled=_bool_config(base, "schedule_pack_diagnostic_enabled", False),
        schedule_pack_diagnostic_max_candidate_routes=int(base.get("schedule_pack_diagnostic_max_candidate_routes", 180)),
        schedule_pack_diagnostic_max_columns=int(base.get("schedule_pack_diagnostic_max_columns", 8000)),
        schedule_pack_diagnostic_beam_width=int(base.get("schedule_pack_diagnostic_beam_width", 800)),
        schedule_pack_diagnostic_max_sorties=int(base.get("schedule_pack_diagnostic_max_sorties", 0)),
        schedule_pack_diagnostic_time_limit=float(base.get("schedule_pack_diagnostic_time_limit", 60.0)),
        schedule_pack_pricing_batch_size=int(base.get("schedule_pack_pricing_batch_size", 32)),
        schedule_pack_relaxation_enabled=_bool_config(base, "schedule_pack_relaxation_enabled", False),
        schedule_pack_relaxation_max_depth=int(base.get("schedule_pack_relaxation_max_depth", 2)),
        schedule_pack_relaxation_time_limit=float(base.get("schedule_pack_relaxation_time_limit", 30.0)),
        schedule_pack_relaxation_use_for_priority=_bool_config(base, "schedule_pack_relaxation_use_for_priority", True),
        schedule_pack_full_pricing_enabled=_bool_config(base, "schedule_pack_full_pricing_enabled", False),
        schedule_pack_full_pricing_max_depth=int(base.get("schedule_pack_full_pricing_max_depth", 0)),
        schedule_pack_full_pricing_max_states=int(base.get("schedule_pack_full_pricing_max_states", 0)),
        schedule_pack_adaptive_enabled=_bool_config(base, "schedule_pack_adaptive_enabled", False),
        schedule_pack_adaptive_gap_abs=float(base.get("schedule_pack_adaptive_gap_abs", 10.0)),
        schedule_pack_adaptive_gap_ratio=float(base.get("schedule_pack_adaptive_gap_ratio", 3.0e-2)),
        schedule_pack_adaptive_skip_if_fathomable=_bool_config(
            base,
            "schedule_pack_adaptive_skip_if_fathomable",
            True,
        ),
        route_enumeration_adaptive_enabled=_bool_config(base, "route_enumeration_adaptive_enabled", False),
        route_enumeration_adaptive_gap_abs=float(base.get("route_enumeration_adaptive_gap_abs", 10.0)),
        route_enumeration_adaptive_gap_ratio=float(base.get("route_enumeration_adaptive_gap_ratio", 3.0e-2)),
        cut_purge_age=int(base.get("cut_purge_age", 20)),
        cut_purge_slack=float(base.get("cut_purge_slack", 1.0e-5)),
        cut_purge_dual=float(base.get("cut_purge_dual", 1.0e-8)),
        schedule_nogood_purge_enabled=_bool_config(base, "schedule_nogood_purge_enabled", True),
        schedule_nogood_purge_age=int(base.get("schedule_nogood_purge_age", 8)),
        schedule_nogood_purge_slack=float(base.get("schedule_nogood_purge_slack", 1.0e-4)),
        schedule_nogood_purge_dual=float(base.get("schedule_nogood_purge_dual", 1.0e-8)),
    )


def main() -> None:
    args = parse_args()
    ablation = load_config(args.config)
    base_config_path = args.base_config or ablation.get("base_config", "configs/bpc_clean.yaml")
    base = load_config(base_config_path)
    run_id = args.run_id or datetime.now().strftime("%Y%m%d_%H%M%S_bpc_ablation")
    run_root = ROOT / "results" / "ablation" / run_id
    results_csv = ROOT / (args.results_csv or str(Path("results") / "ablation" / run_id / "summary.csv"))
    instances = args.instances or ablation.get("instances") or base.get("instances", ["medium"])
    variants = args.variants or ablation.get("variants") or list(VARIANTS)
    time_limit = float(args.time_limit if args.time_limit is not None else ablation.get("time_limit", base.get("time_limit", 3600)))
    max_nodes = int(args.max_nodes if args.max_nodes is not None else ablation.get("max_nodes", base.get("max_nodes", 100000)))

    fieldnames = [
        "run_id",
        "variant",
        "task_vehicle_linking_enabled",
        "schedule_capacity_cuts_enabled",
        *list(BPCResult.__dataclass_fields__.keys()),
    ]
    for instance in instances:
        data = load_bpc_data(str(instance), instance_dir=base.get("instance_dir", "json/instances"))
        for variant in variants:
            if variant not in VARIANTS:
                raise ValueError(f"未知 ablation variant: {variant}")
            result = _solve_one(
                data=data,
                base=base,
                variant=variant,
                overrides=VARIANTS[variant],
                run_root=run_root,
                time_limit=time_limit,
                max_nodes=max_nodes,
                quiet=bool(args.quiet),
            )
            row = {
                "run_id": run_id,
                "variant": variant,
                **VARIANTS[variant],
                **result.to_row(),
            }
            _append_row(results_csv, row, fieldnames)
            print(
                f"完成 variant={variant}: status={result.status}, primal={result.primal_bound}, "
                f"dual={result.dual_bound}, gap={result.gap}, nodes={result.node_count}, "
                f"branch_test_time={result.branch_testing_time}s",
                flush=True,
            )
    print(f"ablation CSV 已写入：{results_csv}", flush=True)


if __name__ == "__main__":
    main()
