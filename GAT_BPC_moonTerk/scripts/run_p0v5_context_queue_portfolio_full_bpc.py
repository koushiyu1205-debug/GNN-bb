#!/usr/bin/env python3
"""Run sequential paired development-E2E or formal-full100 BPC evidence."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
import analyze_p0v5_qg2_paired_acceptance as paired  # noqa: E402
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import (  # noqa: E402
    verify_portfolio_freezes,
)


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_context_queue_portfolio_v1_20260807_r1"
MANIFEST_ENV = "LUNAR_ICE_P0V5_CONTEXT_QUEUE_PORTFOLIO_V1_MANIFEST"
EVALUATION_ENV = "LUNAR_ICE_P0V5_CONTEXT_QUEUE_PORTFOLIO_V1_EVALUATION_MODE"


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
    config = _load(run_root / "config.freeze.json")
    manifest = run_root / "research_candidate.manifest.json"
    if not manifest.is_file():
        raise SystemExit("research candidate manifest is missing")
    if args.mode == "development_e2e":
        heldout = _load(run_root / "heldout.decision.json")["decision"]
        if not bool(heldout.get("passed")):
            raise SystemExit("development E2E forbidden before heldout pass")
        instances = _development_instances(run_root)
        repeats = 3
    else:
        development = _load(run_root / "development_e2e.decision.json")["decision"]
        if not bool(development.get("passed")):
            raise SystemExit("formal full100 forbidden before development E2E pass")
        candidate_freeze = _load(run_root / "research_candidate.freeze.json")
        if candidate_freeze["manifest_sha256"] != _sha256(manifest):
            raise SystemExit("formal candidate manifest drift")
        instances = _formal_instances(config)
        repeats = 1
    schedule = _schedule(
        args.mode, instances, repeats=repeats, cap_sec=3600.0,
        manifest=manifest, run_root=run_root,
    )
    freeze_path = run_root / f"{args.mode}_execution.freeze.json"
    _write_once(freeze_path, schedule)
    output_root = run_root / args.mode
    evidence = []
    for task in schedule["tasks"]:
        task_root = output_root / str(task["task_id"])
        parsed_path = task_root / "canonical_instance_row.json"
        if not parsed_path.is_file():
            _run_one(task, task_root, config, manifest)
            row = _parse_one(task_root, task, cap_sec=3600.0)
            _write_once(parsed_path, row)
        evidence.append(_load(parsed_path))
    result = (
        _development_payload(evidence, freeze_path)
        if args.mode == "development_e2e"
        else _formal_payload(evidence, freeze_path)
    )
    result_path = run_root / f"{args.mode}_rows.json"
    _write_once(result_path, result)
    print(json.dumps({
        "mode": args.mode, "task_count": len(evidence),
        "result": str(result_path), "single_native_process": True,
    }, ensure_ascii=False, indent=2))
    return 0


def _development_instances(run_root):
    split = _load(run_root / "instance_split.freeze.json")
    rows = [
        dict(row) for row in split["rows"]
        if row["partition"] == "development_e2e"
    ]
    if {
        scale: sum(int(row["scale"]) == scale for row in rows)
        for scale in (30, 50)
    } != {30: 3, 50: 3}:
        raise SystemExit("development E2E split is not 3+3")
    return rows


def _formal_instances(config):
    root = (ROOT / config["formal_instance_root"]).resolve()
    rows = []
    for scale in (5, 10, 20, 30, 50):
        paths = sorted((root / f"lunar_ice_sp50_{scale:03d}").glob(
            "instance_*_logical_graph.json"
        ))[:20]
        if len(paths) != 20:
            raise SystemExit(f"formal scale{scale} instances != 20")
        for path in paths:
            data = load_lunar_ice_data(_load(path))
            rows.append({
                "scale": scale, "instance_path": str(path),
                "instance_content_hash": data.instance_content_hash,
            })
    return rows


def _schedule(mode, instances, *, repeats, cap_sec, manifest, run_root):
    tasks = []
    for row in sorted(instances, key=lambda value: (
        int(value["scale"]), str(value["instance_content_hash"])
    )):
        for repeat in range(repeats):
            sides = sorted(("Q0", "candidate"), key=lambda side: hashlib.sha256(
                f"{row['instance_content_hash']}:{repeat}:{side}".encode()
            ).hexdigest())
            for ordinal, side in enumerate(sides):
                task_id = hashlib.sha256(
                    f"{mode}:{row['instance_content_hash']}:{repeat}:{side}".encode()
                ).hexdigest()[:24]
                tasks.append({
                    "task_id": task_id,
                    "scale": int(row["scale"]),
                    "instance_hash": str(row["instance_content_hash"]),
                    "instance_path": str(Path(row["instance_path"]).resolve()),
                    "instance_sha256": _sha256(Path(row["instance_path"])),
                    "repeat": repeat,
                    "ordinal_in_block": ordinal,
                    "side": side,
                    "cap_sec": cap_sec,
                    "fresh_process": True,
                })
    return {
        "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_full_bpc_execution.v1",
        "mode": mode,
        "status": "FROZEN_BEFORE_CORRESPONDING_FULL_BPC_OUTCOMES",
        "single_native_process": True,
        "arm_order": "instance_hash_blocked",
        "manifest": str(manifest), "manifest_sha256": _sha256(manifest),
        "source_freeze_sha256": _sha256(run_root / "source.freeze.json"),
        "tasks": tasks,
    }


def _run_one(task, output, config, manifest):
    if output.exists():
        raise SystemExit(f"partial full-BPC task requires audit before rerun:{output}")
    command = [
        sys.executable,
        str(ROOT / "scripts/run_lunar_ice_native_spprc_acceptance.py"),
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
        raise SystemExit(f"full-BPC task execution error:{task['task_id']}")


def _parse_one(root, task, *, cap_sec):
    rows = paired._rows(root)
    if set(rows) != {task["instance_hash"]}:
        raise SystemExit("full-BPC acceptance output instance mismatch")
    row = dict(rows[task["instance_hash"]])
    tree = _load(Path(row["tree_result"])) if row.get("tree_result") else {}
    telemetry = _portfolio_telemetry(tree)
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


def _portfolio_telemetry(payload):
    selector_calls = model_calls = ranker_calls = 0
    action_counts = {}
    preparation = []
    def visit(value):
        nonlocal selector_calls, model_calls, ranker_calls
        if isinstance(value, dict):
            enabled = bool(value.get("proof_tail_portfolio_runtime_enabled"))
            action = str(value.get("proof_tail_portfolio_action") or "")
            if enabled and action in {"Q0", "QD1", "QB1", "QGR1"}:
                selector_calls += 1
                model_calls += 1
                action_counts[action] = action_counts.get(action, 0) + 1
                if action == "QGR1":
                    ranker_calls += 1
                preparation.append(float(
                    value.get("proof_tail_portfolio_total_prepare_wall_ms") or 0.0
                ))
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
    visit(payload)
    return {
        "selector_calls": selector_calls, "model_calls": model_calls,
        "ranker_calls": ranker_calls,
        "selected_action_counts": dict(sorted(action_counts.items())),
        "preparation_wall_ms_values": preparation,
    }


def _development_payload(rows, freeze_path):
    canonical, exact = [], {"Q0": {}, "candidate": {}}
    for scale in (30, 50):
        for side in ("Q0", "candidate"):
            by_instance = defaultdict(list)
            for row in rows:
                if row["scale"] == scale and row["side"] == side:
                    by_instance[row["instance_hash"]].append(bool(row["exact"]))
            exact[side][str(scale)] = sum(
                len(values) == 3 and all(values)
                for values in by_instance.values()
            )
    by_pair = {(row["instance_hash"], row["repeat"], row["side"]): row for row in rows}
    for row in rows:
        peer = by_pair[(row["instance_hash"], row["repeat"], "Q0")]
        redlines = list(row["correctness_redlines"])
        if (
            row["side"] == "candidate" and row["exact"] and peer["exact"]
            and row["objective"] is not None and peer["objective"] is not None
            and abs(float(row["objective"]) - float(peer["objective"])) > 2.0e-6
        ):
            redlines.append("objective_mismatch")
        canonical.append({
            "context_id": row["instance_hash"], "instance_hash": row["instance_hash"],
            "scale": row["scale"], "partition": "development_e2e",
            "arm": row["side"], "repeat": row["repeat"],
            "status": "COMPLETED" if row["exact"] else "TIMEOUT",
            "wall_sec": row["wall_sec"], "milestone_reached": row["exact"],
            "correctness_redlines": redlines,
        })
    return {
        "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_development_e2e_rows.v1",
        "execution_freeze": str(freeze_path), "execution_freeze_sha256": _sha256(freeze_path),
        "q0_exact_count_by_scale": exact["Q0"],
        "candidate_exact_count_by_scale": exact["candidate"],
        "rows": canonical,
        "raw_instance_rows": rows,
    }


def _formal_payload(rows, freeze_path):
    if any(int(row["repeat"]) != 0 for row in rows):
        raise SystemExit("formal evidence must be single-run")
    by_instance = defaultdict(dict)
    for row in rows:
        by_instance[row["instance_hash"]][row["side"]] = row
    canonical = []
    for pair in by_instance.values():
        if set(pair) != {"Q0", "candidate"}:
            raise SystemExit("formal paired evidence incomplete")
        objective_mismatch = bool(
            pair["Q0"]["exact"] and pair["candidate"]["exact"]
            and pair["Q0"]["objective"] is not None
            and pair["candidate"]["objective"] is not None
            and abs(float(pair["Q0"]["objective"]) - float(pair["candidate"]["objective"])) > 2.0e-6
        )
        for side, row in pair.items():
            redlines = list(row["correctness_redlines"])
            if objective_mismatch:
                redlines.append("objective_mismatch")
            canonical.append({**row, "correctness_redlines": redlines})
    return {
        "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_formal_full100_rows.v1",
        "execution_freeze": str(freeze_path), "execution_freeze_sha256": _sha256(freeze_path),
        "rows": canonical,
    }


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
        env[MANIFEST_ENV] = str(manifest)
        env[EVALUATION_ENV] = "1"
    return env


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_once(path, payload):
    path = Path(path)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != text:
        raise SystemExit(f"immutable full-BPC artifact drift:{path}")
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
