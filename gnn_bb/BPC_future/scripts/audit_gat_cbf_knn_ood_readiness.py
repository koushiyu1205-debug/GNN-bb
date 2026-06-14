#!/usr/bin/env python3
"""Audit whether the existing GAT can be used under the CBF kNN/OOD shell.

This is a read-only diagnostic.  It never runs BPC, pricing, RMP, or a worker,
and it never creates certificates or official bounds.  The intended contract is:

* GAT may provide trajectory/residual-family embeddings or impact predictions.
* kNN/OOD remains the conservative safety shell.
* unsafe true-RC negative columns must go to a delay queue, not be discarded.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


DEFAULT_SELECTOR_MANIFEST = Path("BPC_future/data/column_selector/v1/manifest.json")
DEFAULT_SELECTOR_SUMMARY = Path("BPC_future/data/column_selector/v1/summary.json")
DEFAULT_CHECKPOINT = Path("BPC_future/data/column_selector/v1/context_aware_column_selector.pt")
DEFAULT_TRAJECTORY_SUMMARY = Path(
    "BPC_future/results/cbf_trajectory_gate_dataset_global_all_h2_20260614/summary.json"
)
DEFAULT_KNN_OOD_SUMMARY = Path(
    "BPC_future/results/cbf_knn_ood_sector_wave_smoke_runbook_20260614/"
    "sector_wave_knn_ood_capture_validation/summary.json"
)
DEFAULT_GAT_EMBEDDING_VALIDATION_SUMMARY = Path(
    "BPC_future/results/gat_embedding_knn_ood_sector_wave_validation_20260614/summary.json"
)
DEFAULT_GAT_EMBEDDING_CAPTURE_VALIDATION_SUMMARY = Path(
    "BPC_future/results/gat_embedding_knn_ood_sector_wave_capture_validation_20260614/summary.json"
)
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/gat_cbf_knn_ood_readiness_20260614")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_gat_cbf_knn_ood_readiness_zh.md"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selector-manifest", type=Path, default=DEFAULT_SELECTOR_MANIFEST)
    parser.add_argument("--selector-summary", type=Path, default=DEFAULT_SELECTOR_SUMMARY)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--trajectory-summary", type=Path, default=DEFAULT_TRAJECTORY_SUMMARY)
    parser.add_argument("--knn-ood-summary", type=Path, default=DEFAULT_KNN_OOD_SUMMARY)
    parser.add_argument(
        "--gat-embedding-validation-summary",
        type=Path,
        default=DEFAULT_GAT_EMBEDDING_VALIDATION_SUMMARY,
    )
    parser.add_argument(
        "--gat-embedding-capture-validation-summary",
        type=Path,
        default=DEFAULT_GAT_EMBEDDING_CAPTURE_VALIDATION_SUMMARY,
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--min-trajectory-rows", type=int, default=100)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = audit_gat_cbf_knn_ood_readiness(
        selector_manifest=args.selector_manifest,
        selector_summary=args.selector_summary,
        checkpoint=args.checkpoint,
        trajectory_summary=args.trajectory_summary,
        knn_ood_summary=args.knn_ood_summary,
        gat_embedding_validation_summary=args.gat_embedding_validation_summary,
        gat_embedding_capture_validation_summary=args.gat_embedding_capture_validation_summary,
        output_dir=args.output_dir,
        report=args.report,
        min_trajectory_rows=int(args.min_trajectory_rows),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def audit_gat_cbf_knn_ood_readiness(
    *,
    selector_manifest: Path,
    selector_summary: Path,
    checkpoint: Path,
    trajectory_summary: Path,
    knn_ood_summary: Path,
    output_dir: Path,
    report: Path,
    gat_embedding_validation_summary: Path = DEFAULT_GAT_EMBEDDING_VALIDATION_SUMMARY,
    gat_embedding_capture_validation_summary: Path = DEFAULT_GAT_EMBEDDING_CAPTURE_VALIDATION_SUMMARY,
    min_trajectory_rows: int = 100,
) -> dict[str, Any]:
    manifest = _load_json_optional(selector_manifest)
    selector_summary_data = _load_json_optional(selector_summary)
    checkpoint_meta = _load_checkpoint_metadata(checkpoint)
    trajectory = _load_json_optional(trajectory_summary)
    knn_ood = _load_json_optional(knn_ood_summary)
    gat_embedding_validation = _load_json_optional(gat_embedding_validation_summary)
    gat_embedding_capture_validation = _load_json_optional(gat_embedding_capture_validation_summary)

    selector_dataset_contract = _selector_dataset_contract(manifest, selector_summary_data)
    checkpoint_contract = _checkpoint_contract(checkpoint_meta)
    trajectory_contract = _trajectory_dataset_contract(trajectory, min_rows=int(min_trajectory_rows))
    knn_contract = _knn_ood_contract(knn_ood)
    gat_embedding_contract = _gat_embedding_validation_contract(
        gat_embedding_validation,
        gat_embedding_capture_validation,
    )

    checks = {
        "diagnostic_only": True,
        "runs_bpc_or_pricing_false": True,
        "no_certificate_or_official_bound_effect": True,
        "gat_not_pricing_oracle": not checkpoint_contract["checkpoint_can_certificate"],
        "delay_queue_exactness_guard_required": True,
    }
    embedding_candidate_ready = bool(
        checkpoint_contract["has_embedding_model_config"]
        and checkpoint_contract["has_exactness_contract"]
        and selector_dataset_contract["has_horizon_cbf_label"]
        and checkpoint_contract["has_horizon_cbf_target"]
        and not selector_dataset_contract["column_level_add_skip_dataset"]
        and trajectory_contract["trajectory_rows_sufficient"]
        and trajectory_contract["has_horizon_labels"]
        and knn_contract["safety_shell_checks_pass"]
    )
    production_blockers = _production_blockers(
        selector_dataset_contract=selector_dataset_contract,
        checkpoint_contract=checkpoint_contract,
        trajectory_contract=trajectory_contract,
        knn_contract=knn_contract,
        gat_embedding_contract=gat_embedding_contract,
    )
    summary = {
        "schema_version": "gat_cbf_knn_ood_readiness_audit_v1",
        "status": "gat_cbf_knn_ood_readiness_audited",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "official_bound_effect": False,
        "selector_manifest": str(selector_manifest),
        "selector_summary": str(selector_summary),
        "checkpoint": str(checkpoint),
        "trajectory_summary": str(trajectory_summary),
        "knn_ood_summary": str(knn_ood_summary),
        "gat_embedding_validation_summary": str(gat_embedding_validation_summary),
        "gat_embedding_capture_validation_summary": str(gat_embedding_capture_validation_summary),
        "relationship": {
            "gat_role": "trajectory_or_residual_family_embedding_candidate",
            "knn_ood_role": "conservative_safety_shell",
            "gate_policy": "high_priority_or_delay_queue_never_permanent_reject_for_negative_columns",
            "pricing_oracle": False,
            "certificate_source": False,
        },
        "selector_dataset_contract": selector_dataset_contract,
        "checkpoint_contract": checkpoint_contract,
        "trajectory_dataset_contract": trajectory_contract,
        "knn_ood_shell_contract": knn_contract,
        "gat_embedding_validation_contract": gat_embedding_contract,
        "embedding_candidate_ready": embedding_candidate_ready,
        "production_ready": False,
        "production_blockers": production_blockers,
        "next_actions": _next_actions(
            selector_dataset_contract=selector_dataset_contract,
            checkpoint_contract=checkpoint_contract,
            gat_embedding_contract=gat_embedding_contract,
        ),
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    _write_report(report, summary)
    return summary


def _load_json_optional(path: Path) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        return {"_missing": True, "_path": str(path)}
    return json.loads(path.read_text(encoding="utf-8"))


def _load_checkpoint_metadata(path: Path) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        return {"_missing": True, "_path": str(path)}
    if path.suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    try:
        import torch  # type: ignore

        checkpoint = torch.load(path, map_location="cpu", weights_only=False)
    except Exception as exc:  # pragma: no cover - environment dependent.
        return {
            "_load_error": type(exc).__name__,
            "_load_error_message": str(exc),
            "_path": str(path),
        }
    if not isinstance(checkpoint, dict):
        return {"_load_error": "unexpected_checkpoint_type", "_path": str(path)}
    keep_keys = {
        "version",
        "schema_version",
        "selector_class_names",
        "exactness_contract",
        "model_config",
        "training",
        "target_label",
        "label_schema",
        "trajectory_contract",
    }
    return {key: checkpoint.get(key) for key in keep_keys if key in checkpoint}


def _selector_dataset_contract(manifest: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
    label_counts = manifest.get("label_counts") or summary.get("label_counts") or {}
    manifest_schema = str(manifest.get("schema_version", ""))
    summary_schema = str(summary.get("schema_version", ""))
    label_schema = manifest.get("label_schema") or summary.get("label_schema") or []
    if isinstance(label_schema, str):
        label_schema = [label_schema]
    has_horizon_label = "label_horizon_cbf_feasible" in set(str(item) for item in label_schema)
    manifest_is_legacy_selector = str(manifest.get("schema_version", "")).startswith(
        "gnn_column_selector"
    )
    summary_is_legacy_selector = str(summary.get("schema_version", "")).startswith(
        "gnn_column_selector"
    )
    column_level_features = bool(
        not has_horizon_label
        and (manifest_is_legacy_selector or summary_is_legacy_selector)
        and "candidate_feature_schema" in manifest
        and {"add", "skip"}.intersection(set(str(key) for key in label_counts))
    )
    return {
        "manifest_missing": bool(manifest.get("_missing")),
        "summary_missing": bool(summary.get("_missing")),
        "manifest_schema_version": manifest_schema or None,
        "summary_schema_version": summary_schema or None,
        "sample_count": int(manifest.get("sample_count") or summary.get("sample_count") or 0),
        "instance_count": int(summary.get("instance_count") or len(manifest.get("instance_counts") or {})),
        "label_counts": label_counts,
        "column_level_add_skip_dataset": column_level_features,
        "trajectory_horizon_cbf_dataset": has_horizon_label and not column_level_features,
        "has_horizon_cbf_label": has_horizon_label,
        "ready_for_trajectory_gat_training": has_horizon_label and not column_level_features,
    }


def _checkpoint_contract(checkpoint: dict[str, Any]) -> dict[str, Any]:
    class_names = checkpoint.get("selector_class_names") or []
    if isinstance(class_names, tuple):
        class_names = list(class_names)
    exactness_contract = checkpoint.get("exactness_contract")
    model_config = checkpoint.get("model_config")
    training = checkpoint.get("training") or {}
    label_schema = checkpoint.get("label_schema") or checkpoint.get("target_label") or checkpoint.get(
        "trajectory_contract"
    )
    label_text = json.dumps(label_schema, ensure_ascii=False, sort_keys=True)
    has_horizon_target = "label_horizon_cbf_feasible" in label_text
    can_certificate = bool(
        checkpoint.get("selector_can_certificate")
        or checkpoint.get("certificate_source")
        or checkpoint.get("pricing_oracle")
    )
    if exactness_contract and "never" in str(exactness_contract).lower():
        can_certificate = False
    return {
        "checkpoint_missing": bool(checkpoint.get("_missing")),
        "checkpoint_load_error": checkpoint.get("_load_error"),
        "version": checkpoint.get("version") or checkpoint.get("schema_version"),
        "selector_class_names": class_names,
        "has_exactness_contract": bool(exactness_contract),
        "exactness_contract": exactness_contract,
        "has_embedding_model_config": isinstance(model_config, dict) and bool(model_config),
        "model_config": model_config or {},
        "has_horizon_cbf_target": has_horizon_target,
        "checkpoint_can_certificate": can_certificate,
        "train_instances": (training.get("split") or {}).get("train_instances") or [],
        "validation_instances": (training.get("split") or {}).get("validation_instances") or [],
    }


def _trajectory_dataset_contract(summary: dict[str, Any], *, min_rows: int) -> dict[str, Any]:
    checks = summary.get("checks") or {}
    row_count = int(summary.get("row_count") or 0)
    feasible = int(summary.get("horizon_cbf_feasible_count") or 0)
    infeasible = int(summary.get("horizon_cbf_infeasible_count") or 0)
    return {
        "summary_missing": bool(summary.get("_missing")),
        "schema_version": summary.get("schema_version"),
        "row_count": row_count,
        "min_rows": int(min_rows),
        "trajectory_rows_sufficient": row_count >= int(min_rows),
        "has_horizon_labels": feasible > 0 and infeasible > 0,
        "horizon_cbf_feasible_count": feasible,
        "horizon_cbf_infeasible_count": infeasible,
        "diagnostic_only": bool(summary.get("diagnostic_only")),
        "no_certificate_effect": bool(checks.get("all_rows_no_certificate_effect")),
        "checks_pass": bool(summary.get("all_checks_pass")),
        "production_ready": bool(summary.get("production_ready")),
    }


def _knn_ood_contract(summary: dict[str, Any]) -> dict[str, Any]:
    external = summary.get("external_validation_summary") or {}
    metrics = external.get("validation_metrics", {}).get("overall", {})
    decision_reason_counts = external.get("decision_reason_counts") or {}
    predicted_positive = int(metrics.get("predicted_positive") or 0)
    false_positive = int(metrics.get("fp") or 0)
    checks = summary.get("checks") or {}
    external_checks = external.get("checks") or {}
    return {
        "summary_missing": bool(summary.get("_missing")),
        "safety_shell_checks_pass": bool(summary.get("all_checks_pass"))
        and bool(checks.get("delay_queue_proof_budget_guard_present"))
        and bool(external_checks.get("delay_queue_exactness_guard_present")),
        "validation_candidate_ready": bool(external.get("validation_candidate_ready")),
        "validation_row_count": int(external.get("validation_row_count") or 0),
        "predicted_positive": predicted_positive,
        "false_positive": false_positive,
        "has_productivity_signal": predicted_positive > 0,
        "decision_reason_counts": decision_reason_counts,
        "production_ready": bool(external.get("production_ready")) or bool(summary.get("production_ready")),
    }


def _gat_embedding_validation_contract(
    summary: dict[str, Any],
    capture_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    capture_summary = capture_summary or {}
    use_capture = bool(
        not capture_summary.get("_missing")
        and capture_summary.get("all_checks_pass") is True
        and isinstance(capture_summary.get("external_validation_summary"), dict)
    )
    source = capture_summary if use_capture else summary
    external = (
        source.get("external_validation_summary")
        if isinstance(source.get("external_validation_summary"), dict)
        else source
    )
    metrics = external.get("validation_metrics", {}).get("overall", {})
    predicted_positive = int(metrics.get("predicted_positive") or 0)
    false_positive = int(metrics.get("fp") or 0)
    checks = source.get("checks") or {}
    external_checks = external.get("checks") or {}
    return {
        "summary_missing": bool(source.get("_missing")),
        "evidence_source": "capture_validation" if use_capture else "external_validation",
        "capture_validation_available": use_capture,
        "checks_pass": bool(source.get("all_checks_pass")) and bool(external.get("all_checks_pass", True)),
        "validation_candidate_ready": bool(external.get("validation_candidate_ready")),
        "validation_row_count": int(external.get("validation_row_count") or source.get("validation_row_count") or 0),
        "predicted_positive": predicted_positive,
        "false_positive": false_positive,
        "precision": metrics.get("precision"),
        "recall": metrics.get("recall"),
        "production_ready": bool(source.get("production_ready")) or bool(external.get("production_ready")),
        "no_certificate_effect": source.get("official_bound_effect") is False
        and external.get("official_bound_effect", False) is False,
        "delay_queue_guard_present": (
            source.get("delay_queue_can_extend_proof_budget") is False
            and source.get("delay_queue_runs_proof_sweep") is False
        )
        or bool(checks.get("delay_queue_proof_budget_guard_present"))
        or bool(external_checks.get("delay_queue_proof_budget_guard_present")),
    }


def _production_blockers(
    *,
    selector_dataset_contract: dict[str, Any],
    checkpoint_contract: dict[str, Any],
    trajectory_contract: dict[str, Any],
    knn_contract: dict[str, Any],
    gat_embedding_contract: dict[str, Any],
) -> list[str]:
    blockers: list[str] = []
    if selector_dataset_contract["column_level_add_skip_dataset"]:
        blockers.append("gat_checkpoint_is_column_level_add_skip_not_trajectory_cbf")
    if not selector_dataset_contract["has_horizon_cbf_label"] and not checkpoint_contract["has_horizon_cbf_target"]:
        blockers.append("gat_training_contract_missing_label_horizon_cbf_feasible")
    if not checkpoint_contract["has_exactness_contract"]:
        blockers.append("gat_checkpoint_missing_exactness_contract")
    if not trajectory_contract["trajectory_rows_sufficient"]:
        blockers.append("trajectory_dataset_too_small_for_training_contract")
    if not trajectory_contract["has_horizon_labels"]:
        blockers.append("trajectory_dataset_missing_mixed_horizon_labels")
    if not knn_contract["safety_shell_checks_pass"]:
        blockers.append("knn_ood_safety_shell_not_validated")
    if not knn_contract["has_productivity_signal"] and not gat_embedding_contract["validation_candidate_ready"]:
        blockers.append("sector_wave_knn_ood_smoke_has_no_high_priority_productivity_signal")
    if not gat_embedding_contract["validation_candidate_ready"]:
        blockers.append("no_gat_embedding_knn_ood_external_validation_yet")
    blockers.extend(
        [
            "no_5_10_no_regression_bpc_ab_yet",
            "no_20_task_wall_time_roi_ab_yet",
            "no_online_opt_in_solver_integration_yet",
        ]
    )
    return blockers


def _next_actions(
    *,
    selector_dataset_contract: dict[str, Any],
    checkpoint_contract: dict[str, Any],
    gat_embedding_contract: dict[str, Any],
) -> list[str]:
    actions: list[str] = []
    if not selector_dataset_contract["ready_for_trajectory_gat_training"]:
        actions.append("build trajectory-labeled GAT dataset with label_horizon_cbf_feasible targets")
    if not checkpoint_contract["has_horizon_cbf_target"]:
        actions.append("train GAT impact/barrier head with horizon CBF targets")
    if not gat_embedding_contract["validation_candidate_ready"]:
        actions.append("validate GAT embeddings with kNN/OOD on independent sector-wave captures")
    actions.extend(
        [
            "run audit-only 5/10 no-regression and 20-sector-wave ROI smoke before any online effect",
            "keep certificate and official lower-bound paths on exact final judge only",
        ]
    )
    return actions


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GAT + CBF kNN/OOD Readiness 审计报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "确认现有 GAT 是否可以进入 CBF/kNN/OOD 生产化链路。该审计只读现有",
        "manifest、checkpoint 和 validation summary，不运行 BPC / pricing / RMP，",
        "不生成列，也不产生 certificate 或 official bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "gat_cbf_knn_ood_readiness = current",
        f"status = {summary['status']}",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"official_bound_effect = {str(summary['official_bound_effect']).lower()}",
        f"embedding_candidate_ready = {str(summary['embedding_candidate_ready']).lower()}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 关系结论",
        "",
        "- GAT 的正确角色是 trajectory / residual-family embedding 或 impact predictor。",
        "- kNN+OOD 的正确角色是 conservative safety shell。",
        "- GAT 不能成为 pricing oracle、certificate source 或 official lower-bound source。",
        "- kNN/OOD 判为 unsafe 的 true-RC negative column 只能进入 delay queue，不能永久丢弃。",
        "",
        "## 当前审计结论",
        "",
        "```json",
        json.dumps(
            {
                "selector_dataset_contract": summary["selector_dataset_contract"],
                "checkpoint_contract": summary["checkpoint_contract"],
                "trajectory_dataset_contract": summary["trajectory_dataset_contract"],
                "knn_ood_shell_contract": summary["knn_ood_shell_contract"],
                "gat_embedding_validation_contract": summary["gat_embedding_validation_contract"],
                "embedding_candidate_ready": summary["embedding_candidate_ready"],
                "production_ready": summary["production_ready"],
                "production_blockers": summary["production_blockers"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## 下一步",
        "",
    ]
    lines.extend(f"- {item}" for item in summary["next_actions"])
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
