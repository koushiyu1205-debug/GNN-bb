#!/usr/bin/env python3
"""Run sequential paired full-BPC evidence for Interaction-GAT V2."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import scripts.run_p0v5_context_queue_portfolio_full_bpc as base  # noqa: E402
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import (  # noqa: E402
    verify_portfolio_freezes,
)
from lunar_ice_bpc.guidance.context_queue_portfolio_gates import (  # noqa: E402
    geometric_mean,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_runtime_v2 import (  # noqa: E402
    INTERACTION_GAT_EVALUATION_ENV,
    INTERACTION_GAT_MANIFEST_ENV,
)


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_interaction_gat_queue_selector_v2_20260807"
BOOTSTRAP = ROOT / "scripts/run_lunar_ice_interaction_gat_acceptance_v2.py"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("development_e2e", "formal_full100"))
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    try:
        verify_portfolio_freezes(run_root, ROOT)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    state = _load(run_root / "state.json")
    if bool(state.get("terminal")):
        raise SystemExit("terminal chain forbids full-BPC execution")
    config = _load(run_root / "config.freeze.json")
    manifest = run_root / "research_candidate.manifest.json"
    if not manifest.is_file():
        raise SystemExit("V2 research candidate manifest is missing")
    if args.mode == "development_e2e":
        heldout = _load(run_root / "heldout.decision.json")["decision"]
        if not bool(heldout.get("passed")):
            raise SystemExit("development E2E forbidden before heldout pass")
        instances = base._development_instances(run_root)
        repeats = 3
    else:
        development = _load(run_root / "development_e2e.decision.json")["decision"]
        if not bool(development.get("passed")):
            raise SystemExit("formal full100 forbidden before development E2E pass")
        candidate = _load(run_root / "research_candidate.freeze.json")
        if str(candidate.get("manifest_sha256")) != base._sha256(manifest):
            raise SystemExit("formal V2 candidate manifest drift")
        instances = base._formal_instances(config)
        repeats = 1
    schedule = base._schedule(
        args.mode, instances, repeats=repeats, cap_sec=3600.0,
        manifest=manifest, run_root=run_root,
    )
    schedule["schema_version"] = (
        "lunar_ice_bpc.p0v5_interaction_gat_full_bpc_execution.v2"
    )
    schedule["runtime_bootstrap"] = str(BOOTSTRAP)
    schedule["runtime_bootstrap_sha256"] = base._sha256(BOOTSTRAP)
    freeze_path = run_root / f"{args.mode}_execution.freeze.json"
    base._write_once(freeze_path, schedule)
    output_root = run_root / args.mode
    evidence = []
    for task in schedule["tasks"]:
        task_root = output_root / str(task["task_id"])
        parsed_path = task_root / "canonical_instance_row.json"
        if not parsed_path.is_file():
            _run_one(task, task_root, config, manifest)
            row = _parse_one(task_root, task, cap_sec=3600.0)
            base._write_once(parsed_path, row)
        evidence.append(_load(parsed_path))
    payload = (
        _development_payload(evidence, freeze_path)
        if args.mode == "development_e2e"
        else _formal_payload(evidence, freeze_path)
    )
    output = run_root / f"{args.mode}_rows.json"
    base._write_once(output, payload)
    print(json.dumps({
        "mode": args.mode,
        "task_count": len(evidence),
        "result": str(output),
        "single_native_process": True,
        "exact_source_modified": False,
    }, ensure_ascii=False, indent=2))
    return 0


def _run_one(task, output, config, manifest):
    if output.exists():
        raise SystemExit(f"partial V2 full-BPC task requires audit:{output}")
    runner = BOOTSTRAP if task["side"] == "candidate" else (
        ROOT / "scripts/run_lunar_ice_native_spprc_acceptance.py"
    )
    command = [
        sys.executable, str(runner),
        "--config", str((ROOT / config["selected_exact_config"]).resolve()),
        "--scales", str(task["scale"]),
        "--instance", str(task["instance_path"]),
        "--limit", "1", "--output-dir", str(output), "--no-resume",
    ]
    completed = subprocess.run(
        command, cwd=ROOT,
        env=_environment(config, manifest if task["side"] == "candidate" else None),
        check=False,
    )
    if completed.returncode not in {0, 1}:
        raise SystemExit(f"V2 full-BPC execution error:{task['task_id']}")


def _environment(config, manifest):
    env = dict(os.environ)
    for key in tuple(env):
        if (
            key.startswith("LUNAR_ICE_P0V5_")
            or key.startswith("LUNAR_ICE_PROOF_TAIL_GAT")
            or key.startswith("LUNAR_ICE_GAT_")
        ):
            env.pop(key, None)
    env["PYTHONPATH"] = os.pathsep.join((
        str((ROOT / config["native_build_dir"]).resolve()),
        str((ROOT / "src").resolve()),
    ))
    if manifest is not None:
        env[INTERACTION_GAT_MANIFEST_ENV] = str(manifest)
        env[INTERACTION_GAT_EVALUATION_ENV] = "1"
    return env


def _parse_one(root, task, *, cap_sec):
    rows = base.paired._rows(root)
    if set(rows) != {task["instance_hash"]}:
        raise SystemExit("V2 full-BPC acceptance output instance mismatch")
    row = dict(rows[task["instance_hash"]])
    tree = _load(Path(row["tree_result"])) if row.get("tree_result") else {}
    telemetry = _interaction_telemetry(tree)
    return {
        "task_id": task["task_id"], "scale": task["scale"],
        "instance_hash": task["instance_hash"], "repeat": task["repeat"],
        "side": task["side"], "exact": bool(row["exact"]),
        "objective": row["objective"], "wall_sec": float(row["wall_sec"]),
        "par2_wall_sec": float(row["wall_sec"]) if row["exact"] else 2.0 * cap_sec,
        "correctness_redlines": [] if row["redlines_zero"] else ["solver_redline"],
        **telemetry,
        "tree_result": row["tree_result"],
    }


def _interaction_telemetry(payload):
    counters = defaultdict(int)
    action_counts = defaultdict(int)
    preparation = []

    def visit(value):
        if isinstance(value, dict):
            if "proof_tail_interaction_gat_action" in value:
                reason = str(value.get("proof_tail_interaction_gat_decision_reason") or "")
                action = str(value.get("proof_tail_interaction_gat_action") or "Q0")
                counters["selector_calls"] += int(bool(value.get(
                    "proof_tail_interaction_gat_runtime_enabled"
                )))
                counters["manifest_reads"] += int(bool(value.get(
                    "proof_tail_interaction_gat_manifest_read"
                )))
                counters["graph_build_calls"] += int(value.get(
                    "proof_tail_interaction_gat_graph_build_calls"
                ) or 0)
                counters["model_calls"] += int(value.get(
                    "proof_tail_interaction_gat_model_calls"
                ) or 0)
                counters["ranker_calls"] += int(value.get(
                    "proof_tail_interaction_gat_ranker_calls"
                ) or 0)
                counters["torch_imports"] += int(float(value.get(
                    "proof_tail_interaction_gat_torch_first_import_wall_ms"
                ) or 0.0) > 0.0)
                if reason.startswith("non_root_lifecycle"):
                    counters["tree_model_calls"] += int(value.get(
                        "proof_tail_interaction_gat_model_calls"
                    ) or 0)
                if bool(value.get("proof_tail_interaction_gat_runtime_enabled")):
                    action_counts[action] += 1
                    preparation.append(float(value.get(
                        "proof_tail_interaction_gat_total_prepare_wall_ms"
                    ) or 0.0))
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(payload)
    return {
        **{key: int(counters[key]) for key in (
            "selector_calls", "manifest_reads", "graph_build_calls",
            "model_calls", "ranker_calls", "torch_imports", "tree_model_calls",
        )},
        "selected_action_counts": dict(sorted(action_counts.items())),
        "preparation_wall_ms_values": preparation,
    }


def _development_payload(rows, freeze_path):
    redlines = []
    by_pair = {
        (row["instance_hash"], int(row["repeat"]), row["side"]): row
        for row in rows
    }
    scales = {}
    for scale in (30, 50):
        scale_rows = [row for row in rows if int(row["scale"]) == scale]
        instances = sorted({row["instance_hash"] for row in scale_rows})
        instance_ratios = []
        activation_instances = 0
        q0_exact = candidate_exact = 0
        tree_calls = 0
        scale_redlines = []
        for instance in instances:
            ratios = []
            activated = False
            q0_complete = candidate_complete = True
            for repeat in range(3):
                q0 = by_pair[(instance, repeat, "Q0")]
                candidate = by_pair[(instance, repeat, "candidate")]
                q0_complete = q0_complete and bool(q0["exact"])
                candidate_complete = candidate_complete and bool(candidate["exact"])
                ratios.append(float(candidate["par2_wall_sec"]) / float(q0["par2_wall_sec"]))
                activated = activated or any(
                    action != "Q0" and int(count) > 0
                    for action, count in candidate["selected_action_counts"].items()
                )
                tree_calls += int(candidate.get("tree_model_calls") or 0)
                scale_redlines.extend(q0["correctness_redlines"])
                scale_redlines.extend(candidate["correctness_redlines"])
                if (
                    q0["exact"] and candidate["exact"]
                    and q0["objective"] is not None and candidate["objective"] is not None
                    and abs(float(q0["objective"]) - float(candidate["objective"])) > 2.0e-6
                ):
                    scale_redlines.append("objective_mismatch")
            q0_exact += int(q0_complete)
            candidate_exact += int(candidate_complete)
            activation_instances += int(activated)
            instance_ratios.append(statistics.median(ratios))
        redlines.extend(scale_redlines)
        scales[str(scale)] = {
            "gm": geometric_mean(instance_ratios),
            "q0_exact_count": q0_exact,
            "candidate_exact_count": candidate_exact,
            "activation_instances": activation_instances,
            "worst_instance_median_ratio": max(instance_ratios),
            "tree_model_calls": tree_calls,
            "correctness_redlines": sorted(set(scale_redlines)),
        }
    return {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_development_e2e_rows.v2",
        "execution_freeze": str(freeze_path),
        "execution_freeze_sha256": base._sha256(freeze_path),
        "scales": scales,
        "correctness_redlines": sorted(set(redlines)),
        "raw_instance_rows": rows,
    }


def _formal_payload(rows, freeze_path):
    payload = base._formal_payload(rows, freeze_path)
    payload["schema_version"] = (
        "lunar_ice_bpc.p0v5_interaction_gat_formal_full100_rows.v2"
    )
    counters = {}
    activations = {}
    for scale in (5, 10, 20, 30, 50):
        candidate = [
            row for row in payload["rows"]
            if int(row["scale"]) == scale and row["side"] == "candidate"
        ]
        counters[str(scale)] = {
            "manifest_reads": sum(int(row.get("manifest_reads") or 0) for row in candidate),
            "torch_imports": sum(int(row.get("torch_imports") or 0) for row in candidate),
            "gat_calls": sum(int(row.get("model_calls") or 0) for row in candidate),
            "ranker_calls": sum(int(row.get("ranker_calls") or 0) for row in candidate),
        }
        activations[str(scale)] = sum(
            any(action != "Q0" and int(count) > 0 for action, count in row[
                "selected_action_counts"
            ].items())
            for row in candidate
        )
    payload["runtime_counters_by_scale"] = counters
    payload["activation_instances_by_scale"] = activations
    return payload


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
