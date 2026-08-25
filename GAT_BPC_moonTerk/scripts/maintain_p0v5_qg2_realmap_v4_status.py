#!/usr/bin/env python3
"""Atomically maintain the small auto-progress block in the V4 status page.

This process is observability-only: it counts completed development instances
and reads controller state JSON files.  It never starts, stops, or mutates a
solver, training job, replay, checkpoint, or audit artifact.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
import json
import math
import os
from pathlib import Path
import time


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs/p0v5_qg2_v4_realmap_gat_first_20260806"
STATUS = RUN / "STATUS_ZH.md"
DEVELOPMENT = ROOT / "data/p0v5_qg2_realmap_development_v4"
SNAPSHOTS = RUN / "fallback_snapshots_realmap_v4"
SPLIT = RUN / "realmap_v4_instance_split.json"
BEGIN = "<!-- AUTO_PROGRESS_BEGIN -->"
END = "<!-- AUTO_PROGRESS_END -->"
PREFLIGHT_CONTEXT_REQUIREMENTS = {
    "train": 10, "calibration": 4, "heldout": 4,
}
PREFLIGHT_INSTANCE_REQUIREMENTS = {
    "train": 6, "calibration": 2, "heldout": 2,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generation-pid", type=int, default=0)
    parser.add_argument("--watch-pid", type=int, default=0)
    parser.add_argument("--successor-pid", type=int, default=0)
    parser.add_argument("--handoff-pid", type=int, default=0)
    parser.add_argument("--poll-sec", type=float, default=30.0)
    args = parser.parse_args()
    poll = min(60.0, max(5.0, float(args.poll_sec)))
    while True:
        _update(args)
        if not any(
            _alive(pid) for pid in (
                args.generation_pid, args.watch_pid, args.successor_pid,
                args.handoff_pid,
            )
        ):
            return 0
        time.sleep(poll)


def _update(args) -> None:
    counts = {
        30: _count(DEVELOPMENT / "lunar_ice_sp50_030"),
        50: _count(DEVELOPMENT / "lunar_ice_sp50_050"),
    }
    watch = _read_state(RUN / "realmap_v4_watch_controller_state.json")
    successor = _read_state(RUN / "realmap_v4_tree_successor_state.json")
    supplement = _read_state(RUN / "realmap_v4_tree_supplement_state.json")
    collection = _read_state(RUN / "realmap_v4_collection_state.json")
    gat = _read_state(RUN / "realmap_v4_gat_first_state.json")
    handoff = _read_state(RUN / "instance_balanced_handoff_state.json")
    collection_progress = {
        scale: _collection_progress(scale) for scale in (30, 50)
    }
    rows = _pipeline_rows(counts, collection_progress)
    block = "\n".join((
        BEGIN,
        "## 自动进度（只读维护）",
        "",
        f"- 更新时间：`{datetime.now().astimezone().isoformat(timespec='seconds')}`；",
        f"- real-map development corpus：scale30 `{counts[30]}/20`，scale50 `{counts[50]}/20`；",
        f"- 生成进程：`{'RUNNING' if _alive(args.generation_pid) else 'STOPPED'}`；",
        f"- watcher 历史记录：`{watch}`；",
        f"- tree-supplement successor 历史记录：`{successor}`；",
        f"- tree supplement：`{supplement}`；",
        f"- snapshot collection：`{collection}`；",
        "- collection progress："
        + "；".join(
            _collection_progress_text(scale, collection_progress[scale])
            for scale in (30, 50)
        )
        + "；",
        f"- GAT-first pipeline：`{gat}`。",
        f"- GAT-first controller 进程：`{_process_state(args.successor_pid)}`；",
        f"- instance-balanced handoff：`{handoff}`；进程 "
        f"`{_process_state(args.handoff_pid)}`；",
        "- 阶段判定以 GAT-first pipeline 与下表为准；上游历史记录"
        "不代表当前 Oracle/训练失败。",
        "",
        "| 阶段 | 当前证据 |",
        "|---|---|",
        *(f"| {name} | {value} |" for name, value in rows),
        END,
    ))
    text = STATUS.read_text(encoding="utf-8") if STATUS.is_file() else ""
    if BEGIN in text and END in text:
        prefix, remainder = text.split(BEGIN, 1)
        _old, suffix = remainder.split(END, 1)
        updated = prefix.rstrip() + "\n\n" + block + suffix
    else:
        updated = text.rstrip() + "\n\n" + block + "\n"
    temporary = STATUS.with_suffix(".md.tmp")
    temporary.write_text(updated, encoding="utf-8")
    os.replace(temporary, STATUS)


def _count(directory: Path) -> int:
    return sum(1 for _ in directory.glob("instance_*_logical_graph.json"))


def _read_state(path: Path) -> str:
    if not path.is_file():
        return "NOT_STARTED"
    try:
        return str(json.loads(path.read_text(encoding="utf-8")).get("status") or "UNKNOWN")
    except (OSError, ValueError, TypeError):
        return "UNREADABLE_FAIL_CLOSED"


def _pipeline_rows(
    counts: dict[int, int], collection_progress: dict[int, dict]
) -> list[tuple[str, str]]:
    result = [
        ("Real-map corpus", f"scale30 {counts[30]}/20；scale50 {counts[50]}/20"),
        (
            "Snapshot collection",
            "；".join(
                _collection_progress_text(scale, collection_progress[scale])
                for scale in (30, 50)
            ),
        ),
    ]
    oracle = _json(RUN / "oracle_realmap_v4.json")
    if oracle:
        result.append((
            "Bounded Oracle",
            "contexts " + str(len(oracle.get("context_rows") or ()))
            + "；training_permitted " + str(bool(oracle.get("training_permitted"))),
        ))
    else:
        result.append(("Bounded Oracle", _oracle_progress()))
        result.append((
            "Initial-arm provisional GM",
            _oracle_initial_arm_summary(),
        ))
        result.append((
            "Q0 milestone/headroom",
            _oracle_q0_mechanism_summary(),
        ))
    result.append(("Training provenance", _training_provenance_summary()))
    result.append(("Fitting gate freeze", _fitting_gate_freeze_summary()))
    for label, path in (
        ("Label GAT", RUN / "ranker_gat_v4/training_curve.jsonl"),
        ("Context GAT", RUN / "selector_gat_v4/training_curve.jsonl"),
        ("Label MLP/Linear", RUN / "ranker_controls_v4/training_curve.jsonl"),
        ("Context MLP", RUN / "selector_mlp_control_v4/training_curve.jsonl"),
        ("Context Linear", RUN / "selector_linear_control_v4/training_curve.jsonl"),
    ):
        result.append((label, _curve(path)))
    for label, path in (
        ("GAT calibration fresh", RUN / "selector_gat_fresh_calibration_v4/fresh_records.jsonl"),
        ("GAT heldout fresh", RUN / "selector_gat_fresh_heldout_v4/fresh_records.jsonl"),
    ):
        result.append((label, _jsonl_count(path)))
    comparison = _json(RUN / "gat_mlp_linear_comparison_v4.json")
    result.append((
        "GAT/MLP/Linear comparison",
        "尚未生成" if not comparison else (
            "graph_advantage_supported "
            + str(bool(comparison.get("graph_advantage_supported")))
            + "；GAT/best-control "
            + _number(comparison.get("gat_to_best_control_net_ratio"))
        ),
    ))
    for label, path in (
        ("Development E2E", RUN / "development_e2e_v4_acceptance.json"),
        ("Formal full20", RUN / "formal_full20_v4_acceptance.json"),
    ):
        payload = _json(path)
        result.append((label, _acceptance(payload)))
    instance_audit = _json(
        RUN / "realmap_v4_instance_balanced_completion_audit.json"
    )
    result.append((
        "Instance-balanced completion audit",
        "尚未开始" if not instance_audit else (
            "passed " + str(bool(instance_audit.get("passed")))
            + "；errors " + str(int(instance_audit.get("error_count") or 0))
        ),
    ))
    final = _json(
        RUN
        / "P0V5_QG2_LABEL_STATE_GAT_V4_INSTANCE_BALANCED_FINAL_candidate_freeze.json"
    )
    result.append((
        "Independent final candidate",
        "尚未冻结" if not final else str(final.get("candidate_id") or "UNKNOWN"),
    ))
    return result


def _collection_progress(scale: int) -> dict:
    rows_path = (
        RUN / f"snapshot_collection_realmap_v4_scale{scale}"
        / f"scale_{scale:03d}" / "b4_2_cold_exact_rows.csv"
    )
    pilot_rows = _csv_rows(rows_path)
    completed_instances = len(pilot_rows)
    tree_rows_path = (
        RUN / f"snapshot_collection_realmap_v4_tree_scale{scale}"
        / f"scale_{scale:03d}" / "b4_2_cold_exact_rows.csv"
    )
    tree_rows = _csv_rows(tree_rows_path)
    tree_completed_instances = len(tree_rows)
    split = _json(SPLIT)
    assignments = dict(split.get("assignments") or {})
    snapshot_root = SNAPSHOTS / f"scale{scale}"
    snapshot_paths = tuple(snapshot_root.glob("*/*.json"))
    instance_hashes = {path.parent.name for path in snapshot_paths}
    partition_contexts = {
        name: sum(
            assignments.get(path.parent.name) == name for path in snapshot_paths
        )
        for name in ("train", "calibration", "heldout")
    }
    partition_instances = {
        name: sum(
            assignments.get(instance_hash) == name
            for instance_hash in instance_hashes
        )
        for name in ("train", "calibration", "heldout")
    }
    context_deficits = {
        name: max(0, required - partition_contexts[name])
        for name, required in PREFLIGHT_CONTEXT_REQUIREMENTS.items()
    }
    instance_deficits = {
        name: max(0, required - partition_instances[name])
        for name, required in PREFLIGHT_INSTANCE_REQUIREMENTS.items()
    }
    return {
        "completed_instances": completed_instances,
        "tree_completed_instances": tree_completed_instances,
        "pilot_root_certified_count": sum(
            _truth(row.get("route_opportunity_collection_root_pool_certified"))
            for row in pilot_rows
        ),
        "pilot_cap_reached_count": sum(
            _truth(row.get(
                "route_opportunity_collection_root_pool_time_cap_reached"
            ))
            for row in pilot_rows
        ),
        "pilot_redline_count": sum(_row_has_redline(row) for row in pilot_rows),
        "tree_exact_count": sum(
            str(row.get("algorithm_status") or "") == "BPC_OPTIMAL"
            for row in tree_rows
        ),
        "tree_redline_count": sum(_row_has_redline(row) for row in tree_rows),
        "context_count": len(snapshot_paths),
        "instance_count": len(instance_hashes),
        "partition_contexts": partition_contexts,
        "partition_instances": partition_instances,
        "overall_context_deficit": max(0, 20 - len(snapshot_paths)),
        "overall_instance_deficit": max(0, 10 - len(instance_hashes)),
        "partition_context_deficits": context_deficits,
        "partition_instance_deficits": instance_deficits,
    }


def _collection_progress_text(scale: int, progress: dict) -> str:
    contexts = progress["partition_contexts"]
    instances = progress["partition_instances"]
    context_deficits = progress["partition_context_deficits"]
    instance_deficits = progress["partition_instance_deficits"]
    return (
        f"s{scale} instances {progress['completed_instances']}/20，"
        f"tree {progress['tree_completed_instances']}/20，"
        f"root-certified/cap/redline "
        f"{progress['pilot_root_certified_count']}/"
        f"{progress['pilot_cap_reached_count']}/"
        f"{progress['pilot_redline_count']}，"
        f"tree-exact/redline {progress['tree_exact_count']}/"
        f"{progress['tree_redline_count']}，"
        f"snapshots {progress['context_count']}@{progress['instance_count']} instances，"
        f"T/C/H {contexts['train']}/{contexts['calibration']}/{contexts['heldout']} contexts "
        f"@ {instances['train']}/{instances['calibration']}/{instances['heldout']} instances，"
        f"preflight deficit total ctx/inst "
        f"{progress['overall_context_deficit']}/{progress['overall_instance_deficit']}，"
        f"T/C/H ctx {context_deficits['train']}/"
        f"{context_deficits['calibration']}/{context_deficits['heldout']}，"
        f"inst {instance_deficits['train']}/"
        f"{instance_deficits['calibration']}/{instance_deficits['heldout']}"
    )


def _csv_rows(path: Path) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
    except OSError:
        return []


def _truth(value) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _row_has_redline(row: dict[str, str]) -> bool:
    numeric_fields = (
        "certificate_leak",
        "manual_rc_fail",
        "pricing_rc_fail",
        "root_pool_large_task_direct_worker_certificate_leak_count",
        "root_pool_support_continuation_certificate_leak_count",
        "root_pool_tail_dual_certificate_leak_count",
        "root_pool_true_dual_rc_recompute_missing_count",
        "root_pool_worker_certificate_leak_count",
        "tail_dual_certificate_leak",
        "true_dual_rc_recompute_missing",
        "worker_certificate_leak",
    )
    try:
        numeric_redline = any(
            int(float(row.get(name) or 0)) != 0 for name in numeric_fields
        )
    except (TypeError, ValueError):
        return True
    return bool(numeric_redline or not _truth(row.get("no_cheat_pass")))


def _curve(path: Path) -> str:
    if not path.is_file():
        return "尚未训练"
    try:
        rows = [
            json.loads(line) for line in path.read_text(
                encoding="utf-8"
            ).splitlines() if line.strip()
        ]
    except (OSError, ValueError, TypeError):
        return "曲线暂不可读"
    if not rows:
        return "已创建，等待 epoch 1"
    row = rows[-1]
    text = (
        f"model {row.get('model')}；epoch {row.get('epoch')}；"
        f"loss total/rank/benefit/positive-gain/adverse "
        f"{_number(row.get('total_loss'))}/"
        f"{_number(row.get('rank_loss'))}/"
        f"{_number(row.get('benefit_loss'))}/"
        f"{_number(row.get('positive_gain_loss'))}/"
        f"{_number(row.get('adverse_loss'))}；"
        f"epoch wall {_number(row.get('epoch_wall_sec'))}s；"
        f"best {bool(row.get('is_best_epoch'))}"
    )
    if row.get("calibration_mean_instance_pair_accuracy") is not None:
        text += (
            "；calibration pair accuracy instance/raw-context "
            f"{_number(row.get('calibration_mean_instance_pair_accuracy'))}/"
            f"{_number(row.get('calibration_raw_mean_context_pair_accuracy'))}"
        )
    elif row.get("calibration_instance_balanced_total_loss") is not None:
        text += (
            "；calibration loss instance/raw-context "
            f"{_number(row.get('calibration_instance_balanced_total_loss'))}/"
            f"{_number(row.get('calibration_raw_context_total_loss'))}"
        )
    report = _json(path.parent / "training_report.json")
    model_name = str(row.get("model") or "").removesuffix("_arm_selector")
    model_rows = [
        dict(value) for value in report.get("models") or ()
        if str(value.get("model_kind") or "") == model_name
    ]
    if len(model_rows) == 1:
        metrics = dict(model_rows[0].get("partition_metrics") or {})
        instance_accuracies = [
            dict(metrics.get(partition) or {}).get(
                "mean_instance_pair_accuracy"
            )
            for partition in ("train", "calibration", "heldout")
        ]
        raw_accuracies = [
            dict(metrics.get(partition) or {}).get(
                "raw_mean_context_pair_accuracy"
            )
            for partition in ("train", "calibration", "heldout")
        ]
        legacy_accuracies = [
            dict(metrics.get(partition) or {}).get(
                "mean_context_pair_accuracy"
            )
            for partition in ("train", "calibration", "heldout")
        ]
        if all(value is not None for value in instance_accuracies):
            text += (
                "；pair accuracy instance T/C/H "
                + "/".join(_number(value) for value in instance_accuracies)
            )
            if all(value is not None for value in raw_accuracies):
                text += (
                    "；raw-context T/C/H "
                    + "/".join(_number(value) for value in raw_accuracies)
                )
        elif all(value is not None for value in legacy_accuracies):
            text += (
                "；pair accuracy T/C/H "
                + "/".join(_number(value) for value in legacy_accuracies)
            )
        text += f"；parameters {int(model_rows[0].get('parameter_count') or 0)}"
    elif str(report.get("trained_model") or "") == model_name:
        metrics = dict(report.get("arm_rank_metrics") or {})
        instance_accuracies = [
            dict(metrics.get(partition) or {}).get(
                "mean_instance_pair_accuracy"
            )
            for partition in ("train", "calibration", "heldout")
        ]
        raw_accuracies = [
            dict(metrics.get(partition) or {}).get(
                "mean_context_pair_accuracy"
            )
            for partition in ("train", "calibration", "heldout")
        ]
        if all(value is not None for value in instance_accuracies):
            text += (
                "；arm-rank accuracy instance T/C/H "
                + "/".join(_number(value) for value in instance_accuracies)
            )
            if all(value is not None for value in raw_accuracies):
                text += (
                    "；raw-context T/C/H "
                    + "/".join(_number(value) for value in raw_accuracies)
                )
        elif all(value is not None for value in raw_accuracies):
            text += (
                "；arm-rank accuracy T/C/H "
                + "/".join(_number(value) for value in raw_accuracies)
            )
        text += f"；parameters {int(report.get('parameter_count') or 0)}"
    return text


def _training_provenance_summary() -> str:
    authority = _json(RUN / "oracle_realmap_v4_training_view.json")
    gate = _json(RUN / "realmap_v4_training_gate.json")
    smoke = _json(
        RUN / "instance_balanced_pretraining_smoke_v4/smoke_report.json"
    )
    freeze = _json(
        RUN / "realmap_v4_instance_balanced_training_freeze.json"
    )
    if not any((authority, gate, smoke, freeze)):
        return "等待完整 Oracle；尚无 training-only authority 或模型输出"
    return (
        "gate " + str(bool(
            gate.get("training_authorized")
            and dict(gate.get("gate") or {}).get("passed")
        ))
        + "；authorized view " + str(bool(authority.get("training_permitted")))
        + "；1-epoch smoke " + str(bool(smoke.get("passed")))
        + "；formal-training freeze " + (
            str(freeze.get("schema_version") or "ABSENT")
        )
    )


def _fitting_gate_freeze_summary() -> str:
    payload = _json(
        RUN / "realmap_v4_instance_balanced_fitting_gate_freeze.json"
    )
    if not payload:
        return "缺失"
    thresholds = dict(payload.get("thresholds") or {})
    return (
        "profile " + str(payload.get("fitting_gate_profile") or "UNKNOWN")
        + "；pre-scale50 "
        + str(bool(payload.get("frozen_before_scale50_oracle_outcomes")))
        + "；determined ctx/instances per scale "
        + str(int(thresholds.get("minimum_determined_contexts_per_scale") or 0))
        + "/"
        + str(int(thresholds.get("minimum_determined_instances_per_scale") or 0))
    )


def _jsonl_count(path: Path) -> str:
    if not path.is_file():
        return "尚未开始"
    try:
        count = sum(
            bool(line.strip())
            for line in path.read_text(encoding="utf-8").splitlines()
        )
    except OSError:
        return "暂不可读"
    return f"completed contexts {count}"


def _oracle_progress() -> str:
    root = RUN / "oracle_realmap_v4"
    if not root.is_dir():
        return "尚未开始"
    execution_freeze = _json(RUN / "realmap_v4_oracle_execution_freeze.json")
    scheduled_total = int(
        execution_freeze.get("scheduled_oracle_contexts") or 0
    )
    scheduled_per_scale = int(
        execution_freeze.get("scheduled_oracle_contexts_per_scale") or 0
    )
    index_rows = tuple(
        _json(RUN / "realmap_v4_snapshot_index.json").get("rows") or ()
    )
    available_by_scale = {
        scale: sum(int(row.get("scale") or 0) == scale for row in index_rows)
        for scale in (30, 50)
    }
    selected_by_scale = {
        scale: (
            min(available_by_scale[scale], scheduled_per_scale)
            if scheduled_per_scale
            else available_by_scale[scale]
        )
        for scale in (30, 50)
    }
    selected_total = sum(selected_by_scale.values())
    if scheduled_total:
        selected_total = min(selected_total, scheduled_total)
    outcomes: list[tuple[Path, dict]] = []
    for path in root.glob("*/*.json"):
        # Q0 trace artifacts can be tens of MiB because they contain up to
        # 50,000 label rows.  The status process is observability-only and
        # must not repeatedly materialize those arrays.  Count them by file
        # existence and parse only compact fresh-arm outcome JSON files.
        if path.name == "q0_trace.json":
            continue
        payload = _json(path)
        if (
            payload.get("policy")
            and payload.get("engine_status")
            and payload.get("total_fresh_process_wall_sec") is not None
        ):
            outcomes.append((path, payload))
    if not outcomes:
        return "运行中；等待首个 replay outcome"
    trace_contexts = sum(
        path.is_file() for path in root.glob("*/q0_trace.json")
    )
    touched = len({path.parent.name for path, _payload in outcomes})
    touched_by_scale = {
        scale: len({
            path.parent.name
            for path, payload in outcomes
            if int(payload.get("scale") or 0) == scale
        })
        for scale in (30, 50)
    }
    touched_instances_by_scale = {
        scale: len({
            str(
                payload.get("instance_content_hash")
                or payload.get("instance_id")
                or ""
            )
            for _path, payload in outcomes
            if int(payload.get("scale") or 0) == scale
            and (
                payload.get("instance_content_hash")
                or payload.get("instance_id")
            )
        })
        for scale in (30, 50)
    }
    complete = sum(
        str(payload.get("engine_status") or "") == "COMPLETE"
        for _path, payload in outcomes
    )
    timeout = sum(
        str(payload.get("engine_status") or "") == "TIMEOUT"
        for _path, payload in outcomes
    )
    latest_path, latest = max(
        outcomes, key=lambda row: row[0].stat().st_mtime
    )
    return (
        f"运行中；contexts touched {touched}"
        + (f"/{selected_total}" if selected_total else "")
        + "（"
        + "/".join(
            f"s{scale} {touched_by_scale[scale]}"
            + (f"/{selected_by_scale[scale]}" if selected_by_scale[scale] else "")
            + f"@{touched_instances_by_scale[scale]} instances"
            for scale in (30, 50)
        )
        + "）；"
        f"trace contexts {trace_contexts}；"
        f"replay outcomes {len(outcomes)}；"
        f"complete/timeout {complete}/{timeout}；latest "
        f"{latest_path.parent.name}/{latest_path.name} "
        f"{latest.get('engine_status')} "
        f"{_number(latest.get('total_fresh_process_wall_sec'))}s"
    )


def _oracle_initial_arm_summary() -> str:
    root = RUN / "oracle_realmap_v4"
    if not root.is_dir():
        return "尚未开始"
    arm_files = {
        "QD1": "qd1_initial.json",
        "QB1": "qb1_initial.json",
        "QO2-1e-4": "qo2_0.0001_initial.json",
        "QO2-3e-4": "qo2_0.0003_initial.json",
        "QO2-1e-3": "qo2_0.001_initial.json",
    }
    ratios: dict[str, list[float]] = {key: [] for key in arm_files}
    censored: dict[str, int] = {key: 0 for key in arm_files}
    for q0_path in root.glob("*/q0_initial.json"):
        q0 = _json(q0_path)
        try:
            q0_wall = float(q0["total_fresh_process_wall_sec"])
        except (KeyError, TypeError, ValueError):
            continue
        if q0_wall <= 0.0:
            continue
        for arm, filename in arm_files.items():
            payload = _json(q0_path.parent / filename)
            try:
                arm_wall = float(payload["total_fresh_process_wall_sec"])
            except (KeyError, TypeError, ValueError):
                continue
            if arm_wall <= 0.0:
                continue
            ratios[arm].append(arm_wall / q0_wall)
            if (
                str(q0.get("engine_status") or "") != "COMPLETE"
                or str(payload.get("engine_status") or "") != "COMPLETE"
            ):
                censored[arm] += 1
    parts = []
    for arm in arm_files:
        values = ratios[arm]
        if not values:
            parts.append(f"{arm} n=0")
            continue
        geomean = math.exp(sum(math.log(value) for value in values) / len(values))
        parts.append(
            f"{arm} {_number(geomean)}（n={len(values)}，"
            f"censored={censored[arm]}）"
        )
    return "仅为进行中 initial screen；" + "；".join(parts)


def _oracle_q0_mechanism_summary() -> str:
    """Summarize where literal-Q0 wall is spent without reading trace arrays."""

    root = RUN / "oracle_realmap_v4"
    if not root.is_dir():
        return "尚未开始"
    by_scale: dict[int, list[dict]] = {30: [], 50: []}
    for path in root.glob("*/q0_initial.json"):
        payload = _json(path)
        try:
            scale = int(payload.get("scale") or 0)
            total = float(payload["total_fresh_process_wall_sec"])
            native = float(payload.get("native_search_wall_sec") or 0.0)
            audit = float(payload.get("admission_audit_wall_sec") or 0.0)
            selector = float(
                payload.get("admission_selector_wall_sec") or 0.0
            )
        except (KeyError, TypeError, ValueError):
            continue
        if (
            scale not in by_scale
            or not all(math.isfinite(value) for value in (
                total, native, audit, selector,
            ))
            or total <= 0.0
            or min(native, audit, selector) < 0.0
        ):
            continue
        by_scale[scale].append({
            "total": total,
            "native": native,
            "post": audit + selector,
            "milestone": str(payload.get("milestone_kind") or "OTHER"),
        })
    parts = []
    for scale in (30, 50):
        rows = by_scale[scale]
        if not rows:
            parts.append(f"s{scale} n=0")
            continue
        total = sum(row["total"] for row in rows)
        milestone_counts = {
            "admission": sum(
                row["milestone"] == "ADMISSION_BATCH_READY" for row in rows
            ),
            "proof": sum(
                row["milestone"] == "EXACT_PROOF_COMPLETION" for row in rows
            ),
        }
        milestone_counts["other"] = (
            len(rows) - milestone_counts["admission"]
            - milestone_counts["proof"]
        )
        parts.append(
            f"s{scale} n={len(rows)} admission/proof/other "
            f"{milestone_counts['admission']}/"
            f"{milestone_counts['proof']}/{milestone_counts['other']}，"
            f"weighted Native-search {100.0 * sum(row['native'] for row in rows) / total:.3f}%，"
            f"audit+selector {100.0 * sum(row['post'] for row in rows) / total:.3f}%"
        )
    return "进行中 Q0 compact outcomes；" + "；".join(parts)


def _acceptance(payload: dict) -> str:
    if not payload:
        return "尚未开始"
    scales = []
    for scale, row in sorted((payload.get("by_scale") or {}).items()):
        scales.append(
            f"s{scale}: exact {row.get('guided_exact_count')}/"
            f"{row.get('instance_count')} GM {_number(row.get('paired_geomean_wall_ratio'))}"
        )
    return f"passed {bool(payload.get('passed'))}；" + "；".join(scales)


def _json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}


def _number(value) -> str:
    try:
        return f"{float(value):.6f}"
    except (TypeError, ValueError):
        return "NA"


def _alive(pid: int) -> bool:
    return int(pid) > 0 and Path(f"/proc/{int(pid)}").is_dir()


def _process_state(pid: int) -> str:
    if not _alive(pid):
        return "STOPPED"
    try:
        lines = Path(f"/proc/{int(pid)}/status").read_text(
            encoding="utf-8"
        ).splitlines()
        raw = next(line for line in lines if line.startswith("State:"))
        code = raw.split(":", 1)[1].strip().split(None, 1)[0]
    except (OSError, StopIteration, IndexError):
        return "UNKNOWN_FAIL_CLOSED"
    return "PAUSED_SIGSTOP" if code in {"T", "t"} else "RUNNING"


if __name__ == "__main__":
    raise SystemExit(main())
