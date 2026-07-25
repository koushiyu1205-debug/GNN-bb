#!/usr/bin/env python3
"""Run resource-bounded binding-V2 B0 over only the new development pool."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
from time import perf_counter

try:
    import psutil
except ImportError:  # Optional process telemetry must not block exact runs.
    psutil = None

from lunar_ice_bpc.guidance.resources import (
    recommended_parallelism,
    resource_snapshot,
)
from lunar_ice_bpc.guidance.deployment import (
    DeploymentEligibilityManifest,
)
from lunar_ice_bpc.guidance.identity import (
    P0V2_BINDING_V2_B0_CONTROL_ID,
)


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--development-manifest",
        default="data/gat_p0v2/development_instances_manifest.json",
    )
    parser.add_argument(
        "--config",
        default="configs/benchmarks/p0v2_gat_binding_v2_b0_probe.yaml",
    )
    parser.add_argument(
        "--output-dir",
        default="runs/p0v2_gat_binding_v2_b0_development",
    )
    parser.add_argument(
        "--results-jsonl",
        default="data/gat_p0v2/b0_development_results.jsonl",
    )
    parser.add_argument("--scales", default="5,10,20,30")
    parser.add_argument(
        "--split-manifest",
        default="",
        help="Optional audited split manifest for fold/partition filtering.",
    )
    parser.add_argument("--fold", type=int)
    parser.add_argument(
        "--partition",
        choices=("development", "calibration"),
        default="development",
    )
    parser.add_argument(
        "--deployment-manifest",
        default="",
        help="Explicit checkpoint deployment manifest for H/HA experiments.",
    )
    parser.add_argument(
        "--guidance-mode",
        choices=("off", "harvest", "task_arc", "shadow"),
        default="off",
    )
    parser.add_argument("--experiment-variant", default="P0")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--max-per-scale", type=int, default=0)
    parser.add_argument(
        "--indices",
        default="",
        help=(
            "Optional comma-separated instance indices. This is intended for "
            "audited targeted reruns; scale filtering still applies."
        ),
    )
    parser.add_argument("--snapshot-max-per-instance", type=int, default=8)
    parser.add_argument(
        "--collect-training",
        action="store_true",
        help=(
            "Opt in to snapshot/training-row collection. Leave this off for "
            "the clean same-code B0 timing control."
        ),
    )
    parser.add_argument("--outer-timeout-sec", type=float, default=420.0)
    parser.add_argument("--min-free-gb", type=float, default=50.0)
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()
    manifest = json.loads(
        (ROOT / args.development_manifest).read_text(encoding="utf-8")
    )
    if manifest.get("source_role") != "new_development":
        raise SystemExit("B0 development runner accepts new_development only")
    selected_scales = {
        int(value) for value in args.scales.split(",") if value.strip()
    }
    if not selected_scales.issubset({5, 10, 20, 30}):
        raise SystemExit("B0 development scales must be 5/10/20/30")
    rows = [
        row
        for row in manifest.get("instances", ())
        if int(row["scale"]) in selected_scales
    ]
    if args.indices:
        selected_indices = {
            int(value)
            for value in str(args.indices).split(",")
            if value.strip()
        }
        if not selected_indices or min(selected_indices) < 1:
            raise SystemExit("--indices must contain positive integers")
        rows = [
            row
            for row in rows
            if int(row["index"]) in selected_indices
        ]
    split_manifest_hash = ""
    if args.split_manifest:
        split = json.loads(
            (ROOT / args.split_manifest).read_text(encoding="utf-8")
        )
        if not bool((split.get("audit") or {}).get("passed")):
            raise SystemExit("split manifest audit did not pass")
        split_manifest_hash = str(split.get("manifest_hash") or "")
        if not split_manifest_hash:
            raise SystemExit("split manifest has no immutable manifest hash")
        selected_hashes = {
            str(row["instance_content_hash"])
            for row in split.get(args.partition, ())
            if args.fold is None
            or (
                args.partition == "development"
                and int(row["fold"]) == int(args.fold)
            )
        }
        rows = [
            row
            for row in rows
            if str(row["instance_content_hash"]) in selected_hashes
        ]
    if args.guidance_mode != "off" and not args.deployment_manifest:
        raise SystemExit(
            "guided mode requires an explicit --deployment-manifest"
        )
    if args.guidance_mode == "off" and args.deployment_manifest:
        raise SystemExit(
            "--deployment-manifest is invalid when guidance mode is off"
        )
    expected_variant = {
        "harvest": "H",
        "task_arc": "HA",
    }.get(str(args.guidance_mode))
    if expected_variant is not None and str(args.experiment_variant) != expected_variant:
        raise SystemExit(
            f"guidance mode {args.guidance_mode!r} requires "
            f"--experiment-variant {expected_variant}"
        )
    deployment_scope = "p0_control"
    deployment_manifest_hash = ""
    guidance_checkpoint_id = ""
    guidance_model_kind = ""
    if args.guidance_mode != "off":
        if not args.split_manifest or args.fold is None:
            raise SystemExit(
                "guided discovery requires --split-manifest and one held-out --fold"
            )
        if args.partition != "development":
            raise SystemExit(
                "guided discovery cannot run calibration/protected partitions"
            )
        deployment_path = (ROOT / args.deployment_manifest).resolve()
        deployment_payload = json.loads(
            deployment_path.read_text(encoding="utf-8")
        )
        deployment_manifest_hash = str(
            deployment_payload.get("manifest_hash") or ""
        )
        if not deployment_manifest_hash:
            raise SystemExit("deployment manifest has no immutable manifest hash")
        deployment = DeploymentEligibilityManifest.load(deployment_path)
        guidance_checkpoint_id = str(deployment.checkpoint_id)
        guidance_model_kind = str(deployment.model_kind)
        if deployment.experimental_discovery_only:
            if deployment.formal_promotion_eligible:
                raise SystemExit(
                    "discovery-only manifest cannot be formal-promotion eligible"
                )
            deployment_scope = "held_out_development_fold_discovery_only"
            if int(deployment.discovery_validation_fold) != int(args.fold):
                raise SystemExit(
                    "discovery manifest/checkpoint validation fold mismatch"
                )
        elif not deployment.formal_promotion_eligible:
            raise SystemExit(
                "guided manifest is neither discovery-only nor formally promoted"
            )
        else:
            deployment_scope = "formal_promotion"
    if int(args.max_per_scale) > 0:
        rows = [
            row
            for scale in sorted(selected_scales)
            for row in [
                item for item in rows if int(item["scale"]) == scale
            ][: int(args.max_per_scale)]
        ]
    output_root = (ROOT / args.output_dir).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    resources = resource_snapshot(output_root)
    if resources.disk_available_bytes < float(args.min_free_gb) * 1024**3:
        raise SystemExit("insufficient disk for B0 development run")
    workers = recommended_parallelism(
        resources,
        requested=max(1, int(args.workers)),
        min_memory_per_worker_bytes=2 * 1024**3,
        min_disk_free_bytes=int(float(args.min_free_gb) * 1024**3),
    )
    results_path = (ROOT / args.results_jsonl).resolve()
    results_path.parent.mkdir(parents=True, exist_ok=True)
    ledger = _load_result_ledger(results_path)
    started = perf_counter()
    results = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(
                _run_one,
                row,
                config=(ROOT / args.config).resolve(),
                output_root=output_root,
                snapshot_max_per_instance=int(
                    args.snapshot_max_per_instance
                ),
                outer_timeout_sec=float(args.outer_timeout_sec),
                resume=not args.no_resume,
                collect_training=bool(args.collect_training),
                deployment_manifest=(
                    None
                    if not args.deployment_manifest
                    else (ROOT / args.deployment_manifest).resolve()
                ),
                guidance_mode=str(args.guidance_mode),
                experiment_variant=str(args.experiment_variant),
            ): row
            for row in rows
        }
        for completed, future in enumerate(as_completed(futures), start=1):
            result = future.result()
            result.update(
                {
                    "split_manifest_hash": split_manifest_hash,
                    "fold": args.fold,
                    "partition": str(args.partition),
                    "deployment_scope": deployment_scope,
                    "deployment_manifest_hash": deployment_manifest_hash,
                    "guidance_checkpoint_id": guidance_checkpoint_id,
                    "guidance_model_kind": guidance_model_kind,
                }
            )
            results.append(result)
            ledger[str(result["instance_content_hash"])] = result
            _write_result_ledger(results_path, ledger)
            print(
                f"[{completed:03d}/{len(rows):03d}] "
                f"scale={result['scale']} index={result['index']:03d} "
                f"status={result['algorithm_status']} "
                f"wall={result['cold_start_total_sec']}",
                flush=True,
            )
    results.sort(key=lambda row: (int(row["scale"]), int(row["index"])))
    # ``--no-resume`` controls whether selected instances are recomputed.  It
    # must not erase completed rows for other scales from the shared ledger.
    for row in results:
        ledger[str(row["instance_content_hash"])] = row
    all_results = sorted(
        ledger.values(),
        key=lambda row: (int(row["scale"]), int(row["index"])),
    )
    _write_result_ledger(results_path, ledger)
    summary = {
        "schema_version": "lunar_ice_bpc.p0v2_b0_development_run.v1",
        "source_role": "new_development",
        "source_baseline_id": P0V2_BINDING_V2_B0_CONTROL_ID,
        "selected_scales": sorted(selected_scales),
        "workers": workers,
        "run_count": len(results),
        "total_record_count": len(all_results),
        "wall_sec": perf_counter() - started,
        "resource_snapshot_before": resources.__dict__,
        "exact_count": sum(
            row["algorithm_status"] == "BPC_OPTIMAL"
            for row in all_results
        ),
        "legal_incomplete_count": sum(
            row["algorithm_status"] != "BPC_OPTIMAL"
            and row["redlines_zero"]
            for row in all_results
        ),
        "redline_failure_count": sum(
            not row["redlines_zero"] for row in all_results
        ),
        "protected_instance_count_run": 0,
        "training_instrumentation_enabled": bool(args.collect_training),
        "experiment_variant": str(args.experiment_variant),
        "guidance_mode": str(args.guidance_mode),
        "deployment_manifest": (
            ""
            if not args.deployment_manifest
            else str((ROOT / args.deployment_manifest).resolve())
        ),
        "deployment_scope": deployment_scope,
        "split_manifest": str(args.split_manifest),
        "split_manifest_hash": split_manifest_hash,
        "fold": args.fold,
        "partition": str(args.partition),
        "deployment_manifest_hash": deployment_manifest_hash,
        "guidance_checkpoint_id": guidance_checkpoint_id,
        "guidance_model_kind": guidance_model_kind,
        "results_jsonl": str(results_path),
    }
    summary_path = results_path.with_suffix(".summary.json")
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    print(str(summary_path))
    return 0 if summary["redline_failure_count"] == 0 else 2


def _load_result_ledger(path: Path) -> dict[str, dict]:
    ledger = {}
    if not path.exists():
        return ledger
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            ledger[str(row["instance_content_hash"])] = row
    return ledger


def _write_result_ledger(path: Path, ledger: dict[str, dict]) -> None:
    rows = sorted(
        ledger.values(),
        key=lambda row: (int(row["scale"]), int(row["index"])),
    )
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )
    temporary.replace(path)


def _run_one(
    row: dict,
    *,
    config: Path,
    output_root: Path,
    snapshot_max_per_instance: int,
    outer_timeout_sec: float,
    resume: bool,
    collect_training: bool,
    deployment_manifest: Path | None,
    guidance_mode: str,
    experiment_variant: str,
) -> dict:
    scale = int(row["scale"])
    index = int(row["index"])
    target = (
        output_root
        / f"scale_{scale:03d}"
        / f"instance_{index:03d}"
    )
    summary_path = target / "native_spprc_acceptance_summary.json"
    if resume and summary_path.exists():
        parsed = _parse_result(target, row)
        if parsed is not None:
            parsed["resumed"] = True
            parsed["experiment_variant"] = str(experiment_variant)
            parsed["guidance_mode"] = str(guidance_mode)
            parsed["source_baseline_id"] = P0V2_BINDING_V2_B0_CONTROL_ID
            return parsed
    target.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    for key in (
        "LUNAR_ICE_GAT_SNAPSHOT_DIR",
        "LUNAR_ICE_GAT_SNAPSHOT_MAX_PER_PROCESS",
        "LUNAR_ICE_GAT_SNAPSHOT_MAX_PER_INSTANCE",
        "LUNAR_ICE_GAT_TRAINING_ROWS_DIR",
        "LUNAR_ICE_GAT_DEPLOYMENT_MANIFEST",
        "LUNAR_ICE_GAT_GUIDANCE_MODE",
    ):
        env.pop(key, None)
    if collect_training:
        env.update({
            "LUNAR_ICE_GAT_SNAPSHOT_DIR": str(
                output_root / "snapshots"
            ),
            "LUNAR_ICE_GAT_SNAPSHOT_MAX_PER_PROCESS": str(
                max(1, snapshot_max_per_instance)
            ),
            "LUNAR_ICE_GAT_SNAPSHOT_MAX_PER_INSTANCE": str(
                max(1, snapshot_max_per_instance)
            ),
            "LUNAR_ICE_GAT_TRAINING_ROWS_DIR": str(
                output_root / "training_rows"
            ),
        })
    if deployment_manifest is not None:
        env["LUNAR_ICE_GAT_DEPLOYMENT_MANIFEST"] = str(
            deployment_manifest
        )
        env["LUNAR_ICE_GAT_GUIDANCE_MODE"] = str(guidance_mode)
    command = [
        sys.executable,
        str(ROOT / "scripts" / "run_lunar_ice_native_spprc_acceptance.py"),
        "--config",
        str(config),
        "--scales",
        str(scale),
        "--instance",
        str((ROOT / row["path"]).resolve()),
        "--output-dir",
        str(target),
    ]
    command.append("--no-resume")
    started = perf_counter()
    process = subprocess.Popen(
        command,
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    rss_samples: list[int] = []
    monitor_stop = threading.Event()
    monitor = threading.Thread(
        target=_monitor_process_tree_rss,
        args=(process.pid, monitor_stop, rss_samples),
        daemon=True,
    )
    monitor.start()
    timed_out = False
    try:
        stdout, stderr = process.communicate(
            timeout=max(1.0, outer_timeout_sec)
        )
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(process.pid, signal.SIGTERM)
        try:
            stdout, stderr = process.communicate(timeout=10.0)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
    finally:
        monitor_stop.set()
        monitor.join(timeout=2.0)
    (target / "b0_runner_stdout.log").write_text(stdout, encoding="utf-8")
    (target / "b0_runner_stderr.log").write_text(stderr, encoding="utf-8")
    parsed = _parse_result(target, row)
    if parsed is not None:
        parsed.update(
            {
                "outer_timeout": timed_out,
                "subprocess_returncode": process.returncode,
                "resumed": False,
                "experiment_variant": str(experiment_variant),
                "guidance_mode": str(guidance_mode),
                "source_baseline_id": P0V2_BINDING_V2_B0_CONTROL_ID,
                "process_tree_rss_peak_bytes": max(
                    rss_samples, default=0
                ),
                "process_tree_rss_p90_bytes": _quantile_int(
                    rss_samples, 0.90
                ),
                "result_artifact_bytes": _directory_size_bytes(target),
            }
        )
        return parsed
    return {
        "schema_version": "lunar_ice_bpc.p0v2_b0_development_row.v1",
        "instance_content_hash": row["instance_content_hash"],
        "instance_id": row["instance_id"],
        "scale": scale,
        "index": index,
        "algorithm_status": "BPC_INCOMPLETE_PRICING",
        "cold_start_total_sec": perf_counter() - started,
        "bpc_tree_optimal": False,
        "row_terminal": False,
        "redlines_zero": process.returncode in {0, 143} and not timed_out,
        "outer_timeout": timed_out,
        "subprocess_returncode": process.returncode,
        "resumed": False,
        "result_missing": True,
        "experiment_variant": str(experiment_variant),
        "guidance_mode": str(guidance_mode),
        "source_baseline_id": P0V2_BINDING_V2_B0_CONTROL_ID,
        "process_tree_rss_peak_bytes": max(rss_samples, default=0),
        "process_tree_rss_p90_bytes": _quantile_int(rss_samples, 0.90),
        "result_artifact_bytes": _directory_size_bytes(target),
    }


def _parse_result(target: Path, source: dict) -> dict | None:
    paths = sorted(target.rglob("b4_2_cold_exact_rows.csv"))
    if not paths:
        return None
    with paths[-1].open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        return None
    row = rows[-1]
    redline_fields = (
        "certificate_leak",
        "manual_rc_fail",
        "pricing_rc_fail",
        "tail_dual_certificate_leak",
        "true_dual_rc_recompute_missing",
        "worker_certificate_leak",
    )
    raw_redlines_zero = all(
        str(row.get(field) or "0").lower() in {"0", "false", ""}
        for field in redline_fields
    ) and str(row.get("no_cheat_pass") or "").lower() == "true"
    redline_audit = _semantic_redline_audit(
        target, row, raw_fields=redline_fields
    )
    cold_start_total_sec = float(
        row.get("cold_start_total_sec") or 0.0
    )
    return {
        "schema_version": "lunar_ice_bpc.p0v2_b0_development_row.v1",
        "instance_content_hash": source["instance_content_hash"],
        "instance_id": source["instance_id"],
        "scale": int(source["scale"]),
        "index": int(source["index"]),
        "algorithm_status": str(row.get("algorithm_status") or ""),
        "cold_start_total_sec": cold_start_total_sec,
        "root_cg_sec": float(row.get("root_cg_sec") or 0.0),
        "tree_sec": float(row.get("tree_sec") or 0.0),
        "bpc_tree_optimal": str(row.get("bpc_tree_optimal") or "").lower()
        == "true",
        "row_terminal": str(row.get("row_terminal") or "").lower()
        == "true",
        "row_budget_exhausted": str(
            row.get("row_budget_exhausted") or ""
        ).lower()
        == "true",
        "redlines_zero": bool(redline_audit["passed"]),
        "raw_redlines_zero": raw_redlines_zero,
        "redline_audit": redline_audit,
        "config_hash": str(row.get("config_hash") or ""),
        "model_id": str(row.get("model_id") or ""),
        "result_csv": str(paths[-1].resolve()),
        **_collect_stage_b_metrics(
            target, cold_start_total_sec=cold_start_total_sec
        ),
    }


def _semantic_redline_audit(
    target: Path,
    cold_row: dict,
    *,
    raw_fields: tuple[str, ...],
) -> dict:
    """Separate fail-closed certificate safety from diagnostic timeouts."""

    raw = {
        field: int(
            str(cold_row.get(field) or "0").lower()
            not in {"0", "false", ""}
        )
        for field in raw_fields
    }
    issues = []
    certifying_scope = str(cold_row.get("certificate_scope") or "") in {
        "BPC_NODE_LP_CERTIFIED",
        "BPC_TREE_OPTIMAL",
    }
    if certifying_scope and raw["manual_rc_fail"]:
        issues.append("certifying_manual_rc_audit_failed")
    if certifying_scope and raw["pricing_rc_fail"]:
        issues.append("certifying_pricing_rc_audit_failed")
    if raw["worker_certificate_leak"]:
        issues.append("worker_certificate_leak")
    if raw["true_dual_rc_recompute_missing"]:
        issues.append("true_dual_rc_recompute_missing")

    direct_certificate_leak = False
    tail_dual_certificate_leak = False
    b41_summary_paths = sorted(target.rglob("b4_1_summary.json"))
    if b41_summary_paths:
        try:
            summary = json.loads(
                b41_summary_paths[-1].read_text(encoding="utf-8")
            )
            summary_redlines = dict(summary.get("redlines") or {})
            direct_certificate_leak = int(
                summary_redlines.get("certificate_leak_count") or 0
            ) > 0
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            issues.append("b4_1_summary_unreadable")
    elif raw["certificate_leak"] and not raw["tail_dual_certificate_leak"]:
        direct_certificate_leak = True

    b41_row_paths = sorted(target.rglob("b4_1_rows.jsonl"))
    if b41_row_paths:
        try:
            from lunar_ice_bpc.runners.b4_1_true_dual_proof_tail import (
                _tail_dual_certificate_leak,
            )

            for path in b41_row_paths:
                for line in path.read_text(encoding="utf-8").splitlines():
                    if line.strip() and _tail_dual_certificate_leak(
                        json.loads(line)
                    ):
                        tail_dual_certificate_leak = True
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            issues.append("b4_1_tail_rows_unreadable")
    elif raw["tail_dual_certificate_leak"]:
        tail_dual_certificate_leak = True

    if direct_certificate_leak:
        issues.append("direct_certificate_leak")
    if tail_dual_certificate_leak:
        issues.append("tail_dual_certificate_leak")
    if str(cold_row.get("no_cheat_pass") or "").lower() != "true":
        issues.append("no_cheat_pass_false")
    return {
        "schema_version": (
            "lunar_ice_bpc.p0v2_semantic_redline_audit.v1"
        ),
        "passed": not issues,
        "issues": issues,
        "raw_fields": raw,
        "certifying_scope_claimed": certifying_scope,
        "direct_certificate_leak_recomputed": direct_certificate_leak,
        "tail_dual_certificate_leak_recomputed": (
            tail_dual_certificate_leak
        ),
        "diagnostic_timeout_rc_flags_ignored": bool(
            not certifying_scope
            and (raw["manual_rc_fail"] or raw["pricing_rc_fail"])
        ),
        "configured_but_unobserved_worker_tail_flag_ignored": bool(
            raw["tail_dual_certificate_leak"]
            and not tail_dual_certificate_leak
        ),
    }


def _collect_stage_b_metrics(
    target: Path, *, cold_start_total_sec: float
) -> dict:
    """Extract deduplicated discovery, overhead, and safety telemetry."""

    json_paths = sorted(
        {
            *target.rglob("probe.json"),
            *target.rglob("tree_closure_*.json"),
        }
    )
    lifecycle_events: dict[tuple, dict] = {}
    first_addable_seconds = []
    first_addable_by_context = []
    best_rc_trajectories = []
    duplicate_negative_count = 0
    candidate_negative_count = 0
    bound_gain = 0.0
    pricing_sec_for_bound = 0.0
    global_ub = None
    seen_history_hashes = set()
    safety = {
        "guidance_induced_permanent_drop": 0,
        "binding_mismatch_accepted": 0,
        "nonfinite_hint_accepted": 0,
        "legal_universe_hash_mismatch": 0,
        "labels_dropped": False,
    }
    for path in json_paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if path.name.startswith("tree_closure_"):
            value = payload.get("global_ub")
            if value is not None:
                global_ub = float(value)
        for dictionary in _walk_dictionaries(payload):
            _collect_lifecycle_event(dictionary, lifecycle_events)
            safety["guidance_induced_permanent_drop"] = max(
                safety["guidance_induced_permanent_drop"],
                int(dictionary.get("guidance_filter_count") or 0),
                int(dictionary.get("guidance_arc_drop_count") or 0),
                int(dictionary.get("guidance_label_drop_count") or 0),
                int(dictionary.get("guidance_branch_pair_drop_count") or 0),
            )
            if bool(dictionary.get("labels_dropped")):
                safety["labels_dropped"] = True
            before = dictionary.get(
                "legal_action_universe_hash_before_sort"
            )
            after = dictionary.get(
                "legal_action_universe_hash_after_sort"
            )
            if before and after and before != after:
                safety["legal_universe_hash_mismatch"] += 1
            guidance_effective = bool(
                dictionary.get("guidance_effective")
                or str(
                    dictionary.get("guidance_effective_mode") or "off"
                )
                != "off"
            )
            guidance_validation = dict(
                dictionary.get("guidance_validation") or {}
            )
            if guidance_effective and (
                dictionary.get("guidance_binding_match") is False
                or dictionary.get("request_bindings_match") is False
                or (
                    guidance_validation
                    and not bool(
                        guidance_validation.get("guidance_accepted")
                    )
                )
            ):
                safety["binding_mismatch_accepted"] += 1
            if bool(dictionary.get("nonfinite_hint_accepted")):
                safety["nonfinite_hint_accepted"] += 1
        for history_index, history in enumerate(_walk_histories(payload)):
            history_hash = json.dumps(
                history,
                ensure_ascii=True,
                sort_keys=True,
                separators=(",", ":"),
            )
            if history_hash in seen_history_hashes:
                continue
            seen_history_hashes.add(history_hash)
            context_id = _history_context_id(
                path, history, history_index=history_index
            )
            cumulative_pricing_sec = 0.0
            first_addable = None
            trajectory = []
            best_rc = None
            bounds = []
            for row in history:
                pricing_sec = float(row.get("worker_wall_time") or 0.0) + float(
                    row.get("final_judge_wall_time") or 0.0
                )
                cumulative_pricing_sec += pricing_sec
                addable_count = int(row.get("addable_negative_count") or 0)
                if addable_count > 0 and first_addable is None:
                    first_addable = cumulative_pricing_sec
                value = row.get("harvest_best_true_rc")
                if value is not None:
                    best_rc = (
                        float(value)
                        if best_rc is None
                        else min(best_rc, float(value))
                    )
                    trajectory.append(
                        {
                            "pricing_budget_sec": cumulative_pricing_sec,
                            "best_true_rc": best_rc,
                        }
                    )
                duplicate_negative_count += int(
                    row.get("harvest_rejected_duplicate_count") or 0
                )
                candidate_negative_count += int(
                    row.get("harvest_candidate_negative_count") or 0
                )
                if row.get("node_lp_bound") is not None:
                    bounds.append(float(row["node_lp_bound"]))
            if first_addable is not None:
                first_addable_seconds.append(first_addable)
                first_addable_by_context.append(
                    {
                        "context_id": context_id,
                        "pricing_sec": first_addable,
                    }
                )
            if trajectory:
                best_rc_trajectories.append(
                    {
                        "context_id": context_id,
                        "points": trajectory,
                    }
                )
            if len(bounds) >= 2 and cumulative_pricing_sec > 0.0:
                bound_gain += max(0.0, bounds[-1] - bounds[0])
                pricing_sec_for_bound += cumulative_pricing_sec
    lifecycle_totals = {
        field: sum(float(event.get(field) or 0.0) for event in lifecycle_events.values())
        for field in (
            "guidance_import_sec",
            "guidance_checkpoint_load_sec",
            "guidance_tensorize_sec",
            "guidance_forward_total_sec",
            "guidance_binding_validation_sec",
            "guidance_native_install_sec",
            "guidance_total_wall_sec",
        )
    }
    lifecycle_totals["guidance_call_count"] = sum(
        int(event.get("guidance_call_count") or 0)
        for event in lifecycle_events.values()
    )
    return {
        **lifecycle_totals,
        "guidance_total_wall_ratio": (
            None
            if float(cold_start_total_sec) <= 0.0
            else lifecycle_totals["guidance_total_wall_sec"]
            / float(cold_start_total_sec)
        ),
        "guidance_lifecycle_event_count": len(lifecycle_events),
        "first_addable_negative_pricing_sec": first_addable_seconds,
        "first_addable_negative_by_context": first_addable_by_context,
        "equal_budget_best_rc_trajectories": best_rc_trajectories,
        "duplicate_negative_count": duplicate_negative_count,
        "candidate_negative_count": candidate_negative_count,
        "duplicate_negative_rate": (
            0.0
            if candidate_negative_count <= 0
            else duplicate_negative_count / candidate_negative_count
        ),
        "rmp_bound_gain_per_pricing_second": (
            None
            if pricing_sec_for_bound <= 0.0
            else bound_gain / pricing_sec_for_bound
        ),
        "global_ub": global_ub,
        "stage_b_safety": safety,
    }


def _history_context_id(
    path: Path, history: list[dict], *, history_index: int
) -> str:
    first = history[0] if history else {}
    node_id = str(first.get("node_id") or "unknown-node")
    return (
        f"{path.name}:{node_id}:"
        f"{int(history_index)}"
    )


def _walk_dictionaries(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_dictionaries(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_dictionaries(child)


def _walk_histories(value):
    if isinstance(value, dict):
        history = value.get("history")
        if isinstance(history, list) and all(
            isinstance(row, dict) for row in history
        ):
            yield history
        for child in value.values():
            yield from _walk_histories(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_histories(child)


def _collect_lifecycle_event(
    row: dict, events: dict[tuple, dict]
) -> None:
    lifecycle_fields = (
        "guidance_import_sec",
        "guidance_checkpoint_load_sec",
        "guidance_tensorize_sec",
        "guidance_forward_total_sec",
        "guidance_call_count",
        "guidance_binding_validation_sec",
        "guidance_native_install_sec",
        "guidance_total_wall_sec",
    )
    if "guidance_total_wall_sec" in row:
        request_bindings = dict(row.get("request_bindings") or {})
        binding_hash = str(
            row.get("guidance_binding_hash")
            or request_bindings.get("canonical_solve_binding_v2_hash")
            or ""
        )
        if binding_hash:
            event = {field: row.get(field) for field in lifecycle_fields}
            key = (
                binding_hash,
                str(row.get("guidance_effective_mode") or ""),
                tuple(event.get(field) for field in lifecycle_fields),
            )
            events[key] = event
    lifecycle = row.get("guidance_lifecycle")
    diagnostics = row.get("guidance_diagnostics")
    if isinstance(lifecycle, dict) and isinstance(diagnostics, dict):
        binding_hash = str(diagnostics.get("binding_hash") or "")
        if binding_hash:
            event = {
                field: lifecycle.get(field) for field in lifecycle_fields
            }
            key = (
                binding_hash,
                str(row.get("guidance_mode") or "harvest"),
                tuple(event.get(field) for field in lifecycle_fields),
            )
            events[key] = event


def _monitor_process_tree_rss(
    process_id: int,
    stop: threading.Event,
    samples: list[int],
) -> None:
    if psutil is None:
        return
    try:
        process = psutil.Process(int(process_id))
    except psutil.Error:
        return
    while not stop.is_set():
        total = 0
        try:
            processes = [process, *process.children(recursive=True)]
        except psutil.Error:
            processes = [process]
        for child in processes:
            try:
                total += int(child.memory_info().rss)
            except psutil.Error:
                continue
        samples.append(total)
        stop.wait(0.25)


def _quantile_int(values: list[int], probability: float) -> int:
    if not values:
        return 0
    ordered = sorted(int(value) for value in values)
    index = round((len(ordered) - 1) * float(probability))
    return ordered[max(0, min(len(ordered) - 1, index))]


def _directory_size_bytes(root: Path) -> int:
    total = 0
    for path in root.rglob("*"):
        try:
            if path.is_file():
                total += path.stat().st_size
        except OSError:
            continue
    return total


if __name__ == "__main__":
    raise SystemExit(main())
