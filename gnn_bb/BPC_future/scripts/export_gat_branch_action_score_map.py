#!/usr/bin/env python3
"""Export opt-in Journey branch score rows from a trained branch/action GAT.

This is an offline scheduler helper. It reads existing
``journey_branch_candidates`` JSONL events, scores the logged Ryan-Foster
candidate pairs with a diagnostic GAT checkpoint, and writes score rows that
the solver can consume with ``journey_branch_candidate_priority=branch_score``
or ``branch_score_horizon``.

The exported scores are not a pricing oracle, branching oracle, certificate, or
official bound. They only affect opt-in branch candidate ordering.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import json
from pathlib import Path
import sys
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch

from BPC_future.learning.branch_impact_model import GATBranchImpactModel
from BPC_future.learning.graph_builder import FutureGraphBuilder
from BPC_future.scripts.audit_journey_branch_impact import BRANCH_IMPACT_FEATURE_SCHEMA
from BPC_future.scripts.build_gat_branch_action_sanity_dataset import (
    BRANCH_ACTION_CONTEXT_FEATURE_SCHEMA,
    PHASED_TESTING_DECISION_CODES,
    PHASED_TESTING_ELIMINATION_REASON_CODES,
    PHASED_TESTING_STAGE_CODES,
)


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/gat_branch_action_v430_randomtw60_20260626/score_map")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260626_bpc_future_gat_branch_action_v430_score_map_zh.md"
)


def _iter_jsonl_files(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if path.is_dir():
            yield from sorted(path.glob("**/*.jsonl"))
        elif path.is_file() and path.suffix == ".jsonl":
            yield path


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            yield payload


def _number(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return float(default)
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float(default)
    if parsed != parsed:
        return float(default)
    return float(parsed)


def _code(mapping: dict[str, int], value: Any) -> float:
    text = str(value or "")
    return float(mapping.get(text, mapping.get("", 0)))


def _bool_feature(value: Any) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    text = str(value or "").strip().lower()
    if text in {"1", "true", "yes", "y"}:
        return 1.0
    if text in {"0", "false", "no", "n"}:
        return 0.0
    return 0.0


def _rank(value: int | None) -> float:
    return -1.0 if value is None else float(value)


def _pair(candidate: dict[str, Any]) -> tuple[int, int] | None:
    if candidate.get("task_i") is None or candidate.get("task_j") is None:
        return None
    try:
        i = int(candidate["task_i"])
        j = int(candidate["task_j"])
    except (TypeError, ValueError):
        return None
    if i <= 0 or j <= 0 or i == j:
        return None
    return tuple(sorted((i, j)))


def _candidate_key(candidate: dict[str, Any]) -> str | None:
    pair = _pair(candidate)
    if pair is None:
        return None
    return f"{pair[0]},{pair[1]}"


def _rank_map(candidates: Any) -> dict[str, int]:
    ranks: dict[str, int] = {}
    if not isinstance(candidates, list):
        return ranks
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, dict):
            continue
        key = _candidate_key(candidate)
        if key is not None and key not in ranks:
            ranks[key] = int(index)
    return ranks


def _candidate_union(event: dict[str, Any]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for field in ("priority_top", "top", "selected"):
        payload = event.get(field)
        candidates = payload if isinstance(payload, list) else [payload]
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            key = _candidate_key(candidate)
            if key is None:
                continue
            if key not in merged:
                merged[key] = dict(candidate)
            else:
                merged[key].update({k: v for k, v in candidate.items() if v is not None})
    return list(merged.values())


def _instance_path_from_log(log_path: Path) -> Path | None:
    text = str(log_path).replace("\\", "/")
    marker = "BPC_future/logical_graph/"
    offset = text.find(marker)
    if offset < 0:
        return None
    instance_text = text[offset:]
    if instance_text.endswith(".jsonl"):
        instance_text = instance_text[: -len(".jsonl")]
    candidate = Path(instance_text)
    if candidate.is_file():
        return candidate
    absolute = ROOT / candidate
    if absolute.is_file():
        return candidate
    return None


def _branch_feature_vector(
    event: dict[str, Any],
    candidate: dict[str, Any],
    *,
    rank_in_top: int | None,
    rank_in_priority_top: int | None,
) -> list[float]:
    relation = candidate.get("incumbent_relation")
    features = {
        "depth": _number(event.get("depth")),
        "candidate_count": _number(event.get("candidate_count")),
        "eligible_count": _number(event.get("eligible_count")),
        "has_candidate_log": 1.0,
        "branch_rank_in_top": _rank(rank_in_top),
        "branch_rank_in_priority_top": _rank(rank_in_priority_top),
        "same_mass": _number(candidate.get("same_mass")),
        "fractionality": _number(candidate.get("fractionality")),
        "support_count": _number(candidate.get("support_count")),
        "incumbent_relation_known": 1.0 if relation is not None else 0.0,
        "incumbent_relation_same": 1.0 if relation is True else 0.0,
        "incumbent_disagreement": _number(candidate.get("incumbent_disagreement")),
        "pool_same_allowed": _number(candidate.get("pool_same_allowed")),
        "pool_separate_allowed": _number(candidate.get("pool_separate_allowed")),
        "pool_max_child_width": _number(candidate.get("pool_max_child_width")),
        "pool_total_child_width": _number(candidate.get("pool_total_child_width")),
        "pool_balance_gap": _number(candidate.get("pool_balance_gap")),
    }
    return [float(features[name]) for name in BRANCH_IMPACT_FEATURE_SCHEMA]


def _context_feature_vector(
    event: dict[str, Any],
    candidate: dict[str, Any],
    *,
    rank_in_top: int | None,
    rank_in_priority_top: int | None,
) -> list[float]:
    pair = _pair(candidate) or (0, 0)
    selected = event.get("selected") if isinstance(event.get("selected"), dict) else {}
    selected_pair = _pair(selected) if isinstance(selected, dict) else None
    baseline_pair = selected_pair or pair
    phase2_best_rc = _number(candidate.get("phase2_best_reduced_cost"))
    return [
        _number(event.get("node_id")),
        _number(event.get("depth")),
        _number(event.get("time")),
        _number(event.get("candidate_count")),
        _number(event.get("eligible_count")),
        _rank(rank_in_top),
        _rank(rank_in_priority_top),
        _code(PHASED_TESTING_STAGE_CODES, candidate.get("phased_testing_stage")),
        _code(PHASED_TESTING_DECISION_CODES, candidate.get("phased_testing_decision")),
        _code(
            PHASED_TESTING_ELIMINATION_REASON_CODES,
            candidate.get("phased_testing_elimination_reason"),
        ),
        _bool_feature(candidate.get("phased_testing_phase0_passed")),
        _bool_feature(candidate.get("phased_testing_phase1_lp_complete")),
        _bool_feature(candidate.get("phased_testing_phase2_heuristic_complete")),
        float(baseline_pair[0]),
        float(baseline_pair[1]),
        float(pair[0]),
        float(pair[1]),
        _number(candidate.get("phase1_min_child_lp_gain")),
        _number(candidate.get("phase1_child_lp_gain_product")),
        _number(candidate.get("phase1_child_width_balance")),
        _number(candidate.get("phase1_wall_time")),
        _number(candidate.get("phase1_dynamic_k_probe_count")),
        _number(candidate.get("phase2_negative_child_count")),
        _number(candidate.get("phase2_negative_journey_count")),
        phase2_best_rc,
        _number(candidate.get("phase2_worst_negative_severity")),
        _number(candidate.get("phase2_wall_time")),
        _number(candidate.get("phase2_dynamic_k_probe_count")),
    ]


def _score_key(pair: tuple[int, int], *, node_id: int | None, depth: int | None) -> str:
    pair_text = f"{pair[0]},{pair[1]}"
    if node_id is not None and depth is not None:
        return f"node:{int(node_id)}:depth:{int(depth)}:{pair_text}"
    if depth is not None:
        return f"depth:{int(depth)}:{pair_text}"
    if node_id is not None:
        return f"node:{int(node_id)}:{pair_text}"
    return pair_text


def _scoped_score_key(instance: Path, key: str) -> str:
    return f"{str(instance).replace(chr(92), '/')}|{key}"


def _branch_constraints_from_event(event: dict[str, Any]) -> list[str] | None:
    constraints = event.get("branch_constraints")
    if constraints is None:
        return None
    if isinstance(constraints, str):
        text = constraints.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return [text]
        constraints = parsed
    if isinstance(constraints, (list, tuple)):
        return [str(item) for item in constraints if str(item)]
    return [str(constraints)]


def _branch_state_key_from_event(event: dict[str, Any]) -> str | None:
    value = event.get("branch_state_key")
    if value not in (None, ""):
        return str(value)
    constraints = _branch_constraints_from_event(event)
    if constraints is not None:
        return ";".join(constraints) if constraints else "root"
    try:
        depth = int(event.get("depth"))
    except (TypeError, ValueError):
        return None
    return "root" if depth == 0 else None


def _state_score_key(branch_state_key: str | None, key: str) -> str | None:
    if not branch_state_key:
        return None
    return f"state:{branch_state_key}::{key}"


def _load_model(checkpoint_path: Path, device: torch.device) -> GATBranchImpactModel:
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    config = dict(checkpoint.get("model_config") or {})
    model = GATBranchImpactModel(**config)
    state_dict = checkpoint["model_state_dict"]
    model.load_state_dict(state_dict, strict=False)
    setattr(
        model,
        "_branch_action_has_walltime_head",
        any(str(key).startswith("walltime_gain_head.") for key in state_dict),
    )
    setattr(
        model,
        "_branch_action_has_tree_policy_head",
        any(str(key).startswith("tree_policy_head.") for key in state_dict),
    )
    model.to(device)
    model.eval()
    return model


def _walltime_score(predicted_walltime_gain: float) -> float:
    return float(torch.sigmoid(torch.tensor(float(predicted_walltime_gain) / 100.0)).item())


def _branch_score_from_output(
    *,
    probability: float,
    predicted_walltime_gain: float | None,
    tree_policy_probability: float | None,
    score_mode: str,
) -> float:
    mode = str(score_mode or "branch_probability")
    if mode == "tree_policy" and tree_policy_probability is not None:
        return float(tree_policy_probability)
    if predicted_walltime_gain is None:
        return float(probability)
    gain_score = _walltime_score(float(predicted_walltime_gain))
    if mode == "walltime_gain":
        return float(gain_score)
    if mode == "hybrid":
        return float(0.7 * float(probability) + 0.3 * float(gain_score))
    return float(probability)


def export_score_map(
    *,
    checkpoint: Path,
    logs: list[Path],
    output_dir: Path,
    report: Path,
    device_name: str,
    max_events_per_log: int = 0,
    max_candidates_per_event: int = 0,
    min_probability: float = 0.0,
    score_mode: str = "branch_probability",
) -> dict[str, Any]:
    device = torch.device(device_name)
    model = _load_model(checkpoint, device)
    builder = FutureGraphBuilder()
    graph_cache: dict[str, Any] = {}
    score_rows: list[dict[str, Any]] = []
    skipped: Counter[str] = Counter()
    log_files = list(_iter_jsonl_files(logs))

    for log_path in log_files:
        instance_path = _instance_path_from_log(log_path)
        if instance_path is None:
            skipped["log_without_instance_path"] += 1
            continue
        graph = graph_cache.get(str(instance_path))
        if graph is None:
            try:
                graph = builder.build_from_json(instance_path)
            except Exception:
                skipped["invalid_instance_graph"] += 1
                continue
            graph_cache[str(instance_path)] = graph
        task_ids = [int(value) for value in graph.task_ids.tolist()]
        task_to_index = {task_id: index for index, task_id in enumerate(task_ids)}
        event_count = 0
        for event_index, event in enumerate(_iter_jsonl(log_path)):
            if event.get("event") != "journey_branch_candidates":
                continue
            event_count += 1
            if max_events_per_log and event_count > int(max_events_per_log):
                skipped["max_events_per_log_reached"] += 1
                break
            top_rank = _rank_map(event.get("top"))
            priority_rank = _rank_map(event.get("priority_top"))
            for candidate in _candidate_union(event):
                pair = _pair(candidate)
                if pair is None:
                    skipped["invalid_candidate_pair"] += 1
                    continue
                if pair[0] not in task_to_index or pair[1] not in task_to_index:
                    skipped["pair_task_missing_from_graph"] += 1
                    continue
                key = f"{pair[0]},{pair[1]}"
                rank_in_top = top_rank.get(key)
                rank_in_priority_top = priority_rank.get(key)
                if str(score_mode or "") == "tree_policy":
                    feature_rank_in_top = 0
                    feature_rank_in_priority_top = 0
                else:
                    feature_rank_in_top = rank_in_top
                    feature_rank_in_priority_top = rank_in_priority_top
                if int(max_candidates_per_event) > 0:
                    ranks = [
                        int(rank)
                        for rank in (rank_in_top, rank_in_priority_top)
                        if rank is not None
                    ]
                    if not ranks or min(ranks) >= int(max_candidates_per_event):
                        skipped["candidate_rank_above_cap"] += 1
                        continue
                sample = graph.clone()
                sample.branch_pair_indices = torch.tensor(
                    [[task_to_index[pair[0]], task_to_index[pair[1]]]],
                    dtype=torch.long,
                )
                sample.branch_pair_features = torch.tensor(
                    [
                        _branch_feature_vector(
                            event,
                            candidate,
                            rank_in_top=feature_rank_in_top,
                            rank_in_priority_top=feature_rank_in_priority_top,
                        )
                    ],
                    dtype=torch.float32,
                )
                sample.context_features = torch.tensor(
                    _context_feature_vector(
                        event,
                        candidate,
                        rank_in_top=feature_rank_in_top,
                        rank_in_priority_top=feature_rank_in_priority_top,
                    ),
                    dtype=torch.float32,
                )
                sample = sample.to(device)
                with torch.no_grad():
                    output = model(
                        sample,
                        sample.branch_pair_indices,
                        sample.branch_pair_features,
                        sample.context_features,
                    )
                probability = float(output["branch_priority_probability"].view(-1)[0].detach().cpu())
                logit = float(output["branch_priority_logit"].view(-1)[0].detach().cpu())
                tail_probability = float(output["tail_improved_probability"].view(-1)[0].detach().cpu())
                predicted_walltime_gain = (
                    float(output["predicted_walltime_gain"].view(-1)[0].detach().cpu())
                    if bool(getattr(model, "_branch_action_has_walltime_head", False))
                    else None
                )
                predicted_child_proof_cpu = (
                    float(output["predicted_child_proof_cpu"].view(-1)[0].detach().cpu())
                    if bool(getattr(model, "_branch_action_has_walltime_head", False))
                    else None
                )
                predicted_time_to_certificate = (
                    float(output["predicted_time_to_certificate"].view(-1)[0].detach().cpu())
                    if bool(getattr(model, "_branch_action_has_walltime_head", False))
                    else None
                )
                tree_policy_probability = (
                    float(output["tree_policy_probability"].view(-1)[0].detach().cpu())
                    if bool(getattr(model, "_branch_action_has_tree_policy_head", False))
                    else None
                )
                if probability < float(min_probability):
                    skipped["below_min_probability"] += 1
                    continue
                final_score = _branch_score_from_output(
                    probability=probability,
                    predicted_walltime_gain=predicted_walltime_gain,
                    tree_policy_probability=tree_policy_probability,
                    score_mode=score_mode,
                )
                node_id = None if event.get("node_id") is None else int(event.get("node_id"))
                depth = None if event.get("depth") is None else int(event.get("depth"))
                row_key = _score_key(pair, node_id=node_id, depth=depth)
                branch_constraints = _branch_constraints_from_event(event)
                branch_state_key = _branch_state_key_from_event(event)
                state_key = _state_score_key(branch_state_key, row_key)
                score_rows.append(
                    {
                        "schema_version": "gat_branch_action_score_row_v1",
                        "diagnostic_only": True,
                        "production_ready": False,
                        "official_bound_effect": False,
                        "certificate_effect": False,
                        "pricing_oracle": False,
                        "branching_oracle": False,
                        "instance": str(instance_path),
                        "source_log_file": str(log_path),
                        "instance_key": str(instance_path).replace("\\", "/"),
                        "event_index": int(event_index),
                        "node_id": node_id,
                        "depth": depth,
                        "pair": [int(pair[0]), int(pair[1])],
                        "task_i": int(pair[0]),
                        "task_j": int(pair[1]),
                        "key": row_key,
                        "scoped_key": _scoped_score_key(instance_path, row_key),
                        "state_key": state_key,
                        "state_scoped_key": (
                            None if state_key is None else _scoped_score_key(instance_path, state_key)
                        ),
                        "branch_constraints": branch_constraints,
                        "branch_state_key": branch_state_key,
                        "score": final_score,
                        "gat_score": final_score,
                        "predicted_score": final_score,
                        "branch_score": final_score,
                        "score_mode": str(score_mode),
                        "branch_priority_probability": probability,
                        "branch_priority_logit": logit,
                        "tail_improved_probability": tail_probability,
                        "predicted_walltime_gain": predicted_walltime_gain,
                        "predicted_child_proof_cpu": predicted_child_proof_cpu,
                        "predicted_time_to_certificate": predicted_time_to_certificate,
                        "tree_policy_probability": tree_policy_probability,
                        "candidate_count": event.get("candidate_count"),
                        "eligible_count": event.get("eligible_count"),
                        "effective_eligible_count": event.get("effective_eligible_count"),
                        "max_fractionality": event.get("max_fractionality"),
                        "rank_in_top": rank_in_top,
                        "rank_in_priority_top": rank_in_priority_top,
                        "priority_mode": event.get("priority_mode"),
                        "candidate": candidate,
                    }
                )

    score_rows.sort(
        key=lambda row: (
            str(row["instance"]),
            int(row["node_id"] if row["node_id"] is not None else -1),
            int(row["depth"] if row["depth"] is not None else -1),
            -float(row["score"]),
            int(row["task_i"]),
            int(row["task_j"]),
        )
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    rows_json = output_dir / "journey_branch_score_rows.json"
    rows_jsonl = output_dir / "journey_branch_score_rows.jsonl"
    rows_json.write_text(json.dumps(score_rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    rows_jsonl.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in score_rows),
        encoding="utf-8",
    )
    audit_map: dict[str, float] = {}
    for row in score_rows:
        audit_map[f"{row['instance']}|{row['key']}"] = float(row["score"])
        if row.get("state_key"):
            audit_map[f"{row['instance']}|{row['state_key']}"] = float(row["score"])
    (output_dir / "journey_branch_score_map.json").write_text(
        json.dumps(audit_map, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    instance_count = len({str(row["instance"]) for row in score_rows})
    summary = {
        "schema_version": "gat_branch_action_score_map_summary_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "official_bound_effect": False,
        "certificate_effect": False,
        "pricing_oracle": False,
        "branching_oracle": False,
        "production_ready": False,
        "checkpoint": str(checkpoint),
        "input_paths": [str(path) for path in logs],
        "resolved_log_file_count": len(log_files),
        "output_dir": str(output_dir),
        "solver_score_path": str(rows_json),
        "score_row_count": len(score_rows),
        "score_instance_count": int(instance_count),
        "min_probability": float(min_probability),
        "score_mode": str(score_mode),
        "has_walltime_regression_head": bool(getattr(model, "_branch_action_has_walltime_head", False)),
        "has_tree_policy_head": bool(getattr(model, "_branch_action_has_tree_policy_head", False)),
        "max_events_per_log": int(max_events_per_log),
        "max_candidates_per_event": int(max_candidates_per_event),
        "skipped_counts": dict(sorted(skipped.items())),
        "branch_feature_schema": list(BRANCH_IMPACT_FEATURE_SCHEMA),
        "context_feature_schema": list(BRANCH_ACTION_CONTEXT_FEATURE_SCHEMA),
        "score_min": min((float(row["score"]) for row in score_rows), default=None),
        "score_max": max((float(row["score"]) for row in score_rows), default=None),
        "score_mean": (
            sum(float(row["score"]) for row in score_rows) / float(len(score_rows))
            if score_rows
            else None
        ),
        "state_key_row_count": sum(1 for row in score_rows if row.get("state_key")),
        "branch_state_count": len({str(row.get("branch_state_key")) for row in score_rows if row.get("branch_state_key")}),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(report, summary, score_rows)
    return summary


def _write_report(report: Path, summary: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GAT Branch/Action Score Map",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 目的",
        "",
        "用已训练的 branch/action GAT checkpoint 对既有 `journey_branch_candidates` 日志离线打分，导出 solver 可 opt-in 读取的 branch score rows。",
        "",
        "## 机器字段",
        "",
        "```text",
    ]
    for key in [
        "checkpoint",
        "resolved_log_file_count",
        "score_row_count",
        "score_instance_count",
        "solver_score_path",
        "score_mode",
        "has_walltime_regression_head",
        "has_tree_policy_head",
        "max_candidates_per_event",
        "state_key_row_count",
        "branch_state_count",
        "score_min",
        "score_max",
        "score_mean",
        "skipped_counts",
        "runs_bpc_or_pricing",
        "official_bound_effect",
        "certificate_effect",
        "pricing_oracle",
        "branching_oracle",
        "production_ready",
    ]:
        lines.append(f"{key} = {summary.get(key)}")
    lines.extend(["```", "", "## Top Rows", ""])
    for row in sorted(rows, key=lambda item: float(item.get("score") or 0.0), reverse=True)[:12]:
        lines.append(
            "- "
            f"instance={Path(str(row['instance'])).name} node={row.get('node_id')} "
            f"depth={row.get('depth')} state={row.get('branch_state_key')} "
            f"pair={row.get('pair')} score={row.get('score'):.6f}"
        )
    lines.extend(
        [
            "",
            "## 使用边界",
            "",
            "`solver_score_path` 应作为 `journey_branch_candidate_score_path` 使用；不要使用无上下文聚合 map 作为生产配置。",
            "这些分数只改变 opt-in 的 Ryan-Foster pair 排序；所有下界、剪枝和 OPTIMAL 证书仍由 exact pricing / BPC 逻辑产生。",
        ]
    )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("logs", nargs="+", type=Path)
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--max-events-per-log", type=int, default=0)
    parser.add_argument("--max-candidates-per-event", type=int, default=0)
    parser.add_argument("--min-probability", type=float, default=0.0)
    parser.add_argument(
        "--score-mode",
        choices=("branch_probability", "walltime_gain", "hybrid", "tree_policy"),
        default="branch_probability",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = export_score_map(
        checkpoint=args.checkpoint,
        logs=list(args.logs),
        output_dir=args.output_dir,
        report=args.report,
        device_name=str(args.device),
        max_events_per_log=max(0, int(args.max_events_per_log)),
        max_candidates_per_event=max(0, int(args.max_candidates_per_event)),
        min_probability=float(args.min_probability),
        score_mode=str(args.score_mode),
    )
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["score_row_count"] > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
