#!/usr/bin/env python3
"""Run resumable B4.1 true-dual proof-tail strengthening stages."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.runners.b4_1_true_dual_proof_tail import (  # noqa: E402
    B41_STAGE_A_MODES,
    B41_STAGE_B_VARIANTS,
    B41_TARGETED_RESTRICTED_REGION_VARIANT_CONFIGS,
    build_b4_1_restricted_region_bound_ledger,
    build_b4_1_partition_candidate_audit,
    build_b4_1_restricted_region_taskset_diagnostic,
    build_b4_1_report,
    run_b4_1_required_task_set_partition_probe,
    run_b4_1_targeted_restricted_region_probe,
    run_b4_1_stage_a_regression,
    run_b4_1_stage_b_from_probe,
    run_b4_1_stage_b_worker_tail_hidden_probe,
    run_b4_1_stage_c_selected_from_probe,
    run_b4_1_tree_closure_from_probe,
    rows_from_b4_1_partition_candidate_audit,
    write_b4_1_artifacts,
    write_b4_1_partition_candidate_audit,
    write_b4_1_restricted_region_bound_ledger,
    write_b4_1_restricted_region_taskset_diagnostic,
    write_b4_1_required_task_set_partition_probe,
    write_b4_1_targeted_restricted_region_probe,
)
from lunar_ice_bpc.exact.bpc.solver.pricing_tail_solver import (  # noqa: E402
    DIRECT_LABEL_WORKER,
    RELAXED_LABELING_WORKER,
)

B41_ROOT_TAIL_PARTITION_DEFAULT_MAX_TASK_SETS = 5


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="runs/b4_1_true_dual_proof_tail_strengthening")
    parser.add_argument("--rows-jsonl", default="b4_1_rows.jsonl")
    parser.add_argument("--instance", action="append", default=[])
    parser.add_argument("--manifest")
    parser.add_argument("--scales", nargs="*", type=int, default=[])
    parser.add_argument("--limit-per-scale", type=int, default=0)
    parser.add_argument("--import-partition-candidate-audit-json", action="append", default=[])
    parser.add_argument("--stage-a", action="store_true")
    parser.add_argument("--stage-a-modes", nargs="*", default=list(B41_STAGE_A_MODES))
    parser.add_argument("--max-direct-tasks", type=int, default=5)
    parser.add_argument("--max-rounds", type=int, default=16)
    parser.add_argument("--row-time-limit-sec", type=float)
    parser.add_argument("--max-columns-per-round", type=int, default=128)
    parser.add_argument("--max-tree-nodes", type=int, default=31)
    parser.add_argument("--max-branch-depth", type=int, default=4)
    parser.add_argument(
        "--labeling-final-judge-exact-harvest-target",
        type=int,
        default=5,
        help=(
            "Opt-in exact true-dual labeling final-judge negative harvest target. "
            "This controls candidate harvesting only; no-column certificates still require exact proof."
        ),
    )
    parser.add_argument("--source-probe-json", action="append", default=[])
    parser.add_argument("--import-rows-jsonl", action="append", default=[])
    parser.add_argument("--stage-b", action="store_true")
    parser.add_argument("--stage-b-variants", nargs="*", default=list(B41_STAGE_B_VARIANTS))
    parser.add_argument(
        "--stage-b-v4-root-tail-partition-proof",
        action="store_true",
        help=(
            "Convenience alias for the B4.1 V4 root-tail region proof chain: "
            "run required-task-set partition proof when source probes are given, "
            "build partition candidate audit, and import the audit as diagnostic rows."
        ),
    )
    parser.add_argument("--stage-b-worker-tail-hidden-probe", action="store_true")
    parser.add_argument("--stage-b-worker-tail-output-subdir", default="stage_b_worker_tail_hidden_negative")
    parser.add_argument("--stage-b-worker-tail-max-direct-tasks", type=int, default=30)
    parser.add_argument("--stage-b-worker-tail-max-rounds", type=int, default=2)
    parser.add_argument("--stage-b-worker-tail-time-limit-sec", type=float, default=60.0)
    parser.add_argument("--stage-b-worker-tail-max-columns-per-round", type=int, default=32)
    parser.add_argument(
        "--stage-b-worker-tail-use-b0-direct",
        dest="stage_b_worker_tail_skip_b0_direct",
        action="store_false",
        default=True,
    )
    parser.add_argument("--stage-b-worker-tail-tail-dual-stabilization", action="store_true")
    parser.add_argument("--stage-c", action="store_true")
    parser.add_argument("--stage-c-source-probe-json", action="append", default=[])
    parser.add_argument("--stage-c-variants", nargs="*", default=list(B41_STAGE_B_VARIANTS))
    parser.add_argument("--tree-closure-from-probe", action="store_true")
    parser.add_argument("--tree-closure-max-rounds", type=int, default=1)
    parser.add_argument("--tree-closure-time-limit-sec", type=float)
    parser.add_argument("--tree-closure-max-columns-per-round", type=int, default=128)
    parser.add_argument("--tree-closure-max-nodes", type=int, default=31)
    parser.add_argument("--tree-closure-max-branch-depth", type=int, default=4)
    parser.add_argument(
        "--tree-closure-worker-pricer-kind",
        choices=(DIRECT_LABEL_WORKER, RELAXED_LABELING_WORKER),
        default=DIRECT_LABEL_WORKER,
    )
    parser.add_argument("--tree-closure-tail-dual-stabilization-enabled", action="store_true")
    parser.add_argument("--tree-closure-tail-dual-stabilization-alpha", type=float, default=0.7)
    parser.add_argument("--tree-closure-tail-dual-stabilization-window", type=int, default=5)
    parser.add_argument(
        "--tree-closure-labeling-final-judge-mode",
        choices=("env", "off", "on", "auto"),
        default="env",
    )
    parser.add_argument("--tree-closure-labeling-final-judge-max-exact-tasks", type=int)
    parser.add_argument("--tree-closure-labeling-final-judge-exact-harvest-target", type=int)
    parser.add_argument(
        "--tree-closure-live-sri-policy",
        choices=(
            "no_cut",
            "P0",
            "P0_GROUP_SCREEN_V1",
            "P1",
            "P2",
        ),
        default="no_cut",
    )
    parser.add_argument("--tree-closure-result-subdir", default="tree_closure_results")
    parser.add_argument("--history-round", type=int, default=-1)
    parser.add_argument("--negative-feasibility-time-limit-sec", type=float, default=600.0)
    parser.add_argument("--optimization-proof-time-limit-sec", type=float, default=900.0)
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--min-available-mem-gb", type=float, default=2.0)
    parser.add_argument("--min-free-disk-gb", type=float, default=20.0)
    parser.add_argument("--max-output-dir-gb", type=float, default=5.0)
    parser.add_argument("--resource-check-action", choices=("stop", "warn"), default="stop")
    parser.add_argument("--no-resume", dest="resume", action="store_false", default=True)
    parser.add_argument("--restricted-region-taskset-diagnostic", action="store_true")
    parser.add_argument(
        "--restricted-region-taskset-diagnostic-basename",
        default="restricted_region_taskset_diagnostic",
    )
    parser.add_argument("--targeted-restricted-region-proof-probe", action="store_true")
    parser.add_argument(
        "--targeted-region-variants",
        nargs="*",
        default=list(B41_TARGETED_RESTRICTED_REGION_VARIANT_CONFIGS),
    )
    parser.add_argument("--targeted-region-time-limit-sec", type=float, default=120.0)
    parser.add_argument("--targeted-region-max-regions", type=int, default=0)
    parser.add_argument("--targeted-region-id", action="append", default=[])
    parser.add_argument("--targeted-region-history-round", type=int, default=-1)
    parser.add_argument(
        "--targeted-region-basename",
        default="targeted_restricted_region_probe",
    )
    parser.add_argument("--required-task-set-partition-proof-probe", action="store_true")
    parser.add_argument(
        "--partition-region-variants",
        nargs="*",
        default=("V4_current_strengthening",),
    )
    parser.add_argument("--partition-region-time-limit-sec", type=float, default=120.0)
    parser.add_argument("--partition-region-max-task-sets", type=int, default=0)
    parser.add_argument("--partition-region-history-round", type=int, default=-1)
    parser.add_argument("--partition-residual-task-count-proof", action="store_true")
    parser.add_argument("--partition-residual-task-count-min", type=int, default=1)
    parser.add_argument("--partition-residual-task-count-max", type=int, default=0)
    parser.add_argument("--partition-residual-task-count-max-regions", type=int, default=0)
    parser.add_argument("--partition-residual-active-sortie-count-proof", action="store_true")
    parser.add_argument("--partition-residual-active-sortie-count-min", type=int, default=0)
    parser.add_argument("--partition-residual-active-sortie-count-max", type=int, default=0)
    parser.add_argument("--partition-adaptive-active-sortie-refinement", action="store_true")
    parser.add_argument("--partition-negative-feasibility-fallback", action="store_true")
    parser.add_argument("--partition-refresh-dual-from-active-pool", action="store_true")
    parser.add_argument("--partition-refresh-rmp-max-iterations", type=int, default=100)
    parser.add_argument(
        "--partition-region-basename",
        default="required_task_set_partition_probe",
    )
    parser.add_argument("--partition-candidate-audit", action="store_true")
    parser.add_argument("--partition-region-result-json", action="append", default=[])
    parser.add_argument(
        "--partition-candidate-audit-basename",
        default="partition_candidate_audit",
    )
    parser.add_argument("--partition-candidate-audit-import-rows", action="store_true")
    parser.add_argument("--restricted-region-bound-ledger", action="store_true")
    parser.add_argument(
        "--restricted-region-bound-ledger-basename",
        default="restricted_region_bound_ledger",
    )
    parser.add_argument("--targeted-region-result-json", action="append", default=[])
    args = parser.parse_args()
    _apply_stage_b_v4_root_tail_partition_alias(args)

    output_dir = _resolve(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    rows_jsonl = _resolve(args.rows_jsonl) if Path(args.rows_jsonl).is_absolute() else output_dir / args.rows_jsonl
    rows_csv = output_dir / "b4_1_rows.csv"
    summary_json = output_dir / "b4_1_summary.json"
    report_md = output_dir / "b4_1_report_zh.md"

    row_mode_requested = bool(
        args.import_rows_jsonl
        or args.import_partition_candidate_audit_json
        or args.partition_candidate_audit_import_rows
        or args.stage_a
        or args.stage_b
        or args.stage_b_worker_tail_hidden_probe
        or args.stage_c
        or args.tree_closure_from_probe
    )
    if not args.resume and row_mode_requested and rows_jsonl.exists():
        rows_jsonl.unlink()
    rows = _load_rows_jsonl(rows_jsonl) if (args.resume or not row_mode_requested) else []
    row_artifacts_dirty = False
    if args.import_rows_jsonl:
        imported_count = _merge_imported_rows(rows, (_resolve(path) for path in args.import_rows_jsonl))
        if imported_count:
            _write_rows_jsonl(rows_jsonl, rows)
            _write(rows, rows_csv=rows_csv, summary_json=summary_json, report_md=report_md)
            row_artifacts_dirty = True
            print(f"Imported {imported_count} B4.1 row(s) into {rows_jsonl}")
    if args.import_partition_candidate_audit_json:
        imported_count = _merge_partition_candidate_audit_rows(
            rows,
            (_resolve(path) for path in args.import_partition_candidate_audit_json),
        )
        if imported_count:
            _write_rows_jsonl(rows_jsonl, rows)
            _write(rows, rows_csv=rows_csv, summary_json=summary_json, report_md=report_md)
            row_artifacts_dirty = True
            print(f"Imported {imported_count} B4.1 partition audit evidence row(s) into {rows_jsonl}")
    stage_a_keys = {_stage_a_key(row) for row in rows if row.get("stage") == "A"}
    stage_b_keys = {_stage_b_key(row) for row in rows if row.get("stage") == "B"}
    stage_c_keys = {_stage_b_key(row) for row in rows if row.get("stage") == "C"}
    stage_d_keys = {_tree_closure_key(row) for row in rows if row.get("stage") == "D"}

    if args.restricted_region_taskset_diagnostic:
        source_probes = tuple(args.source_probe_json)
        for index, probe in enumerate(source_probes, start=1):
            suffix = "" if len(source_probes) == 1 else f"_{index:03d}"
            diagnostic = build_b4_1_restricted_region_taskset_diagnostic(_resolve(probe))
            write_b4_1_restricted_region_taskset_diagnostic(
                diagnostic,
                summary_json=output_dir
                / f"{args.restricted_region_taskset_diagnostic_basename}{suffix}.json",
                report_md=output_dir
                / f"{args.restricted_region_taskset_diagnostic_basename}{suffix}_zh.md",
            )
            print(
                "B4.1 restricted-region task-set diagnostic written for "
                f"{_resolve(probe)}"
            )

    if args.targeted_restricted_region_proof_probe:
        source_probes = tuple(args.source_probe_json)
        for index, probe in enumerate(source_probes, start=1):
            if not _resource_status(
                output_dir=output_dir,
                min_available_mem_gb=float(args.min_available_mem_gb),
                min_free_disk_gb=float(args.min_free_disk_gb),
                max_output_dir_gb=float(args.max_output_dir_gb),
            )[0]:
                print(f"B4.1 targeted restricted-region resource gate failed before {probe}", file=sys.stderr)
                return 2
            suffix = "" if len(source_probes) == 1 else f"_{index:03d}"
            targeted = run_b4_1_targeted_restricted_region_probe(
                _resolve(probe),
                variants=tuple(args.targeted_region_variants),
                history_round=int(args.targeted_region_history_round),
                time_limit_sec=float(args.targeted_region_time_limit_sec),
                threads=int(args.threads),
                max_regions=int(args.targeted_region_max_regions),
                target_region_ids=tuple(args.targeted_region_id),
            )
            write_b4_1_targeted_restricted_region_probe(
                targeted,
                summary_json=output_dir / f"{args.targeted_region_basename}{suffix}.json",
                report_md=output_dir / f"{args.targeted_region_basename}{suffix}_zh.md",
            )
            print(
                "B4.1 targeted restricted-region proof probe written for "
                f"{_resolve(probe)}"
            )

    generated_partition_jsons: list[Path] = []
    if args.required_task_set_partition_proof_probe:
        source_probes = tuple(args.source_probe_json)
        for index, probe in enumerate(source_probes, start=1):
            if not _resource_status(
                output_dir=output_dir,
                min_available_mem_gb=float(args.min_available_mem_gb),
                min_free_disk_gb=float(args.min_free_disk_gb),
                max_output_dir_gb=float(args.max_output_dir_gb),
            )[0]:
                print(f"B4.1 required-task-set partition resource gate failed before {probe}", file=sys.stderr)
                return 2
            suffix = "" if len(source_probes) == 1 else f"_{index:03d}"
            partition = run_b4_1_required_task_set_partition_probe(
                _resolve(probe),
                variants=tuple(args.partition_region_variants),
                history_round=int(args.partition_region_history_round),
                time_limit_sec=float(args.partition_region_time_limit_sec),
                threads=int(args.threads),
                max_task_sets=int(args.partition_region_max_task_sets),
                refresh_dual_from_active_pool=bool(args.partition_refresh_dual_from_active_pool),
                refresh_rmp_max_iterations=int(args.partition_refresh_rmp_max_iterations),
                residual_task_count_partition=bool(args.partition_residual_task_count_proof),
                residual_task_count_min=int(args.partition_residual_task_count_min),
                residual_task_count_max=int(args.partition_residual_task_count_max),
                residual_task_count_max_regions=int(args.partition_residual_task_count_max_regions),
                residual_active_sortie_count_partition=bool(args.partition_residual_active_sortie_count_proof),
                residual_active_sortie_count_min=int(args.partition_residual_active_sortie_count_min),
                residual_active_sortie_count_max=int(args.partition_residual_active_sortie_count_max),
                residual_active_sortie_adaptive_refinement=bool(
                    args.partition_adaptive_active_sortie_refinement
                ),
                negative_feasibility_fallback=bool(args.partition_negative_feasibility_fallback),
            )
            partition_json = output_dir / f"{args.partition_region_basename}{suffix}.json"
            write_b4_1_required_task_set_partition_probe(
                partition,
                summary_json=partition_json,
                report_md=output_dir / f"{args.partition_region_basename}{suffix}_zh.md",
            )
            generated_partition_jsons.append(partition_json)
            print(
                "B4.1 required-task-set partition proof probe written for "
                f"{_resolve(probe)}"
            )

    generated_partition_audit_jsons: list[Path] = []
    if args.partition_candidate_audit:
        partition_jsons = tuple(_resolve(path) for path in args.partition_region_result_json) + tuple(
            generated_partition_jsons
        )
        if not partition_jsons:
            print(
                "B4.1 partition candidate audit requested but no partition probe JSON was provided or generated",
                file=sys.stderr,
            )
            return 2
        audit = build_b4_1_partition_candidate_audit(partition_jsons)
        audit_json = output_dir / f"{args.partition_candidate_audit_basename}.json"
        write_b4_1_partition_candidate_audit(
            audit,
            summary_json=audit_json,
            report_md=output_dir / f"{args.partition_candidate_audit_basename}_zh.md",
        )
        generated_partition_audit_jsons.append(audit_json)
        print(f"B4.1 partition candidate audit written for {len(partition_jsons)} probe(s)")
    if args.partition_candidate_audit_import_rows and generated_partition_audit_jsons:
        imported_count = _merge_partition_candidate_audit_rows(rows, tuple(generated_partition_audit_jsons))
        if imported_count:
            _write_rows_jsonl(rows_jsonl, rows)
            _write(rows, rows_csv=rows_csv, summary_json=summary_json, report_md=report_md)
            row_artifacts_dirty = True
            print(
                f"Imported {imported_count} generated B4.1 partition audit evidence row(s) into {rows_jsonl}"
            )

    if args.restricted_region_bound_ledger:
        source_probes = tuple(args.source_probe_json)
        targeted_probe_jsons = tuple(_resolve(path) for path in args.targeted_region_result_json)
        for index, probe in enumerate(source_probes, start=1):
            suffix = "" if len(source_probes) == 1 else f"_{index:03d}"
            ledger = build_b4_1_restricted_region_bound_ledger(
                _resolve(probe),
                targeted_probe_jsons=targeted_probe_jsons,
                max_regions=int(args.targeted_region_max_regions),
            )
            write_b4_1_restricted_region_bound_ledger(
                ledger,
                summary_json=output_dir / f"{args.restricted_region_bound_ledger_basename}{suffix}.json",
                report_md=output_dir / f"{args.restricted_region_bound_ledger_basename}{suffix}_zh.md",
            )
            print(
                "B4.1 restricted-region bound ledger written for "
                f"{_resolve(probe)}"
            )

    if args.stage_a:
        instances = _stage_a_instances(args)
        for instance_path in instances:
            for mode in tuple(args.stage_a_modes):
                key = (str(_resolve(instance_path)), str(mode))
                if key in stage_a_keys:
                    continue
                if not _resource_gate(
                    args,
                    rows,
                    rows_jsonl=rows_jsonl,
                    rows_csv=rows_csv,
                    summary_json=summary_json,
                    report_md=report_md,
                    output_dir=output_dir,
                    stage="A",
                    matrix_group="B4.1 Stage A regression",
                    instance_path=str(_resolve(instance_path)),
                    source_probe_json="",
                    mode=str(mode),
                    variant="",
                    phase="resource_precheck",
                ):
                    return 2
                report = run_b4_1_stage_a_regression(
                    [str(_resolve(instance_path))],
                    matrix_group="B4.1 Stage A regression",
                    modes=(str(mode),),
                    max_direct_tasks=int(args.max_direct_tasks),
                    max_rounds=int(args.max_rounds),
                    wall_time_limit_sec=args.row_time_limit_sec,
                    max_columns_per_round=int(args.max_columns_per_round),
                    max_tree_nodes=int(args.max_tree_nodes),
                    max_branch_depth=int(args.max_branch_depth),
                    labeling_final_judge_exact_harvest_target=int(
                        args.labeling_final_judge_exact_harvest_target
                    ),
                )
                for row in report["rows"]:
                    rows.append(row)
                    stage_a_keys.add(_stage_a_key(row))
                    _append_row_jsonl(rows_jsonl, row)
                    row_artifacts_dirty = True
            _write(rows, rows_csv=rows_csv, summary_json=summary_json, report_md=report_md)

    if args.stage_b_worker_tail_hidden_probe:
        instances = _stage_a_instances(args)
        probe_dir = output_dir / str(args.stage_b_worker_tail_output_subdir)
        for instance_path in instances:
            probe_path = probe_dir / f"{Path(instance_path).stem}_b2_worker_tail_probe.json"
            if not _resource_gate(
                args,
                rows,
                rows_jsonl=rows_jsonl,
                rows_csv=rows_csv,
                summary_json=summary_json,
                report_md=report_md,
                output_dir=output_dir,
                stage="B",
                matrix_group="B4.1 Stage B 30-scale worker-tail hidden-negative diagnostic",
                instance_path=str(_resolve(instance_path)),
                source_probe_json=str(probe_path),
                mode="B4.1_worker_tail_hidden_negative_probe",
                variant="V2_latest_service_start_slot_bound",
                phase="resource_precheck",
            ):
                return 2
            if args.resume and probe_path.exists():
                report = run_b4_1_stage_b_from_probe(
                    probe_path,
                    matrix_group="B4.1 Stage B 30-scale worker-tail hidden-negative diagnostic",
                    variants=(),
                    skip_keys=stage_b_keys,
                )
            else:
                report = run_b4_1_stage_b_worker_tail_hidden_probe(
                    str(_resolve(instance_path)),
                    output_probe_json=probe_path,
                    matrix_group="B4.1 Stage B 30-scale worker-tail hidden-negative diagnostic",
                    max_direct_tasks=int(args.stage_b_worker_tail_max_direct_tasks),
                    max_rounds=int(args.stage_b_worker_tail_max_rounds),
                    wall_time_limit_sec=float(args.stage_b_worker_tail_time_limit_sec),
                    max_columns_per_round=int(args.stage_b_worker_tail_max_columns_per_round),
                    skip_b0_direct=bool(args.stage_b_worker_tail_skip_b0_direct),
                    tail_dual_stabilization_enabled=bool(args.stage_b_worker_tail_tail_dual_stabilization),
                    labeling_final_judge_exact_harvest_target=int(
                        args.labeling_final_judge_exact_harvest_target
                    ),
                    skip_keys=stage_b_keys,
                )
            for row in report["rows"]:
                rows.append(row)
                stage_b_keys.add(_stage_b_key(row))
                _append_row_jsonl(rows_jsonl, row)
                row_artifacts_dirty = True
            _write(rows, rows_csv=rows_csv, summary_json=summary_json, report_md=report_md)

    if args.stage_b:
        for probe in args.source_probe_json:
            for variant in tuple(args.stage_b_variants):
                if not _resource_gate(
                    args,
                    rows,
                    rows_jsonl=rows_jsonl,
                    rows_csv=rows_csv,
                    summary_json=summary_json,
                    report_md=report_md,
                    output_dir=output_dir,
                    stage="B",
                    matrix_group="B4.1 Stage B 30-scale staged frontier",
                    instance_path="",
                    source_probe_json=str(_resolve(probe)),
                    mode="B4.1_compact_pricing_formulation",
                    variant=str(variant),
                    phase="resource_precheck",
                ):
                    return 2
            report = run_b4_1_stage_b_from_probe(
                _resolve(probe),
                matrix_group="B4.1 Stage B 30-scale staged frontier",
                variants=tuple(args.stage_b_variants),
                history_round=int(args.history_round),
                negative_feasibility_time_limit_sec=float(args.negative_feasibility_time_limit_sec),
                optimization_proof_time_limit_sec=float(args.optimization_proof_time_limit_sec),
                threads=int(args.threads),
                skip_keys=stage_b_keys,
            )
            for row in report["rows"]:
                rows.append(row)
                stage_b_keys.add(_stage_b_key(row))
                _append_row_jsonl(rows_jsonl, row)
                row_artifacts_dirty = True
            _write(rows, rows_csv=rows_csv, summary_json=summary_json, report_md=report_md)

    if args.stage_c:
        stage_c_probes = tuple(args.stage_c_source_probe_json or args.source_probe_json)
        for probe in stage_c_probes:
            for variant in tuple(args.stage_c_variants):
                if not _resource_gate(
                    args,
                    rows,
                    rows_jsonl=rows_jsonl,
                    rows_csv=rows_csv,
                    summary_json=summary_json,
                    report_md=report_md,
                    output_dir=output_dir,
                    stage="C",
                    matrix_group="B4.1 Stage C 30-scale selected diagnostic",
                    instance_path="",
                    source_probe_json=str(_resolve(probe)),
                    mode="B4.1_selected_30_diagnostic",
                    variant=str(variant),
                    phase="resource_precheck",
                ):
                    return 2
            report = run_b4_1_stage_c_selected_from_probe(
                _resolve(probe),
                matrix_group="B4.1 Stage C 30-scale selected diagnostic",
                variants=tuple(args.stage_c_variants),
                history_round=int(args.history_round),
                negative_feasibility_time_limit_sec=float(args.negative_feasibility_time_limit_sec),
                optimization_proof_time_limit_sec=float(args.optimization_proof_time_limit_sec),
                threads=int(args.threads),
                skip_keys=stage_c_keys,
            )
            for row in report["rows"]:
                rows.append(row)
                stage_c_keys.add(_stage_b_key(row))
                _append_row_jsonl(rows_jsonl, row)
                row_artifacts_dirty = True
            _write(rows, rows_csv=rows_csv, summary_json=summary_json, report_md=report_md)

    if args.tree_closure_from_probe:
        result_dir = output_dir / str(args.tree_closure_result_subdir)
        result_dir.mkdir(parents=True, exist_ok=True)
        for index, probe in enumerate(tuple(args.source_probe_json), start=1):
            probe_path = _resolve(probe)
            key = (str(probe_path), "B4.1_30_tree_closure_from_probe")
            if args.resume and key in stage_d_keys:
                continue
            if not _resource_gate(
                args,
                rows,
                rows_jsonl=rows_jsonl,
                rows_csv=rows_csv,
                summary_json=summary_json,
                report_md=report_md,
                output_dir=output_dir,
                stage="D",
                matrix_group="B4.1 Stage D 30-scale tree closure from root-tail probe",
                instance_path="",
                source_probe_json=str(probe_path),
                mode="B4.1_30_tree_closure_from_probe",
                variant="V4_root_tail_probe_tree_gate",
                phase="resource_precheck",
            ):
                return 2
            report = run_b4_1_tree_closure_from_probe(
                probe_path,
                max_rounds=int(args.tree_closure_max_rounds),
                wall_time_limit_sec=args.tree_closure_time_limit_sec,
                max_columns_per_round=int(args.tree_closure_max_columns_per_round),
                max_tree_nodes=int(args.tree_closure_max_nodes),
                max_branch_depth=int(args.tree_closure_max_branch_depth),
                worker_pricer_kind=str(args.tree_closure_worker_pricer_kind),
                tail_dual_stabilization_enabled=bool(args.tree_closure_tail_dual_stabilization_enabled),
                tail_dual_stabilization_alpha=float(args.tree_closure_tail_dual_stabilization_alpha),
                tail_dual_stabilization_window=int(args.tree_closure_tail_dual_stabilization_window),
                labeling_final_judge_enabled=_tree_closure_labeling_final_judge_enabled(
                    str(args.tree_closure_labeling_final_judge_mode)
                ),
                labeling_final_judge_max_exact_tasks=args.tree_closure_labeling_final_judge_max_exact_tasks,
                labeling_final_judge_exact_harvest_target=int(
                    args.tree_closure_labeling_final_judge_exact_harvest_target
                    if args.tree_closure_labeling_final_judge_exact_harvest_target is not None
                    else args.labeling_final_judge_exact_harvest_target
                ),
                live_sri_policy=str(args.tree_closure_live_sri_policy),
            )
            raw_results = report.get("tree_closure_raw_results") or []
            if raw_results:
                result_path = result_dir / f"tree_closure_{index:03d}.json"
                result_path.write_text(
                    json.dumps(raw_results[0], ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
            for row in report["rows"]:
                rows.append(row)
                stage_d_keys.add(_tree_closure_key(row))
                _append_row_jsonl(rows_jsonl, row)
                row_artifacts_dirty = True
            _write(rows, rows_csv=rows_csv, summary_json=summary_json, report_md=report_md)

    if row_artifacts_dirty:
        _write(rows, rows_csv=rows_csv, summary_json=summary_json, report_md=report_md)
        print(f"B4.1 report written to {report_md}")
    return 0


def _apply_stage_b_v4_root_tail_partition_alias(args) -> None:
    if not bool(getattr(args, "stage_b_v4_root_tail_partition_proof", False)):
        return
    if getattr(args, "source_probe_json", None):
        args.required_task_set_partition_proof_probe = True
        if int(getattr(args, "partition_region_max_task_sets", 0) or 0) <= 0:
            args.partition_region_max_task_sets = B41_ROOT_TAIL_PARTITION_DEFAULT_MAX_TASK_SETS
    args.partition_candidate_audit = True
    args.partition_candidate_audit_import_rows = True


def _stage_a_instances(args) -> list[Path]:
    explicit = [_resolve(path) for path in args.instance]
    if explicit:
        return explicit
    if not args.manifest:
        return []
    manifest = json.loads(_resolve(args.manifest).read_text(encoding="utf-8"))
    entries = manifest.get("instances") if isinstance(manifest, dict) else manifest
    if not isinstance(entries, list):
        return []
    scales = {int(value) for value in args.scales} if args.scales else set()
    limit = max(0, int(args.limit_per_scale))
    counts: dict[int, int] = {}
    selected: list[Path] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        path = entry.get("path") or entry.get("instance_path")
        scale = int(entry.get("task_count") or entry.get("scale") or _scale_from_path(path) or 0)
        if scales and scale not in scales:
            continue
        if limit and counts.get(scale, 0) >= limit:
            continue
        selected.append(_resolve(path))
        counts[scale] = int(counts.get(scale, 0)) + 1
    return selected


def _scale_from_path(path: object) -> int | None:
    raw = str(path or "")
    for token in raw.replace("\\", "/").split("/"):
        if token.startswith("lunar_ice_") and token[-3:].isdigit():
            return int(token[-3:])
    return None


def _stage_a_key(row: dict) -> tuple[str, str]:
    return (str(_resolve(row.get("instance_path") or "")), str(row.get("mode") or ""))


def _stage_b_key(row: dict) -> tuple[str, str, str, str]:
    return (
        str(_resolve(row.get("source_probe_json") or "")),
        str(row.get("round") or ""),
        str(row.get("variant") or ""),
        str(row.get("phase") or ""),
    )


def _tree_closure_key(row: dict) -> tuple[str, str]:
    return (
        str(_resolve(row.get("source_probe_json") or "")),
        str(row.get("mode") or ""),
    )


def _write(rows: list[dict], *, rows_csv: Path, summary_json: Path, report_md: Path) -> None:
    write_b4_1_artifacts(
        build_b4_1_report(rows),
        rows_csv=rows_csv,
        summary_json=summary_json,
        report_md=report_md,
    )


def _load_rows_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped:
            rows.append(json.loads(stripped))
    return rows


def _merge_imported_rows(rows: list[dict], row_sources: Iterable[Path]) -> int:
    seen = {_row_import_key(row) for row in rows}
    added = 0
    for source in row_sources:
        for row in _load_rows_jsonl(source):
            key = _row_import_key(row)
            if key in seen:
                continue
            rows.append(row)
            seen.add(key)
            added += 1
    return added


def _merge_partition_candidate_audit_rows(rows: list[dict], audit_sources: Iterable[Path]) -> int:
    seen = {_row_import_key(row) for row in rows}
    added = 0
    for source in audit_sources:
        for row in rows_from_b4_1_partition_candidate_audit(source):
            key = _row_import_key(row)
            if key in seen:
                continue
            rows.append(row)
            seen.add(key)
            added += 1
    return added


def _row_import_key(row: dict) -> tuple[str, ...]:
    stage = str(row.get("stage") or "")
    if stage == "A":
        return ("A", str(_resolve(row.get("instance_path") or "")), str(row.get("mode") or ""))
    if stage in {"B", "C"}:
        source = str(_resolve(row.get("source_probe_json") or ""))
        if str(row.get("mode") or "") == "B4.1_partition_candidate_audit":
            return (
                stage,
                str(_resolve(row.get("partition_candidate_audit_json") or "")),
                str(_resolve(row.get("partition_probe_json") or "")),
                source,
                str(row.get("round") or ""),
                str(row.get("variant") or ""),
                str(row.get("phase") or ""),
            )
        return (
            stage,
            source,
            str(row.get("round") or ""),
            str(row.get("mode") or ""),
            str(row.get("variant") or ""),
            str(row.get("phase") or ""),
        )
    if stage == "D":
        return ("D", *_tree_closure_key(row))
    return (
        stage,
        str(row.get("matrix_group") or ""),
        str(row.get("instance_path") or ""),
        str(row.get("source_probe_json") or ""),
        str(row.get("mode") or ""),
        str(row.get("variant") or ""),
        str(row.get("phase") or ""),
        str(row.get("round") or ""),
    )


def _write_rows_jsonl(path: Path, rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _append_row_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()


def _tree_closure_labeling_final_judge_enabled(mode: str) -> bool | None:
    normalized = str(mode or "env").strip().lower()
    if normalized == "on":
        return True
    if normalized == "off":
        return False
    if normalized in {"env", "auto"}:
        return None
    raise ValueError(f"unsupported tree closure labeling final judge mode: {mode!r}")


def _resource_gate(
    args,
    rows: list[dict],
    *,
    rows_jsonl: Path,
    rows_csv: Path,
    summary_json: Path,
    report_md: Path,
    output_dir: Path,
    stage: str,
    matrix_group: str,
    instance_path: str,
    source_probe_json: str,
    mode: str,
    variant: str,
    phase: str,
) -> bool:
    ok, reason, payload = _resource_status(
        output_dir=output_dir,
        min_available_mem_gb=float(args.min_available_mem_gb),
        min_free_disk_gb=float(args.min_free_disk_gb),
        max_output_dir_gb=float(args.max_output_dir_gb),
    )
    if ok:
        return True
    message = f"B4.1 resource gate failed before {stage}/{mode}/{variant or '-'}: {reason}"
    if str(args.resource_check_action) == "warn":
        print(f"WARNING: {message}", file=sys.stderr)
        return True
    row = _resource_guard_row(
        stage=stage,
        matrix_group=matrix_group,
        instance_path=instance_path,
        source_probe_json=source_probe_json,
        mode=mode,
        variant=variant,
        phase=phase,
        reason=reason,
        payload=payload,
    )
    rows.append(row)
    _append_row_jsonl(rows_jsonl, row)
    _write(rows, rows_csv=rows_csv, summary_json=summary_json, report_md=report_md)
    print(message, file=sys.stderr)
    return False


def _resource_status(
    *,
    output_dir: Path,
    min_available_mem_gb: float,
    min_free_disk_gb: float,
    max_output_dir_gb: float,
) -> tuple[bool, str, dict]:
    available_mem_gb = _available_memory_gb()
    free_disk_gb = _free_disk_gb(output_dir)
    output_dir_gb = _directory_size_gb(output_dir)
    payload = {
        "available_mem_gb": available_mem_gb,
        "min_available_mem_gb": float(min_available_mem_gb),
        "free_disk_gb": free_disk_gb,
        "min_free_disk_gb": float(min_free_disk_gb),
        "output_dir_gb": output_dir_gb,
        "max_output_dir_gb": float(max_output_dir_gb),
    }
    failures = []
    if available_mem_gb is not None and available_mem_gb < float(min_available_mem_gb):
        failures.append(f"available_mem_gb={available_mem_gb:.3f} < {float(min_available_mem_gb):.3f}")
    if free_disk_gb is not None and free_disk_gb < float(min_free_disk_gb):
        failures.append(f"free_disk_gb={free_disk_gb:.3f} < {float(min_free_disk_gb):.3f}")
    if output_dir_gb is not None and output_dir_gb > float(max_output_dir_gb):
        failures.append(f"output_dir_gb={output_dir_gb:.3f} > {float(max_output_dir_gb):.3f}")
    return (not failures, "; ".join(failures), payload)


def _resource_guard_row(
    *,
    stage: str,
    matrix_group: str,
    instance_path: str,
    source_probe_json: str,
    mode: str,
    variant: str,
    phase: str,
    reason: str,
    payload: dict,
) -> dict:
    return {
        "stage": stage,
        "matrix_group": matrix_group,
        "instance_path": instance_path,
        "source_probe_json": source_probe_json,
        "scale": "",
        "instance_id": "",
        "mode": mode,
        "variant": variant,
        "phase": phase,
        "round": "",
        "algorithm_status": "RESOURCE_GUARD_STOPPED",
        "certificate_scope": "FEASIBLE_INCUMBENT_ONLY",
        "underlying_certificate_scope": "",
        "pricing_state": "INCOMPLETE_LIMIT",
        "exact_status": "NOT_SOLVED",
        "bpc_tree_optimal": False,
        "manual_rc_fail": 0,
        "pricing_rc_fail": 0,
        "certificate_leak": 0,
        "hidden_negative_count": "",
        "hidden_negative_miss_reason_counts": {},
        "hidden_negative_top_miss_reason": "",
        "hidden_negative_worker_not_generated_count": 0,
        "hidden_negative_pruned_by_dominance_count": 0,
        "hidden_negative_pricing_timeout_only_count": 0,
        "active_column_count": "",
        "pool_column_count": "",
        "columns_added": "",
        "active_columns_after_merge": "",
        "new_task_set_count": "",
        "replacement_task_set_count": "",
        "best_negative_rc": "",
        "last_best_reduced_cost": "",
        "final_judge_wall_time": "",
        "rmp_round_count": "",
        "diagnostic_claimed_certificate": 0,
        "can_certify_no_negative": False,
        "underlying_can_certify_no_negative": False,
        "b4_1_certificate_suppressed": False,
        "frontier_lb_official": False,
        "frontier_coverage_complete": False,
        "frontier_unsupported_region_count": 1,
        "pricing_proof_kind": "FRONTIER_BOUND_INCOMPLETE",
        "wall_time": 0.0,
        "fail_closed_reason": f"resource_guard_failed: {reason}; payload={json.dumps(payload, sort_keys=True)}",
    }


def _available_memory_gb() -> float | None:
    meminfo = Path("/proc/meminfo")
    if not meminfo.exists():
        return None
    for line in meminfo.read_text(encoding="utf-8").splitlines():
        if line.startswith("MemAvailable:"):
            parts = line.split()
            if len(parts) >= 2:
                return int(parts[1]) / (1024.0 * 1024.0)
    return None


def _free_disk_gb(path: Path) -> float | None:
    try:
        usage = shutil.disk_usage(path)
    except OSError:
        return None
    return usage.free / (1024.0**3)


def _directory_size_gb(path: Path) -> float | None:
    if not path.exists():
        return 0.0
    total = 0
    try:
        for item in path.rglob("*"):
            if item.is_file():
                total += item.stat().st_size
    except OSError:
        return None
    return total / (1024.0**3)


def _resolve(path: object) -> Path:
    raw = Path(str(path))
    return raw if raw.is_absolute() else ROOT / raw


if __name__ == "__main__":
    raise SystemExit(main())
