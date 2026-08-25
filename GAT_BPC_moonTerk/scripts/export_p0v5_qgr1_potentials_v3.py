#!/usr/bin/env python3
"""Export deterministic QGR1 potentials for a frozen V3 execution schedule."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import verify_portfolio_freezes  # noqa: E402


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_interaction_gat_queue_selector_v3_20260814"
PREDICTOR = ROOT / "scripts/predict_p0v5_qgr1_residual_potential_v2.py"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--schedule", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    verify_portfolio_freezes(run_root, ROOT)
    if bool(_load(run_root / "state.json").get("terminal")):
        raise SystemExit("terminal V3 chain forbids QGR1 potential writer")
    checkpoint = args.checkpoint.resolve()
    schedule = (
        args.schedule.resolve() if args.schedule
        else run_root / "qgr1_force_on_execution.freeze.json"
    )
    schedule_payload = _load(schedule)
    corpus = _load(run_root / "corpus.freeze.json")
    by_context = {row["context_id"]: row for row in corpus["rows"]}
    context_ids = sorted({
        str(row["context_id"]) for row in schedule_payload["tasks"]
        if str(row["arm"]) == "QGR1"
    })
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    index = {}
    environment = dict(os.environ)
    for context_id in context_ids:
        context = by_context[context_id]
        output = output_dir / f"{context['state_hash']}.json"
        if not output.is_file():
            completed = subprocess.run([
                sys.executable, str(PREDICTOR),
                "--instance", str(context["instance_path"]),
                "--snapshot", str(context["snapshot_path"]),
                "--checkpoint", str(checkpoint), "--output", str(output),
                "--run-root", str(run_root),
            ], cwd=ROOT, env=environment, check=False)
            if completed.returncode != 0:
                raise SystemExit(f"QGR1 V3 potential export failed:{context_id}")
        payload = _load(output)
        if str(payload.get("source_state_hash")) != str(context["state_hash"]):
            raise SystemExit("QGR1 V3 potential state binding drift")
        index[str(context["state_hash"])] = str(output)
    result = {
        "schema_version": "lunar_ice_bpc.p0v5_qgr1_potential_index.v3",
        "source_schedule": str(schedule), "source_schedule_sha256": _sha256(schedule),
        "checkpoint": str(checkpoint), "checkpoint_sha256": _sha256(checkpoint),
        "by_state_hash": index,
    }
    index_path = output_dir / "potential_index.json"
    _write_once(index_path, result)
    print(json.dumps({"contexts": len(index), "index": str(index_path)}, indent=2))
    return 0


def _write_once(path, payload):
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != encoded:
        raise SystemExit(f"immutable V3 potential index differs:{path}")
    if not path.exists(): path.write_text(encoded, encoding="utf-8")


def _load(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def _sha256(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__": raise SystemExit(main())
