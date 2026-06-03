"""JSONL logger for BPC_future."""

from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any


class FutureLogger:
    def __init__(self, path: str | Path | None, *, console: bool = True) -> None:
        self.path = Path(path) if path else None
        self.console = bool(console)
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
        record = {"time": round(time.perf_counter() - self.started, 6), "event": event, **payload}
        if self.handle is not None:
            self.handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            self.handle.flush()
        if self.console and event in {
            "start",
            "node_start",
            "rmp",
            "pricing",
            "branch",
            "incumbent",
            "fathom",
            "journey_rmp",
            "journey_pricing",
            "journey_branch",
            "journey_fathom",
            "finish",
        }:
            print(self._format(record), flush=True)

    def _format(self, record: dict[str, Any]) -> str:
        prefix = f"[BPC_future {record['time']:8.2f}s]"
        event = record["event"]
        if event == "rmp":
            return f"{prefix} node {record['node_id']} cg={record['cg_iter']} obj={record.get('objective')} cols={record.get('columns')}"
        if event == "pricing":
            return (
                f"{prefix} node {record['node_id']} cg={record['cg_iter']} kind={record.get('pricing_kind')} "
                f"veh={record.get('vehicle')} best_rc={record.get('best_reduced_cost')} "
                f"neg={record.get('negative_trips')} exhausted={record.get('exhausted')}"
            )
        if event == "journey_rmp":
            return (
                f"{prefix} journey node {record.get('node_id', 0)} cg={record.get('cg_iter')} "
                f"obj={record.get('objective')} journeys={record.get('journeys')} "
                f"fleet_limit={record.get('fleet_limit')} status={record.get('status')}"
            )
        if event == "journey_pricing":
            return (
                f"{prefix} journey node {record.get('node_id', 0)} cg={record.get('cg_iter')} "
                f"kind={record.get('pricing_kind')} best_rc={record.get('best_reduced_cost')} "
                f"journeys={record.get('negative_journeys')} exhausted={record.get('exhausted')} "
                f"reason={record.get('reason')}"
            )
        if event == "node_start":
            return f"{prefix} node {record['node_id']} d={record.get('depth')} lb={record.get('lower_bound')} open={record.get('open_nodes')}"
        if event == "branch":
            return f"{prefix} branch node {record['node_id']}: {record.get('left')} | {record.get('right')}"
        if event == "journey_branch":
            return f"{prefix} journey branch node {record.get('node_id')}: {record.get('left')} | {record.get('right')}"
        if event == "journey_fathom":
            return f"{prefix} journey fathom node {record.get('node_id')}: {record.get('reason')}"
        if event == "finish":
            return f"{prefix} finish status={record.get('status')} primal={record.get('primal_bound')} dual={record.get('dual_bound')} gap={record.get('gap')}"
        return f"{prefix} {event}: {record}"
