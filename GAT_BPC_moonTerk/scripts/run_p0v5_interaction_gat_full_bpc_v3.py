#!/usr/bin/env python3
"""Run sequential paired development/formal full-BPC evidence for V3."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
import scripts.run_p0v5_context_queue_portfolio_full_bpc as base  # noqa: E402
import scripts.run_p0v5_interaction_gat_full_bpc_v2 as v2  # noqa: E402
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import verify_portfolio_freezes  # noqa: E402
from lunar_ice_bpc.guidance.interaction_gat_queue_runtime_v3 import (  # noqa: E402
    INTERACTION_GAT_EVALUATION_ENV_V3, INTERACTION_GAT_MANIFEST_ENV_V3,
)


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_interaction_gat_queue_selector_v3_20260814"
BOOTSTRAP = ROOT / "scripts/run_lunar_ice_interaction_gat_acceptance_v3.py"
FINALIZER = ROOT / "scripts/finalize_p0v5_interaction_gat_stage_v3.py"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("development_e2e", "formal_full100"))
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    verify_portfolio_freezes(run_root, ROOT)
    if bool(_load(run_root / "state.json").get("terminal")):
        raise SystemExit("terminal V3 chain forbids full-BPC execution")
    config = _load(run_root / "config.freeze.json")
    manifest = run_root / "research_candidate.manifest.json"
    if not manifest.is_file():
        raise SystemExit("V3 research candidate manifest is missing")
    if args.mode == "development_e2e":
        heldout = _load(run_root / "selector_heldout.decision.json")
        if not bool(dict(heldout.get("gate") or {}).get("passed")):
            raise SystemExit("development E2E forbidden before heldout pass")
        instances = _development_instances_v3(run_root)
        repeats = 3
    else:
        development = _load(run_root / "development_e2e.decision.json")
        if not bool(development.get("passed")):
            raise SystemExit("formal full100 forbidden before development E2E pass")
        candidate = _load(run_root / "research_candidate.freeze.json")
        if str(candidate.get("manifest_sha256")) != base._sha256(manifest):
            raise SystemExit("formal V3 candidate manifest drift")
        instances = base._formal_instances(config)
        repeats = 1
    schedule = base._schedule(
        args.mode, instances, repeats=repeats, cap_sec=3600.0,
        manifest=manifest, run_root=run_root,
    )
    schedule["schema_version"] = "lunar_ice_bpc.p0v5_interaction_gat_full_bpc_execution.v3"
    schedule["runtime_bootstrap"] = str(BOOTSTRAP)
    schedule["runtime_bootstrap_sha256"] = base._sha256(BOOTSTRAP)
    freeze_path = run_root / f"{args.mode}_execution.freeze.json"
    base._write_once(freeze_path, schedule)
    # Reuse V2's audited parsers/telemetry walker, but bind only V3 bootstrap
    # and environment names.  No V2 artifact or exact source is modified.
    v2.BOOTSTRAP = BOOTSTRAP
    v2.INTERACTION_GAT_MANIFEST_ENV = INTERACTION_GAT_MANIFEST_ENV_V3
    v2.INTERACTION_GAT_EVALUATION_ENV = INTERACTION_GAT_EVALUATION_ENV_V3
    evidence = []
    output_root = run_root / args.mode
    for task in schedule["tasks"]:
        task_root = output_root / str(task["task_id"])
        parsed_path = task_root / "canonical_instance_row.json"
        if not parsed_path.is_file():
            v2._run_one(task, task_root, config, manifest)
            row = v2._parse_one(task_root, task, cap_sec=3600.0)
            base._write_once(parsed_path, row)
        evidence.append(_load(parsed_path))
    payload = (
        v2._development_payload(evidence, freeze_path)
        if args.mode == "development_e2e" else v2._formal_payload(evidence, freeze_path)
    )
    payload["schema_version"] = f"lunar_ice_bpc.p0v5_interaction_gat_{args.mode}_rows.v3"
    output = run_root / f"{args.mode}_rows.json"
    base._write_once(output, payload)
    completed = subprocess.run([
        sys.executable, str(FINALIZER), args.mode,
        "--run-root", str(run_root), "--matrix", str(output),
    ], cwd=ROOT, check=False)
    print(json.dumps({
        "mode": args.mode, "task_count": len(evidence), "result": str(output),
        "single_native_process": True, "exact_source_modified": False,
        "finalizer_returncode": completed.returncode,
    }, ensure_ascii=False, indent=2))
    return int(completed.returncode)


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _development_instances_v3(run_root):
    corpus = _load(run_root / "corpus.freeze.json")
    by_instance = {}
    for row in corpus["rows"]:
        if row["partition"] == "development_e2e":
            by_instance.setdefault(str(row["instance_content_hash"]), {
                "scale": int(row["scale"]),
                "instance_path": str(row["instance_path"]),
                "instance_content_hash": str(row["instance_content_hash"]),
            })
    rows = list(by_instance.values())
    if {scale: sum(row["scale"] == scale for row in rows) for scale in (30, 50)} != {30: 3, 50: 3}:
        raise SystemExit("V3 development E2E split is not 3+3 instances")
    return rows


if __name__ == "__main__":
    raise SystemExit(main())
