"""中文摘要：本文件提供 clean BPC 的 JSONL 日志器。每条日志立即 flush，避免长运行时内存堆积。"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class BPCLogger:
    def __init__(self, path: str | Path | None, *, console: bool = True) -> None:
        self.path = Path(path) if path is not None else None
        self.console = console
        self.started = time.perf_counter()
        self.handle = None
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.handle = self.path.open("w", encoding="utf-8")

    def close(self) -> None:
        if self.handle is not None:
            self.handle.close()
            self.handle = None

    def log(self, event: str, **payload: Any) -> None:
        record = {
            "time": round(time.perf_counter() - self.started, 6),
            "event": event,
            **payload,
        }
        if self.handle is not None:
            self.handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            self.handle.flush()
        if self.console and event in {
            "start",
            "node_start",
            "rmp",
            "pricing",
            "restricted_integer_master",
            "schedule_capacity_candidates",
            "schedule_capacity_diagnostics",
            "root_schedule_capacity_diagnostics",
            "task_schedule_capacity_diagnostics",
            "subset_row_diagnostics",
            "lm_rank1_diagnostics",
            "schedule_subset_cost_diagnostics",
            "route_set_schedule_packing_diagnostics",
            "weighted_route_schedule_packing_diagnostics",
            "route_pack_roi_diagnostics",
            "schedule_route_set_packing_conflict_diagnostics",
            "schedule_pack_diagnostic",
            "schedule_pack_relaxation",
            "schedule_pack_adaptive",
            "route_enumeration_adaptive",
            "rim_conflict_diagnostics",
            "cut_purged",
            "cut_added",
            "cut_roi",
            "persistent_rmp_fallback",
            "branch",
            "fathom",
            "incumbent",
            "node_end",
            "timeout_diagnostics",
            "finish",
        }:
            print(self._format_console(record), flush=True)

    def _format_console(self, record: dict[str, Any]) -> str:
        event = record["event"]
        prefix = f"[clean-BPC {record['time']:8.2f}s]"
        if event == "node_start":
            return f"{prefix} node {record['node_id']} d={record['depth']} lb={record.get('node_lb')} open={record.get('open_nodes')}"
        if event == "rmp":
            backend = record.get("backend")
            backend_text = "" if backend is None else f" backend={backend}"
            return (
                f"{prefix} node {record['node_id']} cg={record['cg_iter']} phase={record['phase']} "
                f"obj={record.get('objective')} artificial={record.get('artificial_sum')} cols={record.get('route_count')}"
                f"{backend_text}"
            )
        if event == "pricing":
            kind = record.get("pricing_kind", "exact")
            extras: list[str] = []
            if record.get("ng_relaxation_enabled"):
                extras.append(f"ng={record.get('ng_memory_size')}")
            if record.get("dssr_pricing_enabled"):
                extras.append(
                    f"dssr={record.get('dssr_iterations')}/"
                    f"{record.get('dssr_memory_expansions')}"
                )
            if record.get("dssr_fallback"):
                extras.append("dssr_fallback=True")
            if record.get("completion_pruned"):
                extras.append(f"cb_pruned={record.get('completion_pruned')}")
            if record.get("enumerated_routes"):
                extras.append(f"enum={record.get('enumerated_routes')}")
            suffix = "" if not extras else " " + " ".join(extras)
            return (
                f"{prefix} node {record['node_id']} cg={record['cg_iter']} phase={record['phase']} kind={kind} "
                f"best_rc={record.get('best_reduced_cost')} found={record.get('negative_routes')} "
                f"added={record.get('added_routes')} exhausted={record.get('exhausted')} cert={record.get('certificate')}"
                f"{suffix}"
            )
        if event == "schedule_capacity_candidates":
            return f"{prefix} node {record['node_id']} schedule-cap candidates={record.get('by_vehicle')}"
        if event == "schedule_capacity_diagnostics":
            return (
                f"{prefix} schedule-cap diag node {record['node_id']} round={record.get('round')} "
                f"vehicles={record.get('vehicles_active')}/{record.get('vehicles_checked')} "
                f"cand={record.get('candidate_subsets')} oracle={record.get('oracle_queries')} "
                f"incomplete={record.get('skipped_oracle_incomplete')} "
                f"not_tight={record.get('skipped_not_tight')} not_viol={record.get('skipped_not_violated')} "
                f"dup={record.get('skipped_duplicate')} violated={record.get('violated_candidates')} "
                f"added={record.get('added')} max_viol={record.get('max_violation')} "
                f"states_max={record.get('oracle_states_max')}"
            )
        if event == "root_schedule_capacity_diagnostics":
            return (
                f"{prefix} root-schedule-cap diag node {record['node_id']} "
                f"cand={record.get('candidates_generated')}/{record.get('candidates_after_precheck')} "
                f"oracle={record.get('oracle_queries')} incomplete={record.get('oracle_incomplete')} "
                f"cache={record.get('cache_hits')} not_tight={record.get('not_tight')} "
                f"not_viol={record.get('tight_not_violated')} dup={record.get('duplicate')} "
                f"viol={record.get('violated')} added={record.get('cuts_added')} "
                f"best_viol={record.get('best_violation')} time={record.get('oracle_time')}"
            )
        if event == "task_schedule_capacity_diagnostics":
            stopped = record.get("stopped_by")
            stopped_text = "" if not stopped else f" stopped={stopped}"
            return (
                f"{prefix} task-schedule-cap diag node {record['node_id']} round={record.get('round')} "
                f"cand={record.get('candidates_generated')}/{record.get('candidates_after_precheck')} "
                f"pair={record.get('pair_candidates')} triple={record.get('triple_candidates')} "
                f"small={record.get('small_set_candidates')} oracle={record.get('oracle_computations')}/"
                f"{record.get('oracle_requests')} cache={record.get('cache_hits')} "
                f"incomplete={record.get('oracle_incomplete')} not_tight={record.get('exact_not_tight')} "
                f"not_viol={record.get('exact_tight_not_violated')} viol={record.get('violated_candidates')} "
                f"added={record.get('cuts_added', record.get('added'))} best_viol={record.get('best_violation')} "
                f"states_max={record.get('oracle_states_max')} time={record.get('oracle_time')}{stopped_text}"
            )
        if event == "subset_row_diagnostics":
            return (
                f"{prefix} subset-row diag node {record['node_id']} round={record.get('round')} "
                f"cand={record.get('candidate_subsets')} k={record.get('k_values')} "
                f"dup={record.get('skipped_duplicate')} not_viol={record.get('skipped_not_violated')} "
                f"violated={record.get('violated_candidates')} added={record.get('added')} "
                f"max_viol={record.get('max_violation')}"
            )
        if event == "lm_rank1_diagnostics":
            return (
                f"{prefix} lm-rank1 diag node {record['node_id']} round={record.get('round')} "
                f"cand={record.get('candidate_subsets')} denom={record.get('denominators')} "
                f"patterns={record.get('patterns')} dup={record.get('skipped_duplicate')} "
                f"not_viol={record.get('skipped_not_violated')} violated={record.get('violated_candidates')} "
                f"added={record.get('added')} max_viol={record.get('max_violation')}"
            )
        if event == "schedule_subset_cost_diagnostics":
            return (
                f"{prefix} sched-cost diag node {record['node_id']} round={record.get('round')} "
                f"vehicles={record.get('vehicles_active')}/{record.get('vehicles_checked')} "
                f"cand={record.get('candidate_subsets')} oracle={record.get('oracle_queries')} "
                f"incomplete={record.get('skipped_oracle_incomplete')} infeas={record.get('skipped_oracle_infeasible')} "
                f"not_viol={record.get('skipped_not_violated')} violated={record.get('violated_candidates')} "
                f"added={record.get('added')} max_viol={record.get('max_violation')} "
                f"states_max={record.get('oracle_states_max')}"
            )
        if event == "route_set_schedule_packing_diagnostics":
            disabled = record.get("disabled_by_roi_guard")
            disabled_text = "" if not disabled else f" disabled={disabled}"
            return (
                f"{prefix} route-pack diag node {record['node_id']} round={record.get('round')} "
                f"vehicles={record.get('vehicles_with_support')}/{record.get('vehicles_checked')} "
                f"support_max={record.get('support_routes_max')} cand={record.get('candidate_sets')} "
                f"oracle={record.get('oracle_queries')} incomplete={record.get('skipped_oracle_incomplete')} "
                f"not_tight={record.get('skipped_not_tight')} not_viol={record.get('skipped_not_violated')} "
                f"dup={record.get('skipped_duplicate')} violated={record.get('violated_candidates')} "
                f"added={record.get('added')} max_viol={record.get('max_violation')} "
                f"states_max={record.get('oracle_states_max')} cache={record.get('cache_hits')} "
                f"time={record.get('oracle_time')}{disabled_text}"
            )
        if event == "weighted_route_schedule_packing_diagnostics":
            stopped = record.get("stopped_by")
            stopped_text = "" if not stopped else f" stopped={stopped}"
            return (
                f"{prefix} weighted-route-pack diag node {record['node_id']} round={record.get('round')} "
                f"vehicles={record.get('vehicles_with_support')}/{record.get('vehicles_checked')} "
                f"cand={record.get('candidate_sets')}/{record.get('candidates_after_precheck')} "
                f"oracle={record.get('oracle_computations')}/{record.get('oracle_requests')} "
                f"cache={record.get('cache_hits')} incomplete={record.get('oracle_incomplete')} "
                f"not_viol={record.get('exact_not_violated')} dup={record.get('duplicate')} "
                f"violated={record.get('violated_candidates')} added={record.get('cuts_added', record.get('added'))} "
                f"best_viol={record.get('best_violation')} states_max={record.get('oracle_states_max')} "
                f"time={record.get('oracle_time')}{stopped_text}"
            )
        if event == "route_pack_roi_diagnostics":
            return (
                f"{prefix} route-pack-roi node {record.get('node_id')} family={record.get('family')} "
                f"stage={record.get('stage')} class={record.get('classification')} "
                f"core={record.get('cut_core_signature_count')} "
                f"same_pool={record.get('same_pool_replacement_count')} "
                f"pricing={record.get('pricing_replacement_count')} "
                f"old_overlap={record.get('max_task_overlap_old_pool')} "
                f"new_overlap={record.get('max_task_overlap_new_pricing')} "
                f"delta={record.get('objective_improvement')}"
            )
        if event == "schedule_route_set_packing_conflict_diagnostics":
            return (
                f"{prefix} route-pack-conflict diag node {record['node_id']} "
                f"source_vehicle={record.get('source_vehicle')} routes={record.get('route_count')} "
                f"U={record.get('upper_bound')} complete={record.get('oracle_complete')} "
                f"cache_hit={record.get('cache_hit')} states={record.get('oracle_states')} "
                f"added={record.get('added')}"
            )
        if event == "schedule_pack_diagnostic":
            return (
                f"{prefix} schedule-pack diag node {record['node_id']} status={record.get('status')} "
                f"obj={record.get('objective')} root={record.get('root_route_vehicle_bound')} "
                f"delta={record.get('gap_vs_root')} cols={record.get('columns')} "
                f"routes={record.get('candidate_routes')} states={record.get('generated_states')} "
                f"cg={record.get('pricing_iterations')} rc={record.get('best_reduced_cost')} "
                f"pool_exact={record.get('exact_over_candidate_routes')} "
                f"full_exact={record.get('exact_over_full_route_space')} "
                f"full_routes={record.get('full_pricing_route_count')} "
                f"full_states={record.get('full_pricing_generated_states')} "
                f"seeds={record.get('seed_columns')} "
                f"time={record.get('solving_time')} exact_bound={record.get('exact_bound')}"
            )
        if event == "schedule_pack_relaxation":
            return (
                f"{prefix} schedule-pack relax node {record['node_id']} d={record.get('depth')} "
                f"status={record.get('status')} obj={record.get('objective')} "
                f"node_lb={record.get('node_route_vehicle_bound')} delta={record.get('gap_vs_node')} "
                f"cols={record.get('columns')} routes={record.get('candidate_routes')} "
                f"cg={record.get('pricing_iterations')} rc={record.get('best_reduced_cost')} "
                f"pool_exact={record.get('exact_over_candidate_routes')} "
                f"full_exact={record.get('exact_over_full_route_space')} "
                f"full_routes={record.get('full_pricing_route_count')} "
                f"full_states={record.get('full_pricing_generated_states')} "
                f"time={record.get('solving_time')} priority={record.get('used_for_priority')} "
                f"exact_bound={record.get('exact_bound')} applied={record.get('exact_bound_applied')} "
                f"official_lb={record.get('official_node_bound')}"
            )
        if event == "schedule_pack_adaptive":
            return (
                f"{prefix} schedule-pack adaptive node {record['node_id']} d={record.get('depth')} "
                f"action={record.get('action')} reason={record.get('reason')} "
                f"gap={record.get('gap')} threshold={record.get('threshold')} "
                f"inc={record.get('incumbent')} lb={record.get('node_bound')} "
                f"diag={record.get('root_diagnostic')} relax={record.get('node_relaxation')}"
            )
        if event == "route_enumeration_adaptive":
            return (
                f"{prefix} route-enum adaptive node {record['node_id']} d={record.get('depth')} "
                f"action={record.get('action')} reason={record.get('reason')} "
                f"gap={record.get('gap')} threshold={record.get('threshold')} "
                f"inc={record.get('incumbent')} lb={record.get('node_bound')}"
            )
        if event == "rim_conflict_diagnostics":
            return (
                f"{prefix} rim-conflict diag node {record['node_id']} "
                f"conflicts={record.get('conflicts_checked')} pair_events={record.get('pair_conflict_events')} "
                f"pair_cuts={record.get('pair_cuts_added')} schedcap_events={record.get('schedule_capacity_events')} "
                f"schedcap_cuts={record.get('schedule_capacity_cuts_added')} "
                f"routepack_events={record.get('route_set_packing_events')} "
                f"routepack_cuts={record.get('route_set_packing_cuts_added')} "
                f"routepack_cache={record.get('route_set_packing_cache_hits')} "
                f"routepack_states_max={record.get('route_set_packing_oracle_states_max')} "
                f"routepack_budget_skip={record.get('route_set_packing_budget_skips')} "
                f"nogood_events={record.get('nogood_violated_conflicts')} "
                f"nogood_cuts={record.get('nogood_cuts_added')} "
                f"weak_skip={record.get('weak_nogood_not_violated')}"
            )
        if event == "cut_purged":
            return (
                f"{prefix} cut_purged node={record.get('node_id')} removed={record.get('removed')} "
                f"by_kind={record.get('removed_by_kind')} remaining={record.get('remaining')}"
            )
        if event == "restricted_integer_master":
            return (
                f"{prefix} restricted-MIP node {record['node_id']} status={record.get('status')} "
                f"obj={record.get('objective')} accepted={record.get('accepted')} "
                f"routes={record.get('route_pool')} rejected={record.get('rejected_solutions')} "
                f"pair={record.get('pair_conflict_cuts')} ng={record.get('no_good_cuts')} "
                f"route_pack={record.get('route_set_packing_cuts')} "
                f"sched_cap={record.get('schedule_capacity_cuts')} "
                f"added_cuts={record.get('added_schedule_cuts')} "
                f"time={record.get('time')}"
            )
        if event == "cut_added":
            cuts = record.get("cuts") or []
            head = cuts[0] if cuts else {}
            detail = ""
            if str(record.get("family", "")).startswith("schedule_capacity") and head:
                detail = (
                    f" first(vehicle={head.get('vehicle')}, |S|={len(head.get('tasks', []))}, "
                    f"U={head.get('upper_bound')}, viol={head.get('activity_minus_rhs')})"
                )
            elif str(record.get("family", "")) == "schedule_subset_cost_lb" and head:
                detail = (
                    f" first(vehicle={head.get('vehicle')}, |S|={len(head.get('tasks', []))}, "
                    f"L={head.get('lower_bound')}, viol={head.get('violation')}, states={head.get('oracle_states')})"
                )
            elif str(record.get("family", "")) == "subset_row" and head:
                detail = (
                    f" first(|S|={len(head.get('tasks', []))}, k={head.get('divisor')}, "
                    f"viol={head.get('activity_minus_rhs')})"
                )
            elif str(record.get("family", "")) == "limited_memory_rank1" and head:
                detail = (
                    f" first(|S|={len(head.get('tasks', []))}, d={head.get('denominator')}, "
                    f"mem={head.get('memory_tasks')}, viol={head.get('activity_minus_rhs')})"
                )
            elif str(record.get("family", "")) == "schedule_route_set_packing" and head:
                if record.get("source") == "schedule_conflict":
                    detail = (
                        f" source=schedule_conflict first(vehicle={head.get('vehicle')}, "
                        f"routes={head.get('route_count')}, U={head.get('upper_bound')}, "
                        f"states={head.get('oracle_states')}, cache_hit={head.get('cache_hit')})"
                    )
                else:
                    detail = (
                        f" first(vehicle={head.get('vehicle')}, routes={head.get('route_count')}, "
                        f"U={head.get('upper_bound')}, y={head.get('y')}, viol={head.get('activity_minus_rhs')}, "
                        f"states={head.get('oracle_states')})"
                    )
            elif str(record.get("family", "")) == "weighted_schedule_route_set_packing" and head:
                detail = (
                    f" first(vehicle={head.get('vehicle')}, routes={head.get('route_count')}, "
                    f"beta={head.get('upper_bound')}, alpha={head.get('alpha_pattern')}, "
                    f"viol={head.get('activity_minus_rhs')}, states={head.get('oracle_states')})"
                )
            elif str(record.get("family", "")) == "schedule_incompatibility" and head:
                detail = (
                    f" pair={record.get('pair_added')} clique={record.get('clique_added')} "
                    f"first(kind={head.get('kind')}, vehicle={head.get('vehicle')}, "
                    f"routes={head.get('route_count')}, U={head.get('upper_bound')}, "
                    f"y={head.get('y')}, viol={head.get('activity_minus_rhs')})"
                )
            elif str(record.get("family", "")).startswith("schedule_") and record.get("signatures"):
                detail = (
                    f" source_vehicle={record.get('source_vehicle')} "
                    f"route_count={record.get('route_count')} signatures={record.get('signatures')}"
                )
            elif head:
                detail = f" first={head}"
            upgraded = record.get("upgraded")
            upgrade_text = "" if upgraded is None else f" upgraded={upgraded}"
            return (
                f"{prefix} cut_added family={record.get('family')} node={record.get('node_id')} "
                f"added={record.get('added')}{upgrade_text}{detail}"
            )
        if event == "branch":
            return f"{prefix} branch node {record['node_id']}: left={record.get('left')} right={record.get('right')}"
        if event == "cut_roi":
            return (
                f"{prefix} cut-roi node {record['node_id']} family={record.get('family')} "
                f"added={record.get('added')} delta={record.get('objective_improvement')} "
                f"low={record.get('low_improvement')}"
            )
        if event == "persistent_rmp_fallback":
            return (
                f"{prefix} persistent-rmp fallback node {record.get('node_id')} phase={record.get('phase')} "
                f"reason={record.get('reason')}"
            )
        if event == "node_end":
            return (
                f"{prefix} node-end {record['node_id']} children={record.get('children')} "
                f"open={record.get('open_nodes')} lb={record.get('certified_lower_bound')} "
                f"inc={record.get('incumbent')}"
            )
        if event == "timeout_diagnostics":
            return (
                f"{prefix} timeout diag pending={record.get('pending_node_bound')} "
                f"certified={record.get('timeout_pending_node_certified')} "
                f"official={record.get('official_bound')} diagnostic={record.get('diagnostic_bound')}"
            )
        if event == "fathom":
            return f"{prefix} fathom node {record['node_id']}: reason={record.get('reason')} bound={record.get('bound')}"
        if event == "incumbent":
            return f"{prefix} incumbent node {record['node_id']}: obj={record.get('objective')}"
        if event == "finish":
            return (
                f"{prefix} finish status={record.get('status')} primal={record.get('primal_bound')} "
                f"dual={record.get('dual_bound')} gap={record.get('gap')} cuts={record.get('cuts')} "
                f"diag_dual={record.get('diagnostic_dual_bound')} diag_gap={record.get('diagnostic_gap')} "
                f"crossing={record.get('crossing_cuts_added')} "
                f"crossing_upgraded={record.get('crossing_cuts_upgraded')} "
                f"subset_row={record.get('subset_row_cuts_added')} "
                f"lm_rank1={record.get('lm_rank1_cuts_added')} "
                f"sched_cost={record.get('schedule_subset_cost_cuts_added')} "
                f"pair={record.get('schedule_pair_conflict_cuts_added')} "
                f"clique={record.get('schedule_clique_conflict_cuts_added')} "
                f"route_pack={record.get('schedule_route_set_packing_cuts_added')} "
                f"weighted_route_pack={record.get('weighted_route_schedule_packing_cuts_added')} "
                f"nogood={record.get('schedule_nogood_cuts_added')} "
                f"sched_cap={record.get('schedule_capacity_cuts_added')} "
                f"sched_pack_adapt={record.get('schedule_pack_adaptive_runs')}/"
                f"{record.get('schedule_pack_adaptive_decisions')} "
                f"route_enum_adapt={record.get('route_enumeration_adaptive_runs')}/"
                f"{record.get('route_enumeration_adaptive_decisions')}"
            )
        return f"{prefix} {event}: {record}"
