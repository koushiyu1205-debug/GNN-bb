#!/usr/bin/env python3
"""Freeze the low-cost 256-label base-frontier observability diagnostic."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
import sys
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.guidance.base_frontier_gat_qd1_v9 import (  # noqa: E402
    CHECKPOINT_SCHEMA_V1,
    FEATURE_SCHEMA_V1,
    GRAPH_SCHEMA_V1,
    MODEL_KINDS,
    MODEL_SEEDS,
    RUNTIME_POLICY_V1,
    BaseFrontierExample,
    graph_from_payload,
)
from lunar_ice_bpc.guidance.counterfactual_prefix_gat_qd1_v8 import (  # noqa: E402
    CONTEXT_FEATURE_NAMES,
    EDGE_FEATURE_NAMES,
    NODE_FEATURE_NAMES,
)
from scripts.p0v5_base_label_frontier_v9r0_common import (  # noqa: E402
    CONFIG,
    DEFAULT_RUN_ROOT,
    load,
    sha256,
    stable_hash,
    verify_freezes,
    write_mutable,
    write_once,
)


SOURCE_PATHS = (
    "configs/experiments/p0v5_base_label_frontier_observability_v9r0.json",
    "plan/GAT/P0V5_BASE_LABEL_FRONTIER_OBSERVABILITY_V9R0_20260818_ZH.md",
    "scripts/initialize_p0v5_base_label_frontier_observability_v9r0.py",
    "scripts/p0v5_base_label_frontier_v9r0_common.py",
    "scripts/train_p0v5_base_label_frontier_observability_v9r0.py",
    "src/lunar_ice_bpc/guidance/base_frontier_gat_qd1_v9.py",
    "src/lunar_ice_bpc/guidance/counterfactual_prefix_gat_qd1_v8.py",
    "tests/test_p0v5_base_label_frontier_observability_v9r0.py",
)

V8_REQUIRED = (
    "terminal_decision.json",
    "source.freeze.json",
    "representation_triplets.json",
    "representation_development.report.json",
    "cross_binary_native_differential.report.json",
    "v8_measurement_repair.freeze.json",
)
V7R3_REQUIRED = (
    "terminal_decision.json",
    "source.freeze.json",
    "feature_sufficiency.report.json",
    "switch_oracle.decision.json",
)
EXPECTED = {
    30: {"contexts": 19, "instances": 15},
    50: {"contexts": 19, "instances": 16},
}


def _assert_source_contract(v8_root: Path, v7r3_root: Path) -> None:
    v8_terminal = load(v8_root / "terminal_decision.json")
    if (
        v8_terminal.get("decision") != "FAIL"
        or v8_terminal.get("reason") != "COUNTERFACTUAL_PREFIX_NOT_IDENTIFIABLE"
        or v8_terminal.get("detail", {}).get("immediate_cause")
        != "PREFIX_COST_GATE_FAILED_BEFORE_OOF"
    ):
        raise SystemExit("V8R1 terminal contract drift")
    if load(v8_root / "cross_binary_native_differential.report.json").get(
        "decision"
    ) != "PASS":
        raise SystemExit("V8R1 exact differential is not PASS")
    if load(v8_root / "representation_development.report.json").get(
        "ooF_training_started"
    ) is not False:
        raise SystemExit("V8R1 OOF outcome exposure drift")
    v7_terminal = load(v7r3_root / "terminal_decision.json")
    if (
        v7_terminal.get("decision") != "FAIL"
        or v7_terminal.get("reason") != "SCALE50_BENEFIT_HARM_NOT_SEPARABLE"
    ):
        raise SystemExit("V7R3 terminal contract drift")
    oracle = load(v7r3_root / "switch_oracle.decision.json")
    if oracle.get("decision") != "PASS" or int(
        oracle.get("correctness_redline_count", -1)
    ) != 0:
        raise SystemExit("V7R3 oracle/correctness contract drift")


def _collapse_rows(v8_root: Path) -> list[dict[str, Any]]:
    payload = load(v8_root / "representation_triplets.json")
    rows = list(payload.get("rows") or ())
    if len(rows) != 114 or int(payload.get("context_count", -1)) != 38:
        raise SystemExit("V8R1 triplet count drift")
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["context_id"])].append(row)
    if len(grouped) != 38:
        raise SystemExit("V8R1 unique-context count drift")

    collapsed = []
    for context_id, values in sorted(grouped.items()):
        if sorted(int(row["rollout_budget"]) for row in values) != [128, 512, 2048]:
            raise SystemExit(f"V8R1 budget coverage drift:{context_id}")
        selected = next(row for row in values if int(row["rollout_budget"]) == 128)
        invariant_keys = (
            "base", "instance_hash", "scale", "state_hash", "target",
            "qpf0_reference_wall_seconds",
        )
        for key in invariant_keys:
            if any(row[key] != selected[key] for row in values):
                raise SystemExit(f"V8R1 base/target drift:{context_id}:{key}")
        if any(
            not bool(row.get("diagnostic_only"))
            or bool(row.get("performance_authority"))
            for row in values
        ):
            raise SystemExit(f"V8R1 authority drift:{context_id}")

        raw_path = v8_root / "representation_prefix_raw" / f"{context_id}_Q0_PREFIX.json"
        raw = load(raw_path)
        prefix = dict(raw.get("prefix") or {})
        if (
            raw.get("policy") != "Q0_PREFIX"
            or raw.get("exact") is not False
            or raw.get("routes") != []
            or raw.get("certificate") is not None
            or raw.get("truncated_diagnostic") is not True
        ):
            raise SystemExit(f"V8R1 telemetry-only prefix contract drift:{context_id}")
        graph_build = float(prefix.get("base_graph_build_wall_seconds") or 0.0)
        if graph_build <= 0.0:
            raise SystemExit(f"V8R1 base graph timing missing:{context_id}")
        target = dict(selected["target"])
        graph = graph_from_payload(selected["base"])
        example = BaseFrontierExample(
            graph=graph,
            context_id=context_id,
            instance_hash=str(selected["instance_hash"]),
            state_hash=str(selected["state_hash"]),
            scale=int(selected["scale"]),
            ratio=float(target["ratio"]),
            benefit=int(target["benefit"]),
            positive_gain=float(target["positive_gain"]),
            adverse=int(target["adverse"]),
            qpf0_wall_seconds=float(selected["qpf0_reference_wall_seconds"]),
            graph_build_wall_seconds=graph_build,
        )
        example.validate()
        collapsed.append({
            "context_id": context_id,
            "instance_hash": example.instance_hash,
            "state_hash": example.state_hash,
            "scale": example.scale,
            "graph": selected["base"],
            "target": target,
            "qpf0_reference_wall_seconds": example.qpf0_wall_seconds,
            "base_graph_build_wall_seconds": graph_build,
            "source_rollout_budget": 128,
            "source_raw_q0_prefix": str(raw_path.relative_to(v8_root)),
            "diagnostic_only": True,
            "performance_authority": False,
        })

    for scale, expected in EXPECTED.items():
        scale_rows = [row for row in collapsed if int(row["scale"]) == scale]
        instances = {str(row["instance_hash"]) for row in scale_rows}
        if len(scale_rows) != expected["contexts"] or len(instances) != expected["instances"]:
            raise SystemExit(f"V8R1 scale{scale} corpus count drift")
    if len({row["state_hash"] for row in collapsed}) != len(collapsed):
        raise SystemExit("duplicate state hash in base-frontier corpus")
    return collapsed


def assign_folds(rows: list[Mapping[str, Any]], *, seed: int = 2608184096) -> list[dict[str, Any]]:
    by_instance: dict[tuple[int, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        by_instance[(int(row["scale"]), str(row["instance_hash"]))].append(row)
    if len({instance for _, instance in by_instance}) != len(by_instance):
        raise SystemExit("instance hash appears in both scales")
    output = []
    for scale in (30, 50):
        items = [
            (instance, len(values))
            for (item_scale, instance), values in by_instance.items()
            if item_scale == scale
        ]
        items.sort(key=lambda item: (
            -item[1], stable_hash(f"{seed}:{scale}:{item[0]}")
        ))
        context_load = [0] * 5
        instance_load = [0] * 5
        for instance, multiplicity in items:
            fold = min(range(5), key=lambda index: (
                context_load[index], instance_load[index], index
            ))
            context_load[fold] += multiplicity
            instance_load[fold] += 1
            output.append({
                "scale": scale, "instance_hash": instance,
                "context_count": multiplicity, "fold": fold,
            })
        if any(value == 0 for value in instance_load):
            raise SystemExit(f"empty instance-grouped fold at scale{scale}")
    return sorted(output, key=lambda row: (row["scale"], row["instance_hash"]))


def initialize(config_path: Path, run_root: Path) -> None:
    config = load(config_path)
    v8_root = (ROOT / config["source_v8r1_run_root"]).resolve()
    v7r3_root = (ROOT / config["source_v7r3_run_root"]).resolve()
    _assert_source_contract(v8_root, v7r3_root)
    for path in SOURCE_PATHS:
        if not (ROOT / path).is_file():
            raise SystemExit(f"missing V9R0 source:{path}")

    # The new model imports the V8 graph contract, so the current file must
    # still equal the source frozen by the read-only V8R1 chain.
    v8_source = load(v8_root / "source.freeze.json")
    imported_module = "src/lunar_ice_bpc/guidance/counterfactual_prefix_gat_qd1_v8.py"
    expected_module_hash = v8_source["source_sha256"].get(imported_module)
    if expected_module_hash != sha256(ROOT / imported_module):
        raise SystemExit("V8R1 graph/model source drift")

    rows = _collapse_rows(v8_root)
    folds = assign_folds(rows)
    raw_relatives = sorted(str(row["source_raw_q0_prefix"]) for row in rows)
    v8_artifacts = {
        relative: sha256(v8_root / relative)
        for relative in (*V8_REQUIRED, *raw_relatives)
    }
    v7_artifacts = {
        relative: sha256(v7r3_root / relative)
        for relative in V7R3_REQUIRED
    }

    run_root.mkdir(parents=True, exist_ok=True)
    write_once(run_root / "config.freeze.json", config)
    write_once(run_root / "source.freeze.json", {
        "schema_version": "lunar_ice_bpc.p0v5_base_label_frontier_source_freeze.v1",
        "source_sha256": {path: sha256(ROOT / path) for path in SOURCE_PATHS},
        "worktree_may_be_dirty": True,
        "no_native_change": True,
    })
    write_once(run_root / "evidence_import.freeze.json", {
        "schema_version": "lunar_ice_bpc.p0v5_base_label_frontier_evidence_import.v1",
        "source_v8r1_root": str(v8_root),
        "source_v7r3_root": str(v7r3_root),
        "source_artifacts": {
            "source_v8r1_root": v8_artifacts,
            "source_v7r3_root": v7_artifacts,
        },
        "context_count": 38,
        "instance_count": 31,
        "arm_outcomes_created_in_this_chain": 0,
        "heldout_or_formal_outcomes_imported": 0,
        "diagnostic_only": True,
        "performance_authority": False,
    })
    write_once(run_root / "corpus.freeze.json", {
        "schema_version": "lunar_ice_bpc.p0v5_base_label_frontier_corpus.v1",
        "rows": rows,
        "context_count": len(rows),
        "instance_count": len({row["instance_hash"] for row in rows}),
        "selection": "one frozen 4096-pop base graph per V7R3 context",
        "outcome_exposure": "diagnostic labels already known; no performance authority",
    })
    write_once(run_root / "folds.freeze.json", {
        "schema_version": "lunar_ice_bpc.p0v5_base_label_frontier_folds.v1",
        "seed": 2608184096,
        "fold_count": 5,
        "rows": folds,
    })
    write_once(run_root / "interface.freeze.json", {
        "schema_version": "lunar_ice_bpc.p0v5_base_label_frontier_interface.v1",
        "feature_schema": FEATURE_SCHEMA_V1,
        "graph_schema": GRAPH_SCHEMA_V1,
        "checkpoint_schema": CHECKPOINT_SCHEMA_V1,
        "runtime_policy": RUNTIME_POLICY_V1,
        "node_feature_names": list(NODE_FEATURE_NAMES),
        "edge_feature_names": list(EDGE_FEATURE_NAMES),
        "context_feature_names": list(CONTEXT_FEATURE_NAMES),
        "model_kinds": list(MODEL_KINDS),
        "model_seeds": list(MODEL_SEEDS),
        "action_universe": ["CONTINUE_Q0", "SWITCH_QD1_AT_4096"],
        "single_formal_request": True,
        "counterfactual_prefix_requests": 0,
    })
    write_once(run_root / "acceptance.freeze.json", {
        "schema_version": "lunar_ice_bpc.p0v5_base_label_frontier_acceptance.v1",
        "gate": config["gate"],
        "if_pass": "authorize a separate Native runtime implementation stage",
        "if_fail": "terminal BASE_LABEL_FRONTIER_NOT_IDENTIFIABLE",
        "threshold_relaxation_forbidden": True,
    })
    initial_state = {
        "schema_version": "lunar_ice_bpc.p0v5_base_label_frontier_state.v1",
        "experiment_id": config["experiment_id"],
        "current_stage": "OOF_DIAGNOSTIC",
        "status": "READY",
        "terminal": False,
        "diagnostic_only": True,
        "performance_authority": False,
    }
    write_once(run_root / "state.initial.json", initial_state)
    registry_files = (
        "config.freeze.json", "source.freeze.json", "evidence_import.freeze.json",
        "corpus.freeze.json", "folds.freeze.json", "interface.freeze.json",
        "acceptance.freeze.json", "state.initial.json",
    )
    write_once(run_root / "freeze.registry.json", {
        "schema_version": "lunar_ice_bpc.p0v5_base_label_frontier_freeze_registry.v1",
        "artifact_sha256": {
            relative: sha256(run_root / relative) for relative in registry_files
        },
    })
    if (run_root / "state.json").exists():
        existing = load(run_root / "state.json")
        if existing != initial_state:
            raise SystemExit("existing V9R0 state drift")
    else:
        write_mutable(run_root / "state.json", initial_state)
    verify_freezes(run_root)
    print(f"V9R0_BASE_LABEL_FREEZE_OK:{run_root}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args()
    initialize(args.config.resolve(), args.run_root.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
