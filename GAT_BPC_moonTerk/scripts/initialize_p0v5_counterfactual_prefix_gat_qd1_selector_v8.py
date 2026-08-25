#!/usr/bin/env python3
"""Freeze V8 bootstrap and the outcome-free representation schedule."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.guidance.counterfactual_prefix_gat_qd1_v8 import (  # noqa: E402
    CHECKPOINT_SCHEMA_V1,
    CONTEXT_FEATURE_NAMES,
    COUNTER_DELTA_NAMES,
    DATASET_SCHEMA_V1,
    EDGE_FEATURE_NAMES,
    FEATURE_SCHEMA_V1,
    LABEL_FEATURE_NAMES,
    LABEL_GRAPH_SCHEMA_V1,
    MODEL_SEEDS,
    NODE_FEATURE_NAMES,
    PORTABLE_BUNDLE_SCHEMA_V1,
    PREFIX_BOUNDARY,
    PREFIX_PROBE_SCHEMA_V1,
    ROLLOUT_CHECKPOINTS,
    RUNTIME_POLICY_V8,
)
from scripts.p0v5_counterfactual_prefix_gat_qd1_v8_common import (  # noqa: E402
    CONFIG,
    DEFAULT_RUN_ROOT,
    V7R3_ROOT,
    load,
    sha256,
    stable_hash,
    verify_v7r3_import,
    write_once,
)


SOURCE_PATHS = (
    "native/lunar_spprc/include/lunar_spprc/native_pricer.hpp",
    "native/lunar_spprc/src/native_pricer.cpp",
    "native/lunar_spprc/src/pybind_module.cpp",
    "native/lunar_spprc/tests/test_native_pricer.cpp",
    "src/lunar_ice_bpc/exact/bpc/pricing/backends/base.py",
    "src/lunar_ice_bpc/exact/bpc/pricing/backends/native_rcspp.py",
    "src/lunar_ice_bpc/guidance/counterfactual_prefix_gat_qd1_v8.py",
    "src/lunar_ice_bpc/guidance/counterfactual_prefix_gat_qd1_runtime_v8.py",
    "scripts/replay_p0v5_qg2_label_state_snapshot.py",
    "scripts/audit_p0v5_counterfactual_native_differential_v8.py",
    "scripts/p0v5_counterfactual_prefix_gat_qd1_v8_common.py",
    "scripts/initialize_p0v5_counterfactual_prefix_gat_qd1_selector_v8.py",
    "scripts/run_p0v5_counterfactual_representation_v8.py",
    "scripts/train_p0v5_counterfactual_representation_v8.py",
    "tests/test_p0v5_counterfactual_prefix_gat_qd1_selector_v8.py",
    "plan/GAT/P0V5_COUNTERFACTUAL_PREFIX_INTERACTION_GAT_QD1_SELECTOR_V8_IMPLEMENTATION_20260818_ZH.md",
    "plan/GAT/P0V5_COUNTERFACTUAL_PREFIX_INTERACTION_GAT_QD1_SELECTOR_V8_RUNBOOK_20260818_ZH.md",
    "plan/GAT/P0V5_COUNTERFACTUAL_PREFIX_V8R1_EVIDENCE_REPAIR_20260818_ZH.md",
)


def _snapshot_hash(payload: dict) -> str:
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode()).hexdigest()


def _engine_bindings(build_dir: Path) -> dict:
    code = """
