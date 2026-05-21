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
            "route_set_schedule_packing_diagnostics",
            "rim_conflict_diagnostics",
            "cut_purged",
            "cut_added",
            "branch",
            "fathom",
            "incumbent",
            "finish",
        }:
            print(self._format_console(record), flush=True)

    def _format_console(self, record: dict[str, Any]) -> str:
        event = record["event"]
        prefix = f"[clean-BPC {record['time']:8.2f}s]"
        if event == "node_start":
            return f"{prefix} node {record['node_id']} d={record['depth']} lb={record.get('node_lb')} open={record.get('open_nodes')}"
        if event == "rmp":
            return (
                f"{prefix} node {record['node_id']} cg={record['cg_iter']} phase={record['phase']} "
                f"obj={record.get('objective')} artificial={record.get('artificial_sum')} cols={record.get('route_count')}"
            )
        if event == "pricing":
            kind = record.get("pricing_kind", "exact")
            return (
                f"{prefix} node {record['node_id']} cg={record['cg_iter']} phase={record['phase']} kind={kind} "
                f"best_rc={record.get('best_reduced_cost')} found={record.get('negative_routes')} "
                f"added={record.get('added_routes')} exhausted={record.get('exhausted')} cert={record.get('certificate')}"
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
        if event == "route_set_schedule_packing_diagnostics":
            return (
                f"{prefix} route-pack diag node {record['node_id']} round={record.get('round')} "
                f"vehicles={record.get('vehicles_with_support')}/{record.get('vehicles_checked')} "
                f"support_max={record.get('support_routes_max')} cand={record.get('candidate_sets')} "
                f"oracle={record.get('oracle_queries')} incomplete={record.get('skipped_oracle_incomplete')} "
                f"not_tight={record.get('skipped_not_tight')} not_viol={record.get('skipped_not_violated')} "
                f"dup={record.get('skipped_duplicate')} violated={record.get('violated_candidates')} "
                f"added={record.get('added')} max_viol={record.get('max_violation')} "
                f"states_max={record.get('oracle_states_max')}"
            )
        if event == "rim_conflict_diagnostics":
            return (
                f"{prefix} rim-conflict diag node {record['node_id']} "
                f"conflicts={record.get('conflicts_checked')} pair_events={record.get('pair_conflict_events')} "
                f"pair_cuts={record.get('pair_cuts_added')} schedcap_events={record.get('schedule_capacity_events')} "
                f"schedcap_cuts={record.get('schedule_capacity_cuts_added')} "
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
            elif str(record.get("family", "")) == "schedule_route_set_packing" and head:
                detail = (
                    f" first(vehicle={head.get('vehicle')}, routes={head.get('route_count')}, "
                    f"U={head.get('upper_bound')}, y={head.get('y')}, viol={head.get('activity_minus_rhs')}, "
                    f"states={head.get('oracle_states')})"
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
                f"pair={record.get('schedule_pair_conflict_cuts_added')} "
                f"clique={record.get('schedule_clique_conflict_cuts_added')} "
                f"route_pack={record.get('schedule_route_set_packing_cuts_added')} "
                f"nogood={record.get('schedule_nogood_cuts_added')} "
                f"sched_cap={record.get('schedule_capacity_cuts_added')}"
            )
        return f"{prefix} {event}: {record}"
