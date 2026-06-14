#!/usr/bin/env python3
"""Build a diagnostic CBF mode-transition audit from existing JSONL logs.

This script is read-only with respect to solver state.  It does not run BPC,
pricing, RMP, Pulse, workers, or certificates.  It reconstructs adjacent
``journey_counterfactual_replay_capture`` events into approximate
``state_t, action_t, state_{t+1}`` transitions and computes a first-pass
Lyapunov-surrogate / CBF-slack diagnostic for later GAT impact modeling.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


CAPTURE_EVENT = "journey_counterfactual_replay_capture"
CAPTURE_SCHEMA = "journey_counterfactual_replay_capture_v1"
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/cbf_mode_transition_audit_20260614")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_cbf_mode_transition_audit_zh.md"
)


def _iter_jsonl_paths(paths: Iterable[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_file() and path.suffix == ".jsonl":
            files.append(path)
        elif path.is_dir():
            files.extend(sorted(candidate for candidate in path.rglob("*.jsonl") if candidate.is_file()))
    return sorted(dict.fromkeys(files))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError as exc:
            records.append(
                {
                    "event": "__json_decode_error__",
                    "_source_file": str(path),
                    "_line": int(line_number),
                    "error": str(exc),
                }
            )
            continue
        if isinstance(row, dict):
            event = dict(row)
            event["_source_file"] = str(path)
            event["_line"] = int(line_number)
            records.append(event)
    return records


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        result = float(value)
        if math.isnan(result) or math.isinf(result):
            return default
        return result
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _round(value: float | None, ndigits: int = 9) -> float | None:
    if value is None:
        return None
    return round(float(value), ndigits)


def _task_set(journey: dict[str, Any]) -> tuple[int, ...]:
    raw = journey.get("task_set", [])
    if not isinstance(raw, (list, tuple, set)):
        return tuple()
    result: list[int] = []
    for item in raw:
        try:
            result.append(int(item))
        except (TypeError, ValueError):
            continue
    return tuple(sorted(dict.fromkeys(result)))


def _flatten_sequence(journey: dict[str, Any]) -> tuple[int, ...]:
    raw = journey.get("sequence", [])
    result: list[int] = []
    if isinstance(raw, (list, tuple)):
        for sortie in raw:
            if isinstance(sortie, (list, tuple)):
                for task in sortie:
                    try:
                        result.append(int(task))
                    except (TypeError, ValueError):
                        continue
            else:
                try:
                    result.append(int(sortie))
                except (TypeError, ValueError):
                    continue
    return tuple(result)


def _first_second_action(journey: dict[str, Any]) -> tuple[str, str]:
    seq = _flatten_sequence(journey)
    if not seq:
        return ("empty", "empty")
    first = str(seq[0])
    second = "return" if len(seq) == 1 else str(seq[1])
    return (first, second)


def _true_rc(journey: dict[str, Any]) -> float | None:
    try:
        return float(journey.get("true_reduced_cost"))
    except (TypeError, ValueError):
        return None


def _hist_hash(counter: Counter[Any]) -> str:
    return repr(tuple(sorted((str(key), int(value)) for key, value in counter.items())))


def _entropy(counter: Counter[Any]) -> float:
    total = sum(int(value) for value in counter.values())
    if total <= 0:
        return 0.0
    entropy = 0.0
    for value in counter.values():
        p = float(value) / float(total)
        if p > 0.0:
            entropy -= p * math.log(p)
    return entropy


def _journeys(event: dict[str, Any], key: str) -> list[dict[str, Any]]:
    raw = event.get(key)
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, dict)]


def _active_task_sets(event: dict[str, Any]) -> set[tuple[int, ...]]:
    result: set[tuple[int, ...]] = set()
    raw = event.get("active_task_sets")
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, (list, tuple, set)):
                try:
                    result.add(tuple(sorted(int(task) for task in item)))
                except (TypeError, ValueError):
                    continue
    return result


def _mode_signature(event: dict[str, Any]) -> dict[str, Any]:
    returned = _journeys(event, "returned_journeys")
    pool = _journeys(event, "pool_journeys")
    active_sets = _active_task_sets(event)
    all_observed = returned + pool
    first_hist: Counter[str] = Counter()
    second_hist: Counter[str] = Counter()
    size_hist: Counter[int] = Counter()
    replacement_count = 0
    support_changing_count = 0
    negative_count = 0
    best_rc: float | None = None
    for journey in all_observed:
        first, second = _first_second_action(journey)
        first_hist[first] += 1
        second_hist[f"{first}->{second}"] += 1
        task_set = _task_set(journey)
        size_hist[len(task_set)] += 1
        rc = _true_rc(journey)
        if rc is not None:
            best_rc = rc if best_rc is None else min(best_rc, rc)
            if rc < -1.0e-9:
                negative_count += 1
        if journey in returned:
            if task_set in active_sets:
                replacement_count += 1
            else:
                support_changing_count += 1
    returned_count = len(returned)
    replacement_ratio = 0.0 if returned_count <= 0 else replacement_count / returned_count
    support_changing_ratio = 0.0 if returned_count <= 0 else support_changing_count / returned_count
    signature = {
        "active_hash": str(event.get("active_hash_before", "")),
        "pool_signature_hash": str(event.get("pool_signature_hash", "")),
        "pool_task_set_hash": str(event.get("pool_task_set_hash", "")),
        "first_task_hist": dict(sorted(first_hist.items())),
        "second_action_hist": dict(sorted(second_hist.items())),
        "task_set_size_hist": dict(sorted(size_hist.items())),
        "mode_entropy": _entropy(first_hist) + _entropy(second_hist),
        "observed_journey_count": len(all_observed),
        "returned_journey_count": returned_count,
        "negative_count": negative_count,
        "best_true_rc": best_rc,
        "replacement_ratio": replacement_ratio,
        "support_changing_ratio": support_changing_ratio,
    }
    signature["z_hash"] = repr(
        (
            signature["active_hash"],
            signature["pool_signature_hash"],
            _hist_hash(first_hist),
            _hist_hash(second_hist),
            _hist_hash(size_hist),
        )
    )
    return signature


def _latest_event(events: list[dict[str, Any]], name: str, cg_iter: int) -> dict[str, Any]:
    candidates = [
        event
        for event in events
        if event.get("event") == name and _as_int(event.get("cg_iter"), -1) == cg_iter
    ]
    return candidates[-1] if candidates else {}


def _capture_ok(event: dict[str, Any]) -> bool:
    return (
        event.get("event") == CAPTURE_EVENT
        and event.get("schema_version") == CAPTURE_SCHEMA
        and event.get("diagnostic_only") is True
        and event.get("replay_no_certificate_effect") is True
        and event.get("certificate_capable") is False
        and event.get("official_bound_effect") is False
    )


def _surrogate_components(
    event: dict[str, Any],
    *,
    previous_capture: dict[str, Any] | None,
    events: list[dict[str, Any]],
) -> dict[str, float]:
    cg_iter = _as_int(event.get("cg_iter"), -1)
    dual_diag = _latest_event(events, "journey_rmp_dual_diagnostics", cg_iter)
    progress = _latest_event(events, "journey_cg_progress_diagnostics", cg_iter)
    mode = _mode_signature(event)
    current_objective = _as_float(event.get("rmp_objective_before"), 0.0)
    previous_objective = (
        _as_float(previous_capture.get("rmp_objective_before"), current_objective)
        if previous_capture is not None
        else current_objective
    )
    objective_progress = max(0.0, previous_objective - current_objective)
    previous_active_hash = "" if previous_capture is None else str(previous_capture.get("active_hash_before", ""))
    active_hash = str(event.get("active_hash_before", ""))
    basis_turnover = 0.0 if not previous_active_hash or previous_active_hash == active_hash else 1.0
    dual_l1_delta = _as_float(
        dual_diag.get("dual_l1_delta", progress.get("scip_dual_l1_delta")),
        0.0,
    )
    hidden_negative_count = float(mode["negative_count"]) / max(1.0, float(mode["observed_journey_count"]))
    final_judge_retry_count = _as_float(
        event.get("final_judge_retry_count", progress.get("certificate_flat_rounds")),
        0.0,
    )
    return {
        "dual_l1_delta": dual_l1_delta,
        "basis_turnover": basis_turnover,
        "residual_mode_entropy": float(mode["mode_entropy"]),
        "hidden_negative_count": hidden_negative_count,
        "final_judge_retry_count": final_judge_retry_count,
        "replacement_ratio": float(mode["replacement_ratio"]),
        "objective_progress": objective_progress,
        "support_changing_progress": float(mode["support_changing_ratio"]),
    }


def _surrogate_energy(components: dict[str, float]) -> float:
    return (
        components["dual_l1_delta"]
        + components["basis_turnover"]
        + components["residual_mode_entropy"]
        + components["hidden_negative_count"]
        + components["final_judge_retry_count"]
        + components["replacement_ratio"]
        - components["objective_progress"]
        - components["support_changing_progress"]
    )


def _transition_record(
    current: dict[str, Any],
    nxt: dict[str, Any],
    *,
    previous: dict[str, Any] | None,
    events: list[dict[str, Any]],
    alpha: float,
    v_crit: float,
) -> dict[str, Any]:
    current_mode = _mode_signature(current)
    next_mode = _mode_signature(nxt)
    current_components = _surrogate_components(current, previous_capture=previous, events=events)
    next_components = _surrogate_components(nxt, previous_capture=current, events=events)
    v_t = _surrogate_energy(current_components)
    v_next = _surrogate_energy(next_components)
    h_t = float(v_crit) - v_t
    h_next = float(v_crit) - v_next
    barrier_slack = h_next - h_t + float(alpha) * h_t
    returned = _journeys(current, "returned_journeys")
    action_task_sets = [_task_set(journey) for journey in returned]
    action_first_second = [_first_second_action(journey) for journey in returned]
    return {
        "source_file": current.get("_source_file", ""),
        "node_id": current.get("node_id", 0),
        "depth": current.get("depth", 0),
        "cg_iter": current.get("cg_iter"),
        "next_cg_iter": nxt.get("cg_iter"),
        "instance": current.get("instance", ""),
        "task_count": current.get("task_count"),
        "context_hash": current.get("context_hash", ""),
        "next_context_hash": nxt.get("context_hash", ""),
        "state_t_z_hash": current_mode["z_hash"],
        "state_next_z_hash": next_mode["z_hash"],
        "mode_switched": bool(current_mode["z_hash"] != next_mode["z_hash"]),
        "active_hash_before": current.get("active_hash_before", ""),
        "active_hash_next": nxt.get("active_hash_before", ""),
        "active_hash_switched": bool(current.get("active_hash_before") != nxt.get("active_hash_before")),
        "action_returned_count": len(returned),
        "action_negative_count": sum(
            1 for journey in returned if (_true_rc(journey) is not None and float(_true_rc(journey)) < -1.0e-9)
        ),
        "action_task_sets": [list(task_set) for task_set in action_task_sets],
        "action_first_second": [list(pair) for pair in action_first_second],
        "state_t_mode": current_mode,
        "state_next_mode": next_mode,
        "v_t_components": {key: _round(value) for key, value in current_components.items()},
        "v_next_components": {key: _round(value) for key, value in next_components.items()},
        "v_t": _round(v_t),
        "v_next": _round(v_next),
        "delta_v": _round(v_next - v_t),
        "v_crit": _round(v_crit),
        "alpha": _round(alpha),
        "h_t": _round(h_t),
        "h_next": _round(h_next),
        "barrier_slack": _round(barrier_slack),
        "cbf_feasible_observed": bool(barrier_slack >= -1.0e-9),
        "bad_mode_transition": bool(current_mode["z_hash"] != next_mode["z_hash"] and v_next > v_t),
    }


def audit(paths: Iterable[Path], *, alpha: float = 0.25, v_crit: float = 1.0) -> dict[str, Any]:
    files = _iter_jsonl_paths(paths)
    all_events_by_file: dict[str, list[dict[str, Any]]] = {}
    decode_error_count = 0
    for path in files:
        events = _read_jsonl(path)
        decode_error_count += sum(1 for event in events if event.get("event") == "__json_decode_error__")
        all_events_by_file[str(path)] = [event for event in events if event.get("event") != "__json_decode_error__"]

    transitions: list[dict[str, Any]] = []
    capture_count = 0
    bad_capture_count = 0
    for source_file, events in all_events_by_file.items():
        captures = [event for event in events if event.get("event") == CAPTURE_EVENT]
        capture_count += len(captures)
        bad_capture_count += sum(1 for event in captures if not _capture_ok(event))
        valid_captures = [event for event in captures if _capture_ok(event)]
        grouped: dict[tuple[Any, Any, Any], list[dict[str, Any]]] = defaultdict(list)
        for event in valid_captures:
            grouped[(event.get("node_id", 0), event.get("depth", 0), event.get("instance", ""))].append(event)
        for group_events in grouped.values():
            ordered = sorted(group_events, key=lambda event: (_as_int(event.get("cg_iter"), -1), _as_float(event.get("time"), 0.0)))
            for idx in range(len(ordered) - 1):
                current = ordered[idx]
                nxt = ordered[idx + 1]
                if _as_int(nxt.get("cg_iter"), -1) <= _as_int(current.get("cg_iter"), -1):
                    continue
                previous = ordered[idx - 1] if idx > 0 else None
                transitions.append(
                    _transition_record(
                        current,
                        nxt,
                        previous=previous,
                        events=events,
                        alpha=alpha,
                        v_crit=v_crit,
                    )
                )

    transition_count = len(transitions)
    feasible_count = sum(1 for item in transitions if item["cbf_feasible_observed"])
    mode_switch_count = sum(1 for item in transitions if item["mode_switched"])
    bad_mode_count = sum(1 for item in transitions if item["bad_mode_transition"])
    negative_action_count = sum(1 for item in transitions if int(item["action_negative_count"]) > 0)
    by_task_count = Counter(str(item.get("task_count")) for item in transitions)
    checks = {
        "diagnostic_only": True,
        "runs_bpc_or_pricing_false": True,
        "all_capture_events_no_certificate_effect": bool(capture_count == 0 or bad_capture_count == 0),
        "transitions_have_state_action_next": all(
            item.get("state_t_z_hash") and item.get("state_next_z_hash") and "action_returned_count" in item
            for item in transitions
        ),
        "barrier_values_are_present": all(item.get("barrier_slack") is not None for item in transitions),
        "no_decode_errors": decode_error_count == 0,
    }
    return {
        "schema_version": "cbf_mode_transition_audit_v1",
        "status": "cbf_mode_transition_audited"
        if transition_count > 0
        else "cbf_mode_transition_audited_no_transition_evidence",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "input_file_count": len(files),
        "capture_event_count": capture_count,
        "bad_capture_event_count": bad_capture_count,
        "decode_error_count": decode_error_count,
        "transition_count": transition_count,
        "cbf_feasible_observed_count": feasible_count,
        "cbf_infeasible_observed_count": transition_count - feasible_count,
        "mode_switch_count": mode_switch_count,
        "bad_mode_transition_count": bad_mode_count,
        "negative_action_transition_count": negative_action_count,
        "transition_task_count_histogram": dict(sorted(by_task_count.items())),
        "has_transition_evidence": bool(transition_count > 0),
        "training_ready": False,
        "alpha": float(alpha),
        "v_crit": float(v_crit),
        "checks": checks,
        "all_checks_pass": all(bool(value) for value in checks.values()),
        "transitions": transitions,
        "transition_samples": transitions[:10],
        "production_ready": False,
        "goal_complete": False,
    }


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# CBF Mode Transition Audit 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告只从已有 JSONL 中重建 `state_t, action_t, state_{t+1}` transition，",
        "计算 Lyapunov surrogate 与 CBF barrier slack。它不运行 BPC / pricing / RMP / Pulse，",
        "也不改变 worker、certificate 或 official lower bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "cbf_mode_transition_audit = current",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"status = {summary['status']}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"goal_complete = {str(summary['goal_complete']).lower()}",
        "```",
        "",
        "## 摘要",
        "",
        "```json",
        json.dumps(
            {
                "input_file_count": summary["input_file_count"],
                "capture_event_count": summary["capture_event_count"],
                "bad_capture_event_count": summary["bad_capture_event_count"],
                "transition_count": summary["transition_count"],
                "cbf_feasible_observed_count": summary["cbf_feasible_observed_count"],
                "cbf_infeasible_observed_count": summary["cbf_infeasible_observed_count"],
                "mode_switch_count": summary["mode_switch_count"],
                "bad_mode_transition_count": summary["bad_mode_transition_count"],
                "negative_action_transition_count": summary["negative_action_transition_count"],
                "transition_task_count_histogram": summary["transition_task_count_histogram"],
                "has_transition_evidence": summary["has_transition_evidence"],
                "training_ready": summary["training_ready"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## 检查项",
        "",
        "```json",
        json.dumps(summary["checks"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## 解释",
        "",
        "- `cbf_feasible_observed_count` 只表示相邻 capture 事件在该 surrogate 下满足离散 CBF slack；",
        "- `cbf_infeasible_observed_count` 表示当前 observed action 后 energy 没有满足该安全约束；",
        "- 本报告不能证明 production speedup，也不能作为 certificate；",
        "- 下一步应扩大 no-certificate-effect capture，覆盖 5/10/20 多实例和 mixed/noop/improved contexts。",
    ]
    if summary["transition_samples"]:
        lines.extend(
            [
                "",
                "## Transition samples",
                "",
                "```json",
                json.dumps(summary["transition_samples"], ensure_ascii=False, indent=2, sort_keys=True),
                "```",
            ]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="JSONL files or directories to scan.")
    parser.add_argument("--alpha", type=float, default=0.25)
    parser.add_argument("--v-crit", type=float, default=1.0)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)

    summary = audit(args.paths, alpha=args.alpha, v_crit=args.v_crit)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_report(args.report, summary)
    print(json.dumps({"summary": str(summary_path), "report": str(args.report), "all_checks_pass": summary["all_checks_pass"]}, ensure_ascii=False))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
