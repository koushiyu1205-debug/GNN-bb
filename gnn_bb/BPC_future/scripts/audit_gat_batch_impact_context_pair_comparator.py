#!/usr/bin/env python3
"""Audit the optional context-pair comparator on focused same-context pairs.

This script is diagnostic-only. It loads an offline ``GATBatchImpactModel``
checkpoint and the focused pair rows already emitted by the Stage 3 training
summary, then scores the optional pair comparator on positive-vs-hard-negative
pairs. It does not run BPC, pricing, RMP, workers, or certificate logic.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import date
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch

from BPC_future.learning.batch_impact_model import GATBatchImpactModel
from BPC_future.scripts.train_gat_batch_impact import (
    _load_sample,
    _normalize_sample,
    _sample_model_kwargs,
)


DEFAULT_DATASET_DIR = Path(
    "BPC_future/data/gat_batch_impact/v119_explicit_label_conflict_filtered_5000_stage4_biased_20260622"
)
DEFAULT_CHECKPOINT = Path(
    "BPC_future/results/gat_batch_impact_training_v130_focused_context_pair_comparator_cached_seed13_20260623/"
    "epoch_checkpoints/epoch_004.pt"
)
DEFAULT_METRICS = Path(
    "BPC_future/results/gat_batch_impact_training_v130_focused_context_pair_comparator_cached_seed13_20260623/"
    "epoch_checkpoints/epoch_004_metrics.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/gat_batch_impact_context_pair_comparator_audit_v131_v130_epoch004_20260623"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260623_bpc_future_gat_target_mode_stage3_v131_context_pair_comparator_audit_zh.md"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--metrics", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--top-contexts", type=int, default=20)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = audit_context_pair_comparator(
        dataset_dir=Path(args.dataset_dir),
        checkpoint=Path(args.checkpoint),
        metrics=Path(args.metrics),
        output_dir=Path(args.output_dir),
        report=Path(args.report),
        device=str(args.device),
        top_contexts=max(1, int(args.top_contexts)),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def audit_context_pair_comparator(
    *,
    dataset_dir: Path = DEFAULT_DATASET_DIR,
    checkpoint: Path = DEFAULT_CHECKPOINT,
    metrics: Path = DEFAULT_METRICS,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    device: str = "cpu",
    top_contexts: int = 20,
) -> dict[str, Any]:
    dataset_dir = Path(dataset_dir)
    checkpoint_data = torch.load(Path(checkpoint), map_location="cpu", weights_only=False)
    training_metrics = _read_json(Path(metrics))
    manifest = _read_json(dataset_dir / "manifest.json")
    _assert_offline_contract(checkpoint_data, training_metrics)

    model = GATBatchImpactModel(**checkpoint_data["model_config"]).to(torch.device(device))
    model.load_state_dict(checkpoint_data["model_state_dict"])
    model.eval()
    if getattr(model, "context_pair_comparator_head", None) is None:
        raise ValueError("checkpoint does not enable the context-pair comparator head")

    pair_rows = list(
        dict(row)
        for row in (training_metrics.get("focused_pair_gate") or {}).get("pair_rows", [])
    )
    row_items = {
        int(item.get("row_index")): item
        for item in manifest.get("samples", [])
        if item.get("row_index") is not None
    }
    needed_rows = sorted(
        {
            int(row[key])
            for row in pair_rows
            for key in ("positive_row_index", "negative_row_index")
            if row.get(key) is not None
        }
    )
    outputs = _score_needed_rows(
        dataset_dir=dataset_dir,
        manifest=manifest,
        row_items=row_items,
        needed_rows=needed_rows,
        model=model,
        device=torch.device(device),
    )
    enriched_pairs = [
        _score_pair_with_comparator(row, outputs=outputs, model=model)
        for row in pair_rows
    ]
    context_rows = _context_summary_rows(enriched_pairs)
    summary_stats = _summary_stats(enriched_pairs, context_rows)
    recommendation = _recommend_next_step(summary_stats)

    output_dir.mkdir(parents=True, exist_ok=True)
    pair_path = output_dir / "context_pair_comparator_pair_rows.jsonl"
    context_path = output_dir / "context_pair_comparator_context_rows.jsonl"
    _write_jsonl(pair_path, enriched_pairs)
    _write_jsonl(context_path, context_rows)

    summary = {
        "schema_version": "gat_batch_impact_context_pair_comparator_audit_v1",
        "status": "gat_batch_impact_context_pair_comparator_audited",
        "dataset_dir": str(dataset_dir),
        "checkpoint": str(checkpoint),
        "metrics": str(metrics),
        "output_dir": str(output_dir),
        "pair_rows_path": str(pair_path),
        "context_rows_path": str(context_path),
        "sample_count": int(manifest.get("sample_count") or 0),
        "focused_pair_count": len(pair_rows),
        "summary": summary_stats,
        "top_contexts_by_unresolved": sorted(
            context_rows,
            key=lambda row: (
                int(row["comparator_unresolved_existing_failure_count"]),
                int(row["existing_failed_pair_count"]),
                int(row["pair_count"]),
            ),
            reverse=True,
        )[: int(top_contexts)],
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


def _score_needed_rows(
    *,
    dataset_dir: Path,
    manifest: dict[str, Any],
    row_items: dict[int, dict[str, Any]],
    needed_rows: list[int],
    model: GATBatchImpactModel,
    device: torch.device,
) -> dict[int, dict[str, torch.Tensor]]:
    outputs: dict[int, dict[str, torch.Tensor]] = {}
    with torch.no_grad():
        for row_index in needed_rows:
            item = row_items.get(int(row_index))
            if item is None:
                raise ValueError(f"focused row {row_index} missing from manifest")
            sample = _normalize_sample(_load_sample(dataset_dir / str(item["path"])), manifest).to(device)
            outputs[int(row_index)] = model(
                sample,
                sample.candidate_task_membership,
                sample.candidate_sequence_positions,
                sample.candidate_features,
                sample.context_features,
                **_sample_model_kwargs(model, sample),
            )
    return outputs


def _score_pair_with_comparator(
    pair: dict[str, Any],
    *,
    outputs: dict[int, dict[str, torch.Tensor]],
    model: GATBatchImpactModel,
) -> dict[str, Any]:
    positive_idx = int(pair["positive_row_index"])
    negative_idx = int(pair["negative_row_index"])
    positive_output = outputs[positive_idx]
    negative_output = outputs[negative_idx]
    forward_logit = model.context_pair_preference_logit(positive_output, negative_output)
    reverse_logit = model.context_pair_preference_logit(negative_output, positive_output)
    forward_value = float(forward_logit.detach().cpu().reshape(-1)[0])
    reverse_value = float(reverse_logit.detach().cpu().reshape(-1)[0])
    comparator_forward_pass = forward_value > 0.0
    comparator_reverse_pass = reverse_value < 0.0
    comparator_pair_pass = comparator_forward_pass and comparator_reverse_pass
    existing_pair_pass = bool(pair.get("pair_pass"))
    return {
        **pair,
        "existing_pair_pass": existing_pair_pass,
        "comparator_forward_logit": forward_value,
        "comparator_reverse_logit": reverse_value,
        "comparator_forward_probability": _sigmoid(forward_value),
        "comparator_reverse_probability": _sigmoid(reverse_value),
        "comparator_forward_pass": comparator_forward_pass,
        "comparator_reverse_pass": comparator_reverse_pass,
        "comparator_pair_pass": comparator_pair_pass,
        "comparator_repairs_existing_failure": (not existing_pair_pass) and comparator_pair_pass,
        "comparator_unresolved_existing_failure": (not existing_pair_pass) and (not comparator_pair_pass),
        "comparator_conflicts_existing_pass": existing_pair_pass and (not comparator_pair_pass),
    }


def _context_summary_rows(pair_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in pair_rows:
        grouped[str(row.get("context_key") or "")].append(row)
    context_rows: list[dict[str, Any]] = []
    for key, rows in sorted(grouped.items()):
        context_rows.append(
            {
                "context_key": key,
                "context_hash": str(rows[0].get("context_hash") or ""),
                "family": str(rows[0].get("family") or "unknown"),
                "pair_count": len(rows),
                "existing_failed_pair_count": sum(int(not row["existing_pair_pass"]) for row in rows),
                "comparator_pair_pass_count": sum(int(row["comparator_pair_pass"]) for row in rows),
                "comparator_repaired_existing_failure_count": sum(
                    int(row["comparator_repairs_existing_failure"]) for row in rows
                ),
                "comparator_unresolved_existing_failure_count": sum(
                    int(row["comparator_unresolved_existing_failure"]) for row in rows
                ),
                "comparator_conflicts_existing_pass_count": sum(
                    int(row["comparator_conflicts_existing_pass"]) for row in rows
                ),
            }
        )
    return context_rows


def _summary_stats(
    pair_rows: list[dict[str, Any]],
    context_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    pair_count = len(pair_rows)
    existing_failed = sum(int(not row["existing_pair_pass"]) for row in pair_rows)
    comparator_pass = sum(int(row["comparator_pair_pass"]) for row in pair_rows)
    repaired = sum(int(row["comparator_repairs_existing_failure"]) for row in pair_rows)
    unresolved = sum(int(row["comparator_unresolved_existing_failure"]) for row in pair_rows)
    conflicts = sum(int(row["comparator_conflicts_existing_pass"]) for row in pair_rows)
    return {
        "pair_count": pair_count,
        "context_count": len(context_rows),
        "existing_strict_pair_pass_count": pair_count - existing_failed,
        "existing_strict_pair_pass_rate": _rate(pair_count - existing_failed, pair_count),
        "existing_failed_pair_count": existing_failed,
        "comparator_pair_pass_count": comparator_pass,
        "comparator_pair_pass_rate": _rate(comparator_pass, pair_count),
        "comparator_repaired_existing_failure_count": repaired,
        "comparator_repaired_existing_failure_rate": _rate(repaired, existing_failed),
        "comparator_unresolved_existing_failure_count": unresolved,
        "comparator_conflicts_existing_pass_count": conflicts,
        "comparator_forward_pass_count": sum(int(row["comparator_forward_pass"]) for row in pair_rows),
        "comparator_reverse_pass_count": sum(int(row["comparator_reverse_pass"]) for row in pair_rows),
        "primary": _primary_diagnosis(
            pair_count=pair_count,
            existing_failed=existing_failed,
            comparator_pass=comparator_pass,
            repaired=repaired,
            unresolved=unresolved,
            conflicts=conflicts,
        ),
    }


def _primary_diagnosis(
    *,
    pair_count: int,
    existing_failed: int,
    comparator_pass: int,
    repaired: int,
    unresolved: int,
    conflicts: int,
) -> str:
    if pair_count <= 0:
        return "no_focused_pairs"
    if comparator_pass == pair_count and existing_failed > 0:
        return "comparator_separates_all_pairs_but_heads_do_not_use_it"
    if repaired > 0 and unresolved > 0:
        return "comparator_partially_repairs_focused_failures"
    if repaired <= 0 and existing_failed > 0:
        return "comparator_does_not_repair_focused_failures"
    if conflicts > 0:
        return "comparator_conflicts_with_existing_passes"
    return "comparator_and_existing_heads_pass"


def _recommend_next_step(summary: dict[str, Any]) -> str:
    primary = str(summary.get("primary") or "")
    if primary == "comparator_separates_all_pairs_but_heads_do_not_use_it":
        return "prototype_default_off_fused_context_pair_score_audit_before_training_more"
    if primary == "comparator_partially_repairs_focused_failures":
        return "inspect_unresolved_contexts_before_fusing_comparator_into_heads"
    if primary == "comparator_does_not_repair_focused_failures":
        return "do_not_fuse_comparator_prioritize_action_consequence_feature_or_label_reaudit"
    return "keep_current_gate_do_not_advance_stage4"


def _assert_offline_contract(checkpoint_data: dict[str, Any], training_metrics: dict[str, Any]) -> None:
    contract = dict(checkpoint_data.get("exactness_contract") or {})
    if contract.get("certificate_source") or contract.get("official_bound_effect"):
        raise ValueError("context-pair comparator audit requires diagnostic-only checkpoint")
    if bool(training_metrics.get("production_ready")) or bool(training_metrics.get("stage4_candidate_ready")):
        raise ValueError("context-pair comparator audit expects non-production training metrics")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _sigmoid(value: float) -> float:
    tensor = torch.tensor(float(value), dtype=torch.float32)
    return float(torch.sigmoid(tensor).item())


def _rate(numerator: int, denominator: int) -> float | None:
    if int(denominator) <= 0:
        return None
    return float(numerator) / float(denominator)


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    stats = summary["summary"]
    checkpoint_name = Path(str(summary.get("checkpoint") or "")).parent.name or "specified checkpoint"
    lines = [
        "# BPC_future GAT target-mode Stage 3 context-pair comparator 审计报告",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 结论",
        "",
        f"本报告只审计 `{checkpoint_name}` 中默认关闭的 context-pair comparator head，",
        "不运行 BPC、pricing、RMP、worker 或 certificate。",
        "",
        "```text",
        f"checkpoint = {summary['checkpoint']}",
        f"metrics = {summary['metrics']}",
        f"pair_count = {stats['pair_count']}",
        f"existing_strict_pair_pass = {stats['existing_strict_pair_pass_count']}/{stats['pair_count']}",
        f"comparator_pair_pass = {stats['comparator_pair_pass_count']}/{stats['pair_count']}",
        "comparator_repaired_existing_failure_count = "
        f"{stats['comparator_repaired_existing_failure_count']}",
        "comparator_unresolved_existing_failure_count = "
        f"{stats['comparator_unresolved_existing_failure_count']}",
        "comparator_conflicts_existing_pass_count = "
        f"{stats['comparator_conflicts_existing_pass_count']}",
        f"primary = {stats['primary']}",
        f"recommended_next_step = {summary['recommended_next_step']}",
        "stage4_candidate_ready = false",
        "production_ready = false",
        "selector_can_certificate = false",
        "```",
        "",
        "## Top Contexts",
        "",
        "| context | family | pairs | existing failed | comparator repaired | comparator unresolved | comparator conflicts |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in summary["top_contexts_by_unresolved"]:
        lines.append(
            "| {context} | {family} | {pair_count} | {existing_failed} | {repaired} | "
            "{unresolved} | {conflicts} |".format(
                context=row["context_hash"],
                family=row["family"],
                pair_count=row["pair_count"],
                existing_failed=row["existing_failed_pair_count"],
                repaired=row["comparator_repaired_existing_failure_count"],
                unresolved=row["comparator_unresolved_existing_failure_count"],
                conflicts=row["comparator_conflicts_existing_pass_count"],
            )
        )
    lines.extend(
        [
            "",
            "## 判断",
            "",
            "- comparator 只是离线诊断 head，不是 admission score，也不是 pricing oracle；",
            "- 即使 comparator 能修复部分 focused pair，也不能直接升级 Stage 4；",
            "- 下一步是否值得做 fused score 或 head 回流，取决于 comparator 是否能覆盖当前原 head 失败 pair。",
            "",
            "## Exactness Boundary",
            "",
            "- `diagnostic_only=true`；",
            "- `runs_bpc_or_pricing=false`；",
            "- `production_ready=false`；",
            "- `selector_is_pricing_oracle=false`；",
            "- `selector_can_certificate=false`；",
            "- `gate_can_permanently_discard_negative_columns=false`；",
            "- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。",
            "",
            "## Output Artifacts",
            "",
            "```text",
            f"summary = {summary['output_dir']}/summary.json",
            f"pairs = {summary['pair_rows_path']}",
            f"contexts = {summary['context_rows_path']}",
            "```",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
