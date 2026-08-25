#!/usr/bin/env python3
"""Sequential development-E2E/formal-full100 runner for frozen V7."""

from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
import scripts.run_p0v5_residual_gat_full_bpc_v4 as shared  # noqa: E402
import scripts.run_p0v5_interaction_gat_full_bpc_v2 as v2  # noqa: E402
from lunar_ice_bpc.guidance.frontier_gat_qd1_runtime_v7 import (  # noqa: E402
    EVALUATION_ENV,
    MANIFEST_ENV,
)
from scripts.p0v5_native_frontier_gat_qd1_v7_common import (  # noqa: E402
    DEFAULT_RUN_ROOT,
    load,
    sha256,
    verify_freezes,
    write_once,
    write_terminal,
)


BOOTSTRAP = ROOT / "scripts/run_lunar_ice_frontier_gat_acceptance_v7.py"


def _verify(run_root, root):
    if Path(root).resolve() != ROOT:
        raise SystemExit("V7 full-BPC root mismatch")
    verify_freezes(Path(run_root).resolve())


def _terminal(run_root, reason, detail):
    write_terminal(Path(run_root), reason=reason,
                   stage=load(Path(run_root) / "state.json")["current_stage"],
                   detail=detail)
    return 1


def _pass(run_root, detail):
    run_root = Path(run_root)
    write_once(run_root / "terminal_decision.json", {
        "schema_version": "lunar_ice_bpc.p0v5_native_frontier_gat_terminal.v7",
        "decision": "PASS", "reason": "FORMAL_FULL100_PASSED", "detail": detail,
        "development_only": True, "deployment_authorized": False,
        "production_switch_authorized": False,
    })
    state = load(run_root / "state.json")
    state.update({"current_stage": "TERMINAL", "status": "PASS", "terminal": True,
                  "terminal_decision": "terminal_decision.json"})
    from scripts.p0v5_native_frontier_gat_qd1_v7_common import write_mutable
    write_mutable(run_root / "state.json", state)


def _development_instances(run_root):
    values = {}
    for row in load(Path(run_root) / "main_corpus.freeze.json")["rows"]:
        if row["partition"] == "development_e2e":
            values[row["instance_content_hash"]] = {
                "scale": row["scale"], "instance_path": row["instance_path"],
                "instance_content_hash": row["instance_content_hash"],
            }
    rows = list(values.values())
    if {scale: sum(int(row["scale"]) == scale for row in rows)
            for scale in (30, 50)} != {30: 3, 50: 3}:
        raise SystemExit("V7 development E2E split is not 3+3")
    return rows


def _frontier_telemetry(payload):
    counters = defaultdict(int)
    actions = defaultdict(int)
    preparation = []

    def visit(value):
        if isinstance(value, dict):
            if "proof_tail_frontier_runtime_action" in value:
                enabled = bool(value.get("proof_tail_frontier_runtime_enabled"))
                bypassed = bool(value.get("proof_tail_frontier_bypassed_before_manifest"))
                counters["selector_calls"] += int(enabled)
                counters["manifest_reads"] += int(not bypassed)
                counters["bundle_loads"] += int(bool(value.get(
                    "proof_tail_frontier_bundle_sha256")))
                preparation.append(float(value.get(
                    "proof_tail_frontier_bundle_load_wall_ms") or 0.0))
            if "schema_version" in value and value.get("schema_version") == (
                "lunar_spprc.frontier_probe_telemetry.v1"
            ):
                counters["graph_build_calls"] += int(bool(value.get("graph_built")))
                counters["model_calls"] += int(bool(value.get("model_called")))
                counters["migration_calls"] += int(bool(value.get("switched_to_qd1")))
                if bool(value.get("reached")):
                    action = "QD1" if value.get("action") == "SWITCH_QD1" else "Q0"
                    actions[action] += 1
                preparation.append(1000.0 * (
                    float(value.get("graph_build_wall_seconds") or 0.0)
                    + float(value.get("inference_wall_seconds") or 0.0)
                    + float(value.get("migration_wall_seconds") or 0.0)
                ))
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(payload)
    return {
        "selector_calls": counters["selector_calls"],
        "manifest_reads": counters["manifest_reads"],
        "graph_build_calls": counters["graph_build_calls"],
        "model_calls": counters["model_calls"],
        "ranker_calls": 0, "torch_imports": 0, "tree_model_calls": 0,
        "selected_action_counts": dict(sorted(actions.items())),
        "preparation_wall_ms_values": preparation,
    }


def main() -> int:
    shared.DEFAULT_RUN_ROOT = DEFAULT_RUN_ROOT
    shared.BOOTSTRAP = BOOTSTRAP
    shared.INTERACTION_GAT_MANIFEST_ENV_V4 = MANIFEST_ENV
    shared.INTERACTION_GAT_EVALUATION_ENV_V4 = EVALUATION_ENV
    shared.verify_portfolio_freezes = _verify
    shared._development_instances = _development_instances
    shared._terminal = _terminal
    shared._pass = _pass
    v2.BOOTSTRAP = BOOTSTRAP
    v2.INTERACTION_GAT_MANIFEST_ENV = MANIFEST_ENV
    v2.INTERACTION_GAT_EVALUATION_ENV = EVALUATION_ENV
    v2._interaction_telemetry = _frontier_telemetry
    return int(shared.main())


if __name__ == "__main__":
    raise SystemExit(main())
