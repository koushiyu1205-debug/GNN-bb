#!/usr/bin/env python3
"""Audit path-token nearest-neighbor labels for focused failures.

This diagnostic scans the offline batch-impact dataset and compares the raw
selected candidates from a path-token attribution audit against path-token
neighbors in the train/validation split. It does not run BPC, pricing, RMP,
workers, model inference, or certificate logic.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch

from BPC_future.scripts.audit_gat_batch_impact_path_token_failure_attribution import (
    _candidate_token_values,
    _jaccard,
    _lcs_ratio,
)


DEFAULT_DATASET_DIR = Path(
    "BPC_future/data/gat_batch_impact/v119_explicit_label_conflict_filtered_5000_stage4_biased_20260622"
)
DEFAULT_METRICS = Path(
    "BPC_future/results/gat_batch_impact_training_v140_trainonly_failure_analog_boost_seed13_20260623/"
    "metrics.json"
)
DEFAULT_PAIR_ROWS = Path(
    "BPC_future/results/gat_batch_impact_path_token_failure_attribution_v142_v140_remaining_20260623/"
    "path_token_failure_pair_rows.jsonl"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/gat_batch_impact_path_token_label_neighbors_v143_v140_remaining_20260623"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260623_bpc_future_gat_target_mode_stage3_v143_v140_remaining_path_token_label_neighbors_zh.md"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--metrics", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--pair-rows", type=Path, default=DEFAULT_PAIR_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--top-k", type=int, default=20)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = audit_path_token_label_neighbors(
        dataset_dir=Path(args.dataset_dir),
        metrics=Path(args.metrics),
        pair_rows_path=Path(args.pair_rows),
        output_dir=Path(args.output_dir),
        report=Path(args.report),
        top_k=max(1, int(args.top_k)),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if bool(summary["all_checks_pass"]) else 1


def audit_path_token_label_neighbors(
    *,
    dataset_dir: Path = DEFAULT_DATASET_DIR,
    metrics: Path = DEFAULT_METRICS,
    pair_rows_path: Path = DEFAULT_PAIR_ROWS,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    top_k: int = 20,
) -> dict[str, Any]:
    dataset_dir = Path(dataset_dir)
    manifest = _read_json(dataset_dir / "manifest.json")
    training_metrics = _read_json(Path(metrics))
    pair_rows = list(_read_jsonl(Path(pair_rows_path)))
    split_by_instance = _split_by_instance(training_metrics)
    candidates = _load_candidate_records(
        dataset_dir=dataset_dir,
        manifest=manifest,
        split_by_instance=split_by_instance,
    )
    queries = _query_candidates(pair_rows)
    query_records = [
        _audit_query(query, candidates=candidates, top_k=int(top_k))
        for query in queries
    ]
    pair_records = _pair_records(pair_rows, query_records)
    summary_stats = _summary_stats(query_records, pair_records)
    recommendation = _recommend_next_step(summary_stats)

    output_dir.mkdir(parents=True, exist_ok=True)
    query_path = output_dir / "path_token_label_neighbor_queries.jsonl"
    pair_path = output_dir / "path_token_label_neighbor_pairs.jsonl"
    _write_jsonl(query_path, query_records)
    _write_jsonl(pair_path, pair_records)

    summary = {
        "schema_version": "gat_batch_impact_path_token_label_neighbors_v1",
        "status": "gat_batch_impact_path_token_label_neighbors_audited",
        "dataset_dir": str(dataset_dir),
        "metrics": str(metrics),
        "pair_rows": str(pair_rows_path),
        "output_dir": str(output_dir),
        "query_rows_path": str(query_path),
        "pair_rows_path": str(pair_path),
        "sample_count": int(manifest.get("sample_count") or 0),
        "candidate_record_count": len(candidates),
        "query_count": len(query_records),
        "failed_pair_count": len(pair_records),
        "top_k": int(top_k),
        "summary": summary_stats,
        "recommended_next_step": recommendation,
        "stage3_completed": False,
        "stage4_candidate_ready": False,
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "runs_rmp": False,
        "production_ready": False,
        "default_enabled": False,
        "official_bound_effect": False,
        "selector_is_pricing_oracle": False,
        "selector_can_certificate": False,
        "gate_can_permanently_discard_negative_columns": False,
        "all_checks_pass": True,
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(Path(report), summary)
    return summary


def _split_by_instance(training_metrics: dict[str, Any]) -> dict[str, str]:
    split = dict(training_metrics.get("split") or {})
    result: dict[str, str] = {}
    for value in split.get("train_instances") or []:
        result[str(value)] = "train"
    for value in split.get("validation_instances") or []:
        result[str(value)] = "validation"
    return result


def _load_candidate_records(
    *,
    dataset_dir: Path,
    manifest: dict[str, Any],
    split_by_instance: dict[str, str],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for item in manifest.get("samples", []):
        row_index = int(item.get("row_index") or 0)
        sample_path = dataset_dir / str(item.get("path") or "")
        sample = torch.load(sample_path, map_location="cpu", weights_only=False)
        signatures = list(getattr(sample, "batch_impact_candidate_signature_ids", []) or [])
        candidate_ids = list(getattr(sample, "batch_impact_candidate_ids", []) or [])
        candidate_count = int(getattr(sample, "candidate_path_token_ids").shape[0])
        instance_path = str(
            item.get("instance_path")
            or getattr(sample, "batch_impact_instance_path", "")
            or ""
        )
        split = split_by_instance.get(instance_path, "unknown")
        for candidate_index in range(candidate_count):
            tokens = _candidate_token_values(sample, candidate_index, "candidate_path_token_ids")
            pairs = _candidate_token_values(sample, candidate_index, "candidate_path_pair_ids")
            types = _candidate_token_values(sample, candidate_index, "candidate_path_type_ids")
            records.append(
                {
                    "row_index": row_index,
                    "candidate_index": int(candidate_index),
                    "split": split,
                    "instance": str(item.get("instance") or ""),
                    "instance_path": instance_path,
                    "family": str(item.get("instance_family") or ""),
                    "task_count": int(item.get("task_count") or 0),
                    "context_hash": str(item.get("context_hash") or ""),
                    "accepted_batch_roi": float(item.get("accepted_batch_roi") or 0.0),
                    "batch_roi_positive": int(item.get("label_batch_roi_positive") or 0),
                    "candidate_id": str(candidate_ids[candidate_index])
                    if candidate_index < len(candidate_ids)
                    else "",
                    "signature_id": str(signatures[candidate_index])
                    if candidate_index < len(signatures)
                    else "",
                    "safe_label": _candidate_label(sample, candidate_index, "y_candidate_high_priority"),
                    "delay_label": _candidate_label(sample, candidate_index, "y_candidate_delay_risk"),
                    "true_rc_negative_label": _candidate_label(
                        sample,
                        candidate_index,
                        "y_candidate_true_rc_negative",
                    ),
                    "token_ids": tokens,
                    "pair_ids": pairs,
                    "type_ids": types,
                    "token_set": sorted(set(tokens)),
                    "pair_set": sorted(set(pairs)),
                    "typed_token_set": sorted({f"{token}:{typ}" for token, typ in zip(tokens, types)}),
                }
            )
    return records


def _query_candidates(pair_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    queries: list[dict[str, Any]] = []
    for row in pair_rows:
        for role, score_key in (("positive", "positive_score_summary"), ("negative", "negative_score_summary")):
            candidate = dict(row[score_key]["raw"]["candidate"])
            queries.append(
                {
                    "query_id": f"{row['context_hash']}:{role}:{row[f'{role}_row_index']}:raw",
                    "pair_context_hash": row["context_hash"],
                    "pair_family": row["family"],
                    "pair_key": f"{row['positive_row_index']}>{row['negative_row_index']}",
                    "role": role,
                    "row_index": int(row[f"{role}_row_index"]),
                    "candidate_index": int(candidate.get("index") or 0),
                    "signature_id": str(candidate.get("signature_id") or ""),
                    "safe_label": int(candidate.get("safe_label") or 0),
                    "delay_label": int(candidate.get("delay_label") or 0),
                    "token_ids": [int(value) for value in candidate.get("path_token_ids") or []],
                    "pair_ids": [int(value) for value in candidate.get("path_pair_ids") or []],
                    "type_ids": [int(value) for value in candidate.get("path_type_ids") or []],
                }
            )
    return queries


def _audit_query(
    query: dict[str, Any],
    *,
    candidates: list[dict[str, Any]],
    top_k: int,
) -> dict[str, Any]:
    neighbors = [
        _neighbor_record(query, candidate)
        for candidate in candidates
        if not (
            int(candidate["row_index"]) == int(query["row_index"])
            and int(candidate["candidate_index"]) == int(query["candidate_index"])
        )
    ]
    neighbors.sort(
        key=lambda row: (
            float(row["token_jaccard"]),
            float(row["typed_token_jaccard"]),
            float(row["token_lcs_ratio"]),
            int(row["same_signature"]),
        ),
        reverse=True,
    )
    top_neighbors = neighbors[: int(top_k)]
    train_neighbors = [row for row in neighbors if row["split"] == "train"][: int(top_k)]
    validation_neighbors = [row for row in neighbors if row["split"] == "validation"][: int(top_k)]
    return {
        **query,
        "top_neighbors": top_neighbors,
        "top_train_neighbors": train_neighbors,
        "top_validation_neighbors": validation_neighbors,
        "top_neighbor_stats": _neighbor_stats(top_neighbors),
        "top_train_neighbor_stats": _neighbor_stats(train_neighbors),
        "top_validation_neighbor_stats": _neighbor_stats(validation_neighbors),
        "diagnosis": _query_diagnosis(query, train_neighbors),
        "diagnostic_only": True,
    }


def _neighbor_record(query: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    query_tokens = [int(value) for value in query.get("token_ids") or []]
    query_pairs = [int(value) for value in query.get("pair_ids") or []]
    query_types = [int(value) for value in query.get("type_ids") or []]
    candidate_tokens = [int(value) for value in candidate.get("token_ids") or []]
    candidate_pairs = [int(value) for value in candidate.get("pair_ids") or []]
    candidate_types = [int(value) for value in candidate.get("type_ids") or []]
    return {
        "row_index": int(candidate["row_index"]),
        "candidate_index": int(candidate["candidate_index"]),
        "split": str(candidate["split"]),
        "family": str(candidate["family"]),
        "task_count": int(candidate["task_count"]),
        "context_hash": str(candidate["context_hash"]),
        "accepted_batch_roi": float(candidate["accepted_batch_roi"]),
        "batch_roi_positive": int(candidate["batch_roi_positive"]),
        "signature_id": str(candidate["signature_id"]),
        "same_signature": str(candidate["signature_id"]) == str(query.get("signature_id") or ""),
        "safe_label": int(candidate["safe_label"]),
        "delay_label": int(candidate["delay_label"]),
        "true_rc_negative_label": int(candidate["true_rc_negative_label"]),
        "token_jaccard": _jaccard(set(query_tokens), set(candidate_tokens)),
        "pair_jaccard": _jaccard(set(query_pairs), set(candidate_pairs)),
        "typed_token_jaccard": _jaccard(
            set(zip(query_tokens, query_types)),
            set(zip(candidate_tokens, candidate_types)),
        ),
        "token_lcs_ratio": _lcs_ratio(query_tokens, candidate_tokens),
        "exact_token_sequence_match": query_tokens == candidate_tokens,
    }


def _pair_records(pair_rows: list[dict[str, Any]], query_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_query = {str(row["query_id"]): row for row in query_records}
    records: list[dict[str, Any]] = []
    for row in pair_rows:
        positive_key = f"{row['context_hash']}:positive:{row['positive_row_index']}:raw"
        negative_key = f"{row['context_hash']}:negative:{row['negative_row_index']}:raw"
        positive = by_query[positive_key]
        negative = by_query[negative_key]
        records.append(
            {
                "context_hash": row["context_hash"],
                "family": row["family"],
                "pair_key": f"{row['positive_row_index']}>{row['negative_row_index']}",
                "path_attribution_diagnosis": row.get("diagnosis"),
                "positive_query_diagnosis": positive["diagnosis"],
                "negative_query_diagnosis": negative["diagnosis"],
                "positive_top_train_stats": positive["top_train_neighbor_stats"],
                "negative_top_train_stats": negative["top_train_neighbor_stats"],
                "same_signature_leakage_like_neighbor": _same_signature_cross_role_neighbor(
                    positive,
                    negative,
                ),
                "diagnosis": _pair_diagnosis(positive, negative),
                "diagnostic_only": True,
            }
        )
    return records


def _same_signature_cross_role_neighbor(
    positive_query: dict[str, Any],
    negative_query: dict[str, Any],
) -> bool:
    negative_signature = str(negative_query.get("signature_id") or "")
    positive_signature = str(positive_query.get("signature_id") or "")
    positive_neighbors = positive_query.get("top_train_neighbors") or []
    negative_neighbors = negative_query.get("top_train_neighbors") or []
    return any(str(row.get("signature_id") or "") == negative_signature for row in positive_neighbors) or any(
        str(row.get("signature_id") or "") == positive_signature for row in negative_neighbors
    )


def _neighbor_stats(neighbors: list[dict[str, Any]]) -> dict[str, Any]:
    count = len(neighbors)
    return {
        "count": count,
        "max_token_jaccard": max([float(row["token_jaccard"]) for row in neighbors], default=None),
        "mean_token_jaccard": _mean([float(row["token_jaccard"]) for row in neighbors]),
        "same_signature_count": sum(int(row["same_signature"]) for row in neighbors),
        "exact_token_sequence_count": sum(int(row["exact_token_sequence_match"]) for row in neighbors),
        "safe_label_count": sum(int(row["safe_label"]) for row in neighbors),
        "safe_label_rate": _rate(sum(int(row["safe_label"]) for row in neighbors), count),
        "delay_label_count": sum(int(row["delay_label"]) for row in neighbors),
        "delay_label_rate": _rate(sum(int(row["delay_label"]) for row in neighbors), count),
        "positive_batch_count": sum(int(row["batch_roi_positive"]) for row in neighbors),
        "positive_batch_rate": _rate(sum(int(row["batch_roi_positive"]) for row in neighbors), count),
        "mean_accepted_batch_roi": _mean([float(row["accepted_batch_roi"]) for row in neighbors]),
        "split_counts": dict(sorted(Counter(str(row["split"]) for row in neighbors).items())),
    }


def _query_diagnosis(query: dict[str, Any], train_neighbors: list[dict[str, Any]]) -> str:
    stats = _neighbor_stats(train_neighbors)
    safe_rate = float(stats.get("safe_label_rate") or 0.0)
    delay_rate = float(stats.get("delay_label_rate") or 0.0)
    max_jaccard = float(stats.get("max_token_jaccard") or 0.0)
    if not train_neighbors:
        return "no_train_path_neighbors"
    if str(query.get("role")) == "positive":
        if delay_rate >= 0.60 and safe_rate <= 0.40 and max_jaccard >= 0.20:
            return "positive_path_neighborhood_train_delay_biased"
        if safe_rate >= 0.60:
            return "positive_path_neighborhood_train_supports_safe_label"
    if str(query.get("role")) == "negative":
        if safe_rate >= 0.40 and max_jaccard >= 0.20:
            return "negative_path_neighborhood_train_safe_conflict"
        if delay_rate >= 0.60:
            return "negative_path_neighborhood_train_supports_delay_label"
    return "path_neighborhood_label_mixed_or_sparse"


def _pair_diagnosis(positive: dict[str, Any], negative: dict[str, Any]) -> str:
    positive_diag = str(positive.get("diagnosis") or "")
    negative_diag = str(negative.get("diagnosis") or "")
    if positive_diag == "positive_path_neighborhood_train_delay_biased":
        return "positive_path_tokens_are_train_delay_biased"
    if negative_diag == "negative_path_neighborhood_train_safe_conflict":
        return "negative_path_tokens_have_train_safe_conflict"
    if positive_diag == "positive_path_neighborhood_train_supports_safe_label" and negative_diag == "negative_path_neighborhood_train_supports_delay_label":
        return "path_neighbors_support_labels_model_head_learned_wrong_direction"
    return "path_neighbor_labels_mixed_or_inconclusive"


def _summary_stats(query_records: list[dict[str, Any]], pair_records: list[dict[str, Any]]) -> dict[str, Any]:
    query_counts = Counter(str(row["diagnosis"]) for row in query_records)
    pair_counts = Counter(str(row["diagnosis"]) for row in pair_records)
    return {
        "query_count": len(query_records),
        "pair_count": len(pair_records),
        "query_diagnosis_counts": dict(sorted(query_counts.items())),
        "pair_diagnosis_counts": dict(sorted(pair_counts.items())),
        "pair_primary": _dominant_key(pair_counts),
        "positive_train_delay_biased_query_count": int(
            query_counts.get("positive_path_neighborhood_train_delay_biased", 0)
        ),
        "negative_train_safe_conflict_query_count": int(
            query_counts.get("negative_path_neighborhood_train_safe_conflict", 0)
        ),
        "same_signature_cross_role_neighbor_count": sum(
            int(row["same_signature_leakage_like_neighbor"]) for row in pair_records
        ),
    }


def _recommend_next_step(summary: dict[str, Any]) -> dict[str, Any]:
    primary = str(summary.get("pair_primary") or "")
    if primary == "path_neighbors_support_labels_model_head_learned_wrong_direction":
        return {
            "primary": "regularize_or_gate_path_token_branch_with_context_pair_loss",
            "reason": "nearest train path neighbors support labels while model path branch hurts",
            "avoid": "do_not_collect_more_duplicate_path_neighbors_first",
        }
    if primary == "positive_path_tokens_are_train_delay_biased":
        return {
            "primary": "collect_train_only_positive_counterexamples_for_these_path_tokens",
            "reason": "positive failed paths are surrounded by delay-labeled train neighbors",
            "avoid": "do_not_increase_path_token_weight_before_counterexamples",
        }
    if primary == "negative_path_tokens_have_train_safe_conflict":
        return {
            "primary": "audit_negative_path_label_conflicts_and_signature_overlap",
            "reason": "negative failed paths have safe-labeled train neighbors",
            "avoid": "do_not_use_path_neighborhood_as_safe_source",
        }
    return {
        "primary": "use_path_ablation_as_targeted_regularization_diagnostic",
        "reason": "path-neighbor labels are mixed or sparse",
        "avoid": "do_not_advance_stage4_before_focused_gate_passes",
    }


def _candidate_label(sample: Any, index: int, attr_name: str) -> int:
    values = getattr(sample, attr_name, None)
    if values is None:
        return 0
    tensor = values.detach().cpu().reshape(-1)
    if int(index) < 0 or int(index) >= int(tensor.numel()):
        return 0
    return int(float(tensor[int(index)].item()) > 0.5)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(float(value) for value in values) / float(len(values))


def _rate(numerator: int, denominator: int) -> float | None:
    if int(denominator) <= 0:
        return None
    return float(numerator) / float(denominator)


def _dominant_key(counter: Counter[str]) -> str:
    if not counter:
        return "none"
    return sorted(counter.items(), key=lambda item: (-int(item[1]), str(item[0])))[0][0]


def _format(value: Any, digits: int = 3) -> str:
    if value is None:
        return "NA"
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "NA"


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    stats = summary["summary"]
    pair_records = _read_jsonl(Path(summary["pair_rows_path"]))
    lines = [
        "# 2026-06-23 BPC_future GAT Stage 3 v143 Path-token 邻域标签审计",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 结论",
        "",
        "本轮只扫描离线 dataset 的候选 path-token 邻域，检查 v142 失败候选在",
        "train/validation split 中的相似路径标签分布；不运行模型推理、BPC、pricing、RMP 或 certificate。",
        "",
        "```text",
        f"candidate_record_count = {summary['candidate_record_count']}",
        f"query_count = {stats['query_count']}",
        f"pair_count = {stats['pair_count']}",
        f"pair_primary = {stats['pair_primary']}",
        "positive_train_delay_biased_query_count = "
        f"{stats['positive_train_delay_biased_query_count']}",
        "negative_train_safe_conflict_query_count = "
        f"{stats['negative_train_safe_conflict_query_count']}",
        f"recommended_next_step = {summary['recommended_next_step']['primary']}",
        "stage4_candidate_ready = false",
        "production_ready = false",
        "selector_can_certificate = false",
        "```",
        "",
        "## Pair 邻域摘要",
        "",
        "| context | pair | pair diagnosis | pos train safe/delay | neg train safe/delay | pos maxJ | neg maxJ |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for row in pair_records:
        pos = row["positive_top_train_stats"]
        neg = row["negative_top_train_stats"]
        lines.append(
            "| {context} | {pair} | {diag} | {pos_safe}/{pos_delay} | {neg_safe}/{neg_delay} | {pos_j} | {neg_j} |".format(
                context=row["context_hash"],
                pair=row["pair_key"],
                diag=row["diagnosis"],
                pos_safe=_format(pos.get("safe_label_rate")),
                pos_delay=_format(pos.get("delay_label_rate")),
                neg_safe=_format(neg.get("safe_label_rate")),
                neg_delay=_format(neg.get("delay_label_rate")),
                pos_j=_format(pos.get("max_token_jaccard")),
                neg_j=_format(neg.get("max_token_jaccard")),
            )
        )
    lines.extend(
        [
            "",
            "## 判断",
            "",
            "- v142 已证明 path-token 分支在当前 checkpoint 上伤害剩余 focused pair；",
            "- v143 用 train split 邻域检查这种伤害是否来自数据邻域标签偏置；",
            "- 若相似 train path 本身以 delay 为主，下一步应补 train-only 正 counterexample，而不是提高 path 分支权重；",
            "- 若邻域标签支持当前正负标签，则应优先做 path 分支正则或 context-pair loss，而不是继续扩数据。",
            "",
            "## Exactness Boundary",
            "",
            "```text",
            "diagnostic_only = true",
            "runs_bpc_or_pricing = false",
            "runs_rmp = false",
            "production_ready = false",
            "default_enabled = false",
            "stage3_completed = false",
            "stage4_candidate_ready = false",
            "selector_is_pricing_oracle = false",
            "selector_can_certificate = false",
            "gate_can_permanently_discard_negative_columns = false",
            "```",
            "",
            "最终 certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。",
            "",
            "## Output Artifacts",
            "",
            "```text",
            f"summary = {summary['output_dir']}/summary.json",
            f"queries = {summary['query_rows_path']}",
            f"pairs = {summary['pair_rows_path']}",
            "```",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
