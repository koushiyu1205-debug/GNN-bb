"""中文摘要：写 vehicle-schedule BPC 的 JSONL 日志和简明终端进度。"""

from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any


class BPCLogger:
    def __init__(self, path: str | Path | None, *, console: bool = True) -> None:
        self.start = time.perf_counter()
        self.console = bool(console)
        self.handle = None
        if path is not None:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            self.handle = p.open("w", encoding="utf-8")

    def close(self) -> None:
        if self.handle is not None:
            self.handle.close()
            self.handle = None

    def log(self, event: str, **payload: Any) -> None:
        record = {"time": round(time.perf_counter() - self.start, 6), "event": event, **payload}
        if self.handle is not None:
            self.handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            self.handle.flush()
        if self.console:
            print(self._format(record), flush=True)

    def _format(self, record: dict[str, Any]) -> str:
        prefix = f"[vehicle-BPC {record['time']:8.2f}s]"
        event = record["event"]
        if event == "start":
            return f"{prefix} start instance={record.get('instance')} tasks={record.get('tasks')} init_cols={record.get('initial_columns')}"
        if event == "node":
            return f"{prefix} node={record.get('node')} d={record.get('depth')} lb={record.get('lower_bound')} open={record.get('open_nodes')}"
        if event == "rmp":
            return (
                f"{prefix} node={record.get('node')} phase={record.get('phase')} cg={record.get('cg_iter')} "
                f"obj={record.get('objective')} artificial={record.get('artificial')} cols={record.get('columns')}"
            )
        if event == "pricing":
            return (
                f"{prefix} node={record.get('node')} phase={record.get('phase')} cg={record.get('cg_iter')} "
                f"best_rc={record.get('best_rc')} found={record.get('found')} added={record.get('added')} "
                f"exhausted={record.get('exhausted')} labels={record.get('labels')} "
                f"queue_peak={record.get('queue_peak')} reason={record.get('stop_reason')}"
            )
        if event == "branch":
            return f"{prefix} branch node={record.get('node')} pair=({record.get('i')},{record.get('j')}) value={record.get('value')}"
        if event == "incumbent":
            return f"{prefix} incumbent node={record.get('node')} obj={record.get('objective')}"
        if event == "fathom":
            return f"{prefix} fathom node={record.get('node')} reason={record.get('reason')}"
        if event == "finish":
            return (
                f"{prefix} finish status={record.get('status')} primal={record.get('primal')} "
                f"dual={record.get('dual')} gap={record.get('gap')} nodes={record.get('nodes')}"
            )
        return f"{prefix} {event}: {record}"
