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
        if event == "branch":
            return f"{prefix} branch node {record['node_id']}: left={record.get('left')} right={record.get('right')}"
        if event == "fathom":
            return f"{prefix} fathom node {record['node_id']}: reason={record.get('reason')} bound={record.get('bound')}"
        if event == "incumbent":
            return f"{prefix} incumbent node {record['node_id']}: obj={record.get('objective')}"
        if event == "finish":
            return (
                f"{prefix} finish status={record.get('status')} primal={record.get('primal_bound')} "
                f"dual={record.get('dual_bound')} gap={record.get('gap')}"
            )
        return f"{prefix} {event}: {record}"
