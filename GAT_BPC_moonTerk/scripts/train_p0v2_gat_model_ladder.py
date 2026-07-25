#!/usr/bin/env python3
"""Train the smallest-first P0 V2 pricing model ladder.

Input JSONL rows are already materialized pricing snapshots.  This command
never reads calibration or protected test rows and never writes an online
eligibility manifest; checkpoints remain shadow artifacts until separately
promoted.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
from statistics import mean
from time import perf_counter

import torch
from torch.nn import functional as F

from lunar_ice_bpc.exact.core.cuts import stable_payload_hash
from lunar_ice_bpc.guidance.models import (
    MODEL_LADDER,
    MODEL_ARCHITECTURE_VERSION,
    build_model,
    checkpoint_payload,
)
from lunar_ice_bpc.guidance.resources import (
    recommended_parallelism,
    resource_snapshot,
)
from lunar_ice_bpc.guidance.tensorization import (
    COMPOSITE_FEATURE_SCHEMA_V3,
    HARVEST_MODEL_CONTEXT_SCHEMA_V2,
    learned_harvest_context,
)
from lunar_ice_bpc.guidance.training import (
    EMALossNormalizer,
    HEAD_SCALE_WEIGHTS,
    counterfactual_soft_listwise_loss,
    discrete_time_survival_nll,
    gradient_cosine,
    survival_ranking_loss,
    survival_concordance_loss,
    should_enable_pcgrad,
)
from lunar_ice_bpc.guidance.trajectory_targets import (
    COUNTERFACTUAL_TRAINING_OBJECTIVE_V2,
    FIXED_POOL_PRICING_PRESSURE_OBJECTIVE_SPEC_V1,
    ORACLE_HEADROOM_AUDIT_SCHEMA_V1,
)
from lunar_ice_bpc.guidance.opportunity_gate import (
    OPPORTUNITY_ROI_AUDIT_SCHEMA_V1,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records-jsonl", required=True)
    parser.add_argument("--split-manifest", required=True)
    parser.add_argument(
        "--static-cache-dir",
        default="data/gat_p0v2/static_tensor_cache",
    )
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--source-baseline-id", required=True)
    parser.add_argument(
        "--engine-hash",
        required=True,
        action="append",
        help=(
            "Repeat for each exact backend hash represented by the shared "
            "cross-scale checkpoint."
        ),
    )
    parser.add_argument("--feature-schema-version", required=True)
    parser.add_argument("--ood-policy-version", required=True)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--shadow-head-epochs", type=int, default=10)
    parser.add_argument("--learning-rate", type=float, default=1.0e-3)
    parser.add_argument(
        "--training-objective",
        choices=(
            COUNTERFACTUAL_TRAINING_OBJECTIVE_V2,
            "legacy_graded_listwise",
        ),
        default=COUNTERFACTUAL_TRAINING_OBJECTIVE_V2,
        help=(
            "The default rejects grade-only rows. The legacy objective is "
            "retained solely for frozen B0 diagnostics and cannot produce "
            "a promotable checkpoint."
        ),
    )
    parser.add_argument(
        "--counterfactual-main-scope",
        choices=(
            "harvest_only",
            "harvest_and_task_arc_experimental",
        ),
        default="harvest_only",
        help=(
            "The reviewed first stage trains only route-level harvest. "
            "Task/arc priority remains a non-promotable mechanism experiment."
        ),
    )
    parser.add_argument(
        "--oracle-headroom-report",
        default="",
        help=(
            "Required for formal route-level counterfactual training. The "
            "report must be bound to --records-jsonl and pass before Torch "
            "optimization is allowed."
        ),
    )
    parser.add_argument(
        "--opportunity-observations-jsonl",
        default="",
        help=(
            "Unbiased sentinel plus targeted opportunity observations. "
            "Required for formal route-level training."
        ),
    )
    parser.add_argument(
        "--opportunity-roi-report",
        default="",
        help=(
            "Must be bound to --opportunity-observations-jsonl and prove "
            "positive perfect-policy net ROI before optimization starts."
        ),
    )
    parser.add_argument("--fold", type=int, action="append")
    parser.add_argument(
        "--final-selection-report",
        default="",
        help=(
            "Train one final all-development checkpoint only after the "
            "cross-validation model-rung selection report has passed."
        ),
    )
    parser.add_argument(
        "--models",
        nargs="+",
        choices=MODEL_LADDER,
        default=["linear", "mlp2x32"],
        help=(
            "First invocation defaults to the linear/MLP rung. Add a GAT "
            "kind only after smaller models fail the paired promotion target."
        ),
    )
    parser.add_argument("--torch-threads", type=int, default=2)
    parser.add_argument(
        "--max-contexts-per-instance-head-phase",
        type=int,
        default=8,
        help=(
            "Deterministic bounded reservoir retained before training. One "
            "context per head/scale/instance/phase is rotated into each epoch."
        ),
    )
    args = parser.parse_args()
    oracle_headroom = _load_oracle_headroom_gate(
        args.oracle_headroom_report,
        records_path=Path(args.records_jsonl),
        required=bool(
            str(args.training_objective)
            == COUNTERFACTUAL_TRAINING_OBJECTIVE_V2
            and args.counterfactual_main_scope == "harvest_only"
        ),
    )
    formal_counterfactual_training = bool(
        str(args.training_objective)
        == COUNTERFACTUAL_TRAINING_OBJECTIVE_V2
        and args.counterfactual_main_scope == "harvest_only"
    )
    opportunity_roi = _load_opportunity_roi_gate(
        args.opportunity_roi_report,
        observations_path=str(args.opportunity_observations_jsonl),
        required=formal_counterfactual_training,
    )
    model_kinds = [
        kind for kind in MODEL_LADDER if kind in set(args.models)
    ]

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    resources = resource_snapshot(output_dir)
    torch_threads = recommended_parallelism(
        resources, requested=max(1, args.torch_threads)
    )
    torch.set_num_threads(torch_threads)
    manifest = json.loads(
        Path(args.split_manifest).read_text(encoding="utf-8")
    )
    if not bool((manifest.get("audit") or {}).get("passed")):
        raise SystemExit("split manifest audit did not pass")
    assignment = {
        str(row["instance_content_hash"]): int(row["fold"])
        for row in manifest.get("development", ())
    }
    forbidden = {
        str(row["instance_content_hash"])
        for partition in ("calibration", "protected_final_test")
        for row in manifest.get(partition, ())
    }
    maximum_contexts = max(
        1, int(args.max_contexts_per_instance_head_phase)
    )
    bounded_records = defaultdict(dict)
    raw_record_count = 0
    for line in Path(args.records_jsonl).open(encoding="utf-8"):
        if not line.strip():
            continue
        raw_record_count += 1
        row = json.loads(line)
        content_hash = str(row["instance_content_hash"])
        if content_hash in forbidden:
            raise SystemExit(
                f"forbidden calibration/test row present in training JSONL: {content_hash}"
            )
        if content_hash not in assignment:
            raise SystemExit(
                f"training row is absent from development manifest: {content_hash}"
            )
        head = str(row.get("head") or "exact_pricing")
        if head not in {"exact_pricing", "harvest", "proof_risk", "branch"}:
            raise SystemExit(f"unsupported training head {head!r}")
        row["head"] = head
        if head in {"exact_pricing", "harvest"}:
            observed_objective = str(
                row.get("training_objective")
                or "legacy_graded_listwise"
            )
            if observed_objective != str(args.training_objective):
                raise SystemExit(
                    "main-head training objective mismatch: "
                    f"requested={args.training_objective!r}, "
                    f"row={observed_objective!r}"
                )
        if (
            head == "harvest"
            and str(args.training_objective)
            == COUNTERFACTUAL_TRAINING_OBJECTIVE_V2
            and args.counterfactual_main_scope == "harvest_only"
        ):
            if not bool(
                row.get(
                    "harvest_counterfactual_formal_first_stage_eligible"
                )
            ):
                raise SystemExit(
                    "formal first-stage training rejects diagnostic or "
                    "noncompliant harvest trajectories"
                )
            if str(
                row.get("harvest_counterfactual_candidate_kind") or ""
            ) != "harvest":
                raise SystemExit(
                    "formal first-stage training requires route-level "
                    "harvest actions"
                )
            if str(
                row.get(
                    "harvest_counterfactual_trajectory_objective_spec_id"
                )
                or ""
            ) != FIXED_POOL_PRICING_PRESSURE_OBJECTIVE_SPEC_V1:
                raise SystemExit(
                    "formal first-stage training objective spec mismatch"
                )
        scale = int(row["scale"])
        if head == "exact_pricing" and scale not in {5, 10, 20, 30}:
            raise SystemExit("exact-pricing head may only train on scales 5/10/20/30")
        if head == "branch" and scale not in {5, 10, 20, 30}:
            raise SystemExit("branch head may only train on scales 5/10/20/30")
        row["fold"] = assignment[content_hash]
        group_key = (
            head,
            scale,
            content_hash,
            str(row.get("node_phase") or ""),
        )
        context_key = (
            str(row.get("rmp_context_hash") or ""),
            str(row.get("candidate_id") or ""),
        )
        current = bounded_records[group_key].get(context_key)
        if current is None or _observed_label_count(
            row
        ) > _observed_label_count(current):
            bounded_records[group_key][context_key] = row
        if len(bounded_records[group_key]) > maximum_contexts:
            drop_key = max(
                bounded_records[group_key],
                key=lambda key: stable_payload_hash(
                    {
                        "group": group_key,
                        "context": key,
                    }
                ),
            )
            bounded_records[group_key].pop(drop_key)
    records = [
        row
        for group_key in sorted(bounded_records)
        for _, row in sorted(bounded_records[group_key].items())
    ]
    if not records:
        raise SystemExit("no development records")
    static_cache = _load_static_tensor_cache(
        records, cache_dir=Path(args.static_cache_dir)
    )
    harvest_rows = [row for row in records if row["head"] == "harvest"]
    if harvest_rows and str(args.feature_schema_version) != (
        COMPOSITE_FEATURE_SCHEMA_V3
    ):
        raise SystemExit(
            "harvest training requires composite feature schema "
            f"{COMPOSITE_FEATURE_SCHEMA_V3}"
        )
    large_harvest_rows = [
        row for row in harvest_rows if int(row["scale"]) in {50, 100}
    ]
    if harvest_rows and len(large_harvest_rows) / len(harvest_rows) > 0.10:
        raise SystemExit(
            "scale50/100 harvest observed rows exceed the 10% contract"
        )

    fold_count = int(manifest["fold_count"])
    folds = sorted(set(args.fold or range(fold_count)))
    report = {
        "schema_version": "lunar_ice_bpc.gat_model_ladder_training.v2",
        "source_baseline_id": args.source_baseline_id,
        "training_objective": str(args.training_objective),
        "trajectory_objective_spec_id": (
            FIXED_POOL_PRICING_PRESSURE_OBJECTIVE_SPEC_V1
            if formal_counterfactual_training
            else ""
        ),
        "legacy_objective_diagnostic_only": (
            str(args.training_objective) == "legacy_graded_listwise"
        ),
        "model_architecture_version": MODEL_ARCHITECTURE_VERSION,
        "counterfactual_main_scope": str(
            args.counterfactual_main_scope
        ),
        "oracle_headroom_gate": oracle_headroom,
        "opportunity_roi_gate": opportunity_roi,
        "split_manifest_hash": manifest.get("manifest_hash"),
        "calibration_used": False,
        "protected_final_test_used": False,
        "torch_threads": torch_threads,
        "resource_snapshot": resources.__dict__,
        "requested_model_rungs": model_kinds,
        "head_sampling_order": (
            "head->scale->instance->node_phase->rmp_context->candidates"
        ),
        "raw_materialized_context_count": raw_record_count,
        "bounded_retained_context_count": len(records),
        "max_contexts_per_instance_head_phase": maximum_contexts,
        "epoch_context_policy": (
            "one_deterministically_rotated_context_per_"
            "head_scale_instance_phase"
        ),
        "static_tensor_cache_entry_count": len(static_cache),
        "large_harvest_row_fraction": (
            0.0
            if not harvest_rows
            else len(large_harvest_rows) / len(harvest_rows)
        ),
        "harvest_model_context_schema_version": (
            HARVEST_MODEL_CONTEXT_SCHEMA_V2
        ),
        "runs": [],
    }
    if args.final_selection_report:
        if args.fold:
            raise SystemExit(
                "--fold cannot be combined with --final-selection-report"
            )
        selection = json.loads(
            Path(args.final_selection_report).read_text(encoding="utf-8")
        )
        if not bool(selection.get("passed")):
            raise SystemExit("final training requires a passed selection report")
        if str(selection.get("split_manifest_hash") or "") != str(
            manifest.get("manifest_hash") or ""
        ):
            raise SystemExit("selection report split manifest mismatch")
        if bool(selection.get("calibration_used")) or bool(
            selection.get("protected_final_test_used")
        ):
            raise SystemExit(
                "selection report illegally used calibration/protected data"
            )
        if str(selection.get("training_objective") or "") != str(
            args.training_objective
        ):
            raise SystemExit("selection report training objective mismatch")
        selected_kind = str(selection.get("selected_model_kind") or "")
        if selected_kind not in MODEL_LADDER:
            raise SystemExit("selection report has no valid selected model")
        report["mode"] = "final_all_development_after_cross_validation"
        report["model_rung_selection_report"] = str(
            Path(args.final_selection_report).resolve()
        )
        report["model_rung_selection_report_hash"] = stable_payload_hash(
            selection
        )
        report["runs"].append(
            _train_final_checkpoint(
                records,
                static_cache=static_cache,
                model_kind=selected_kind,
                output_dir=output_dir,
                manifest=manifest,
                source_baseline_id=args.source_baseline_id,
                engine_hashes=tuple(args.engine_hash),
                feature_schema_version=args.feature_schema_version,
                ood_policy_version=args.ood_policy_version,
                training_objective=str(args.training_objective),
                counterfactual_main_scope=str(
                    args.counterfactual_main_scope
                ),
                epochs=max(1, int(args.epochs)),
                shadow_head_epochs=max(
                    1, int(args.shadow_head_epochs)
                ),
                learning_rate=float(args.learning_rate),
                pcgrad_enabled=bool(
                    selection.get("selected_pcgrad_enabled")
                ),
                selection_report_hash=report[
                    "model_rung_selection_report_hash"
                ],
            )
        )
        report["model_ladder_rule"] = (
            "Final checkpoint uses all development rows only after the "
            "smallest-model cross-validation selection was frozen."
        )
        report_path = output_dir / "final_checkpoint_training_report.json"
        report_path.write_text(
            json.dumps(
                report, ensure_ascii=False, indent=2, sort_keys=True
            )
            + "\n",
            encoding="utf-8",
        )
        print(str(report_path.resolve()))
        return 0
    for fold in folds:
        train_rows = [row for row in records if int(row["fold"]) != fold]
        validation_rows = [row for row in records if int(row["fold"]) == fold]
        if not train_rows or not validation_rows:
            raise SystemExit(f"fold {fold} has empty train or validation rows")
        normalization = _fit_normalization(
            train_rows, static_cache=static_cache
        )
        normalization_version = (
            f"fold{fold}-training-only-{manifest.get('manifest_hash', '')[:12]}"
        )
        main_head_names = (
            {"harvest"}
            if (
                str(args.training_objective)
                == COUNTERFACTUAL_TRAINING_OBJECTIVE_V2
                and args.counterfactual_main_scope == "harvest_only"
            )
            else {"exact_pricing", "harvest"}
        )
        main_train_rows = [
            row
            for row in train_rows
            if row["head"] in main_head_names
        ]
        main_validation_rows = [
            row
            for row in validation_rows
            if row["head"] in main_head_names
        ]
        shadow_train_rows = [
            row
            for row in train_rows
            if row["head"] in {"proof_risk", "branch"}
        ]
        shadow_validation_rows = [
            row
            for row in validation_rows
            if row["head"] in {"proof_risk", "branch"}
        ]
        if not main_train_rows or not main_validation_rows:
            raise SystemExit(
                f"fold {fold} needs {sorted(main_head_names)} main-head rows"
            )
        for kind in model_kinds:
            started = perf_counter()
            node_dim, edge_dim = _feature_dimensions(
                train_rows[0], static_cache=static_cache
            )
            model = build_model(
                kind, node_input_dim=node_dim, edge_input_dim=edge_dim
            )
            optimizer = torch.optim.Adam(
                model.parameters(), lr=float(args.learning_rate)
            )
            normalizer = EMALossNormalizer()
            epoch_rows = []
            validation_gradient_cosines = []
            pcgrad_enabled = False
            for epoch in range(max(1, int(args.epochs))):
                model.train()
                (
                    train_loss,
                    per_scale,
                    train_cosine,
                    train_diagnostics,
                ) = _run_epoch(
                    model,
                    _epoch_context_sample(main_train_rows, epoch),
                    normalization,
                    optimizer=optimizer,
                    loss_normalizer=normalizer,
                    pcgrad_enabled=pcgrad_enabled,
                    static_cache=static_cache,
                )
                model.eval()
                with torch.enable_grad():
                    (
                        validation_loss,
                        _,
                        validation_cosine,
                        validation_diagnostics,
                    ) = _run_epoch(
                        model,
                        _epoch_context_sample(main_validation_rows, 0),
                        normalization,
                        optimizer=None,
                        loss_normalizer=None,
                        pcgrad_enabled=False,
                        static_cache=static_cache,
                    )
                validation_gradient_cosines.append(validation_cosine)
                pcgrad_enabled = pcgrad_enabled or should_enable_pcgrad(
                    validation_gradient_cosines
                )
                epoch_rows.append(
                    {
                        "epoch": epoch + 1,
                        "train_loss": train_loss,
                        "validation_loss": validation_loss,
                        "task_arc_gradient_cosine_train": train_cosine,
                        "task_arc_gradient_cosine_validation": validation_cosine,
                        "per_scale_loss_contribution": per_scale,
                        "per_head_loss": train_diagnostics["per_head_loss"],
                        "encoder_gradient_norm_by_head": train_diagnostics[
                            "encoder_gradient_norm_by_head"
                        ],
                        "gradient_cosine_by_head_pair_train": train_diagnostics[
                            "gradient_cosine_by_head_pair"
                        ],
                        "gradient_cosine_by_head_pair_validation": (
                            validation_diagnostics[
                                "gradient_cosine_by_head_pair"
                            ]
                        ),
                        "pcgrad_triggered": pcgrad_enabled,
                        "note": (
                            "PCGrad will be active from the next training epoch."
                            if pcgrad_enabled
                            else ""
                        ),
                    }
                )
            shadow_epoch_rows = []
            trained_shadow_heads = sorted(
                {row["head"] for row in shadow_train_rows}
            )
            if shadow_train_rows:
                _freeze_for_shadow_heads(model, trained_shadow_heads)
                shadow_parameters = [
                    parameter
                    for parameter in model.parameters()
                    if parameter.requires_grad
                ]
                shadow_optimizer = torch.optim.Adam(
                    shadow_parameters, lr=float(args.learning_rate)
                )
                shadow_normalizer = EMALossNormalizer()
                for shadow_epoch in range(
                    max(1, int(args.shadow_head_epochs))
                ):
                    model.train()
                    (
                        shadow_train_loss,
                        shadow_per_scale,
                        _,
                        shadow_train_diagnostics,
                    ) = _run_epoch(
                        model,
                        _epoch_context_sample(
                            shadow_train_rows, shadow_epoch
                        ),
                        normalization,
                        optimizer=shadow_optimizer,
                        loss_normalizer=shadow_normalizer,
                        pcgrad_enabled=False,
                        static_cache=static_cache,
                    )
                    model.eval()
                    if shadow_validation_rows:
                        with torch.enable_grad():
                            (
                                shadow_validation_loss,
                                _,
                                _,
                                shadow_validation_diagnostics,
                            ) = _run_epoch(
                                model,
                                _epoch_context_sample(
                                    shadow_validation_rows, 0
                                ),
                                normalization,
                                optimizer=None,
                                loss_normalizer=None,
                                pcgrad_enabled=False,
                                static_cache=static_cache,
                            )
                    else:
                        shadow_validation_loss = None
                        shadow_validation_diagnostics = {}
                    shadow_epoch_rows.append(
                        {
                            "epoch": shadow_epoch + 1,
                            "train_loss": shadow_train_loss,
                            "validation_loss": shadow_validation_loss,
                            "per_scale_loss_contribution": shadow_per_scale,
                            "per_head_loss": shadow_train_diagnostics[
                                "per_head_loss"
                            ],
                            "validation_diagnostics": (
                                shadow_validation_diagnostics
                            ),
                            "encoder_frozen": True,
                        }
                    )
                for parameter in model.parameters():
                    parameter.requires_grad_(True)
            checkpoint_id = (
                f"p0v2-{kind}-fold{fold}-"
                f"{manifest.get('manifest_hash', '')[:12]}"
            )
            metadata = {
                "checkpoint_id": checkpoint_id,
                "source_baseline_id": args.source_baseline_id,
                "engine_hash": args.engine_hash[0],
                "compatible_engine_hashes": sorted(set(args.engine_hash)),
                "split_manifest_hash": manifest.get("manifest_hash"),
                "fold": fold,
                "feature_schema_version": args.feature_schema_version,
                "harvest_model_context_schema_version": (
                    HARVEST_MODEL_CONTEXT_SCHEMA_V2
                ),
                "normalization_version": normalization_version,
                "ood_policy_version": args.ood_policy_version,
                "node_feature_mean": normalization["node_mean"],
                "node_feature_std": normalization["node_std"],
                "edge_feature_mean": normalization["edge_mean"],
                "edge_feature_std": normalization["edge_std"],
                "normalization_weighting": normalization["weighting"],
                "normalization_unique_context_count": normalization[
                    "unique_context_count"
                ],
                "ood_max_abs_z": None,
                "ood_calibrated": False,
                "online_eligible": False,
                "training_objective": str(args.training_objective),
                "trajectory_objective_spec_id": (
                    FIXED_POOL_PRICING_PRESSURE_OBJECTIVE_SPEC_V1
                    if str(args.training_objective)
                    == COUNTERFACTUAL_TRAINING_OBJECTIVE_V2
                    else ""
                ),
                "legacy_objective_diagnostic_only": (
                    str(args.training_objective)
                    == "legacy_graded_listwise"
                ),
                "model_architecture_version": MODEL_ARCHITECTURE_VERSION,
                "counterfactual_main_scope": str(
                    args.counterfactual_main_scope
                ),
                "p0_noop_trained": (
                    str(args.training_objective)
                    == COUNTERFACTUAL_TRAINING_OBJECTIVE_V2
                ),
                "auxiliary_encoder_gradient_fraction": (
                    0.0
                    if str(args.training_objective)
                    == COUNTERFACTUAL_TRAINING_OBJECTIVE_V2
                    else None
                ),
                "trajectory_curve_shared_encoder": False,
                "proof_head_encoder_frozen": True,
                "branch_head_encoder_frozen": True,
                "trained_main_heads": sorted(
                    {row["head"] for row in main_train_rows}
                ),
                "trained_shadow_heads": trained_shadow_heads,
            }
            checkpoint_path = output_dir / f"{checkpoint_id}.pt"
            torch.save(
                checkpoint_payload(model, metadata=metadata),
                checkpoint_path,
            )
            report["runs"].append(
                {
                    "fold": fold,
                    "model_kind": kind,
                    "checkpoint_id": checkpoint_id,
                    "checkpoint_path": str(checkpoint_path.resolve()),
                    "parameter_count": sum(
                        parameter.numel() for parameter in model.parameters()
                    ),
                    "training_wall_sec": perf_counter() - started,
                    "final_train_loss": epoch_rows[-1]["train_loss"],
                    "final_validation_loss": epoch_rows[-1]["validation_loss"],
                    "pcgrad_triggered": pcgrad_enabled,
                    "epochs": epoch_rows,
                    "shadow_head_epochs": shadow_epoch_rows,
                }
            )
    report["model_ladder_rule"] = (
        "A larger model is not promoted from this loss report alone. It must "
        "show paired end-to-end significance under equal budgets and pass "
        "safety, small-scale, overhead, and Holm-corrected gates."
    )
    report_path = output_dir / "model_ladder_training_report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(str(report_path.resolve()))
    return 0


def _load_oracle_headroom_gate(
    report_path: str,
    *,
    records_path: Path,
    required: bool,
) -> dict:
    """Bind training authorization to an independently written headroom audit."""

    if not str(report_path).strip():
        if required:
            raise SystemExit(
                "formal counterfactual training requires "
                "--oracle-headroom-report"
            )
        return {
            "required": False,
            "passed": False,
            "training_authorized": False,
        }
    source = Path(report_path)
    report = json.loads(source.read_text(encoding="utf-8"))
    if str(report.get("schema_version") or "") != (
        ORACLE_HEADROOM_AUDIT_SCHEMA_V1
    ):
        raise SystemExit("oracle headroom report schema mismatch")
    records_sha256 = hashlib.sha256(records_path.read_bytes()).hexdigest()
    if str(report.get("records_jsonl_sha256") or "") != records_sha256:
        raise SystemExit(
            "oracle headroom report is not bound to training records"
        )
    if bool(report.get("calibration_used")) or bool(
        report.get("protected_final_test_used")
    ):
        raise SystemExit(
            "oracle headroom report used calibration/protected data"
        )
    if required and (
        not bool(report.get("passed"))
        or not bool(report.get("training_authorized"))
        or not bool(report.get("linear_training_authorized"))
        or str(report.get("route_admission_decision") or "")
        != "ALLOW_LINEAR_TRAINING"
    ):
        raise SystemExit(
            "oracle headroom gate failed; revise the ordering action before "
            "training a model"
        )
    return {
        "required": required,
        "passed": bool(report.get("passed")),
        "training_authorized": bool(
            report.get("training_authorized")
        ),
        "report_path": str(source.resolve()),
        "report_hash": stable_payload_hash(report),
        "records_jsonl_sha256": records_sha256,
        "required_scales": list(report.get("required_scales") or ()),
        "worst_required_scale_mean_oracle_gain_lcb95": report.get(
            "worst_required_scale_mean_oracle_gain_lcb95"
        ),
    }


def _load_opportunity_roi_gate(
    report_path: str,
    *,
    observations_path: str,
    required: bool,
) -> dict:
    """Bind training to unbiased density and amortized net-benefit evidence."""

    if not str(report_path).strip() or not str(observations_path).strip():
        if required:
            raise SystemExit(
                "formal counterfactual training requires both "
                "--opportunity-observations-jsonl and "
                "--opportunity-roi-report"
            )
        return {
            "required": False,
            "passed": False,
            "training_authorized": False,
        }
    source = Path(report_path)
    observations = Path(observations_path)
    report = json.loads(source.read_text(encoding="utf-8"))
    if str(report.get("schema_version") or "") != (
        OPPORTUNITY_ROI_AUDIT_SCHEMA_V1
    ):
        raise SystemExit("opportunity ROI report schema mismatch")
    observations_sha256 = hashlib.sha256(
        observations.read_bytes()
    ).hexdigest()
    if str(report.get("observations_jsonl_sha256") or "") != (
        observations_sha256
    ):
        raise SystemExit(
            "opportunity ROI report is not bound to observations JSONL"
        )
    if bool(report.get("calibration_used")) or bool(
        report.get("protected_final_test_used")
    ):
        raise SystemExit(
            "opportunity ROI report used calibration/protected data"
        )
    if not bool(
        report.get("targeted_rows_excluded_from_population_estimates")
    ):
        raise SystemExit(
            "opportunity ROI report mixed targeted rows into population rates"
        )
    if required and (
        not bool(report.get("passed"))
        or not bool(report.get("training_authorized"))
    ):
        raise SystemExit(
            "opportunity ROI gate failed; a perfect abstaining policy has "
            "not yet shown enough unbiased, cost-adjusted headroom"
        )
    return {
        "required": required,
        "passed": bool(report.get("passed")),
        "training_authorized": bool(
            report.get("training_authorized")
        ),
        "report_path": str(source.resolve()),
        "report_hash": stable_payload_hash(report),
        "observations_jsonl_sha256": observations_sha256,
        "required_scales": list(report.get("required_scales") or ()),
        "sentinel_context_count": int(
            report.get("sentinel_context_count") or 0
        ),
        "targeted_context_count": int(
            report.get("targeted_context_count") or 0
        ),
    }


def _train_final_checkpoint(
    records: list[dict],
    *,
    static_cache: dict[str, dict],
    model_kind: str,
    output_dir: Path,
    manifest: dict,
    source_baseline_id: str,
    engine_hashes: tuple[str, ...],
    feature_schema_version: str,
    ood_policy_version: str,
    training_objective: str,
    counterfactual_main_scope: str,
    epochs: int,
    shadow_head_epochs: int,
    learning_rate: float,
    pcgrad_enabled: bool,
    selection_report_hash: str,
) -> dict:
    started = perf_counter()
    normalization = _fit_normalization(
        records, static_cache=static_cache
    )
    normalization_version = (
        "all-development-after-cv-"
        f"{manifest.get('manifest_hash', '')[:12]}"
    )
    main_head_names = (
        {"harvest"}
        if (
            str(training_objective)
            == COUNTERFACTUAL_TRAINING_OBJECTIVE_V2
            and str(counterfactual_main_scope) == "harvest_only"
        )
        else {"exact_pricing", "harvest"}
    )
    main_rows = [
        row
        for row in records
        if row["head"] in main_head_names
    ]
    shadow_rows = [
        row
        for row in records
        if row["head"] in {"proof_risk", "branch"}
    ]
    if not main_rows:
        raise SystemExit("final training needs pricing/harvest rows")
    node_dim, edge_dim = _feature_dimensions(
        records[0], static_cache=static_cache
    )
    model = build_model(
        model_kind,
        node_input_dim=node_dim,
        edge_input_dim=edge_dim,
    )
    optimizer = torch.optim.Adam(
        model.parameters(), lr=float(learning_rate)
    )
    normalizer = EMALossNormalizer()
    epoch_rows = []
    for epoch in range(epochs):
        model.train()
        loss, per_scale, cosine, diagnostics = _run_epoch(
            model,
            _epoch_context_sample(main_rows, epoch),
            normalization,
            optimizer=optimizer,
            loss_normalizer=normalizer,
            pcgrad_enabled=pcgrad_enabled,
            static_cache=static_cache,
        )
        epoch_rows.append(
            {
                "epoch": epoch + 1,
                "train_loss": loss,
                "per_scale_loss_contribution": per_scale,
                "gradient_cosine": cosine,
                "diagnostics": diagnostics,
                "pcgrad_enabled_from_frozen_cv_selection": pcgrad_enabled,
            }
        )
    trained_shadow_heads = sorted(
        {row["head"] for row in shadow_rows}
    )
    shadow_epoch_rows = []
    if shadow_rows:
        _freeze_for_shadow_heads(model, trained_shadow_heads)
        shadow_optimizer = torch.optim.Adam(
            [
                parameter
                for parameter in model.parameters()
                if parameter.requires_grad
            ],
            lr=float(learning_rate),
        )
        shadow_normalizer = EMALossNormalizer()
        for epoch in range(shadow_head_epochs):
            model.train()
            loss, per_scale, _, diagnostics = _run_epoch(
                model,
                _epoch_context_sample(shadow_rows, epoch),
                normalization,
                optimizer=shadow_optimizer,
                loss_normalizer=shadow_normalizer,
                pcgrad_enabled=False,
                static_cache=static_cache,
            )
            shadow_epoch_rows.append(
                {
                    "epoch": epoch + 1,
                    "train_loss": loss,
                    "per_scale_loss_contribution": per_scale,
                    "diagnostics": diagnostics,
                    "encoder_frozen": True,
                }
            )
        for parameter in model.parameters():
            parameter.requires_grad_(True)
    checkpoint_id = (
        f"p0v2-{model_kind}-final-"
        f"{manifest.get('manifest_hash', '')[:12]}"
    )
    metadata = {
        "checkpoint_id": checkpoint_id,
        "source_baseline_id": source_baseline_id,
        "engine_hash": engine_hashes[0],
        "compatible_engine_hashes": sorted(set(engine_hashes)),
        "split_manifest_hash": manifest.get("manifest_hash"),
        "fold": "all_development_after_cross_validation",
        "feature_schema_version": feature_schema_version,
        "harvest_model_context_schema_version": (
            HARVEST_MODEL_CONTEXT_SCHEMA_V2
        ),
        "normalization_version": normalization_version,
        "ood_policy_version": ood_policy_version,
        "node_feature_mean": normalization["node_mean"],
        "node_feature_std": normalization["node_std"],
        "edge_feature_mean": normalization["edge_mean"],
        "edge_feature_std": normalization["edge_std"],
        "normalization_weighting": normalization["weighting"],
        "normalization_unique_context_count": normalization[
            "unique_context_count"
        ],
        "ood_max_abs_z": None,
        "ood_calibrated": False,
        "online_eligible": False,
        "training_objective": str(training_objective),
        "trajectory_objective_spec_id": (
            FIXED_POOL_PRICING_PRESSURE_OBJECTIVE_SPEC_V1
            if str(training_objective)
            == COUNTERFACTUAL_TRAINING_OBJECTIVE_V2
            else ""
        ),
        "legacy_objective_diagnostic_only": (
            str(training_objective) == "legacy_graded_listwise"
        ),
        "model_architecture_version": MODEL_ARCHITECTURE_VERSION,
        "counterfactual_main_scope": str(
            counterfactual_main_scope
        ),
        "p0_noop_trained": (
            str(training_objective)
            == COUNTERFACTUAL_TRAINING_OBJECTIVE_V2
        ),
        "auxiliary_encoder_gradient_fraction": (
            0.0
            if str(training_objective)
            == COUNTERFACTUAL_TRAINING_OBJECTIVE_V2
            else None
        ),
        "trajectory_curve_shared_encoder": False,
        "proof_head_encoder_frozen": True,
        "branch_head_encoder_frozen": True,
        "trained_main_heads": sorted(
            {row["head"] for row in main_rows}
        ),
        "trained_shadow_heads": trained_shadow_heads,
        "model_rung_selection_report_hash": selection_report_hash,
        "calibration_used_for_training": False,
        "protected_final_test_used": False,
    }
    checkpoint_path = output_dir / f"{checkpoint_id}.pt"
    torch.save(
        checkpoint_payload(model, metadata=metadata),
        checkpoint_path,
    )
    return {
        "fold": "all_development_after_cross_validation",
        "model_kind": model_kind,
        "checkpoint_id": checkpoint_id,
        "checkpoint_path": str(checkpoint_path.resolve()),
        "parameter_count": sum(
            parameter.numel() for parameter in model.parameters()
        ),
        "training_wall_sec": perf_counter() - started,
        "epochs": epoch_rows,
        "shadow_head_epochs": shadow_epoch_rows,
        "calibration_used": False,
        "protected_final_test_used": False,
    }


def _load_static_tensor_cache(
    rows: list[dict], *, cache_dir: Path
) -> dict[str, dict]:
    keys = {
        str(row.get("static_tensor_cache_key") or "")
        for row in rows
        if row.get("static_tensor_cache_key")
    }
    if not keys:
        return {}
    cache = {}
    for key in sorted(keys):
        path = cache_dir / f"{key}.json"
        if not path.exists():
            raise SystemExit(f"static tensor sidecar missing: {key}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        observed_hash = str(
            payload.get("static_tensor_cache_hash") or ""
        )
        unsigned = dict(payload)
        unsigned.pop("static_tensor_cache_hash", None)
        if (
            str(payload.get("instance_content_hash") or "") != key
            or not observed_hash
            or stable_payload_hash(unsigned) != observed_hash
        ):
            raise SystemExit(f"stale static tensor sidecar rejected: {key}")
        cache[key] = payload
    for row in rows:
        key = str(row.get("static_tensor_cache_key") or "")
        if not key:
            if row.get("node_features") is None:
                raise SystemExit("training row has no feature payload")
            continue
        if key != str(row.get("instance_content_hash") or ""):
            raise SystemExit("row/static tensor content hash mismatch")
        if str(row.get("static_tensor_cache_hash") or "") != str(
            cache[key]["static_tensor_cache_hash"]
        ):
            raise SystemExit("row/static tensor payload hash mismatch")
    return cache


def _resolve_feature_arrays(
    row: dict, *, static_cache: dict[str, dict] | None
) -> tuple[list, list, list, list]:
    if row.get("node_features") is not None:
        return (
            row["node_features"],
            row["edge_features"],
            row["edge_index"],
            row.get("task_node_indices")
            or list(range(1, len(row["node_features"]))),
        )
    key = str(row.get("static_tensor_cache_key") or "")
    if not key or static_cache is None or key not in static_cache:
        raise ValueError("compact training row has no loaded static sidecar")
    payload = static_cache[key]
    dynamic = list(row.get("dynamic_node_features") or ())
    static_node = list(payload["node_static_features"])
    if len(dynamic) != len(static_node):
        raise ValueError("static/dynamic node count mismatch")
    node = [
        [*static_values, *dynamic_values]
        for static_values, dynamic_values in zip(
            static_node, dynamic, strict=True
        )
    ]
    return (
        node,
        payload["edge_features"],
        payload["edge_index"],
        payload["task_node_indices"],
    )


def _feature_dimensions(
    row: dict, *, static_cache: dict[str, dict] | None
) -> tuple[int, int]:
    node, edge, _, _ = _resolve_feature_arrays(
        row, static_cache=static_cache
    )
    return len(node[0]), len(edge[0])


def _epoch_context_sample(rows: list[dict], epoch: int) -> list[dict]:
    grouped = defaultdict(list)
    for row in rows:
        key = (
            str(row.get("head") or "exact_pricing"),
            int(row["scale"]),
            str(row.get("instance_content_hash") or ""),
            str(row.get("node_phase") or ""),
        )
        grouped[key].append(row)
    selected = []
    for key in sorted(grouped):
        candidates = sorted(
            grouped[key],
            key=lambda row: (
                str(row.get("rmp_context_hash") or ""),
                str(row.get("candidate_id") or ""),
            ),
        )
        selected.append(candidates[int(epoch) % len(candidates)])
    return selected


def _fit_normalization(
    rows: list[dict],
    *,
    static_cache: dict[str, dict] | None = None,
) -> dict:
    # Fit moments in the same anti-dominance hierarchy used by training:
    # scales are equal, instances are equal within a scale, and contexts are
    # equal within an instance. A scale30 graph therefore does not receive
    # ~36x the normalization weight of scale5 merely because it has more arcs.
    unique_contexts = {}
    for row in rows:
        key = (
            int(row["scale"]),
            str(row.get("instance_content_hash") or ""),
            str(row.get("rmp_context_hash") or ""),
        )
        unique_contexts.setdefault(key, row)
    by_scale_instance = defaultdict(lambda: defaultdict(list))
    for (scale, instance_hash, _), row in unique_contexts.items():
        by_scale_instance[scale][instance_hash].append(row)
    node_means = []
    node_seconds = []
    edge_means = []
    edge_seconds = []
    for scale in sorted(by_scale_instance):
        scale_node_means = []
        scale_node_seconds = []
        scale_edge_means = []
        scale_edge_seconds = []
        for instance_hash in sorted(by_scale_instance[scale]):
            context_node_means = []
            context_node_seconds = []
            context_edge_means = []
            context_edge_seconds = []
            for row in by_scale_instance[scale][instance_hash]:
                node_values, edge_values, _, _ = (
                    _resolve_feature_arrays(
                        row, static_cache=static_cache
                    )
                )
                node = torch.tensor(
                    node_values, dtype=torch.float32
                )
                edge = torch.tensor(
                    edge_values, dtype=torch.float32
                )
                context_node_means.append(node.mean(dim=0))
                context_node_seconds.append((node * node).mean(dim=0))
                context_edge_means.append(edge.mean(dim=0))
                context_edge_seconds.append((edge * edge).mean(dim=0))
            scale_node_means.append(
                torch.stack(context_node_means).mean(dim=0)
            )
            scale_node_seconds.append(
                torch.stack(context_node_seconds).mean(dim=0)
            )
            scale_edge_means.append(
                torch.stack(context_edge_means).mean(dim=0)
            )
            scale_edge_seconds.append(
                torch.stack(context_edge_seconds).mean(dim=0)
            )
        node_means.append(torch.stack(scale_node_means).mean(dim=0))
        node_seconds.append(
            torch.stack(scale_node_seconds).mean(dim=0)
        )
        edge_means.append(torch.stack(scale_edge_means).mean(dim=0))
        edge_seconds.append(
            torch.stack(scale_edge_seconds).mean(dim=0)
        )
    node_mean = torch.stack(node_means).mean(dim=0)
    node_second = torch.stack(node_seconds).mean(dim=0)
    edge_mean = torch.stack(edge_means).mean(dim=0)
    edge_second = torch.stack(edge_seconds).mean(dim=0)
    return {
        "node_mean": node_mean.tolist(),
        "node_std": torch.sqrt(
            (node_second - node_mean * node_mean).clamp_min(1.0e-16)
        ).clamp_min(1.0e-8).tolist(),
        "edge_mean": edge_mean.tolist(),
        "edge_std": torch.sqrt(
            (edge_second - edge_mean * edge_mean).clamp_min(1.0e-16)
        ).clamp_min(1.0e-8).tolist(),
        "weighting": "scale_equal_instance_equal_context_equal",
        "unique_context_count": len(unique_contexts),
    }


def _observed_label_count(row: dict) -> int:
    head = str(row.get("head") or "exact_pricing")
    if head == "exact_pricing":
        if str(row.get("training_objective") or "") == (
            COUNTERFACTUAL_TRAINING_OBJECTIVE_V2
        ):
            return sum(
                bool(value)
                for value in row.get(
                    "task_counterfactual_probe_mask", ()
                )
            ) + sum(
                bool(value)
                for value in row.get(
                    "arc_counterfactual_probe_mask", ()
                )
            )
        return sum(bool(value) for value in row.get("task_observed_mask", ())) + sum(
            bool(value) for value in row.get("arc_observed_mask", ())
        )
    if head == "harvest":
        if str(row.get("training_objective") or "") == (
            COUNTERFACTUAL_TRAINING_OBJECTIVE_V2
        ):
            return sum(
                bool(value)
                for value in row.get(
                    "harvest_counterfactual_probe_mask", ()
                )
            )
        return len(row.get("harvest_grades") or ())
    if head == "proof_risk":
        return len(row.get("proof_observed_lower_bound") or ())
    if head == "branch":
        return len(row.get("branch_observed_lower_bounds") or ())
    return 0


def _run_epoch(
    model,
    rows: list[dict],
    normalization: dict,
    *,
    optimizer,
    loss_normalizer,
    pcgrad_enabled: bool,
    static_cache: dict[str, dict] | None = None,
) -> tuple[float, dict[str, float], float, dict]:
    by_scale = defaultdict(list)
    by_head = defaultdict(list)
    head_scale_counts = defaultdict(int)
    rows_by_instance_phase = defaultdict(int)
    phases_by_instance = defaultdict(set)
    instances_by_head_scale = defaultdict(set)
    row_sampling_keys = []
    for row_index, row in enumerate(rows):
        head = str(row.get("head") or "exact_pricing")
        scale = int(row["scale"])
        instance_hash = str(
            row.get("instance_content_hash")
            or f"legacy-instance-{row_index}"
        )
        node_phase = str(row.get("node_phase") or "unspecified")
        context_hash = str(
            row.get("rmp_context_hash")
            or f"legacy-context-{row_index}"
        )
        head_scale_counts[(head, scale)] += 1
        instances_by_head_scale[(head, scale)].add(instance_hash)
        phases_by_instance[(head, scale, instance_hash)].add(node_phase)
        rows_by_instance_phase[
            (head, scale, instance_hash, node_phase)
        ] += 1
        row_sampling_keys.append(
            (head, scale, instance_hash, node_phase, context_hash)
        )
    scales_by_head = defaultdict(set)
    for head, scale in head_scale_counts:
        scales_by_head[head].add(scale)
    active_head_count = max(1, len(scales_by_head))
    normalized_scale_weights = {}
    for head, scales in scales_by_head.items():
        configured = HEAD_SCALE_WEIGHTS.get(
            head, {scale: 1.0 for scale in scales}
        )
        missing = sorted(scale for scale in scales if scale not in configured)
        if missing:
            raise ValueError(
                f"head {head!r} has no scale weights for {missing}"
            )
        denominator = sum(float(configured[scale]) for scale in scales)
        if denominator <= 0.0:
            raise ValueError(f"head {head!r} has zero active scale weight")
        for scale in scales:
            normalized_scale_weights[(head, scale)] = (
                float(configured[scale]) / denominator
            )
    encoder_gradients: dict[str, torch.Tensor] = {}
    accumulated_pcgrad: dict[str, list[torch.Tensor]] = {}
    instance_weight_totals = defaultdict(float)
    parameters = tuple(
        parameter for parameter in model.parameters() if parameter.requires_grad
    )
    encoder = tuple(
        parameter
        for parameter in model.node_encoder.parameters()
        if parameter.requires_grad
    )
    if optimizer is not None:
        optimizer.zero_grad(set_to_none=True)
    for row, sampling_key in zip(rows, row_sampling_keys, strict=True):
        tensors = _tensors(
            row, normalization, static_cache=static_cache
        )
        output = model(**tensors["inputs"])
        head, scale, instance_hash, node_phase, _ = sampling_key
        losses = _row_head_losses(head, output, tensors)
        loss = (
            loss_normalizer.normalized_sum(losses)
            if loss_normalizer is not None
            else torch.stack(tuple(losses.values())).sum()
        )
        weight = (
            1.0
            / float(active_head_count)
            * normalized_scale_weights[(head, scale)]
            / float(len(instances_by_head_scale[(head, scale)]))
            / float(
                len(phases_by_instance[(head, scale, instance_hash)])
            )
            / float(
                rows_by_instance_phase[
                    (head, scale, instance_hash, node_phase)
                ]
            )
        )
        instance_weight_totals[(head, scale, instance_hash)] += weight
        if encoder:
            gradient = _flat_gradient(
                loss, encoder, retain_graph=True
            ) * weight
            current = encoder_gradients.get(head)
            encoder_gradients[head] = (
                gradient if current is None else current + gradient
            )
        if optimizer is not None:
            if pcgrad_enabled:
                gradients = torch.autograd.grad(
                    loss,
                    parameters,
                    retain_graph=False,
                    allow_unused=True,
                )
                rows_for_head = accumulated_pcgrad.setdefault(
                    head,
                    [torch.zeros_like(parameter) for parameter in parameters],
                )
                for index, (parameter, gradient) in enumerate(
                    zip(parameters, gradients, strict=True)
                ):
                    rows_for_head[index].add_(
                        (
                            torch.zeros_like(parameter)
                            if gradient is None
                            else gradient
                        )
                        * weight
                    )
            else:
                (loss * weight).backward()
        by_scale[scale].append(float(loss.detach()))
        by_head[head].append(float(loss.detach()))

    if optimizer is not None and pcgrad_enabled:
        _assign_projected_head_gradients(
            parameters,
            accumulated_pcgrad,
        )
    scale_losses = {
        scale: mean(values) for scale, values in by_scale.items()
    }
    head_losses = {
        head: mean(values) for head, values in by_head.items()
    }
    total = mean(head_losses.values())
    if optimizer is not None:
        optimizer.step()
    cosine_by_pair = {}
    heads = sorted(encoder_gradients)
    for left_index, left in enumerate(heads):
        for right in heads[left_index + 1 :]:
            cosine_by_pair[f"{left}__{right}"] = gradient_cosine(
                encoder_gradients[left],
                encoder_gradients[right],
            )
    minimum_cosine = min(cosine_by_pair.values(), default=0.0)
    return (
        float(total),
        {
            str(scale): float(value)
            for scale, value in sorted(scale_losses.items())
        },
        minimum_cosine,
        {
            "per_head_loss": {
                head: float(value)
                for head, value in sorted(head_losses.items())
            },
            "encoder_gradient_norm_by_head": {
                head: float(gradient.norm())
                for head, gradient in sorted(encoder_gradients.items())
            },
            "gradient_cosine_by_head_pair": cosine_by_pair,
            "head_scale_sample_count": {
                f"{head}:scale{scale}": count
                for (head, scale), count in sorted(
                    head_scale_counts.items()
                )
            },
            "head_scale_instance_count": {
                f"{head}:scale{scale}": len(instance_hashes)
                for (head, scale), instance_hashes in sorted(
                    instances_by_head_scale.items()
                )
            },
            "effective_head_scale_loss_weight": {
                f"{head}:scale{scale}": (
                    1.0
                    / float(active_head_count)
                    * normalized_scale_weights[(head, scale)]
                )
                for head, scale in sorted(head_scale_counts)
            },
            "effective_instance_loss_weight_range_by_head_scale": {
                f"{head}:scale{scale}": {
                    "min": min(values),
                    "max": max(values),
                }
                for (head, scale), values in sorted(
                    _instance_weight_values(
                        instance_weight_totals
                    ).items()
                )
            },
        },
    )


def _instance_weight_values(
    totals: dict[tuple[str, int, str], float],
) -> dict[tuple[str, int], list[float]]:
    values = defaultdict(list)
    for (head, scale, _), weight in totals.items():
        values[(head, scale)].append(float(weight))
    return values


def _tensors(
    row: dict,
    normalization: dict,
    *,
    static_cache: dict[str, dict] | None = None,
) -> dict:
    node_values, edge_values, edge_index_values, task_index_values = (
        _resolve_feature_arrays(row, static_cache=static_cache)
    )
    node = torch.tensor(node_values, dtype=torch.float32)
    edge = torch.tensor(edge_values, dtype=torch.float32)
    node = (
        node - torch.tensor(normalization["node_mean"], dtype=torch.float32)
    ) / torch.tensor(normalization["node_std"], dtype=torch.float32)
    edge = (
        edge - torch.tensor(normalization["edge_mean"], dtype=torch.float32)
    ) / torch.tensor(normalization["edge_std"], dtype=torch.float32)
    edge_index = torch.tensor(edge_index_values, dtype=torch.long)
    task_indices = torch.tensor(
        task_index_values,
        dtype=torch.long,
    )
    inputs = {
            "node_features": node,
            "edge_index": edge_index,
            "edge_features": edge,
            "task_node_indices": task_indices,
            "resource_context": torch.tensor(
                row["resource_context"], dtype=torch.float32
            ),
    }
    if str(row.get("training_objective") or "") == (
        COUNTERFACTUAL_TRAINING_OBJECTIVE_V2
    ):
        # Survival/calibration heads train independently. Their gradients do
        # not enter the shared encoder, satisfying the <=25% auxiliary
        # gradient cap conservatively.
        inputs["detach_auxiliary_encoder"] = True
    if row.get("harvest_task_masks") is not None:
        inputs["harvest_task_masks"] = torch.tensor(
            row["harvest_task_masks"], dtype=torch.float32
        )
        inputs["harvest_context"] = torch.tensor(
            [
                learned_harvest_context(values)
                for values in row["harvest_context"]
            ],
            dtype=torch.float32,
        )
    if row.get("branch_pairs") is not None:
        inputs["branch_pairs"] = torch.tensor(
            row["branch_pairs"], dtype=torch.long
        )
        inputs["branch_context"] = torch.tensor(
            row["branch_context"], dtype=torch.float32
        )
    tensors = {
        "inputs": inputs,
    }
    for key in (
        "task_grades",
        "task_observed_mask",
        "arc_grades",
        "arc_observed_mask",
        "harvest_grades",
        "task_counterfactual_target_probabilities",
        "task_counterfactual_advantages",
        "task_counterfactual_probe_mask",
        "task_counterfactual_noop_target_probability",
        "task_counterfactual_noop_probe_mask",
        "task_survival_candidate_indices",
        "task_survival_time_fractions",
        "task_survival_event_observed",
        "arc_counterfactual_target_probabilities",
        "arc_counterfactual_advantages",
        "arc_counterfactual_probe_mask",
        "arc_counterfactual_noop_target_probability",
        "arc_counterfactual_noop_probe_mask",
        "arc_survival_candidate_indices",
        "arc_survival_time_fractions",
        "arc_survival_event_observed",
        "harvest_counterfactual_target_probabilities",
        "harvest_counterfactual_advantages",
        "harvest_counterfactual_probe_mask",
        "harvest_counterfactual_noop_target_probability",
        "harvest_counterfactual_noop_probe_mask",
        "harvest_survival_candidate_indices",
        "harvest_survival_time_fractions",
        "harvest_survival_event_observed",
        "proof_observed_lower_bound",
        "proof_exact_mask",
        "branch_observed_lower_bounds",
        "branch_exact_mask",
    ):
        if row.get(key) is not None:
            tensors[key] = torch.tensor(row[key], dtype=torch.float32)
    return tensors


def _row_head_losses(head: str, output: dict, tensors: dict) -> dict:
    if head == "exact_pricing":
        if "task_counterfactual_target_probabilities" in tensors:
            return {
                **_counterfactual_candidate_losses(
                    "task", output, tensors
                ),
                **_counterfactual_candidate_losses(
                    "arc", output, tensors
                ),
            }
        return {
            "task": _listwise_context_loss(
                output["task_scores"],
                tensors["task_grades"],
                tensors.get("task_observed_mask"),
            ),
            "arc": _listwise_context_loss(
                output["arc_scores"],
                tensors["arc_grades"],
                tensors.get("arc_observed_mask"),
            ),
        }
    if head == "harvest":
        if "harvest_counterfactual_target_probabilities" in tensors:
            return _counterfactual_candidate_losses(
                "harvest", output, tensors
            )
        return {
            "harvest": _listwise_context_loss(
                output["harvest_scores"], tensors["harvest_grades"]
            )
        }
    if head == "proof_risk":
        observed = tensors["proof_observed_lower_bound"].reshape(-1)
        exact_mask = tensors["proof_exact_mask"].reshape(-1).bool()
        predicted = output["proof_tail_risk"].reshape(-1)
        if predicted.numel() == 1 and observed.numel() > 1:
            predicted = predicted.expand_as(observed)
        return {
            "proof_risk": survival_ranking_loss(
                predicted,
                observed,
                exact_mask,
            )
        }
    if head == "branch":
        # The model emits larger-is-better ranks, while branch_cost is
        # lower-is-better.
        predicted_cost = -output["branch_scores"].reshape(-1)
        return {
            "branch": survival_ranking_loss(
                predicted_cost,
                tensors["branch_observed_lower_bounds"].reshape(-1),
                tensors["branch_exact_mask"].reshape(-1).bool(),
            )
        }
    raise ValueError(f"unsupported head {head!r}")


def _counterfactual_candidate_losses(
    prefix: str,
    output: dict,
    tensors: dict,
) -> dict:
    scores = torch.cat(
        (
            output[f"{prefix}_noop_score"].reshape(1),
            output[f"{prefix}_scores"].reshape(-1),
        )
    )
    probabilities = torch.cat(
        (
            tensors[
                f"{prefix}_counterfactual_noop_target_probability"
            ].reshape(1),
            tensors[
                f"{prefix}_counterfactual_target_probabilities"
            ].reshape(-1),
        )
    )
    probe_mask = torch.cat(
        (
            tensors[
                f"{prefix}_counterfactual_noop_probe_mask"
            ].reshape(1),
            tensors[f"{prefix}_counterfactual_probe_mask"].reshape(-1),
        )
    )
    hazard_logits = torch.cat(
        (
            output[f"{prefix}_noop_hazard_logits"].reshape(1, -1),
            output[f"{prefix}_hazard_logits"],
        ),
        dim=0,
    )
    candidate_indices = tensors[f"{prefix}_survival_candidate_indices"]
    time_fractions = tensors[f"{prefix}_survival_time_fractions"]
    event_observed = tensors[f"{prefix}_survival_event_observed"]
    rank_loss = counterfactual_soft_listwise_loss(
        scores,
        probabilities,
        probe_mask,
    )
    survival_loss = discrete_time_survival_nll(
        hazard_logits,
        candidate_indices,
        time_fractions,
        event_observed,
    ) + 0.1 * survival_concordance_loss(
        hazard_logits,
        candidate_indices,
        time_fractions,
        event_observed,
    )
    return {
        f"{prefix}_counterfactual_rank_plus_survival": (
            rank_loss + 0.25 * survival_loss
        )
    }


def _listwise_context_loss(scores, grades, observed_mask=None):
    if observed_mask is not None:
        mask = observed_mask.reshape(-1).bool()
        scores = scores.reshape(-1)[mask]
        grades = grades.reshape(-1)[mask]
    if scores.numel() < 2:
        return scores.sum() * 0.0
    return -(F.softmax(grades, dim=0) * F.log_softmax(scores, dim=0)).sum()


def _flat_gradient(loss, parameters, *, retain_graph: bool):
    gradients = torch.autograd.grad(
        loss,
        parameters,
        retain_graph=retain_graph,
        allow_unused=True,
    )
    return torch.cat(
        [
            (
                torch.zeros_like(parameter).flatten()
                if gradient is None
                else gradient.flatten()
            )
            for parameter, gradient in zip(parameters, gradients, strict=True)
        ]
    )


def _assign_projected_head_gradients(
    parameters,
    gradients_by_head: dict[str, list[torch.Tensor]],
) -> None:
    if not gradients_by_head:
        return
    heads = sorted(gradients_by_head)
    original = {
        head: [gradient.clone() for gradient in gradients_by_head[head]]
        for head in heads
    }
    projected = {
        head: [gradient.clone() for gradient in original[head]]
        for head in heads
    }
    for left in heads:
        for right in heads:
            if left == right:
                continue
            dot = sum(
                (left_gradient * right_gradient).sum()
                for left_gradient, right_gradient in zip(
                    projected[left], original[right], strict=True
                )
            )
            if float(dot) >= 0.0:
                continue
            denominator = sum(
                (gradient * gradient).sum()
                for gradient in original[right]
            ).clamp_min(1.0e-12)
            projected[left] = [
                left_gradient - dot / denominator * right_gradient
                for left_gradient, right_gradient in zip(
                    projected[left], original[right], strict=True
                )
            ]
    for index, parameter in enumerate(parameters):
        parameter.grad = (
            sum(projected[head][index] for head in heads) / len(heads)
        )


def _freeze_for_shadow_heads(model, trained_heads: list[str]) -> None:
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    if "proof_risk" in trained_heads:
        for parameter in model.proof_risk_head.parameters():
            parameter.requires_grad_(True)
    if "branch" in trained_heads:
        for parameter in model.branch_head.parameters():
            parameter.requires_grad_(True)


def _pcgrad_backward(task_loss, arc_loss, parameters, *, weight: float) -> None:
    task_gradients = torch.autograd.grad(
        task_loss,
        parameters,
        retain_graph=True,
        allow_unused=True,
    )
    arc_gradients = torch.autograd.grad(
        arc_loss,
        parameters,
        retain_graph=False,
        allow_unused=True,
    )
    task_rows = [
        torch.zeros_like(parameter) if gradient is None else gradient
        for parameter, gradient in zip(
            parameters, task_gradients, strict=True
        )
    ]
    arc_rows = [
        torch.zeros_like(parameter) if gradient is None else gradient
        for parameter, gradient in zip(
            parameters, arc_gradients, strict=True
        )
    ]
    dot = sum(
        (left * right).sum() for left, right in zip(task_rows, arc_rows, strict=True)
    )
    task_norm = sum((gradient * gradient).sum() for gradient in task_rows).clamp_min(
        1.0e-12
    )
    arc_norm = sum((gradient * gradient).sum() for gradient in arc_rows).clamp_min(
        1.0e-12
    )
    if float(dot) < 0.0:
        projected_task = [
            left - dot / arc_norm * right
            for left, right in zip(task_rows, arc_rows, strict=True)
        ]
        projected_arc = [
            right - dot / task_norm * left
            for left, right in zip(task_rows, arc_rows, strict=True)
        ]
    else:
        projected_task = task_rows
        projected_arc = arc_rows
    for parameter, left, right in zip(
        parameters, projected_task, projected_arc, strict=True
    ):
        update = (left + right) * float(weight)
        if parameter.grad is None:
            parameter.grad = update.clone()
        else:
            parameter.grad.add_(update)


if __name__ == "__main__":
    raise SystemExit(main())
