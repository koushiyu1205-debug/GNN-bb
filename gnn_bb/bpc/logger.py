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
            "schedule_capacity_candidates",
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
            return (
                f"{prefix} node {record['node_id']} cg={record['cg_iter']} phase={record['phase']} "
                f"best_rc={record.get('best_reduced_cost')} found={record.get('negative_routes')} "
                f"added={record.get('added_routes')} exhausted={record.get('exhausted')}"
            )
        if event == "schedule_capacity_candidates":
            return f"{prefix} node {record['node_id']} schedule-cap candidates={record.get('by_vehicle')}"
        if event == "cut_added":
            cuts = record.get("cuts") or []
            head = cuts[0] if cuts else {}
            detail = ""
            if record.get("family") == "schedule_capacity" and head:
                detail = (
                    f" first(vehicle={head.get('vehicle')}, |S|={len(head.get('tasks', []))}, "
                    f"U={head.get('upper_bound')}, viol={head.get('activity_minus_rhs')})"
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
                f"crossing={record.get('crossing_cuts_added')} "
                f"crossing_upgraded={record.get('crossing_cuts_upgraded')} "
                f"nogood={record.get('schedule_nogood_cuts_added')} "
                f"sched_cap={record.get('schedule_capacity_cuts_added')}"
            )
        return f"{prefix} {event}: {record}"