import json
import lunar_spprc_native
from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import spprc_engine_build_hash
from lunar_ice_bpc.exact.bpc.pricing.backends.native_rcspp import NATIVE_INPROCESS_BACKEND_ID,NATIVE_HOST_BACKEND_ID
from lunar_ice_bpc.exact.bpc.pricing.backends.native_bidirectional_hybrid import NATIVE_BIDIRECTIONAL_ROOT_PARTIAL_HYBRID_BACKEND_ID
print(json.dumps({
 'inprocess': spprc_engine_build_hash(NATIVE_INPROCESS_BACKEND_ID),
 'host': spprc_engine_build_hash(NATIVE_HOST_BACKEND_ID),
 'root_partial_hybrid': spprc_engine_build_hash(NATIVE_BIDIRECTIONAL_ROOT_PARTIAL_HYBRID_BACKEND_ID),
 'build_info': dict(lunar_spprc_native.build_info()),
 'module_path': lunar_spprc_native.__file__,
}, sort_keys=True))
"""
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join((str(build_dir), str(ROOT / "src")))
    output = subprocess.run(
        [sys.executable, "-c", code], cwd=ROOT, env=environment,
        check=True, text=True, stdout=subprocess.PIPE,
    ).stdout
    return json.loads(output)


def _qpf0_reference_walls() -> dict[str, float]:
    path = (
        ROOT / "runs/p0v5_frontier_observability_root_cause_v7r2_20260818"
        / "switch_matrix.rows.json"
    )
    payload = load(path)
    grouped: dict[str, list[float]] = defaultdict(list)
    for row in payload["rows"]:
        if row["arm"] != "QPF0":
            continue
        wall = float(row["wall_seconds"])
        if row["status"] != "COMPLETE":
            wall = max(wall, float(row["cap_seconds"]))
        grouped[str(row["context_id"])].append(wall)
    if len(grouped) != 38 or any(len(rows) != 3 for rows in grouped.values()):
        raise SystemExit("V8 V7R2 QPF0 reference count drift")
    return {context: statistics.median(rows) for context, rows in grouped.items()}


def _rebind_rows(rows: list[dict], run_root: Path, engine_hash: str) -> list[dict]:
    output = []
    for raw in rows:
        source_path = Path(str(raw["snapshot_path"]))
        if not source_path.is_file() or sha256(source_path) != raw["snapshot_sha256"]:
            raise SystemExit("V8 V7R3 preaction snapshot drift")
        snapshot = load(source_path)
        rebound = dict(snapshot)
        original_state_hash = str(rebound["state_hash"])
        rebound["engine_hash"] = str(engine_hash)
        rebound.pop("state_hash", None)
        rebound["state_hash"] = _snapshot_hash(rebound)
        target = (
            run_root / "rebound_preaction_snapshots"
            / f"scale{int(raw['scale'])}" / str(raw["instance_content_hash"])
            / f"{rebound['state_hash']}.json"
        )
        write_once(target, rebound)
        row = dict(raw)
        row.update({
            "original_snapshot_path": str(source_path.resolve()),
            "original_snapshot_sha256": sha256(source_path),
            "original_state_hash": original_state_hash,
            "snapshot_path": str(target.resolve()),
            "snapshot_sha256": sha256(target),
            "state_hash": rebound["state_hash"],
            "rebound_engine_hash": str(engine_hash),
            "rebound_before_v8_prefix_outcomes": True,
            "rebound_changes_only_engine_and_state_hash": True,
        })
        output.append(row)
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args()
    config_path = args.config.resolve()
    config = load(config_path)
    if config.get("schema_version") != "lunar_ice_bpc.p0v5_counterfactual_prefix_gat_qd1_config.v8":
        raise SystemExit("V8 config schema mismatch")
    run_root = args.run_root.resolve()
    if run_root.exists() and any(run_root.iterdir()):
        raise SystemExit("immutable V8 run root is not empty")
    missing = [path for path in SOURCE_PATHS if not (ROOT / path).is_file()]
    if missing:
        raise SystemExit("V8 bootstrap source missing:" + ",".join(missing))
    imported = verify_v7r3_import()
    build_dir = (ROOT / config["native_build_dir"]).resolve()
    binary = (ROOT / config["native_binary"]).resolve()
    exact_config = (ROOT / config["selected_exact_config"]).resolve()
    if not binary.is_file() or not exact_config.is_file():
        raise SystemExit("V8 Native binary/exact config missing")
    ctest = subprocess.run(
        ["ctest", "--test-dir", str(build_dir), "--output-on-failure"],
        cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    if ctest.returncode:
        raise SystemExit("V8_COUNTERFACTUAL_NATIVE_REDLINE:\n" + ctest.stdout)
    python_environment = dict(os.environ)
    python_environment["PYTHONPATH"] = os.pathsep.join((
        str(build_dir), str(ROOT / "src"),
    ))
    python_validation = subprocess.run(
        [
            sys.executable, "-m", "pytest", "-q",
            "tests/test_p0v5_counterfactual_prefix_gat_qd1_selector_v8.py",
        ],
        cwd=ROOT, env=python_environment, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    if python_validation.returncode:
        raise SystemExit(
            "V8_COUNTERFACTUAL_NATIVE_REDLINE:\n" + python_validation.stdout
        )
    bindings = _engine_bindings(build_dir)
    build_info = dict(bindings["build_info"])
    if (
        build_info.get("counterfactual_prefix_policy")
        not in {
            "q0_4096_then_q0_or_qd1_rollout_128_512_2048_v1",
            "q0_4096_then_selected_q0_or_qd1_rollout_v8r1",
        }
        or build_info.get("counterfactual_public_routes") != "forbidden"
        or build_info.get("counterfactual_certificate") != "forbidden"
        or int(build_info.get("label_state_bytes", -1)) != 176
    ):
        raise SystemExit("V8_COUNTERFACTUAL_NATIVE_REDLINE:capability")

    run_root.mkdir(parents=True, exist_ok=True)
    baseline_build = (ROOT / str(
        config.get("baseline_native_build_dir")
        or "build/native-spprc-frontier-gat-v7"
    )).resolve()
    cross_binary_path = run_root / "cross_binary_native_differential.report.json"
    differential_process = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/audit_p0v5_counterfactual_native_differential_v8.py"),
            "--cases", "500", "--old-build", str(baseline_build),
            "--new-build", str(build_dir), "--output", str(cross_binary_path),
        ],
        cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    if differential_process.returncode:
        raise SystemExit(
            "V8_COUNTERFACTUAL_NATIVE_REDLINE:\n" + differential_process.stdout
        )
    cross_binary_differential = load(cross_binary_path)
    if (
        cross_binary_differential.get("decision") != "PASS"
        or int(cross_binary_differential.get("case_count") or 0) != 500
    ):
        raise SystemExit("V8_COUNTERFACTUAL_NATIVE_REDLINE:cross_binary")
    rows = _rebind_rows(
        list(imported["rows"]), run_root, str(bindings["root_partial_hybrid"])
    )
    counts = {
        str(scale): {
            "contexts": sum(int(row["scale"]) == scale for row in rows),
            "instances": len({row["instance_content_hash"] for row in rows if int(row["scale"]) == scale}),
        } for scale in (30, 50)
    }
    if counts != {"30": {"contexts": 19, "instances": 15}, "50": {"contexts": 19, "instances": 16}}:
        raise SystemExit(f"V8 representation import count drift:{counts}")
    imported["rows"] = rows
    imported["counts"] = counts

    qpf0_walls = _qpf0_reference_walls()
    collapsed_source = load(V7R3_ROOT / "switch_matrix.collapsed.json")
    original_rows = {row["context_id"]: row for row in collapsed_source["rows"]}
    rebound_by_context = {row["context_id"]: row for row in rows}
    collapsed_rows = []
    for context_id, raw in sorted(original_rows.items()):
        if not bool(raw["determined"]) or raw["correctness_redlines"]:
            raise SystemExit("V8 V7R3 diagnostic label is undetermined/redline")
        rebound = rebound_by_context[context_id]
        collapsed_rows.append({
            "context_id": context_id,
            "instance_hash": str(raw["instance_hash"]),
            "state_hash": str(rebound["state_hash"]),
            "original_state_hash": str(raw["state_hash"]),
            "scale": int(raw["scale"]),
            "ratio": float(raw["ratio"]),
            "benefit": bool(raw["benefit"]),
            "positive_gain": float(raw["positive_gain"]),
            "adverse": bool(raw["adverse"]),
            "qpf0_median_wall_seconds": float(qpf0_walls[context_id]),
            "diagnostic_only": True,
            "performance_authority": False,
        })
    if len(collapsed_rows) != 38:
        raise SystemExit("V8 collapsed label count drift")

    tasks = []
    for row in sorted(rows, key=lambda item: (int(item["scale"]), item["context_id"])):
        for arm in ("Q0_PREFIX", "QD1_PREFIX"):
            tasks.append({
                "task_id": f"{row['context_id']}:{arm}",
                "context_id": row["context_id"], "scale": int(row["scale"]),
                "instance_hash": row["instance_content_hash"],
                "instance_path": row["instance_path"],
                "instance_sha256": row["instance_sha256"],
                "state_hash": row["state_hash"],
                "snapshot_path": row["snapshot_path"],
                "snapshot_sha256": row["snapshot_sha256"],
                "arm": arm, "cap_seconds": 300 if int(row["scale"]) == 30 else 600,
                "output_path": str((run_root / "representation_prefix_raw" / f"{row['context_id']}_{arm}.json").resolve()),
                "diagnostic_only": True, "performance_authority": False,
            })
    if len(tasks) != 76:
        raise SystemExit("V8 representation task count drift")

    source_freeze = {
        "schema_version": "lunar_ice_bpc.p0v5_counterfactual_prefix_source_freeze.v1",
        "git_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip(),
        "worktree_may_be_dirty": True,
        "source_sha256": {
            **{path: sha256(ROOT / path) for path in SOURCE_PATHS},
            str(config_path.relative_to(ROOT)): sha256(config_path),
        },
        "native_build_dir": str(build_dir), "native_binary": str(binary),
        "native_binary_sha256": sha256(binary),
        "selected_exact_config": str(exact_config),
        "selected_exact_config_sha256": sha256(exact_config),
        "engine_hashes": {key: bindings[key] for key in ("inprocess", "host", "root_partial_hybrid")},
        "build_info": build_info,
    }
    interface = {
        "schema_version": "lunar_ice_bpc.p0v5_counterfactual_prefix_interface.v1",
        "runtime_policy": RUNTIME_POLICY_V8, "triplet_schema": FEATURE_SCHEMA_V1,
        "label_graph_schema": LABEL_GRAPH_SCHEMA_V1, "probe_schema": PREFIX_PROBE_SCHEMA_V1,
        "bundle_schema": PORTABLE_BUNDLE_SCHEMA_V1, "checkpoint_schema": CHECKPOINT_SCHEMA_V1,
        "dataset_schema": DATASET_SCHEMA_V1, "processed_label_boundary": PREFIX_BOUNDARY,
        "rollout_checkpoints": list(ROLLOUT_CHECKPOINTS), "model_seeds": list(MODEL_SEEDS),
        "feature_names": {
            "label": list(LABEL_FEATURE_NAMES), "node": list(NODE_FEATURE_NAMES),
            "edge": list(EDGE_FEATURE_NAMES), "context": list(CONTEXT_FEATURE_NAMES),
            "counter": list(COUNTER_DELTA_NAMES),
        },
        "action_universe": ["CONTINUE_Q0", "SWITCH_QD1_AT_4096"],
        "forced_veto": ["QB1", "QGR1"], "state_modified": False,
        "python_or_torch_inside_pricing": False, "root_only_authority": True,
    }
    differential = {
        "schema_version": "lunar_ice_bpc.p0v5_counterfactual_native_differential.v1",
        "decision": "PASS", "case_count": 500,
        "ctest_stdout": ctest.stdout, "ctest_stdout_sha256": stable_hash(ctest.stdout),
        "state_size_bytes": 176,
        "cross_binary_report": "cross_binary_native_differential.report.json",
        "cross_binary_report_sha256": sha256(cross_binary_path),
        "python_validation_stdout": python_validation.stdout,
        "python_validation_stdout_sha256": stable_hash(python_validation.stdout),
        "checks": [
            "disabled_vs_v7_q0", "prefix_no_routes_or_certificate",
            "base_graph_hash_q0_qd1", "sample_determinism", "migration_integrity",
            "legal_routes", "minimum_rc", "rc_reconstruction", "certificate",
        ],
    }
    config_freeze = {
        **config, "source_config": str(config_path),
        "source_config_sha256": sha256(config_path),
        "frozen_before_v8_prefix_outcomes": True,
    }
    execution = {
        "schema_version": "lunar_ice_bpc.p0v5_counterfactual_representation_execution.v1",
        "tasks": tasks, "task_count": 76, "single_native_process": True,
        "rollout_checkpoints_collected_in_one_request": True,
        "performance_authority": False,
    }
    initial_state = {
        "schema_version": "lunar_ice_bpc.p0v5_counterfactual_prefix_state.v8",
        "current_stage": "REPRESENTATION_PREFIX", "status": "READY", "terminal": False,
        "development_only": True, "deployment_authorized": False,
        "production_switch_authorized": False,
    }
    artifacts = {
        "config.freeze.json": config_freeze,
        "source.freeze.json": source_freeze,
        "interface.freeze.json": interface,
        "native_differential.report.json": differential,
        "cross_binary_native_differential.report.json": cross_binary_differential,
        "v7r3_representation_import.freeze.json": imported,
        "v7r3_collapsed_labels.freeze.json": {
            "schema_version": "lunar_ice_bpc.p0v5_v7r3_collapsed_labels.v8",
            "rows": collapsed_rows, "diagnostic_only": True, "performance_authority": False,
        },
        "representation_execution.freeze.json": execution,
        "state.initial.json": initial_state,
    }
    repaired_root_value = str(config.get("evidence_repair_of") or "")
    if repaired_root_value:
        repaired_root = (ROOT / repaired_root_value).resolve()
        terminal_path = repaired_root / "terminal_decision.json"
        report_path = repaired_root / "representation_development.report.json"
        if not terminal_path.is_file() or not report_path.is_file():
            raise SystemExit("V8_REPAIR_SOURCE_DRIFT:missing")
        repaired_terminal = load(terminal_path)
        if (
            repaired_terminal.get("decision") != "FAIL"
            or repaired_terminal.get("reason")
            != "COUNTERFACTUAL_PREFIX_NOT_IDENTIFIABLE"
        ):
            raise SystemExit("V8_REPAIR_SOURCE_DRIFT:terminal")
        artifacts["v8_measurement_repair.freeze.json"] = {
            "schema_version": "lunar_ice_bpc.p0v5_counterfactual_prefix_measurement_repair.v1",
            "source_run_root": str(repaired_root),
            "source_remains_read_only": True,
            "source_terminal_sha256": sha256(terminal_path),
            "source_report_sha256": sha256(report_path),
            "source_terminal_performance_authority": False,
            "invalidated_measurement_claims": list(
                config.get("invalidated_measurement_claims") or ()
            ),
            "repair_contract": {
                "warm_wall_source": "native_per_checkpoint_request_elapsed_wall_seconds",
                "selected_budget_stops_native_request": True,
                "fresh_exact_request_after_probes": True,
                "static_preaction_context_bound_into_graph": True
            }
        }
    for name, payload in artifacts.items():
        write_once(run_root / name, payload)
    registry_names = tuple(artifacts)
    write_once(run_root / "bootstrap.freeze.registry.json", {
        "schema_version": "lunar_ice_bpc.p0v5_counterfactual_prefix_bootstrap_freeze.v1",
        "frozen_before_any_v8_prefix_wall": True,
        "artifact_sha256": {name: sha256(run_root / name) for name in registry_names},
    })
    write_once(run_root / "state.json", initial_state)
    print(json.dumps({
        "status": "READY", "stage": "REPRESENTATION_PREFIX", "tasks": 76,
        "run_root": str(run_root), "engine_hash": bindings["root_partial_hybrid"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
