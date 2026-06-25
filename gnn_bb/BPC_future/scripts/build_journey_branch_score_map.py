#!/usr/bin/env python3
"""Build an opt-in branch-score map from counterfactual ranking rows.

This script is offline and diagnostic-only. It reads existing
counterfactual-ranking JSONL artifacts and emits score maps that can be passed
to the solver with ``journey_branch_candidate_priority=branch_score``. It does
not run BPC, pricing, RMP, or produce official bounds/certificates.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_branch_score_map_20260624")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_score_map_zh.md"
)


@dataclass
class _ScoreAccumulator:
    score_sum: float = 0.0
    comparison_count: int = 0
    win_count: int = 0
    loss_count: int = 0
    wall_gap_sum: float = 0.0
    exact_gap_sum: float = 0.0
    ranking_observation_count: int = 0
    child_probe_branch_count: int = 0
    complete_child_probe_branch_count: int = 0
    right_censored_child_probe_branch_count: int = 0
    child_probe_proof_cpu_sum: float = 0.0
    child_probe_completion_bound_retry_sum: float = 0.0
    child_probe_fathom_sum: float = 0.0
    child_probe_max_corrected_bound_gain: float = 0.0
    instance: str = ""
    node_id: int | None = None
    depth: int | None = None
    pair: tuple[int, int] = (0, 0)


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            yield payload


def _load_ranking_rows(paths: Iterable[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        if path.is_dir():
            rows.extend(_iter_jsonl(path / "counterfactual_ranking_pair_rows.jsonl"))
            continue
        if path.name == "summary.json":
            rows.extend(_iter_jsonl(path.parent / "counterfactual_ranking_pair_rows.jsonl"))
            continue
        if path.suffix == ".jsonl":
            rows.extend(_iter_jsonl(path))
    return rows


def _load_child_probe_rows(paths: Iterable[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        if path.is_dir():
            rows.extend(_iter_jsonl(path / "child_probe_rows.jsonl"))
            continue
        if path.name == "summary.json":
            rows.extend(_iter_jsonl(path.parent / "child_probe_rows.jsonl"))
            continue
        if path.name == "child_probe_rows.jsonl":
            rows.extend(_iter_jsonl(path))
    return rows


def _load_child_probe_calibration_summaries(paths: Iterable[Path]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for path in paths:
        summary_path = path / "summary.json" if path.is_dir() else path
        if summary_path.name != "summary.json" or not summary_path.exists():
            continue
        try:
            payload = json.loads(summary_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            summaries.append(payload)
    return summaries


def _child_probe_calibration_status(
    summaries: list[dict[str, Any]],
) -> tuple[bool, str, dict[str, Any]]:
    if not summaries:
        return False, "missing_child_probe_proxy_calibration", {
            "child_probe_calibration_summary_count": 0,
            "child_probe_calibration_matched_pair_count": 0,
            "child_probe_calibration_top_pair_mismatch_count": 0,
            "child_probe_calibration_discordant_pair_count": 0,
        }
    matched_pair_count = sum(_int(summary.get("matched_pair_count"), 0) for summary in summaries)
    top_mismatch_count = sum(
        _int(summary.get("top_pair_mismatch_count"), 0) for summary in summaries
    )
    discordant_pair_count = sum(
        _int(summary.get("discordant_pair_count"), 0) for summary in summaries
    )
    invalid_count = sum(
        1
        for summary in summaries
        if str(summary.get("schema_version") or "")
        != "journey_branch_child_probe_proxy_calibration_summary_v1"
    )
    fields = {
        "child_probe_calibration_summary_count": len(summaries),
        "child_probe_calibration_matched_pair_count": int(matched_pair_count),
        "child_probe_calibration_top_pair_mismatch_count": int(top_mismatch_count),
        "child_probe_calibration_discordant_pair_count": int(discordant_pair_count),
        "child_probe_calibration_invalid_summary_count": int(invalid_count),
    }
    if invalid_count > 0:
        return False, "invalid_child_probe_proxy_calibration_schema", fields
    if matched_pair_count <= 0:
        return False, "empty_child_probe_proxy_calibration", fields
    if top_mismatch_count > 0:
        return False, "child_probe_proxy_top_pair_mismatch", fields
    if discordant_pair_count > 0:
        return False, "child_probe_proxy_pairwise_discordance", fields
    return True, "child_probe_proxy_calibration_passed", fields


def _float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return float(default)
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float(default)
    if parsed != parsed:
        return float(default)
    return float(parsed)


def _int_or_none(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _int(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return int(default)
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _pair_tuple(value: Any) -> tuple[int, int] | None:
    if isinstance(value, str):
        pieces = [piece.strip() for piece in value.replace(";", ",").split(",") if piece.strip()]
        if len(pieces) != 2:
            return None
        try:
            i, j = int(pieces[0]), int(pieces[1])
        except ValueError:
            return None
        if i == j:
            return None
        return tuple(sorted((i, j)))
    if isinstance(value, (list, tuple)) and len(value) == 2:
        try:
            i, j = int(value[0]), int(value[1])
        except (TypeError, ValueError):
            return None
        if i == j:
            return None
        return tuple(sorted((i, j)))
    return None


def _compact_pair(row: dict[str, Any], side: str) -> tuple[int, int] | None:
    payload = row.get(side)
    if not isinstance(payload, dict):
        return None
    return _pair_tuple(payload.get("alternative_pair"))


def _score_weight(
    row: dict[str, Any],
    *,
    wall_gap_scale: float,
    exact_gap_scale: float,
    max_weight: float,
) -> float:
    wall_bonus = max(0.0, _float(row.get("wall_delta_gap"))) / max(1.0e-9, float(wall_gap_scale))
    exact_bonus = max(0.0, _float(row.get("exact_pricing_calls_gap"))) / max(1.0e-9, float(exact_gap_scale))
    return min(max(1.0, float(max_weight)), 1.0 + wall_bonus + exact_bonus)


def _score_key(
    pair: tuple[int, int],
    *,
    key_scope: str,
    node_id: int | None,
    depth: int | None,
) -> str:
    i, j = pair
    pair_text = f"{i},{j}"
    if key_scope == "node_depth" and node_id is not None and depth is not None:
        return f"node:{int(node_id)}:depth:{int(depth)}:{pair_text}"
    if key_scope == "depth" and depth is not None:
        return f"depth:{int(depth)}:{pair_text}"
    return pair_text


def _row_from_accumulator(key: str, acc: _ScoreAccumulator) -> dict[str, Any]:
    score = acc.score_sum / max(1, acc.comparison_count)
    task_i, task_j = acc.pair
    sources: list[str] = []
    if acc.ranking_observation_count:
        sources.append("counterfactual_ranking_pairs")
    if acc.child_probe_branch_count:
        sources.append("child_probe_proof_cost")
    return {
        "schema_version": "journey_branch_score_row_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "key": key,
        "instance": acc.instance,
        "node_id": acc.node_id,
        "depth": acc.depth,
        "pair": [task_i, task_j],
        "task_i": task_i,
        "task_j": task_j,
        "score": round(float(score), 9),
        "branch_score": round(float(score), 9),
        "comparison_count": int(acc.comparison_count),
        "win_count": int(acc.win_count),
        "loss_count": int(acc.loss_count),
        "wall_delta_gap_sum": round(float(acc.wall_gap_sum), 9),
        "exact_pricing_calls_gap_sum": round(float(acc.exact_gap_sum), 9),
        "ranking_observation_count": int(acc.ranking_observation_count),
        "child_probe_branch_count": int(acc.child_probe_branch_count),
        "complete_child_probe_branch_count": int(acc.complete_child_probe_branch_count),
        "right_censored_child_probe_branch_count": int(acc.right_censored_child_probe_branch_count),
        "child_probe_proof_cpu_sum": round(float(acc.child_probe_proof_cpu_sum), 9),
        "child_probe_completion_bound_retry_sum": round(float(acc.child_probe_completion_bound_retry_sum), 9),
        "child_probe_fathom_sum": round(float(acc.child_probe_fathom_sum), 9),
        "child_probe_max_corrected_bound_gain": round(float(acc.child_probe_max_corrected_bound_gain), 9),
        "score_source": "+".join(sources) if sources else "unknown",
    }


def _child_probe_group_key(row: dict[str, Any]) -> tuple[str, int | None, int | None, tuple[int, int]] | None:
    pair = _pair_tuple([row.get("task_i"), row.get("task_j")])
    if pair is None:
        return None
    return (
        str(row.get("log_file") or ""),
        _int_or_none(row.get("branch_node_id")),
        _int_or_none(row.get("branch_depth")),
        pair,
    )


def _group_child_probe_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, int | None, int | None, tuple[int, int]], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = _child_probe_group_key(row)
        if key is None:
            continue
        grouped[key].append(row)
    branch_rows: list[dict[str, Any]] = []
    for (log_file, node_id, depth, pair), children in grouped.items():
        labels = [child.get("child_labels") for child in children if isinstance(child.get("child_labels"), dict)]
        child_count = len(children)
        started_count = sum(1 for child in children if bool(child.get("child_started")))
        unstarted_count = max(0, child_count - started_count)
        right_censored = any(bool(child.get("right_censored")) for child in children)
        label_complete = all(bool(child.get("label_observation_complete")) for child in children)
        proof_cpu = sum(_float(label.get("child_proof_cpu")) for label in labels)
        completion_retries = sum(_float(label.get("child_completion_bound_retry_count")) for label in labels)
        exact_pricing_events = sum(_float(label.get("child_exact_pricing_event_count")) for label in labels)
        negative_pricing_events = sum(_float(label.get("child_negative_pricing_event_count")) for label in labels)
        fathom_count = sum(_float(label.get("child_fathomed")) for label in labels)
        corrected_gains = [_float(label.get("child_max_corrected_bound_gain")) for label in labels]
        max_corrected_gain = max(corrected_gains, default=0.0)
        branch_rows.append(
            {
                "log_file": log_file,
                "node_id": node_id,
                "depth": depth,
                "pair": pair,
                "child_count": int(child_count),
                "started_child_count": int(started_count),
                "unstarted_child_count": int(unstarted_count),
                "right_censored": bool(right_censored),
                "label_observation_complete": bool(label_complete),
                "proof_cpu": float(proof_cpu),
                "completion_bound_retry_count": float(completion_retries),
                "exact_pricing_event_count": float(exact_pricing_events),
                "negative_pricing_event_count": float(negative_pricing_events),
                "fathom_count": float(fathom_count),
                "max_corrected_bound_gain": float(max_corrected_gain),
            }
        )
    return branch_rows


def _child_probe_score(
    row: dict[str, Any],
    *,
    complete_bonus: float,
    right_censored_penalty: float,
    unstarted_child_penalty: float,
    fathom_bonus: float,
    corrected_gain_scale: float,
    corrected_gain_cap: float,
    completion_retry_penalty: float,
    proof_cpu_scale: float,
    negative_pricing_penalty: float,
) -> float:
    score = 0.0
    if bool(row.get("label_observation_complete")):
        score += float(complete_bonus)
    if bool(row.get("right_censored")):
        score -= float(right_censored_penalty)
    score -= float(unstarted_child_penalty) * _float(row.get("unstarted_child_count"))
    score += float(fathom_bonus) * _float(row.get("fathom_count"))
    corrected_gain = min(max(0.0, _float(row.get("max_corrected_bound_gain"))), float(corrected_gain_cap))
    score += corrected_gain / max(1.0e-9, float(corrected_gain_scale))
    score -= float(completion_retry_penalty) * _float(row.get("completion_bound_retry_count"))
    score -= _float(row.get("proof_cpu")) / max(1.0e-9, float(proof_cpu_scale))
    score -= float(negative_pricing_penalty) * _float(row.get("negative_pricing_event_count"))
    return float(score)


def build_branch_score_map(
    inputs: list[Path],
    output_dir: Path,
    report: Path,
    *,
    key_scope: str = "node_depth",
    wall_gap_scale: float = 60.0,
    exact_gap_scale: float = 10.0,
    max_weight: float = 10.0,
    include_instance_contains: tuple[str, ...] = (),
    exclude_instance_contains: tuple[str, ...] = (),
    include_child_probe: bool = False,
    child_probe_calibration_inputs: tuple[Path, ...] = (),
    include_child_probe_log_contains: tuple[str, ...] = (),
    exclude_child_probe_log_contains: tuple[str, ...] = (),
    child_complete_bonus: float = 5.0,
    child_right_censored_penalty: float = 8.0,
    child_unstarted_child_penalty: float = 1.0,
    child_fathom_bonus: float = 1.0,
    child_corrected_gain_scale: float = 5.0,
    child_corrected_gain_cap: float = 25.0,
    child_completion_retry_penalty: float = 0.1,
    child_proof_cpu_scale: float = 120.0,
    child_negative_pricing_penalty: float = 0.0,
) -> dict[str, Any]:
    if key_scope not in {"node_depth", "depth", "pair"}:
        raise ValueError(f"unsupported key_scope: {key_scope}")

    raw_ranking_rows = _load_ranking_rows(inputs)
    raw_child_probe_rows = _load_child_probe_rows(inputs) if include_child_probe else []
    child_probe_calibration_summaries = _load_child_probe_calibration_summaries(
        child_probe_calibration_inputs
    )
    (
        child_probe_calibration_passed,
        child_probe_calibration_reason,
        child_probe_calibration_fields,
    ) = _child_probe_calibration_status(child_probe_calibration_summaries)
    child_probe_score_map_blocked = bool(
        include_child_probe and not child_probe_calibration_passed
    )
    ranking_rows = [
        row
        for row in raw_ranking_rows
        if _instance_filter_accepts(
            str(row.get("instance") or ""),
            include_contains=include_instance_contains,
            exclude_contains=exclude_instance_contains,
        )
    ]
    child_probe_rows = [
        row
        for row in raw_child_probe_rows
        if _instance_filter_accepts(
            str(row.get("log_file") or ""),
            include_contains=include_child_probe_log_contains,
            exclude_contains=exclude_child_probe_log_contains,
        )
    ] if not child_probe_score_map_blocked else []
    accumulators: dict[str, _ScoreAccumulator] = {}
    skipped_rows = 0
    skipped_child_probe_branch_rows = 0

    for row in ranking_rows:
        if row.get("official_bound_effect") not in (False, None):
            skipped_rows += 1
            continue
        better_pair = _compact_pair(row, "better")
        worse_pair = _compact_pair(row, "worse")
        if better_pair is None or worse_pair is None:
            skipped_rows += 1
            continue
        node_id = _int_or_none(row.get("node_id"))
        depth = _int_or_none(row.get("depth"))
        instance = str(row.get("instance") or "")
        weight = _score_weight(
            row,
            wall_gap_scale=wall_gap_scale,
            exact_gap_scale=exact_gap_scale,
            max_weight=max_weight,
        )
        wall_gap = max(0.0, _float(row.get("wall_delta_gap")))
        exact_gap = max(0.0, _float(row.get("exact_pricing_calls_gap")))
        for pair, sign in ((better_pair, 1.0), (worse_pair, -1.0)):
            key = _score_key(pair, key_scope=key_scope, node_id=node_id, depth=depth)
            if key not in accumulators:
                accumulators[key] = _ScoreAccumulator(
                    instance=instance,
                    node_id=node_id,
                    depth=depth,
                    pair=pair,
                )
            acc = accumulators[key]
            acc.score_sum += float(sign) * float(weight)
            acc.comparison_count += 1
            acc.ranking_observation_count += 1
            acc.wall_gap_sum += wall_gap
            acc.exact_gap_sum += exact_gap
            if sign > 0:
                acc.win_count += 1
            else:
                acc.loss_count += 1

    child_probe_branch_rows = _group_child_probe_rows(child_probe_rows)
    for row in child_probe_branch_rows:
        pair = row.get("pair")
        if not isinstance(pair, tuple):
            skipped_child_probe_branch_rows += 1
            continue
        node_id = _int_or_none(row.get("node_id"))
        depth = _int_or_none(row.get("depth"))
        key = _score_key(pair, key_scope=key_scope, node_id=node_id, depth=depth)
        score = _child_probe_score(
            row,
            complete_bonus=child_complete_bonus,
            right_censored_penalty=child_right_censored_penalty,
            unstarted_child_penalty=child_unstarted_child_penalty,
            fathom_bonus=child_fathom_bonus,
            corrected_gain_scale=child_corrected_gain_scale,
            corrected_gain_cap=child_corrected_gain_cap,
            completion_retry_penalty=child_completion_retry_penalty,
            proof_cpu_scale=child_proof_cpu_scale,
            negative_pricing_penalty=child_negative_pricing_penalty,
        )
        if key not in accumulators:
            accumulators[key] = _ScoreAccumulator(
                instance=str(row.get("log_file") or ""),
                node_id=node_id,
                depth=depth,
                pair=pair,
            )
        acc = accumulators[key]
        acc.score_sum += float(score)
        acc.comparison_count += 1
        acc.child_probe_branch_count += 1
        acc.complete_child_probe_branch_count += 1 if bool(row.get("label_observation_complete")) else 0
        acc.right_censored_child_probe_branch_count += 1 if bool(row.get("right_censored")) else 0
        acc.child_probe_proof_cpu_sum += _float(row.get("proof_cpu"))
        acc.child_probe_completion_bound_retry_sum += _float(row.get("completion_bound_retry_count"))
        acc.child_probe_fathom_sum += _float(row.get("fathom_count"))
        acc.child_probe_max_corrected_bound_gain = max(
            float(acc.child_probe_max_corrected_bound_gain),
            _float(row.get("max_corrected_bound_gain")),
        )
        if score > 0.0:
            acc.win_count += 1
        elif score < 0.0:
            acc.loss_count += 1

    score_rows = [
        _row_from_accumulator(key, acc)
        for key, acc in sorted(
            accumulators.items(),
            key=lambda item: (
                -(item[1].score_sum / max(1, item[1].comparison_count)),
                item[1].instance,
                item[0],
            ),
        )
    ]
    score_map = {str(row["key"]): float(row["score"]) for row in score_rows}

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "journey_branch_score_rows.json").write_text(
        json.dumps(score_rows, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "journey_branch_score_rows.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in score_rows),
        encoding="utf-8",
    )
    (output_dir / "journey_branch_score_map.json").write_text(
        json.dumps(score_map, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    instance_names = {str(row.get("instance") or "") for row in ranking_rows if row.get("instance")}
    instance_names.update(str(row.get("log_file") or "") for row in child_probe_branch_rows if row.get("log_file"))
    instance_count = len(instance_names)
    summary = {
        "schema_version": "journey_branch_score_map_summary_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "input_paths": [str(path) for path in inputs],
        "output_dir": str(output_dir),
        "key_scope": key_scope,
        "raw_ranking_pair_row_count": len(raw_ranking_rows),
        "ranking_pair_row_count": len(ranking_rows),
        "include_child_probe": bool(include_child_probe),
        "child_probe_score_map_blocked": bool(child_probe_score_map_blocked),
        "child_probe_score_map_block_reason": child_probe_calibration_reason,
        "child_probe_calibration_input_paths": [
            str(path) for path in child_probe_calibration_inputs
        ],
        **child_probe_calibration_fields,
        "raw_child_probe_row_count": len(raw_child_probe_rows),
        "child_probe_row_count": len(child_probe_rows),
        "child_probe_branch_row_count": len(child_probe_branch_rows),
        "filtered_out_child_probe_row_count": len(raw_child_probe_rows) - len(child_probe_rows),
        "skipped_child_probe_branch_row_count": int(skipped_child_probe_branch_rows),
        "filtered_out_row_count": len(raw_ranking_rows) - len(ranking_rows),
        "skipped_row_count": int(skipped_rows),
        "branch_score_row_count": len(score_rows),
        "branch_score_map_entry_count": len(score_map),
        "instance_count": int(instance_count),
        "wall_gap_scale": float(wall_gap_scale),
        "exact_gap_scale": float(exact_gap_scale),
        "max_weight": float(max_weight),
        "child_complete_bonus": float(child_complete_bonus),
        "child_right_censored_penalty": float(child_right_censored_penalty),
        "child_unstarted_child_penalty": float(child_unstarted_child_penalty),
        "child_fathom_bonus": float(child_fathom_bonus),
        "child_corrected_gain_scale": float(child_corrected_gain_scale),
        "child_corrected_gain_cap": float(child_corrected_gain_cap),
        "child_completion_retry_penalty": float(child_completion_retry_penalty),
        "child_proof_cpu_scale": float(child_proof_cpu_scale),
        "child_negative_pricing_penalty": float(child_negative_pricing_penalty),
        "include_instance_contains": list(include_instance_contains),
        "exclude_instance_contains": list(exclude_instance_contains),
        "include_child_probe_log_contains": list(include_child_probe_log_contains),
        "exclude_child_probe_log_contains": list(exclude_child_probe_log_contains),
        "solver_priority_mode": "branch_score_horizon" if include_child_probe else "branch_score",
        "solver_score_path": str(output_dir / "journey_branch_score_rows.json"),
        "solver_score_map_path": str(output_dir / "journey_branch_score_map.json"),
        "usable_as_certificate": False,
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    _write_report(report, summary, score_rows)
    return summary


def _instance_filter_accepts(
    instance: str,
    *,
    include_contains: tuple[str, ...],
    exclude_contains: tuple[str, ...],
) -> bool:
    if include_contains and not any(token in instance for token in include_contains):
        return False
    if exclude_contains and any(token in instance for token in exclude_contains):
        return False
    return True


def _write_report(report: Path, summary: dict[str, Any], score_rows: list[dict[str, Any]]) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = [
        "# Journey Branch Score Map",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 目的",
        "",
        "把 V33 这类同 parent counterfactual ranking rows 转成 solver 的 `branch_score` opt-in 输入。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。",
        "",
        "## 机器字段",
        "",
        "```text",
    ]
    for key in [
        "ranking_pair_row_count",
        "raw_ranking_pair_row_count",
        "include_child_probe",
        "child_probe_score_map_blocked",
        "child_probe_score_map_block_reason",
        "child_probe_calibration_input_paths",
        "child_probe_calibration_matched_pair_count",
        "child_probe_calibration_top_pair_mismatch_count",
        "child_probe_calibration_discordant_pair_count",
        "raw_child_probe_row_count",
        "child_probe_row_count",
        "child_probe_branch_row_count",
        "filtered_out_child_probe_row_count",
        "filtered_out_row_count",
        "branch_score_row_count",
        "branch_score_map_entry_count",
        "instance_count",
        "key_scope",
        "include_instance_contains",
        "exclude_instance_contains",
        "include_child_probe_log_contains",
        "exclude_child_probe_log_contains",
        "solver_priority_mode",
        "solver_score_path",
        "production_ready",
        "certificate_effect",
        "official_bound_effect",
    ]:
        lines.append(f"{key} = {summary.get(key)}")
    lines.extend(["```", "", "## Top Score Rows", ""])
    for row in sorted(score_rows, key=lambda item: float(item.get("score") or 0.0), reverse=True)[:12]:
        lines.append(
            "- "
            f"key={row['key']} pair={row['pair']} score={row['score']} "
            f"wins={row['win_count']} losses={row['loss_count']} "
            f"comparisons={row['comparison_count']}"
        )
    lines.extend(["", "## 使用边界", ""])
    lines.append(
        "使用方式：`journey_branch_candidate_priority=branch_score`，并把 `journey_branch_candidate_score_path` 指向 `journey_branch_score_rows.json`。"
    )
    if summary.get("include_child_probe"):
        lines.append(
            "child-probe proof-cost 分数只有在提供 proxy-vs-full 校准且校准通过时才会进入 score map；未校准或校准出现 top mismatch / pairwise discordance 时必须 fail-closed。"
        )
    lines.append(
        "`branch_score` 只改变 opt-in 的 Ryan-Foster pair 排序；排序范围仍由 `journey_branch_fractionality_tie_tolerance` 决定。"
    )
    lines.append(
        "它不能提供 official bound、no-negative certificate 或 fathom 依据；所有 child 最终仍必须靠 exact pricing closure。"
    )
    if summary.get("instance_count", 0) > 1:
        lines.append(
            "当前 score map 聚合了多个实例；在没有在线模型泛化验证前，不应直接作为 production 配置批量使用。"
        )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--key-scope", choices=("node_depth", "depth", "pair"), default="node_depth")
    parser.add_argument("--wall-gap-scale", type=float, default=60.0)
    parser.add_argument("--exact-gap-scale", type=float, default=10.0)
    parser.add_argument("--max-weight", type=float, default=10.0)
    parser.add_argument("--include-instance-contains", action="append", default=[])
    parser.add_argument("--exclude-instance-contains", action="append", default=[])
    parser.add_argument("--include-child-probe", action="store_true")
    parser.add_argument(
        "--child-probe-calibration-input",
        action="append",
        type=Path,
        default=[],
        help=(
            "Required when --include-child-probe should contribute scores. "
            "Accepts proxy-vs-full calibration output directories or summary.json files."
        ),
    )
    parser.add_argument("--include-child-probe-log-contains", action="append", default=[])
    parser.add_argument("--exclude-child-probe-log-contains", action="append", default=[])
    parser.add_argument("--child-complete-bonus", type=float, default=5.0)
    parser.add_argument("--child-right-censored-penalty", type=float, default=8.0)
    parser.add_argument("--child-unstarted-child-penalty", type=float, default=1.0)
    parser.add_argument("--child-fathom-bonus", type=float, default=1.0)
    parser.add_argument("--child-corrected-gain-scale", type=float, default=5.0)
    parser.add_argument("--child-corrected-gain-cap", type=float, default=25.0)
    parser.add_argument("--child-completion-retry-penalty", type=float, default=0.1)
    parser.add_argument("--child-proof-cpu-scale", type=float, default=120.0)
    parser.add_argument("--child-negative-pricing-penalty", type=float, default=0.0)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = build_branch_score_map(
        list(args.paths),
        args.output_dir,
        args.report,
        key_scope=args.key_scope,
        wall_gap_scale=args.wall_gap_scale,
        exact_gap_scale=args.exact_gap_scale,
        max_weight=args.max_weight,
        include_instance_contains=tuple(args.include_instance_contains or ()),
        exclude_instance_contains=tuple(args.exclude_instance_contains or ()),
        include_child_probe=bool(args.include_child_probe),
        child_probe_calibration_inputs=tuple(args.child_probe_calibration_input or ()),
        include_child_probe_log_contains=tuple(args.include_child_probe_log_contains or ()),
        exclude_child_probe_log_contains=tuple(args.exclude_child_probe_log_contains or ()),
        child_complete_bonus=args.child_complete_bonus,
        child_right_censored_penalty=args.child_right_censored_penalty,
        child_unstarted_child_penalty=args.child_unstarted_child_penalty,
        child_fathom_bonus=args.child_fathom_bonus,
        child_corrected_gain_scale=args.child_corrected_gain_scale,
        child_corrected_gain_cap=args.child_corrected_gain_cap,
        child_completion_retry_penalty=args.child_completion_retry_penalty,
        child_proof_cpu_scale=args.child_proof_cpu_scale,
        child_negative_pricing_penalty=args.child_negative_pricing_penalty,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
