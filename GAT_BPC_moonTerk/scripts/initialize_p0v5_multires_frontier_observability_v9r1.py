#!/usr/bin/env python3
"""Freeze the 64-cell plus 256-label multi-resolution diagnostic chain."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
import statistics
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.guidance.multires_frontier_gat_qd1_v9 import (  # noqa: E402
    CHECKPOINT_SCHEMA_V1,
    FEATURE_SCHEMA_V1,
    GRAPH_SCHEMA_V1,
    MODEL_KINDS,
    MODEL_SEEDS,
    RUNTIME_POLICY_V1,
    MultiResolutionExample,
    cell_graph_from_payload,
)
from scripts.p0v5_base_label_frontier_v9r0_common import (  # noqa: E402
    verify_freezes as verify_v9r0_freezes,
)
from scripts.p0v5_multires_frontier_v9r1_common import (  # noqa: E402
    CONFIG,
    DEFAULT_RUN_ROOT,
    load,
    sha256,
    verify_freezes,
    write_mutable,
    write_once,
)
from scripts.train_p0v5_multires_frontier_observability_v9r1 import (  # noqa: E402
    _example,
)


SOURCE_PATHS = (
    "configs/experiments/p0v5_multires_frontier_observability_v9r1.json",
    "plan/GAT/P0V5_MULTIRES_FRONTIER_OBSERVABILITY_V9R1_20260818_ZH.md",
    "scripts/initialize_p0v5_multires_frontier_observability_v9r1.py",
    "scripts/p0v5_multires_frontier_v9r1_common.py",
    "scripts/train_p0v5_multires_frontier_observability_v9r1.py",
    "src/lunar_ice_bpc/guidance/base_frontier_gat_qd1_v9.py",
    "src/lunar_ice_bpc/guidance/counterfactual_prefix_gat_qd1_v8.py",
    "src/lunar_ice_bpc/guidance/frontier_gat_qd1_v7.py",
    "src/lunar_ice_bpc/guidance/multires_frontier_gat_qd1_v9.py",
    "tests/test_p0v5_multires_frontier_observability_v9r1.py",
)


V9R0_REQUIRED = (
    "freeze.registry.json", "source.freeze.json", "evidence_import.freeze.json",
    "corpus.freeze.json", "folds.freeze.json", "observability.report.json",
    "runtime_cost_diagnostic.json", "terminal_decision.json",
)
V7R3_REQUIRED = (
    "source.freeze.json", "switch_matrix.collapsed.json",
    "switch_oracle.decision.json", "terminal_decision.json",
)
V7R2_REQUIRED = (
    "source.freeze.json", "switch_matrix.rows.json",
    "switch_matrix.execution.freeze.json", "switch_oracle.decision.json",
)


def _join_corpus(v9r0_root: Path, v7r3_root: Path, v7r2_root: Path):
    label_rows = list(load(v9r0_root / "corpus.freeze.json")["rows"])
    cell_rows = {
        str(row["context_id"]): row
        for row in load(v7r3_root / "switch_matrix.collapsed.json")["rows"]
    }
    timing_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in load(v7r2_root / "switch_matrix.rows.json")["rows"]:
        if str(row["arm"]) == "QPF0":
            timing_rows[str(row["context_id"])].append(row)
    context_ids = {str(row["context_id"]) for row in label_rows}
    if context_ids != set(cell_rows) or context_ids != set(timing_rows):
        raise SystemExit("multi-resolution context join drift")

    output = []
    for label_row in sorted(label_rows, key=lambda row: str(row["context_id"])):
        context_id = str(label_row["context_id"])
        cell_row = cell_rows[context_id]
        if (
            int(cell_row["scale"]) != int(label_row["scale"])
            or str(cell_row["instance_hash"]) != str(label_row["instance_hash"])
            or float(cell_row["ratio"]) != float(label_row["target"]["ratio"])
            or bool(cell_row["benefit"]) != bool(label_row["target"]["benefit"])
            or bool(cell_row["adverse"]) != bool(label_row["target"]["adverse"])
        ):
            raise SystemExit(f"multi-resolution target/binding drift:{context_id}")
        cell_payload = dict(cell_row.get("qpf0_graph") or {})
        cell_graph = cell_graph_from_payload(cell_payload)
        label_context = tuple(float(value) for value in label_row["graph"]["context_features"])
        if label_context != cell_graph.context_features:
            raise SystemExit(f"multi-resolution context feature drift:{context_id}")
        timing = timing_rows[context_id]
        if len(timing) != 3:
            raise SystemExit(f"cell graph repeat coverage drift:{context_id}")
        graph_hashes = {
            str(row["frontier_telemetry"].get("graph_hash") or "") for row in timing
        }
        if graph_hashes != {cell_graph.graph_hash}:
            raise SystemExit(f"cell graph hash nondeterminism:{context_id}")
        build_walls = [
            float(row["frontier_telemetry"].get("graph_build_wall_seconds") or 0.0)
            for row in timing
        ]
        if any(value <= 0.0 for value in build_walls):
            raise SystemExit(f"cell graph build timing missing:{context_id}")
        row = {
            "context_id": context_id,
            "instance_hash": str(label_row["instance_hash"]),
            "state_hash": str(label_row["state_hash"]),
            "source_cell_state_hash": str(cell_row["state_hash"]),
            "scale": int(label_row["scale"]),
            "label_graph": label_row["graph"],
            "cell_graph": cell_payload,
            "target": label_row["target"],
            "qpf0_reference_wall_seconds": float(label_row["qpf0_reference_wall_seconds"]),
            "label_graph_build_wall_seconds": float(label_row["base_graph_build_wall_seconds"]),
            "cell_graph_build_wall_seconds": statistics.median(build_walls),
            "cell_graph_build_repeat_walls": build_walls,
            "additional_label_pops": 0,
            "auxiliary_prefix_requests": 0,
            "diagnostic_only": True,
            "performance_authority": False,
        }
        example = _example(row)
        example.validate()
        output.append(row)
    if len(output) != 38 or len({row["instance_hash"] for row in output}) != 31:
        raise SystemExit("multi-resolution corpus count drift")
    return output


def initialize(config_path: Path, run_root: Path) -> None:
    config = load(config_path)
    v9r0_root = (ROOT / config["source_v9r0_run_root"]).resolve()
    v7r3_root = (ROOT / config["source_v7r3_run_root"]).resolve()
    v7r2_root = (ROOT / config["source_v7r2_run_root"]).resolve()
    verify_v9r0_freezes(v9r0_root)
    v9_terminal = load(v9r0_root / "terminal_decision.json")
    if (
        v9_terminal.get("decision") != "FAIL"
        or v9_terminal.get("reason") != "BASE_LABEL_FRONTIER_NOT_IDENTIFIABLE"
    ):
        raise SystemExit("V9R0 terminal contract drift")
    v7_terminal = load(v7r3_root / "terminal_decision.json")
    if (
        v7_terminal.get("decision") != "FAIL"
        or v7_terminal.get("reason") != "SCALE50_BENEFIT_HARM_NOT_SEPARABLE"
    ):
        raise SystemExit("V7R3 terminal contract drift")
    if load(v7r3_root / "switch_oracle.decision.json").get("decision") != "PASS":
        raise SystemExit("V7R3 switch oracle drift")
    for path in SOURCE_PATHS:
        if not (ROOT / path).is_file():
            raise SystemExit(f"missing V9R1 source:{path}")

    rows = _join_corpus(v9r0_root, v7r3_root, v7r2_root)
    source_artifacts = {
        "source_v9r0_root": {
            relative: sha256(v9r0_root / relative) for relative in V9R0_REQUIRED
        },
        "source_v7r3_root": {
            relative: sha256(v7r3_root / relative) for relative in V7R3_REQUIRED
        },
        "source_v7r2_root": {
            relative: sha256(v7r2_root / relative) for relative in V7R2_REQUIRED
        },
    }
    folds = load(v9r0_root / "folds.freeze.json")
    run_root.mkdir(parents=True, exist_ok=True)
    write_once(run_root / "config.freeze.json", config)
    write_once(run_root / "source.freeze.json", {
        "schema_version": "lunar_ice_bpc.p0v5_multires_frontier_source_freeze.v1",
        "source_sha256": {path: sha256(ROOT / path) for path in SOURCE_PATHS},
        "no_native_change": True, "worktree_may_be_dirty": True,
    })
    write_once(run_root / "evidence_import.freeze.json", {
        "schema_version": "lunar_ice_bpc.p0v5_multires_frontier_evidence_import.v1",
        "source_v9r0_root": str(v9r0_root),
        "source_v7r3_root": str(v7r3_root),
        "source_v7r2_root": str(v7r2_root),
        "source_artifacts": source_artifacts,
        "context_count": 38, "instance_count": 31,
        "cell_label_context_exact_match_count": 38,
        "new_arm_outcome_count": 0,
        "heldout_or_formal_outcome_count": 0,
        "diagnostic_only": True, "performance_authority": False,
    })
    write_once(run_root / "corpus.freeze.json", {
        "schema_version": "lunar_ice_bpc.p0v5_multires_frontier_corpus.v1",
        "rows": rows, "context_count": 38, "instance_count": 31,
        "additional_label_pops": 0, "auxiliary_prefix_requests": 0,
        "cell_graph_is_complete_frontier_mass": True,
        "label_graph_is_deterministic_sample": True,
        "outcome_exposure": "historical diagnostic only",
    })
    write_once(run_root / "folds.freeze.json", {
        **folds,
        "reused_without_change_from": str(v9r0_root / "folds.freeze.json"),
        "source_sha256": sha256(v9r0_root / "folds.freeze.json"),
    })
    write_once(run_root / "interface.freeze.json", {
        "schema_version": "lunar_ice_bpc.p0v5_multires_frontier_interface.v1",
        "feature_schema": FEATURE_SCHEMA_V1,
        "graph_schema": GRAPH_SCHEMA_V1,
        "checkpoint_schema": CHECKPOINT_SCHEMA_V1,
        "runtime_policy": RUNTIME_POLICY_V1,
        "model_kinds": list(MODEL_KINDS), "model_seeds": list(MODEL_SEEDS),
        "views": ["complete_64_cell_mass", "sampled_256_label_plus_tasks"],
        "action_universe": ["CONTINUE_Q0", "SWITCH_QD1_AT_4096"],
        "forced_veto": ["QB1", "QGR1"],
        "single_formal_request": True, "additional_label_pops": 0,
        "auxiliary_prefix_requests": 0,
    })
    write_once(run_root / "acceptance.freeze.json", {
        "schema_version": "lunar_ice_bpc.p0v5_multires_frontier_acceptance.v1",
        "gate": config["gate"],
        "if_pass": "SINGLE_REQUEST_NATIVE_FRESH_PILOT",
        "if_fail": "MULTI_TIMEPOINT_LATE_SWITCH_ORACLE",
        "threshold_relaxation_forbidden": True,
    })
    initial = {
        "schema_version": "lunar_ice_bpc.p0v5_multires_frontier_state.v1",
        "experiment_id": config["experiment_id"],
        "current_stage": "OOF_DIAGNOSTIC", "status": "READY",
        "terminal": False, "diagnostic_only": True,
        "performance_authority": False,
    }
    write_once(run_root / "state.initial.json", initial)
    registry_files = (
        "config.freeze.json", "source.freeze.json", "evidence_import.freeze.json",
        "corpus.freeze.json", "folds.freeze.json", "interface.freeze.json",
        "acceptance.freeze.json", "state.initial.json",
    )
    write_once(run_root / "freeze.registry.json", {
        "schema_version": "lunar_ice_bpc.p0v5_multires_frontier_registry.v1",
        "artifact_sha256": {
            relative: sha256(run_root / relative) for relative in registry_files
        },
    })
    if (run_root / "state.json").exists():
        if load(run_root / "state.json") != initial:
            raise SystemExit("existing V9R1 state drift")
    else:
        write_mutable(run_root / "state.json", initial)
    verify_freezes(run_root)
    print(f"V9R1_MULTIRES_FREEZE_OK:{run_root}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args()
    initialize(args.config.resolve(), args.run_root.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
