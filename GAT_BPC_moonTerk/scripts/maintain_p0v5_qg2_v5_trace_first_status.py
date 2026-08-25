#!/usr/bin/env python3
"""Maintain the compact live Markdown status for the V5 trace-first run."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import math
import os
from pathlib import Path
import time


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs/p0v5_qg2_v5_trace_first_20260807"
STATUS = RUN / "STATUS_ZH.md"
STATE = RUN / "PIPELINE_STATE.json"
PROGRESS = RUN / "trace_corpus/progress.json"
FORCE_PROGRESS = RUN / "label_gat_force_on_train_screen/progress.json"
FORCE_OUTPUT = RUN / "label_gat_force_on_train_screen/force_on_train.json"
FORCE_RECORDS = RUN / "label_gat_force_on_train_screen/force_on_records.jsonl"
BEGIN = "<!-- AUTO_PROGRESS_BEGIN -->"
END = "<!-- AUTO_PROGRESS_END -->"
FORCE_BEGIN = "<!-- AUTO_FORCE_RESULTS_BEGIN -->"
FORCE_END = "<!-- AUTO_FORCE_RESULTS_END -->"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pipeline-pid", type=int, required=True)
    parser.add_argument("--poll-sec", type=float, default=30.0)
    args = parser.parse_args()
    while True:
        running = _alive(int(args.pipeline_pid))
        _update(running=running, pipeline_pid=int(args.pipeline_pid))
        if not running:
            return 0
        time.sleep(max(5.0, float(args.poll_sec)))


def _update(*, running: bool, pipeline_pid: int) -> None:
    text = STATUS.read_text(encoding="utf-8")
    before, marker, tail = text.partition(BEGIN)
    if not marker:
        raise SystemExit("trace-first status lacks auto-progress marker")
    _old, marker, after = tail.partition(END)
    if not marker:
        raise SystemExit("trace-first status lacks auto-progress end marker")
    state = _load_optional(STATE)
    progress = _load_optional(PROGRESS)
    force_progress = _load_optional(FORCE_PROGRESS)
    force_complete = FORCE_OUTPUT.is_file()
    if force_complete:
        status = "LABEL_GAT_FORCE_ON_SCREEN_COMPLETE"
    elif running and force_progress:
        status = "RUNNING_LABEL_GAT_FORCE_ON_AFTER_BINDING_REPAIR"
    else:
        status = str((state or {}).get("status") or (
            "RUNNING_Q0_TRACE_COLLECTION" if running else "STOPPED_BEFORE_STATE"
        ))
    completed = int((progress or {}).get("completed_contexts") or 0)
    selected = int((progress or {}).get("selected_contexts") or 53)
    by_scale = dict((progress or {}).get("completed_by_scale") or {})
    force_completed = int((force_progress or {}).get("completed_contexts") or 0)
    force_selected = int((force_progress or {}).get("selected_contexts") or 10)
    force_by_scale = dict((force_progress or {}).get("completed_by_scale") or {})
    block = "\n".join((
        BEGIN,
        f"`{status}`",
        "",
        f"- 更新时间：`{datetime.now().astimezone().isoformat(timespec='seconds')}`；",
        f"- pipeline：{'RUNNING' if running else 'STOPPED'}，PID `{pipeline_pid}`；",
        f"- Q0 trace：`{completed}/{selected}`；scale30 `{int(by_scale.get('30') or 0)}/33`，scale50 `{int(by_scale.get('50') or 0)}/20`；",
        f"- Label GAT smoke：{'完成' if bool((state or {}).get('label_gat_smoke_ready')) else '未完成'}；",
        f"- Label GAT formal：{'完成' if bool((state or {}).get('label_gat_ready')) else '未完成'}；",
        f"- Q0/QG2 force-on screen：`{force_completed}/{force_selected}`；scale30 `{int(force_by_scale.get('30') or 0)}/5`，scale50 `{int(force_by_scale.get('50') or 0)}/5`；",
        "- Context GAT：等待 Label GAT force-on；",
        "- MLP/Linear：未启动，且不会抢在 GAT fresh 之前运行；",
        "- production/P0V4/P0V5 Exact control：未改动。",
        END,
    ))
    temporary = STATUS.with_suffix(".md.tmp")
    updated = before + block + after
    if FORCE_BEGIN in updated and FORCE_END in updated:
        force_before, _marker, force_tail = updated.partition(FORCE_BEGIN)
        _old_force, _marker, force_after = force_tail.partition(FORCE_END)
        updated = (
            force_before + _force_results_block() + force_after
        )
    temporary.write_text(updated, encoding="utf-8")
    os.replace(temporary, STATUS)


def _force_results_block() -> str:
    rows = []
    if FORCE_RECORDS.is_file():
        for raw in FORCE_RECORDS.read_text(encoding="utf-8").splitlines():
            if raw.strip():
                rows.append(json.loads(raw))
    lines = [FORCE_BEGIN]
    if not rows:
        lines.extend(("尚无完整 matched context。", FORCE_END))
        return "\n".join(lines)
    lines.extend((
        "| scale | state | Q0 median (s) | TinyGAT median (s) | ratio | labels ratio | result |",
        "|---:|---|---:|---:|---:|---:|---|",
    ))
    for row in rows:
        label_ratio = _median_label_ratio(row)
        ratio = float(row.get("ratio") or math.nan)
        result = "beneficial" if ratio < 1.0 else "harmful"
        lines.append(
            f"| {int(row.get('scale') or 0)} | `{str(row.get('state_hash') or '')[:16]}` "
            f"| {float(row.get('q0_median_wall_sec') or 0.0):.3f} "
            f"| {float(row.get('gat_net_median_wall_sec') or 0.0):.3f} "
            f"| {ratio:.3f} | {label_ratio} | {result} |"
        )
    for scale in (30, 50):
        selected = [
            row for row in rows
            if int(row.get("scale") or 0) == scale
            and float(row.get("ratio") or 0.0) > 0.0
        ]
        if selected:
            gm = math.exp(sum(
                math.log(float(row["ratio"])) for row in selected
            ) / len(selected))
            lines.append(
                f"\nscale{scale} 当前 paired GM：`{gm:.4f}`；"
                f"beneficial `{sum(float(row['ratio']) < 1.0 for row in selected)}/{len(selected)}`。"
            )
    lines.append(FORCE_END)
    return "\n".join(lines)


def _median_label_ratio(row: dict) -> str:
    ratios = []
    for repeat in row.get("repeat_rows") or ():
        q0_path = Path(str(repeat.get("q0_path") or ""))
        gat_path = Path(str(repeat.get("gat_path") or ""))
        if not q0_path.is_file() or not gat_path.is_file():
            continue
        q0 = _load_optional(q0_path) or {}
        gat = _load_optional(gat_path) or {}
        q0_labels = int(dict(q0.get("proof_telemetry") or {}).get(
            "processed_labels") or 0)
        gat_labels = int(dict(gat.get("proof_telemetry") or {}).get(
            "processed_labels") or 0)
        if q0_labels > 0:
            ratios.append(gat_labels / q0_labels)
    if not ratios:
        return "n/a"
    ratios.sort()
    return f"{ratios[len(ratios) // 2]:.3f}"


def _alive(pid: int) -> bool:
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError):
        return False


def _load_optional(path: Path):
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
