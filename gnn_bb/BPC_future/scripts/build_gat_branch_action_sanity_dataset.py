#!/usr/bin/env python3
"""Build a small exact-boundary-safe GAT dataset for branch/action sanity training.

The dataset consumes completed Journey branch counterfactual delta rows. It is
offline and diagnostic-only: it does not run BPC, pricing, RMP, or certificates,
and it does not make any pruning decision. The main branch-priority target is a
continuous wall-time improvement signal. The 200-second target wall is retained
as an acceptance metric, not as a hard training discontinuity.
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

from BPC_future.learning.graph_builder import FutureGraphBuilder
from BPC_future.scripts.audit_journey_branch_impact import BRANCH_IMPACT_FEATURE_SCHEMA


DEFAULT_OUTPUT_DIR = Path("BPC_future/data/gat_branch_action_sanity/v244_20260624")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260624_bpc_future_gat_branch_action_sanity_dataset_v244_zh.md"
)

ROW_FILENAME = "branch_counterfactual_delta_rows.jsonl"

BRANCH_ACTION_CONTEXT_FEATURE_SCHEMA: tuple[str, ...] = (
    "node_id",
    "depth",
    "branch_time",
    "candidate_count",
    "eligible_count",
    "branch_rank_in_top",
    "branch_rank_in_priority_top",
    "baseline_task_i",
    "baseline_task_j",
    "alternative_task_i",
    "alternative_task_j",
)

BRANCH_ACTION_LABEL_SCHEMA: tuple[str, ...] = (
    "y_branch_priority_walltime_gain",
    "branch_priority_loss_weight",
    "capped_wall_time_delta",
    "capped_wall_time_delta_ratio",
    "y_target_wall_crossing_positive",
    "y_strict_full_replay_positive",
    "y_weak_positive_not_target",
    "y_counterfactual_regression",
    "y_timeout_regression",
    "y_timeout_resolved",
    "y_tail_improved_aux",
    "tail_improved_loss_weight",
)


def _float(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return float(default)
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float(default)
    if parsed != parsed:
        return float(default)
    return float(parsed)


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _label(row: dict[str, Any], name: str) -> float:
    labels = row.get("labels")
    if not isinstance(labels, dict):
        return 0.0
    return _float(labels.get(name))


def _iter_row_files(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if path.is_dir():
            candidate = path / ROW_FILENAME
            if candidate.exists():
                yield candidate
        elif path.name == "summary.json":
            candidate = path.parent / ROW_FILENAME
            if candidate.exists():
                yield candidate
        elif path.is_file():
            yield path


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _pair(value: Any) -> tuple[int, int] | None:
    if isinstance(value, (list, tuple)) and len(value) == 2:
        left = _int(value[0], -1)
        right = _int(value[1], -1)
        if left > 0 and right > 0 and left != right:
            return left, right
    return None


def _time_window_family(value: Any) -> str:
    text = str(value or "")
    for token in ("greedy-anchor", "random-wave", "sector-wave"):
        if token in text:
            return token
    return ""


def _raw(row: dict[str, Any], key: str) -> dict[str, Any]:
    payload = row.get(key)
    return payload if isinstance(payload, dict) else {}


def _is_strict_full_replay_positive(row: dict[str, Any]) -> bool:
    if str(row.get("counterfactual_label_type") or "") != "strong_positive":
        return False
    if bool(row.get("right_censored_counterfactual")):
        return False
    if row.get("alternative_forced_pair_matched") is False:
        return False
    return str(row.get("alternative_status") or "") == "OPTIMAL"


def _is_target_200_positive(row: dict[str, Any], *, target_wall: float) -> bool:
    if bool(row.get("right_censored_counterfactual")):
        return False
    if row.get("alternative_forced_pair_matched") is False:
        return False
    return bool(
        str(row.get("alternative_status") or "") == "OPTIMAL"
        and _float(row.get("alternative_wall_time")) <= float(target_wall)
        and _float(row.get("baseline_wall_time")) > float(target_wall)
    )


def _status(row: dict[str, Any], prefix: str) -> str:
    return str(row.get(f"{prefix}_status") or "")


def _effective_wall(row: dict[str, Any], prefix: str, *, wall_cap: float) -> float:
    wall = _float(row.get(f"{prefix}_wall_time"), default=float(wall_cap))
    if wall <= 0.0:
        wall = float(wall_cap)
    if _status(row, prefix) != "OPTIMAL":
        wall = max(wall, float(wall_cap))
    return min(float(wall), float(wall_cap))


def _wall_time_delta(row: dict[str, Any], *, wall_cap: float) -> float:
    return _effective_wall(row, "alternative", wall_cap=wall_cap) - _effective_wall(
        row,
        "baseline",
        wall_cap=wall_cap,
    )


def _is_walltime_gain_positive(
    row: dict[str, Any],
    *,
    wall_cap: float,
    min_wall_improvement: float,
) -> bool:
    if bool(row.get("right_censored_counterfactual")):
        return False
    if row.get("alternative_forced_pair_matched") is False:
        return False
    if _status(row, "alternative") != "OPTIMAL":
        return False
    return _wall_time_delta(row, wall_cap=wall_cap) <= -float(min_wall_improvement)


def _is_regression(row: dict[str, Any]) -> bool:
    return bool(
        str(row.get("counterfactual_label_type") or "") == "regression"
        or _label(row, "y_counterfactual_regression") > 0.5
        or _label(row, "y_counterfactual_timeout_regression") > 0.5
    )


def _is_walltime_regression(
    row: dict[str, Any],
    *,
    wall_cap: float,
    min_wall_regression: float,
) -> bool:
    if bool(row.get("right_censored_counterfactual")):
        return False
    if row.get("alternative_forced_pair_matched") is False:
        return False
    if _is_regression(row):
        return True
    return _wall_time_delta(row, wall_cap=wall_cap) >= float(min_wall_regression)


def _branch_feature_vector(row: dict[str, Any]) -> list[float]:
    alt_raw = _raw(row, "alternative_raw_row")
    vector = alt_raw.get("branch_feature_vector")
    if isinstance(vector, list) and len(vector) == len(BRANCH_IMPACT_FEATURE_SCHEMA):
        return [_float(value) for value in vector]
    candidate_count = _float(alt_raw.get("candidate_count"))
    eligible_count = _float(alt_raw.get("eligible_count"))
    return [
        _float(row.get("depth")),
        candidate_count,
        eligible_count,
        1.0 if alt_raw else 0.0,
        _float(alt_raw.get("branch_rank_in_top")),
        _float(alt_raw.get("branch_rank_in_priority_top")),
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
    ]


def _context_feature_vector(row: dict[str, Any]) -> list[float]:
    alt_raw = _raw(row, "alternative_raw_row")
    baseline_pair = _pair(row.get("baseline_pair")) or (0, 0)
    alternative_pair = _pair(row.get("alternative_pair")) or (0, 0)
    return [
        _float(row.get("node_id")),
        _float(row.get("depth")),
        _float(alt_raw.get("branch_time")),
        _float(alt_raw.get("candidate_count")),
        _float(alt_raw.get("eligible_count")),
        _float(alt_raw.get("branch_rank_in_top")),
        _float(alt_raw.get("branch_rank_in_priority_top")),
        float(baseline_pair[0]),
        float(baseline_pair[1]),
        float(alternative_pair[0]),
        float(alternative_pair[1]),
    ]


def _row_kind(
    row: dict[str, Any],
    *,
    target_wall: float,
    wall_cap: float,
    min_wall_improvement: float,
    min_wall_regression: float,
) -> str:
    strict_positive = _is_strict_full_replay_positive(row)
    target_positive = _is_target_200_positive(row, target_wall=target_wall)
    wall_positive = _is_walltime_gain_positive(
        row,
        wall_cap=wall_cap,
        min_wall_improvement=min_wall_improvement,
    )
    regression = _is_walltime_regression(
        row,
        wall_cap=wall_cap,
        min_wall_regression=min_wall_regression,
    )
    if wall_positive:
        if target_positive:
            return "walltime_gain_target_wall_crossing"
        return "walltime_gain_positive"
    if target_positive:
        return "target_wall_crossing_positive"
    if strict_positive:
        return "weak_positive_not_target"
    if regression:
        return "hard_negative_regression"
    if str(row.get("counterfactual_label_type") or "") == "local_only_hard_negative":
        return "local_only_hard_negative"
    return str(row.get("counterfactual_label_type") or "unsupported")


def _labels(
    row: dict[str, Any],
    *,
    target_wall: float,
    wall_cap: float,
    min_wall_improvement: float,
    min_wall_regression: float,
    max_delta_weight: float,
) -> dict[str, float]:
    target_positive = _is_target_200_positive(row, target_wall=target_wall)
    strict_positive = _is_strict_full_replay_positive(row)
    delta = _wall_time_delta(row, wall_cap=wall_cap)
    delta_ratio = delta / max(float(wall_cap), 1.0e-6)
    wall_positive = _is_walltime_gain_positive(
        row,
        wall_cap=wall_cap,
        min_wall_improvement=min_wall_improvement,
    )
    regression = _is_walltime_regression(
        row,
        wall_cap=wall_cap,
        min_wall_regression=min_wall_regression,
    )
    weak_positive = bool(strict_positive and not target_positive)
    magnitude_weight = min(
        float(max_delta_weight),
        max(1.0, abs(delta) / max(float(min_wall_improvement), 1.0)),
    )
    main_weight = magnitude_weight if wall_positive or regression else 0.0
    tail_weight = 1.0 if strict_positive or regression else 0.0
    return {
        "y_branch_priority_walltime_gain": 1.0 if wall_positive else 0.0,
        "branch_priority_loss_weight": main_weight,
        "capped_wall_time_delta": float(delta),
        "capped_wall_time_delta_ratio": float(delta_ratio),
        "y_target_wall_crossing_positive": 1.0 if target_positive else 0.0,
        "y_strict_full_replay_positive": 1.0 if strict_positive else 0.0,
        "y_weak_positive_not_target": 1.0 if weak_positive else 0.0,
        "y_counterfactual_regression": 1.0 if regression else 0.0,
        "y_timeout_regression": 1.0 if bool(row.get("timeout_regression")) else 0.0,
        "y_timeout_resolved": 1.0 if bool(row.get("timeout_resolved")) else 0.0,
        "y_tail_improved_aux": 1.0 if strict_positive else 0.0,
        "tail_improved_loss_weight": tail_weight,
    }


def _sample_allowed(
    row: dict[str, Any],
    *,
    wall_cap: float,
    min_wall_improvement: float,
    min_wall_regression: float,
) -> bool:
    return bool(
        _is_strict_full_replay_positive(row)
        or _is_walltime_gain_positive(
            row,
            wall_cap=wall_cap,
            min_wall_improvement=min_wall_improvement,
        )
        or (
            _is_walltime_regression(
                row,
                wall_cap=wall_cap,
                min_wall_regression=min_wall_regression,
            )
            and not bool(row.get("right_censored_counterfactual"))
            and row.get("alternative_forced_pair_matched") is not False
        )
    )


def _feature_stats(sample_dir: Path, attr_name: str) -> tuple[list[float], list[float]]:
    tensors = []
    for path in sorted(sample_dir.glob("sample_*.pt")):
        sample = torch.load(path, map_location="cpu", weights_only=False)
        value = getattr(sample, attr_name)
        if value.dim() == 1:
            value = value.unsqueeze(0)
        tensors.append(value.to(dtype=torch.float32))
    if not tensors:
        return [], []
    stacked = torch.cat(tensors, dim=0)
    mean = stacked.mean(dim=0)
    std = stacked.std(dim=0, unbiased=False).clamp_min(1.0e-6)
    return [float(value) for value in mean.tolist()], [float(value) for value in std.tolist()]


def build_dataset(
    inputs: list[Path],
    output_dir: Path,
    report: Path,
    *,
    target_wall: float = 200.0,
    wall_cap: float = 600.0,
    min_wall_improvement: float = 5.0,
    min_wall_regression: float = 5.0,
    max_delta_weight: float = 4.0,
    max_rows: int = 0,
) -> dict[str, Any]:
    row_files = list(_iter_row_files(inputs))
    rows: list[dict[str, Any]] = []
    for path in row_files:
        rows.extend(_read_jsonl(path))

    sample_dir = output_dir / "samples"
    sample_dir.mkdir(parents=True, exist_ok=True)
    for stale in sample_dir.glob("sample_*.pt"):
        stale.unlink()

    builder = FutureGraphBuilder()
    graph_cache: dict[str, Any] = {}
    samples: list[dict[str, Any]] = []
    skipped: Counter[str] = Counter()
    row_kind_counts: Counter[str] = Counter()
    main_label_counts: Counter[str] = Counter()
    target_wall_crossing_counts: Counter[str] = Counter()
    aux_label_counts: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    instance_counts: Counter[str] = Counter()

    for row_index, row in enumerate(rows):
        row_kind = _row_kind(
            row,
            target_wall=target_wall,
            wall_cap=wall_cap,
            min_wall_improvement=min_wall_improvement,
            min_wall_regression=min_wall_regression,
        )
        row_kind_counts[row_kind] += 1
        if not _sample_allowed(
            row,
            wall_cap=wall_cap,
            min_wall_improvement=min_wall_improvement,
            min_wall_regression=min_wall_regression,
        ):
            skipped[f"not_training_sample:{row_kind}"] += 1
            continue
        if max_rows and len(samples) >= int(max_rows):
            skipped["max_rows_reached"] += 1
            break
        instance_path = Path(str(row.get("instance") or ""))
        if not instance_path.is_file():
            skipped["missing_instance_file"] += 1
            continue
        alternative_pair = _pair(row.get("alternative_pair"))
        if alternative_pair is None:
            skipped["invalid_alternative_pair"] += 1
            continue
        graph = graph_cache.get(str(instance_path))
        if graph is None:
            try:
                graph = builder.build_from_json(instance_path)
            except Exception:
                skipped["invalid_logical_graph"] += 1
                continue
            graph_cache[str(instance_path)] = graph
        task_ids = [int(value) for value in graph.task_ids.tolist()]
        task_to_index = {task_id: idx for idx, task_id in enumerate(task_ids)}
        if alternative_pair[0] not in task_to_index or alternative_pair[1] not in task_to_index:
            skipped["pair_task_missing_from_graph"] += 1
            continue
        label_values = _labels(
            row,
            target_wall=target_wall,
            wall_cap=wall_cap,
            min_wall_improvement=min_wall_improvement,
            min_wall_regression=min_wall_regression,
            max_delta_weight=max_delta_weight,
        )
        sample = graph.clone()
        sample.branch_pair_indices = torch.tensor(
            [[task_to_index[alternative_pair[0]], task_to_index[alternative_pair[1]]]],
            dtype=torch.long,
        )
        sample.branch_pair_task_ids = torch.tensor([list(alternative_pair)], dtype=torch.long)
        sample.branch_pair_features = torch.tensor(
            [_branch_feature_vector(row)],
            dtype=torch.float32,
        )
        sample.branch_action_context_features = torch.tensor(
            _context_feature_vector(row),
            dtype=torch.float32,
        )
        sample.context_features = sample.branch_action_context_features
        sample.y_branch_priority = torch.tensor(
            [label_values["y_branch_priority_walltime_gain"]],
            dtype=torch.float32,
        )
        sample.branch_priority_loss_weight = torch.tensor(
            [label_values["branch_priority_loss_weight"]],
            dtype=torch.float32,
        )
        sample.y_tail_improved = torch.tensor(
            [label_values["y_tail_improved_aux"]],
            dtype=torch.float32,
        )
        sample.tail_improved_loss_weight = torch.tensor(
            [label_values["tail_improved_loss_weight"]],
            dtype=torch.float32,
        )
        sample.branch_action_labels = torch.tensor(
            [[label_values[name] for name in BRANCH_ACTION_LABEL_SCHEMA]],
            dtype=torch.float32,
        )
        sample.branch_action_row_kind = row_kind
        sample.branch_action_instance = str(instance_path)
        sample.branch_action_experiment = str(row.get("experiment") or "")
        sample.branch_action_context_key = "|".join(
            [
                str(row.get("instance") or ""),
                str(row.get("node_id") if row.get("node_id") is not None else ""),
                str(row.get("depth") if row.get("depth") is not None else ""),
                str(row.get("baseline_pair") or ""),
            ]
        )

        sample_name = f"sample_{len(samples):06d}.pt"
        torch.save(sample, sample_dir / sample_name)
        main_label = "walltime_gain_positive" if label_values["y_branch_priority_walltime_gain"] > 0.5 else "not_walltime_gain"
        if label_values["branch_priority_loss_weight"] <= 0.0:
            main_label = "aux_only_weak_positive"
        main_label_counts[main_label] += 1
        target_wall_crossing_counts[
            "target_wall_crossing_positive"
            if label_values["y_target_wall_crossing_positive"] > 0.5
            else "not_target_wall_crossing"
        ] += 1
        aux_label_counts["tail_improved" if label_values["y_tail_improved_aux"] > 0.5 else "tail_not_improved"] += 1
        family = _time_window_family(instance_path)
        family_counts[family] += 1
        instance_counts[str(instance_path)] += 1
        samples.append(
            {
                "path": f"samples/{sample_name}",
                "source_row_index": int(row_index),
                "row_kind": row_kind,
                "instance": str(instance_path),
                "time_window_family": family,
                "experiment": str(row.get("experiment") or ""),
                "node_id": row.get("node_id"),
                "depth": row.get("depth"),
                "baseline_pair": row.get("baseline_pair"),
                "alternative_pair": list(alternative_pair),
                "branch_priority_label": main_label,
                "branch_priority_loss_weight": label_values["branch_priority_loss_weight"],
                "capped_wall_time_delta": label_values["capped_wall_time_delta"],
                "target_wall_crossing_positive": label_values["y_target_wall_crossing_positive"] > 0.5,
                "tail_improved_aux": label_values["y_tail_improved_aux"],
            }
        )

    branch_feature_mean, branch_feature_std = _feature_stats(sample_dir, "branch_pair_features")
    context_feature_mean, context_feature_std = _feature_stats(sample_dir, "branch_action_context_features")
    manifest = {
        "schema_version": "gat_branch_action_sanity_dataset_manifest_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "official_bound_effect": False,
        "certificate_effect": False,
        "production_ready": False,
        "target_wall": float(target_wall),
        "wall_cap": float(wall_cap),
        "min_wall_improvement": float(min_wall_improvement),
        "min_wall_regression": float(min_wall_regression),
        "max_delta_weight": float(max_delta_weight),
        "input_paths": [str(path) for path in inputs],
        "resolved_row_files": [str(path) for path in row_files],
        "output_dir": str(output_dir),
        "sample_count": len(samples),
        "raw_row_count": len(rows),
        "skipped_counts": dict(sorted(skipped.items())),
        "row_kind_counts": dict(sorted(row_kind_counts.items())),
        "branch_priority_label_counts": dict(sorted(main_label_counts.items())),
        "target_wall_crossing_label_counts": dict(sorted(target_wall_crossing_counts.items())),
        "tail_improved_aux_label_counts": dict(sorted(aux_label_counts.items())),
        "instance_counts": dict(sorted(instance_counts.items())),
        "family_counts": dict(sorted(family_counts.items())),
        "branch_feature_schema": list(BRANCH_IMPACT_FEATURE_SCHEMA),
        "context_feature_schema": list(BRANCH_ACTION_CONTEXT_FEATURE_SCHEMA),
        "label_schema": list(BRANCH_ACTION_LABEL_SCHEMA),
        "branch_feature_mean": branch_feature_mean,
        "branch_feature_std": branch_feature_std,
        "context_feature_mean": context_feature_mean,
        "context_feature_std": context_feature_std,
        "label_semantics": {
            "y_branch_priority_walltime_gain": (
                "1 when the forced branch full replay reaches OPTIMAL and improves capped wall time "
                "by at least min_wall_improvement"
            ),
            "branch_priority_loss_weight": (
                "capped wall-time magnitude weight for wall-time positives and regressions"
            ),
            "y_target_wall_crossing_positive": (
                "acceptance metric: alternative reaches OPTIMAL within target_wall from a baseline over target_wall"
            ),
            "y_strict_full_replay_positive": (
                "auxiliary full-replay improvement label; may still be over target_wall"
            ),
            "y_weak_positive_not_target": (
                "strict full-replay improvement that did not reach target_wall"
            ),
            "y_counterfactual_regression": "full-run regression / timeout regression label",
        },
        "exactness_contract": {
            "scheduler_only": True,
            "pricing_oracle": False,
            "branching_oracle": False,
            "certificate_source": False,
            "official_bound_effect": False,
            "can_prune_branch_candidates": False,
            "can_permanently_discard_true_rc_negative": False,
            "default_solver_effect": False,
        },
        "samples": samples,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "manifest.json", manifest)
    summary = {
        "schema_version": "gat_branch_action_sanity_dataset_summary_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "official_bound_effect": False,
        "certificate_effect": False,
        "production_ready": False,
        "target_wall": float(target_wall),
        "wall_cap": float(wall_cap),
        "min_wall_improvement": float(min_wall_improvement),
        "min_wall_regression": float(min_wall_regression),
        "max_delta_weight": float(max_delta_weight),
        "output_dir": str(output_dir),
        "sample_count": len(samples),
        "raw_row_count": len(rows),
        "row_kind_counts": dict(sorted(row_kind_counts.items())),
        "skipped_counts": dict(sorted(skipped.items())),
        "branch_priority_label_counts": dict(sorted(main_label_counts.items())),
        "target_wall_crossing_label_counts": dict(sorted(target_wall_crossing_counts.items())),
        "tail_improved_aux_label_counts": dict(sorted(aux_label_counts.items())),
        "instance_count": len(instance_counts),
        "family_count": len([key for key in family_counts if key]),
        "branch_feature_schema": list(BRANCH_IMPACT_FEATURE_SCHEMA),
        "context_feature_schema": list(BRANCH_ACTION_CONTEXT_FEATURE_SCHEMA),
        "label_schema": list(BRANCH_ACTION_LABEL_SCHEMA),
        "sanity_training_dataset_ready": bool(
            main_label_counts.get("walltime_gain_positive", 0) > 0
            and main_label_counts.get("not_walltime_gain", 0) > 0
        ),
        "serious_training_dataset_ready": False,
        "optin_training_dataset_ready": False,
    }
    _write_json(output_dir / "summary.json", summary)
    _write_report(report, summary, manifest)
    return summary


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_report(report: Path, summary: dict[str, Any], manifest: dict[str, Any]) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GAT Branch/Action Sanity Dataset",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 目的",
        "",
        "把已完成 branch counterfactual replay 转成小规模 GAT branch/action sanity dataset。该数据集只用于离线试训模型管线，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        f"output_dir = {summary['output_dir']}",
        f"target_wall = {summary['target_wall']}",
        f"wall_cap = {summary['wall_cap']}",
        f"min_wall_improvement = {summary['min_wall_improvement']}",
        f"min_wall_regression = {summary['min_wall_regression']}",
        f"raw_row_count = {summary['raw_row_count']}",
        f"sample_count = {summary['sample_count']}",
        f"row_kind_counts = {summary['row_kind_counts']}",
        f"branch_priority_label_counts = {summary['branch_priority_label_counts']}",
        f"target_wall_crossing_label_counts = {summary['target_wall_crossing_label_counts']}",
        f"tail_improved_aux_label_counts = {summary['tail_improved_aux_label_counts']}",
        f"skipped_counts = {summary['skipped_counts']}",
        f"instance_count = {summary['instance_count']}",
        f"family_count = {summary['family_count']}",
        f"sanity_training_dataset_ready = {str(summary['sanity_training_dataset_ready']).lower()}",
        f"serious_training_dataset_ready = {str(summary['serious_training_dataset_ready']).lower()}",
        f"optin_training_dataset_ready = {str(summary['optin_training_dataset_ready']).lower()}",
        "runs_bpc_or_pricing = false",
        "official_bound_effect = false",
        "certificate_effect = false",
        "```",
        "",
        "## 标签边界",
        "",
        "- 主 `branch_priority` 标签使用 capped wall-time gain，不把 200 秒作为训练硬断点。",
        "- `target_wall_crossing_positive` 只作为验收/报告字段；`199s -> 201s` 这类小变化不会成为强负例，`500s -> 300s` 会成为高权重正例。",
        "- `weak_positive_not_target` 样本保留在数据集中；只要有足够 wall-time gain，也会进入主标签，否则仅作为 `tail_improved` 辅助标签。",
        "- `local_only_hard_negative` 和右删失 proxy 不进入主训练样本，避免把局部证据当 full-run 反例。",
        "",
        "## Schema",
        "",
        "```json",
        json.dumps(
            {
                "branch_feature_schema": manifest["branch_feature_schema"],
                "context_feature_schema": manifest["context_feature_schema"],
                "label_schema": manifest["label_schema"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
    ]
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--target-wall", type=float, default=200.0)
    parser.add_argument("--wall-cap", type=float, default=600.0)
    parser.add_argument("--min-wall-improvement", type=float, default=5.0)
    parser.add_argument("--min-wall-regression", type=float, default=5.0)
    parser.add_argument("--max-delta-weight", type=float, default=4.0)
    parser.add_argument("--max-rows", type=int, default=0)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    summary = build_dataset(
        list(args.inputs),
        args.output_dir,
        args.report,
        target_wall=float(args.target_wall),
        wall_cap=float(args.wall_cap),
        min_wall_improvement=float(args.min_wall_improvement),
        min_wall_regression=float(args.min_wall_regression),
        max_delta_weight=float(args.max_delta_weight),
        max_rows=max(0, int(args.max_rows)),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["sanity_training_dataset_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
