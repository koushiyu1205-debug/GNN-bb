#!/usr/bin/env python3
"""Audit model-visible label/provenance conflicts in GAT batch-impact data.

This is an offline diagnostic. It reads an existing GAT batch-impact dataset
manifest, its saved sample tensors, and the source JSONL rows referenced by the
manifest. It does not run BPC, pricing, RMP, workers, or certificate logic.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch


DEFAULT_DATASET_DIR = Path(
    "BPC_future/data/gat_batch_impact/"
    "v116_context_interaction_label_conflict_cleaned_5000_stage4_biased_20260622"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/"
    "gat_batch_impact_label_provenance_conflicts_v116_current_20260622"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260622_bpc_future_gat_target_mode_stage3_v119_"
    "label_provenance_conflict_audit_zh.md"
)

MODEL_VISIBLE_TENSOR_ATTRS: tuple[str, ...] = (
    "x",
    "task_ids",
    "task_mask",
    "node_ids",
    "pair_edge_index",
    "option_feat",
    "option_pair_id",
    "candidate_task_membership",
    "candidate_sequence_positions",
    "candidate_features",
    "candidate_path_token_ids",
    "candidate_path_pair_ids",
    "candidate_path_type_ids",
    "candidate_path_token_mask",
    "context_features",
    "batch_features",
)

BATCH_LABEL_ATTRS: tuple[str, ...] = (
    "y_batch_roi_positive",
    "y_objective_progress",
    "y_tail_improved",
    "y_bad_mode_switch",
    "y_support_changed_good",
    "y_delta_v",
    "y_barrier_slack",
    "y_accepted_batch_roi",
)

CANDIDATE_LABEL_ATTRS: tuple[str, ...] = (
    "y_candidate_high_priority",
    "y_candidate_delay_risk",
    "y_candidate_true_rc_negative",
)

PROVENANCE_FIELDS: tuple[str, ...] = (
    "_source_input_jsonl",
    "_source_input_line",
    "v107_unique_source_path",
    "worker_source_files",
    "ab_audit_roi_class",
    "source_file",
    "instance",
    "instance_path",
    "context_hash",
    "cg_iter",
    "pricing_kind",
    "node_id",
    "depth",
    "same_run_intervention_observed",
    "same_context_target_intervention_observed",
    "worker_target_causal_match",
    "training_label_allowed",
    "target_signature_samples",
    "target_materialized_signature_samples",
    "worker_returned_candidate_signature_samples",
    "objective_improvement",
    "accepted_batch_roi_label",
    "trajectory_accepted_batch_roi",
    "accepted_batch_roi",
    "label_batch_roi_positive",
    "label_bad_mode_switch",
    "label_tail_improved",
    "label_support_changed_good",
    "delta_v_label",
    "trajectory_delta_v_label",
    "barrier_slack_label",
    "trajectory_barrier_slack_label",
    "final_judge_retry_delta",
    "pricing_tail_retry_delta",
    "hidden_negative_delta",
    "pricing_calls_delta",
    "solving_time_delta",
    "generated_sequences_delta",
    "added_journeys",
    "replacement_journeys",
    "active_changed_task_set_count",
)

EXPLICIT_LONG_HORIZON_LABEL_FIELDS: tuple[str, ...] = (
    "accepted_batch_roi_label",
    "trajectory_accepted_batch_roi",
    "label_batch_roi_positive",
    "label_bad_mode_switch",
    "label_support_changed_good",
    "delta_v_label",
    "trajectory_delta_v_label",
    "barrier_slack_label",
    "trajectory_barrier_slack_label",
)

EPS = 1.0e-8


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--write-all-sample-rows",
        action="store_true",
        help="Also write one JSONL row per dataset sample.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = audit_label_provenance_conflicts(
        dataset_dir=Path(args.dataset_dir),
        output_dir=Path(args.output_dir),
        report=Path(args.report),
        write_all_sample_rows=bool(args.write_all_sample_rows),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def audit_label_provenance_conflicts(
    *,
    dataset_dir: Path,
    output_dir: Path,
    report: Path,
    write_all_sample_rows: bool = False,
) -> dict[str, Any]:
    manifest = _read_json(dataset_dir / "manifest.json")
    samples = list(manifest.get("samples") or [])
    source_rows = _load_source_rows(manifest)

    missing_counts: Counter[str] = Counter()
    sample_records: list[dict[str, Any]] = []
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for manifest_item in samples:
        sample_path = dataset_dir / str(manifest_item.get("path") or "")
        if not sample_path.exists():
            missing_counts["missing_sample_pt"] += 1
            continue
        try:
            sample = torch.load(sample_path, map_location="cpu", weights_only=False)
        except Exception as exc:  # pragma: no cover - diagnostic guard
            missing_counts[f"sample_load_failed:{type(exc).__name__}"] += 1
            continue
        source_row = _source_row_for_manifest_item(manifest_item, source_rows)
        record = _sample_record(
            sample=sample,
            manifest_item=manifest_item,
            source_row=source_row,
        )
        sample_records.append(record)
        groups[str(record["model_visible_hash"])].append(record)

    duplicate_groups: list[dict[str, Any]] = []
    conflict_groups: list[dict[str, Any]] = []
    conflict_field_counts: Counter[str] = Counter()
    conflict_provenance_counts: Counter[str] = Counter()
    for model_hash, records in sorted(groups.items()):
        if len(records) <= 1:
            continue
        group = _group_record(model_hash, records)
        duplicate_groups.append(group)
        if bool(group["has_label_conflict"]):
            conflict_groups.append(group)
            for field in group["conflict_fields"]:
                conflict_field_counts[str(field)] += 1
            for key in group["provenance_variation_fields"]:
                conflict_provenance_counts[str(key)] += 1

    output_dir.mkdir(parents=True, exist_ok=True)
    duplicate_path = output_dir / "model_visible_duplicate_groups.jsonl"
    conflict_path = output_dir / "model_visible_label_conflict_groups.jsonl"
    summary_path = output_dir / "summary.json"
    sample_rows_path = output_dir / "model_visible_sample_rows.jsonl"
    _write_jsonl(duplicate_path, duplicate_groups)
    _write_jsonl(conflict_path, conflict_groups)
    if write_all_sample_rows:
        _write_jsonl(sample_rows_path, sample_records)

    conflicting_row_indices = sorted(
        {
            int(member["row_index"])
            for group in conflict_groups
            for member in group["members"]
        }
    )
    summary = {
        "schema_version": "gat_batch_impact_label_provenance_conflict_audit_v1",
        "status": "gat_batch_impact_label_provenance_conflicts_audited",
        "dataset_dir": str(dataset_dir),
        "output_dir": str(output_dir),
        "report": str(report),
        "summary_path": str(summary_path),
        "duplicate_groups_path": str(duplicate_path),
        "conflict_groups_path": str(conflict_path),
        "sample_rows_path": str(sample_rows_path) if write_all_sample_rows else "",
        "manifest_sample_count": len(samples),
        "audited_sample_count": len(sample_records),
        "source_row_count": len(source_rows),
        "missing_counts": dict(sorted(missing_counts.items())),
        "model_visible_unique_group_count": len(groups),
        "model_visible_duplicate_group_count": len(duplicate_groups),
        "model_visible_duplicate_sample_count": int(
            sum(int(group["sample_count"]) for group in duplicate_groups)
        ),
        "model_visible_label_conflict_group_count": len(conflict_groups),
        "model_visible_label_conflict_sample_count": len(conflicting_row_indices),
        "model_visible_label_conflict_sample_rate": _rate(
            len(conflicting_row_indices),
            len(sample_records),
        ),
        "explicit_long_horizon_conflict_group_count": sum(
            int(bool(group["all_members_have_explicit_long_horizon_label"]))
            for group in conflict_groups
        ),
        "mixed_provenance_conflict_group_count": sum(
            int(bool(group["has_provenance_variation"])) for group in conflict_groups
        ),
        "conflict_field_counts": dict(sorted(conflict_field_counts.items())),
        "conflict_provenance_variation_counts": dict(
            sorted(conflict_provenance_counts.items())
        ),
        "conflicting_row_indices": conflicting_row_indices,
        "top_conflict_groups": conflict_groups[:10],
        "stage3_retrain_safe_without_repair": len(conflict_groups) == 0,
        "recommended_next_step": _recommended_next_step(conflict_groups),
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "default_enabled": False,
        "official_bound_effect": False,
        "selector_is_pricing_oracle": False,
        "selector_can_certificate": False,
        "gate_can_permanently_discard_negative_columns": False,
        "all_checks_pass": True,
    }
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(report, summary)
    return summary


def _sample_record(
    *,
    sample: Any,
    manifest_item: dict[str, Any],
    source_row: dict[str, Any],
) -> dict[str, Any]:
    model_visible_hash = _model_visible_hash(sample)
    candidate_signature_ids = [str(value) for value in manifest_item.get("candidate_signature_ids") or []]
    label_values = _label_values(sample, manifest_item)
    provenance = _provenance_record(source_row=source_row, manifest_item=manifest_item)
    action_key = _action_key(
        manifest_item=manifest_item,
        source_row=source_row,
        candidate_signature_ids=candidate_signature_ids,
    )
    return {
        "row_index": int(manifest_item.get("row_index") or -1),
        "path": str(manifest_item.get("path") or ""),
        "instance": str(manifest_item.get("instance") or ""),
        "instance_family": str(manifest_item.get("instance_family") or ""),
        "task_count": int(manifest_item.get("task_count") or 0),
        "context_hash": str(manifest_item.get("context_hash") or ""),
        "candidate_count": int(manifest_item.get("candidate_count") or 0),
        "candidate_signature_ids": candidate_signature_ids,
        "candidate_signature_ids_hash": _stable_json_hash(candidate_signature_ids),
        "model_visible_hash": model_visible_hash,
        "action_key": action_key,
        "action_key_hash": _stable_json_hash(action_key),
        "labels": label_values,
        "source_has_explicit_long_horizon_label": _has_explicit_long_horizon_label(source_row),
        "source_provenance": provenance,
        "diagnostic_only": True,
        "official_bound_effect": False,
    }


def _model_visible_hash(sample: Any) -> str:
    digest = hashlib.sha256()
    for name in MODEL_VISIBLE_TENSOR_ATTRS:
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        if not hasattr(sample, name):
            digest.update(b"<missing>")
            continue
        _update_digest_with_value(digest, getattr(sample, name))
        digest.update(b"\0")
    return digest.hexdigest()


def _update_digest_with_value(digest: "hashlib._Hash", value: Any) -> None:
    if isinstance(value, torch.Tensor):
        tensor = value.detach().cpu().contiguous()
        digest.update(str(tensor.dtype).encode("utf-8"))
        digest.update(str(tuple(int(dim) for dim in tensor.shape)).encode("utf-8"))
        digest.update(tensor.numpy().tobytes())
        return
    digest.update(json.dumps(_json_safe(value), sort_keys=True).encode("utf-8"))


def _label_values(sample: Any, manifest_item: dict[str, Any]) -> dict[str, Any]:
    labels: dict[str, Any] = {
        "manifest_label_batch_roi_positive": int(
            manifest_item.get("label_batch_roi_positive") or 0
        ),
        "manifest_accepted_batch_roi": _rounded_float(
            manifest_item.get("accepted_batch_roi")
        ),
        "manifest_high_priority_candidate_count": int(
            manifest_item.get("high_priority_candidate_count") or 0
        ),
        "manifest_delay_candidate_count": int(
            manifest_item.get("delay_candidate_count") or 0
        ),
    }
    for name in BATCH_LABEL_ATTRS:
        labels[name] = _tensor_json_value(getattr(sample, name, []))
    for name in CANDIDATE_LABEL_ATTRS:
        labels[name] = _tensor_json_value(getattr(sample, name, []))
    return labels


def _group_record(model_hash: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    conflict_fields = _conflict_fields(records)
    provenance_variation_fields = _provenance_variation_fields(records)
    member_rows = sorted(records, key=lambda row: int(row["row_index"]))
    accepted_rois = [
        _float_or_none(row["labels"].get("manifest_accepted_batch_roi"))
        for row in member_rows
    ]
    roi_values = [float(value) for value in accepted_rois if value is not None]
    return {
        "group_id": _stable_json_hash([model_hash, [row["row_index"] for row in member_rows]]),
        "model_visible_hash": model_hash,
        "sample_count": len(member_rows),
        "row_indices": [int(row["row_index"]) for row in member_rows],
        "paths": [str(row["path"]) for row in member_rows],
        "instances": sorted({str(row["instance"]) for row in member_rows}),
        "families": sorted({str(row["instance_family"]) for row in member_rows}),
        "task_counts": sorted({int(row["task_count"]) for row in member_rows}),
        "context_hashes": sorted({str(row["context_hash"]) for row in member_rows}),
        "candidate_signature_ids_hashes": sorted(
            {str(row["candidate_signature_ids_hash"]) for row in member_rows}
        ),
        "action_key_hashes": sorted({str(row["action_key_hash"]) for row in member_rows}),
        "has_label_conflict": bool(conflict_fields),
        "conflict_fields": conflict_fields,
        "has_binary_label_conflict": any(
            field
            for field in conflict_fields
            if field
            not in {
                "manifest_accepted_batch_roi",
                "y_accepted_batch_roi",
                "y_delta_v",
                "y_barrier_slack",
            }
        ),
        "has_regression_label_conflict": any(
            field
            for field in conflict_fields
            if field
            in {
                "manifest_accepted_batch_roi",
                "y_accepted_batch_roi",
                "y_delta_v",
                "y_barrier_slack",
            }
        ),
        "accepted_batch_roi_min": min(roi_values) if roi_values else None,
        "accepted_batch_roi_max": max(roi_values) if roi_values else None,
        "all_members_have_explicit_long_horizon_label": all(
            bool(row.get("source_has_explicit_long_horizon_label")) for row in member_rows
        ),
        "explicit_long_horizon_label_count": sum(
            int(bool(row.get("source_has_explicit_long_horizon_label"))) for row in member_rows
        ),
        "has_provenance_variation": bool(provenance_variation_fields),
        "provenance_variation_fields": provenance_variation_fields,
        "provenance_source_paths": sorted(
            {
                str(row["source_provenance"].get("v107_unique_source_path") or "")
                for row in member_rows
                if row["source_provenance"].get("v107_unique_source_path")
            }
        ),
        "provenance_roi_classes": sorted(
            {
                str(row["source_provenance"].get("ab_audit_roi_class") or "")
                for row in member_rows
                if row["source_provenance"].get("ab_audit_roi_class")
            }
        ),
        "members": [
            {
                "row_index": int(row["row_index"]),
                "path": str(row["path"]),
                "labels": row["labels"],
                "action_key": row["action_key"],
                "source_has_explicit_long_horizon_label": bool(
                    row["source_has_explicit_long_horizon_label"]
                ),
                "source_provenance": row["source_provenance"],
            }
            for row in member_rows
        ],
        "diagnostic_only": True,
        "official_bound_effect": False,
    }


def _conflict_fields(records: list[dict[str, Any]]) -> list[str]:
    keys: set[str] = set()
    for row in records:
        keys.update(str(key) for key in row["labels"].keys())
    conflict_fields: list[str] = []
    for key in sorted(keys):
        encoded_values = {_value_signature(row["labels"].get(key)) for row in records}
        if len(encoded_values) > 1:
            conflict_fields.append(key)
    return conflict_fields


def _provenance_variation_fields(records: list[dict[str, Any]]) -> list[str]:
    keys = (
        "v107_unique_source_path",
        "worker_source_files",
        "ab_audit_roi_class",
        "source_file",
        "final_judge_retry_delta",
        "pricing_tail_retry_delta",
        "pricing_calls_delta",
        "solving_time_delta",
        "generated_sequences_delta",
    )
    varied: list[str] = []
    for key in keys:
        encoded_values = {
            _value_signature(row["source_provenance"].get(key)) for row in records
        }
        if len(encoded_values) > 1:
            varied.append(key)
    return varied


def _provenance_record(
    *,
    source_row: dict[str, Any],
    manifest_item: dict[str, Any],
) -> dict[str, Any]:
    record: dict[str, Any] = {}
    for key in PROVENANCE_FIELDS:
        if key in source_row:
            record[key] = _json_safe(source_row.get(key))
    record.setdefault("source_file", manifest_item.get("source_file"))
    record.setdefault("context_hash", manifest_item.get("context_hash"))
    record.setdefault("instance", manifest_item.get("instance"))
    record["manifest_row_index"] = int(manifest_item.get("row_index") or -1)
    record["manifest_path"] = str(manifest_item.get("path") or "")
    record["manifest_label_batch_roi_positive"] = int(
        manifest_item.get("label_batch_roi_positive") or 0
    )
    record["manifest_accepted_batch_roi"] = _rounded_float(
        manifest_item.get("accepted_batch_roi")
    )
    return record


def _action_key(
    *,
    manifest_item: dict[str, Any],
    source_row: dict[str, Any],
    candidate_signature_ids: list[str],
) -> dict[str, Any]:
    return {
        "context_hash": str(manifest_item.get("context_hash") or source_row.get("context_hash") or ""),
        "cg_iter": _int_or_none(source_row.get("cg_iter")),
        "pricing_kind": str(source_row.get("pricing_kind") or ""),
        "node_id": _int_or_none(source_row.get("node_id")),
        "depth": _int_or_none(source_row.get("depth")),
        "candidate_signature_ids": candidate_signature_ids,
        "target_signature_samples": _json_safe(
            source_row.get("target_signature_samples")
            or source_row.get("target_materialized_signature_samples")
            or source_row.get("worker_returned_candidate_signature_samples")
            or []
        ),
    }


def _load_source_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw_path in manifest.get("source_jsonl_paths") or []:
        path = Path(str(raw_path))
        if not path.exists():
            continue
        with path.open(encoding="utf-8", errors="ignore") as handle:
            for line_number, line in enumerate(handle, start=1):
                text = line.strip()
                if not text:
                    continue
                try:
                    row = json.loads(text)
                except json.JSONDecodeError:
                    row = {}
                if not isinstance(row, dict):
                    row = {}
                row = dict(row)
                row["_source_input_jsonl"] = str(path)
                row["_source_input_line"] = int(line_number)
                rows.append(row)
    return rows


def _source_row_for_manifest_item(
    manifest_item: dict[str, Any],
    source_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    index = int(manifest_item.get("row_index") or -1)
    if 0 <= index < len(source_rows):
        return source_rows[index]
    return {}


def _has_explicit_long_horizon_label(row: dict[str, Any]) -> bool:
    for key in EXPLICIT_LONG_HORIZON_LABEL_FIELDS:
        if key in row and row.get(key) not in (None, ""):
            return True
    return False


def _tensor_json_value(value: Any) -> Any:
    if isinstance(value, torch.Tensor):
        values = value.detach().cpu().reshape(-1).tolist()
        return [_rounded_float(item) for item in values]
    if isinstance(value, (list, tuple)):
        return [_rounded_float(item) for item in value]
    return _json_safe(value)


def _value_signature(value: Any) -> str:
    return json.dumps(_json_safe(value), ensure_ascii=False, sort_keys=True)


def _stable_json_hash(value: Any) -> str:
    text = json.dumps(_json_safe(value), ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def _json_safe(value: Any) -> Any:
    if isinstance(value, torch.Tensor):
        return _tensor_json_value(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    if isinstance(value, float):
        return _rounded_float(value)
    try:
        if math.isnan(float(value)) or math.isinf(float(value)):
            return None
    except (TypeError, ValueError):
        pass
    return value


def _rounded_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    if abs(number) <= EPS:
        number = 0.0
    return round(number, 9)


def _float_or_none(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _rate(numerator: int, denominator: int) -> float | None:
    if int(denominator) <= 0:
        return None
    return float(numerator) / float(denominator)


def _recommended_next_step(conflict_groups: list[dict[str, Any]]) -> str:
    if not conflict_groups:
        return "no_model_visible_label_conflict_found_continue_focused_pair_gap_audit"
    explicit_groups = sum(
        int(bool(group["all_members_have_explicit_long_horizon_label"]))
        for group in conflict_groups
    )
    if explicit_groups == len(conflict_groups):
        return "deduplicate_or_drop_conflicting_explicit_long_horizon_groups_before_retraining"
    return "repair_label_provenance_priority_then_rebuild_dataset_before_retraining"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    conflict_groups = list(summary.get("top_conflict_groups") or [])
    lines = [
        "# BPC_future GAT Target Mode Stage 3 v119 标签来源冲突审计",
        "",
        f"日期：{_today_text()}",
        "",
        "## 结论",
        "",
    ]
    if int(summary["model_visible_label_conflict_group_count"]) > 0:
        lines.extend(
            [
                "当前 v116 数据集中仍存在模型可见输入完全相同、但 long-horizon / trajectory 标签互相矛盾的样本组。",
                "",
                "这不是继续调 loss multiplier 能解决的问题：同一个 GAT 输入被要求同时学习正负 admission 结论时，",
                "Stage 3 的 focused pair gate 和 false-delay gate 会互相拉扯。因此下一轮重训前应先在 dataset builder",
                "层面对这些冲突组做 deterministic repair：保守做法是丢弃整个冲突组，或在有严格、在线可用的来源优先级时只保留最高可信标签。",
            ]
        )
    else:
        lines.extend(
            [
                "本审计没有发现模型可见输入完全相同但标签冲突的样本组。",
                "",
                "这意味着 v118 top-context collision 至少不是当前全数据集中的普遍 label-provenance 冲突；",
                "下一步可以继续审计可见特征不足或 context-local ranking loss。",
            ]
        )
    lines.extend(
        [
            "",
            "## Exactness 边界",
            "",
            "- 只读取现有 manifest、sample tensor 和 source JSONL；",
            "- 不运行 BPC / pricing / RMP / worker；",
            "- 不生成 official bound 或 certificate；",
            "- GAT/kNN/OOD 不能永久丢弃 true-RC negative；",
            "- final certificate 仍只能来自 exact pricing full closure。",
            "",
            "## 机器字段",
            "",
            "```text",
            f"dataset_dir = {summary['dataset_dir']}",
            f"audited_sample_count = {summary['audited_sample_count']}",
            f"source_row_count = {summary['source_row_count']}",
            f"model_visible_unique_group_count = {summary['model_visible_unique_group_count']}",
            f"model_visible_duplicate_group_count = {summary['model_visible_duplicate_group_count']}",
            f"model_visible_label_conflict_group_count = {summary['model_visible_label_conflict_group_count']}",
            f"model_visible_label_conflict_sample_count = {summary['model_visible_label_conflict_sample_count']}",
            f"model_visible_label_conflict_sample_rate = {summary['model_visible_label_conflict_sample_rate']}",
            f"explicit_long_horizon_conflict_group_count = {summary['explicit_long_horizon_conflict_group_count']}",
            f"mixed_provenance_conflict_group_count = {summary['mixed_provenance_conflict_group_count']}",
            f"stage3_retrain_safe_without_repair = {str(summary['stage3_retrain_safe_without_repair']).lower()}",
            f"recommended_next_step = {summary['recommended_next_step']}",
            f"conflict_groups_path = {summary['conflict_groups_path']}",
            f"duplicate_groups_path = {summary['duplicate_groups_path']}",
            "```",
            "",
            "## 冲突字段统计",
            "",
            "```json",
            json.dumps(
                summary.get("conflict_field_counts") or {},
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            "```",
            "",
            "## 来源差异统计",
            "",
            "```json",
            json.dumps(
                summary.get("conflict_provenance_variation_counts") or {},
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            "```",
        ]
    )
    if conflict_groups:
        lines.extend(["", "## Top 冲突组", ""])
        for index, group in enumerate(conflict_groups[:10], start=1):
            lines.extend(
                [
                    f"### 组 {index}",
                    "",
                    "```text",
                    f"row_indices = {group['row_indices']}",
                    f"context_hashes = {group['context_hashes']}",
                    f"families = {group['families']}",
                    f"task_counts = {group['task_counts']}",
                    f"conflict_fields = {group['conflict_fields']}",
                    f"provenance_source_paths = {group['provenance_source_paths']}",
                    f"provenance_roi_classes = {group['provenance_roi_classes']}",
                    f"accepted_batch_roi_min = {group['accepted_batch_roi_min']}",
                    f"accepted_batch_roi_max = {group['accepted_batch_roi_max']}",
                    "```",
                    "",
                ]
            )
            for member in group["members"][:4]:
                provenance = member["source_provenance"]
                lines.extend(
                    [
                        f"- row {member['row_index']}: "
                        f"roi={member['labels'].get('manifest_accepted_batch_roi')}, "
                        f"batch_positive={member['labels'].get('manifest_label_batch_roi_positive')}, "
                        f"ab_class={provenance.get('ab_audit_roi_class')}, "
                        f"source={provenance.get('v107_unique_source_path')}",
                    ]
                )
            lines.append("")
    lines.extend(
        [
            "## Stage 3 判断",
            "",
            "本审计仍属于 Stage 3 offline diagnostic。即使模型可见标签冲突清零，后续 checkpoint",
            "仍必须证明同一 frozen threshold/OOD/fallback 规则下 precision、safe precision、ROI、",
            "coverage、focused pair 和 kNN/OOD gate 均通过，才能称为 Stage 4 candidate。",
            "",
            "## 下一步",
            "",
        ]
    )
    if conflict_groups:
        lines.extend(
            [
                "1. 在 `build_gat_batch_impact_dataset.py` 中增加 explicit long-horizon 同输入冲突组过滤或严格来源优先级。",
                "2. 重建 dataset，确认 `model_visible_label_conflict_group_count = 0`。",
                "3. 只在冲突清零后再重训 GAT；不要把离线 provenance 字段直接加进模型，除非线上 admission scheduler 也能稳定获得同一字段。",
            ]
        )
    else:
        lines.extend(
            [
                "1. 用当前冲突清零的数据集重训 Stage 3 GAT。",
                "2. 先跑 epoch selector / focused pair audit，确认 v118 的 collision blocker 是否消失。",
                "3. 只有 local gate 与 focused pair gate 同时过线后，再运行 kNN/OOD；仍不得把 diagnostic checkpoint 升级成 Stage 4 candidate。",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _today_text() -> str:
    from datetime import date

    return date.today().isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
