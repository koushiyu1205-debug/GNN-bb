#!/usr/bin/env python3
"""Run the formal P0V4+V5 Temporal-GAT contract against production no_cut."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from math import ceil, exp, log
import os
from pathlib import Path
import sys
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import scripts.run_p0v4_final_acceptance as contract  # noqa: E402
from scripts.analyze_p0v5_qg2_paired_acceptance import _rows  # noqa: E402
from scripts.p0v5_temporal_gat_common import (  # noqa: E402
    load_frozen_config, mark_terminal_negative, write_once,
)
from scripts.run_p0v5_temporal_gat_full_bpc_v1 import (  # noqa: E402
    _environment, _mem_available_gb, _run_process_with_rss,
    _temporal_telemetry,
)
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402


def _load(path: Path) -> dict[str, Any]:
    return dict(json.loads(path.read_text(encoding="utf-8")))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _gm(values):
    rows = [float(value) for value in values]
    if not rows or any(value <= 0.0 for value in rows):
        return None
    return exp(sum(log(value) for value in rows) / len(rows))


def _instances(experiment):
    rows = []
    for scale in (5, 10, 20, 30, 50):
        directory = ROOT / "data/instances" / f"lunar_ice_sp50_{scale:03d}"
        paths = sorted(directory.glob("instance_*_logical_graph.json"))[:20]
        if len(paths) != 20:
            raise SystemExit(f"formal scale{scale} instance count is not 20")
        for index, path in enumerate(paths, start=1):
            data = load_lunar_ice_data(_load(path))
            rows.append({
                "scale": scale, "instance_index": index,
                "instance_key": f"instance_{index:03d}",
                "instance_hash": data.instance_content_hash,
                "instance_path": str(path.resolve()),
                "instance_file_sha256": _sha(path),
                "diagnostic_only": False,
            })
    diagnostic = dict(experiment["scale100_diagnostic"])
    directory = (ROOT / diagnostic["instance_dir"]).resolve()
    for index in range(
        int(diagnostic["first_index"]), int(diagnostic["last_index"]) + 1
    ):
        path = directory / f"instance_{index:03d}_logical_graph.json"
        data = load_lunar_ice_data(_load(path))
        rows.append({
            "scale": 100, "instance_index": index,
            "instance_key": f"instance_{index:03d}",
            "instance_hash": data.instance_content_hash,
            "instance_path": str(path.resolve()),
            "instance_file_sha256": _sha(path),
            "diagnostic_only": True,
        })
    return rows


def _schedule(experiment, manifest, rows):
    tasks = []
    for row in rows:
        for arm in sorted(("Q0", "MODEL"), key=lambda value: hashlib.sha256(
            f"formal:{row['instance_hash']}:{value}".encode()
        ).hexdigest()):
            identity = f"formal:{row['instance_hash']}:{arm}"
            tasks.append({
                **row, "arm": arm,
                "task_id": hashlib.sha256(identity.encode()).hexdigest()[:24],
                "fresh_process": True,
            })
    return {
        "schema_version": (
            "lunar_ice_bpc.p0v5_temporal_gat_formal_execution.v1"
        ),
        "status": "FROZEN_BEFORE_FORMAL_OUTCOMES",
        "contract": str(experiment["_path"]),
        "contract_sha256": _sha(Path(experiment["_path"])),
        "runtime_manifest": str(manifest.resolve()),
        "runtime_manifest_sha256": _sha(manifest),
        "single_host_instance": True, "fresh_process_per_task": True,
        "task_count": len(tasks), "tasks": tasks,
    }


def _run_one(task, output, config, manifest):
    if output.exists():
        raise SystemExit(f"partial formal task requires audit:{output}")
    instance_path = Path(str(task["instance_path"]))
    if (
        not instance_path.is_file()
        or _sha(instance_path) != str(task["instance_file_sha256"])
    ):
        raise SystemExit("formal frozen instance file hash drift")
    command = [
        sys.executable,
        str(ROOT / "scripts/run_lunar_ice_native_spprc_acceptance.py"),
        "--config", str((ROOT / config["selected_exact_config"]).resolve()),
        "--scales", str(task["scale"]),
        "--instance", str(task["instance_path"]),
        "--limit", "1", "--output-dir", str(output), "--no-resume",
        "--effective-memory-cap-gb", str(
            config["execution"]["effective_native_memory_limit_gb"]
        ),
    ]
    returncode = _run_process_with_rss(
        command,
        environment=_environment(
            config, manifest if task["arm"] == "MODEL" else None
        ),
        telemetry_path=output / "process_resource_telemetry.json",
    )
    if returncode not in {0, 1}:
        raise SystemExit(f"formal task execution error:{task['task_id']}")


def _state_row(task, parsed, telemetry):
    exact = bool(parsed["exact"])
    redlines = [] if parsed["redlines_zero"] else ["solver_redline"]
    if int(task["scale"]) not in {30, 50} and (
        telemetry["runtime_calls"] or telemetry["selected_action_counts"]
    ):
        redlines.append("temporal_runtime_outside_authorized_scale")
    if int(telemetry.get("tree_model_calls") or 0):
        redlines.append("temporal_model_called_outside_root_cg")
    return {
        "task_id": task["task_id"], "arm": task["arm"],
        "scale": int(task["scale"]),
        "instance_index": int(task["instance_index"]),
        "instance_key": task["instance_key"],
        "instance_hash": task["instance_hash"],
        "diagnostic_only": bool(task["diagnostic_only"]),
        "algorithm_status": "BPC_OPTIMAL" if exact else str(
            parsed["algorithm_status"]
        ),
        "exact_certificate": exact, "bpc_tree_optimal": exact,
        "no_cheat_pass": not redlines,
        "certificate_leak": 0, "manual_rc_fail": 0,
        "pricing_rc_fail": 0, "tail_dual_certificate_leak": 0,
        "worker_certificate_leak": 0,
        "true_dual_rc_recompute_missing": 0,
        "cold_start_total_sec": float(parsed["wall_sec"]),
        "objective": parsed["objective"],
        "correctness_redlines": redlines,
        "selected_action_counts": telemetry["selected_action_counts"],
        "runtime_calls": telemetry["runtime_calls"],
        "tree_model_calls": telemetry["tree_model_calls"],
        "inference_ms_values": telemetry["inference_ms_values"],
        "fail_closed_reasons": telemetry["fail_closed_reasons"],
        "peak_rss_gb": telemetry["peak_rss_gb"],
        "tree_result": parsed.get("tree_result") or "",
    }


def _parse_one(root, task):
    values = _rows(root)
    if set(values) != {task["instance_hash"]}:
        raise SystemExit("formal acceptance output instance mismatch")
    parsed = dict(values[task["instance_hash"]])
    tree = _load(Path(parsed["tree_result"])) if parsed.get("tree_result") else {}
    telemetry = _temporal_telemetry(tree)
    resource_path = root / "process_resource_telemetry.json"
    resource = _load(resource_path) if resource_path.is_file() else {}
    process_peak_rss_gb = float(
        resource.get("process_tree_peak_rss_bytes") or 0
    ) / float(1024 ** 3)
    telemetry["peak_rss_gb"] = max(
        float(telemetry.get("peak_rss_gb") or 0.0),
        process_peak_rss_gb,
    )
    row = _state_row(task, parsed, telemetry)
    row.update({
        "process_tree_peak_rss_gb": process_peak_rss_gb,
        "process_tree_rss_sample_count": int(
            resource.get("sample_count") or 0
        ),
        "process_resource_telemetry": str(resource_path),
        "process_resource_telemetry_sha256": (
            _sha(resource_path) if resource_path.is_file() else ""
        ),
    })
    ledger = dict(tree.get("certificate_ledger") or {})
    semantics = {
        "algorithm_status": str(tree.get("algorithm_status") or ""),
        "exact_status": str(tree.get("exact_status") or ""),
        "certificate_scope": str(tree.get("certificate_scope") or ""),
        "all_certificate_ledgers_valid": bool(
            tree.get("all_certificate_ledgers_valid")
        ),
        "certificate_ledger_status": str(
            ledger.get("certificate_status") or ""
        ),
        "certificate_ledger_scope": str(
            ledger.get("certificate_scope") or ""
        ),
        "uses_true_dual_bpc_certificate": bool(
            ledger.get("uses_true_dual_bpc_certificate")
        ),
    }
    row["certificate_semantics_signature"] = hashlib.sha256(json.dumps(
        semantics, sort_keys=True, separators=(",", ":")
    ).encode()).hexdigest()
    row["certificate_semantics"] = semantics
    return row


def _incremental(q0, model, gates):
    by_q0 = {(row["scale"], row["instance_key"]): row for row in q0}
    ratios = defaultdict(list)
    objective_mismatches = []
    certificate_semantics_mismatches = []
    for row in model:
        peer = by_q0[(row["scale"], row["instance_key"])]
        if contract._is_exact(row) and contract._is_exact(peer):
            ratios[int(row["scale"])].append(
                float(row["cold_start_total_sec"])
                / float(peer["cold_start_total_sec"])
            )
            if (
                row.get("objective") is not None
                and peer.get("objective") is not None
                and abs(float(row["objective"]) - float(peer["objective"]))
                > 2.0e-6
            ):
                objective_mismatches.append(
                    f"scale{row['scale']}:{row['instance_key']}"
                )
            if str(row.get("certificate_semantics_signature") or "") != str(
                peer.get("certificate_semantics_signature") or ""
            ):
                certificate_semantics_mismatches.append(
                    f"scale{row['scale']}:{row['instance_key']}"
                )
    model_50 = [row for row in model if int(row["scale"]) == 50]
    q0_50 = [row for row in q0 if int(row["scale"]) == 50]
    extra = sum(
        contract._is_exact(row) and not contract._is_exact(
            by_q0[(50, row["instance_key"])]
        ) for row in model_50
    )
    lost = sum(
        contract._is_exact(row) and not contract._is_exact(
            next(value for value in model_50
                 if value["instance_key"] == row["instance_key"])
        ) for row in q0_50
    )
    q0_exact_count = sum(contract._is_exact(row) for row in q0_50)
    model_exact_count = sum(contract._is_exact(row) for row in model_50)
    inference = sorted(
        float(value) for row in model
        for value in row.get("inference_ms_values") or ()
    )
    p99 = (
        inference[min(len(inference) - 1, max(0, ceil(.99 * len(inference)) - 1))]
        if inference else None
    )
    issues = []
    if extra < int(gates["gat_scale50_extra_closure_min"]):
        issues.append("gat_scale50_extra_closure_gate_failed")
    if model_exact_count - q0_exact_count < int(
        gates["gat_scale50_extra_closure_min"]
    ):
        issues.append("gat_scale50_net_closure_gate_failed")
    if lost:
        issues.append("gat_scale50_lost_q0_closure")
    if p99 is None or p99 > float(gates["inference_p99_ms_max"]):
        issues.append("formal_inference_p99_gate_failed")
    if objective_mismatches:
        issues.append("gat_exact_objective_mismatch")
    if certificate_semantics_mismatches:
        issues.append("gat_certificate_semantics_mismatch")
    for scale in (30, 50):
        ratio = _gm(ratios.get(scale, ()))
        if ratio is None or ratio > 1.0 - float(
            gates["gat_common_exact_speedup_min"]
        ):
            issues.append(f"gat_scale{scale}_speedup_gate_failed")
    if any(row["correctness_redlines"] for row in model):
        issues.append("gat_correctness_redline")
    return {
        "pass": not issues, "issues": issues,
        "paired_geometric_mean_ratio_by_scale": {
            str(scale): _gm(values) for scale, values in sorted(ratios.items())
        },
        "commonly_exact_count_by_scale": {
            str(scale): len(values) for scale, values in sorted(ratios.items())
        },
        "q0_scale50_exact_count": q0_exact_count,
        "model_scale50_exact_count": model_exact_count,
        "scale50_extra_exact_closure_count": extra,
        "scale50_lost_q0_closure_count": lost,
        "scale50_net_exact_closure_delta": model_exact_count - q0_exact_count,
        "inference_p99_ms": p99,
        "objective_mismatches": objective_mismatches,
        "certificate_semantics_mismatches": (
            certificate_semantics_mismatches
        ),
    }


def _audit(experiment, rows):
    official = [row for row in rows if not row["diagnostic_only"]]
    diagnostic = [row for row in rows if row["diagnostic_only"]]
    q0 = [row for row in official if row["arm"] == "Q0"]
    model = [row for row in official if row["arm"] == "MODEL"]
    baseline, baseline_audit = contract._baseline_rows(experiment)
    complete_candidate = contract._candidate_metrics(model, baseline)
    complete_gate = contract._exact_gate(
        complete_candidate, experiment["gates"]
    )
    q0_candidate = contract._candidate_metrics(q0, baseline)
    q0_gate = contract._exact_gate(q0_candidate, experiment["gates"])
    incremental = _incremental(q0, model, experiment["gates"])
    diagnostic_issues = []
    memory_issues = [
        f"scale{row['scale']}:{row['arm']}:{row['instance_key']}"
        for row in rows
        if float(row.get("peak_rss_gb") or 0.0) > float(
            experiment["execution"]["effective_native_memory_limit_gb"]
        )
    ]
    memory_telemetry_missing = [
        f"scale{row['scale']}:{row['arm']}:{row['instance_key']}"
        for row in rows if float(row.get("peak_rss_gb") or 0.0) <= 0.0
    ]
    for arm in ("Q0", "MODEL"):
        selected = [row for row in diagnostic if row["arm"] == arm]
        if len(selected) != 5:
            diagnostic_issues.append(f"scale100_{arm}_row_count")
        if any(row["correctness_redlines"] for row in selected):
            diagnostic_issues.append(f"scale100_{arm}_correctness_redline")
        if arm == "MODEL" and any(
            row["runtime_calls"] or row["selected_action_counts"]
            for row in selected
        ):
            diagnostic_issues.append("scale100_temporal_runtime_call")
    expected = 210
    evidence_available = bool(
        len(rows) == expected and baseline_audit["pass"]
        and not any(row["correctness_redlines"] for row in rows)
        and not diagnostic_issues and not memory_issues
        and not memory_telemetry_missing
    )
    passed = bool(
        evidence_available and complete_gate["pass"]
        and q0_gate["pass"] and incremental["pass"]
    )
    return {
        "schema_version": (
            "lunar_ice_bpc.p0v5_temporal_gat_formal_acceptance.v1"
        ),
        "all_required_evidence_available": evidence_available,
        "final_candidate_gate_pass": passed,
        "complete_candidate_vs_production_no_cut": complete_candidate,
        "complete_candidate_gate": complete_gate,
        "p0v4_v5_q0_vs_production_no_cut": q0_candidate,
        "p0v4_v5_q0_gate": q0_gate,
        "temporal_gat_increment_vs_literal_q0": incremental,
        "baseline_evidence_audit": baseline_audit,
        "scale100_is_diagnostic_only": True,
        "scale100_diagnostic_issues": diagnostic_issues,
        "dynamic_memory_cap_issues": memory_issues,
        "memory_telemetry_missing": memory_telemetry_missing,
        "production_default_changed": False,
        "deployment_authorized": False,
        "production_switch_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--task-limit", type=int)
    args = parser.parse_args()
    try:
        config, config_freeze = load_frozen_config(
            args.config, run_root=args.run_root
        )
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    run_root = args.run_root.resolve()
    source_path = run_root / "source.freeze.json"
    sealed_audit_path = run_root / "full_bpc/sealed_final/audit.json"
    sealed_outcomes_path = run_root / "full_bpc/sealed_final/outcomes.json"
    if not all(path.is_file() for path in (
        source_path, sealed_audit_path, sealed_outcomes_path,
    )):
        raise SystemExit("formal acceptance requires sealed-final PASS evidence")
    source = _load(source_path)
    sealed_audit = _load(sealed_audit_path)
    expected_contract = (ROOT / config["formal_acceptance_contract"]).resolve()
    if (
        sealed_audit.get("decision") != "PASS"
        or sealed_audit.get("source_outcomes_sha256")
            != _sha(sealed_outcomes_path)
        or args.contract.resolve() != expected_contract
        or Path(str(source.get("formal_acceptance_contract") or "")).resolve()
            != expected_contract
        or source.get("formal_acceptance_contract_sha256")
            != _sha(expected_contract)
    ):
        raise SystemExit("formal/sealed/contract immutable binding drift")
    experiment = dict(yaml.safe_load(
        args.contract.resolve().read_text(encoding="utf-8")
    ))
    experiment["_path"] = str(args.contract.resolve())
    if float(experiment["execution"][
        "effective_native_memory_limit_gb"
    ]) != float(config["execution"]["effective_native_memory_limit_gb"]):
        raise SystemExit("formal/Temporal effective native cap mismatch")
    manifest = args.manifest.resolve()
    manifest_payload = _load(manifest)
    if not bool(manifest_payload.get("development_e2e_authorized")) or bool(
        manifest_payload.get("deployment_authorized")
    ):
        raise SystemExit("formal runtime manifest authority drift")
    training_report_path = (
        manifest.parent / str(manifest_payload.get("training_report_path") or "")
    ).resolve()
    bundle_path = (
        manifest.parent / str(manifest_payload.get("portable_bundle_path") or "")
    ).resolve()
    native_binary = Path(str(source.get("native_binary") or ""))
    if (
        not training_report_path.is_file()
        or manifest_payload.get("training_report_sha256")
            != _sha(training_report_path)
        or not bundle_path.is_file()
        or manifest_payload.get("portable_bundle_file_sha256") != _sha(bundle_path)
        or manifest_payload.get("selected_exact_config_sha256")
            != source.get("selected_exact_config_sha256")
        or manifest_payload.get("native_binary_sha256")
            != source.get("native_binary_sha256")
        or manifest_payload.get("source_freeze_sha256") != _sha(source_path)
        or manifest_payload.get("experiment_config_sha256")
            != _sha(config_freeze)
        or not native_binary.is_file()
        or _sha(native_binary) != source.get("native_binary_sha256")
    ):
        raise SystemExit("formal model/source/native binding drift")
    root = args.run_root.resolve() / "formal_acceptance"
    schedule_path = root / "execution.freeze.json"
    schedule = _schedule(experiment, manifest, _instances(experiment))
    schedule.update({
        "source_config_freeze_sha256": _sha(config_freeze),
        "source_freeze_sha256": _sha(source_path),
        "source_contract_sha256": _sha(expected_contract),
        "source_sealed_audit_sha256": _sha(sealed_audit_path),
        "source_sealed_outcomes_sha256": _sha(sealed_outcomes_path),
        "source_runtime_manifest_sha256": _sha(manifest),
        "source_training_report_sha256": _sha(training_report_path),
        "source_bundle_sha256": _sha(bundle_path),
        "native_binary_sha256": _sha(native_binary),
    })
    write_once(schedule_path, schedule)
    raw_root = root / "raw"
    launched = 0
    for task in schedule["tasks"]:
        task_root = raw_root / task["task_id"]
        row_path = task_root / "canonical_row.json"
        if row_path.is_file():
            continue
        if args.task_limit is not None and launched >= int(args.task_limit):
            break
        if _mem_available_gb() < float(
            config["execution"]["memavailable_reserve_gb"]
        ):
            raise SystemExit("MemAvailable reserve would be violated")
        _run_one(task, task_root, config, manifest)
        write_once(row_path, _parse_one(task_root, task))
        launched += 1
    missing = [
        task for task in schedule["tasks"]
        if not (raw_root / task["task_id"] / "canonical_row.json").is_file()
    ]
    if missing:
        print(json.dumps({"status": "PARTIAL", "remaining": len(missing)}))
        return 0
    rows = [
        _load(raw_root / task["task_id"] / "canonical_row.json")
        for task in schedule["tasks"]
    ]
    write_once(root / "rows.json", {
        "schema_version": "lunar_ice_bpc.p0v5_temporal_formal_rows.v1",
        "row_count": len(rows), "rows": rows,
        "execution_freeze": str(schedule_path),
        "execution_freeze_sha256": _sha(schedule_path),
    })
    audit = _audit(experiment, rows)
    audit.update({
        "runtime_manifest": str(manifest),
        "runtime_manifest_sha256": _sha(manifest),
        "execution_freeze": str(schedule_path),
        "execution_freeze_sha256": _sha(schedule_path),
        "formal_rows_sha256": _sha(root / "rows.json"),
    })
    write_once(root / "formal_acceptance.json", audit)
    if not audit["final_candidate_gate_pass"]:
        mark_terminal_negative(
            args.run_root, stage="FORMAL_ACCEPTANCE",
            reason="TEMPORAL_FORMAL_ACCEPTANCE_FAILED", detail=audit,
        )
        raise SystemExit("TEMPORAL_FORMAL_ACCEPTANCE_FAILED")
    print(json.dumps({
        "status": "PASS", "output": str(root / "formal_acceptance.json")
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
