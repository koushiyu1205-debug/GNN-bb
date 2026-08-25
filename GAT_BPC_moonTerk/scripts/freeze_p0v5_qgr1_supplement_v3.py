#!/usr/bin/env python3
"""Freeze admitted-scale QGR1 train/calibration supplement before outcomes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import verify_portfolio_freezes  # noqa: E402
from lunar_ice_bpc.guidance.context_queue_portfolio_gates import rotate_blocked_arm_order  # noqa: E402


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_interaction_gat_queue_selector_v3_20260814"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    verify_portfolio_freezes(run_root, ROOT)
    if bool(_load(run_root / "state.json").get("terminal")):
        raise SystemExit("terminal V3 chain forbids QGR1 supplement freeze")
    decision_path = run_root / "qgr1_force_on.decision.json"
    decision = _load(decision_path)
    admitted = {
        int(scale) for scale, row in decision["scales"].items() if bool(row["admitted"])
    }
    corpus = _load(run_root / "corpus.freeze.json")
    config = _load(run_root / "config.freeze.json")
    tasks = []
    for context in corpus["rows"]:
        if (
            context["partition"] not in {"train", "calibration"}
            or int(context["scale"]) not in admitted
        ):
            continue
        common = {
            "context_id": context["context_id"],
            "instance_hash": context["instance_content_hash"],
            "scale": int(context["scale"]), "partition": context["partition"],
            "state_hash": context["state_hash"],
            "cap_sec": float(config["execution"]["replay_caps_sec"][str(context["scale"])]),
            "memory_limit_gb": float(config["execution"]["memory_limit_gb"]),
        }
        for block, order in enumerate(rotate_blocked_arm_order(
            context["state_hash"], arms=("Q0", "QGR1"), repeats=3
        )):
            for ordinal, arm in enumerate(order):
                tasks.append({
                    **common, "arm": arm, "execution_policy": arm,
                    "block": block, "ordinal_in_block": ordinal,
                })
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_matched_execution.v1",
        "status": "FROZEN_AFTER_FORCE_ON_BEFORE_QGR1_SUPPLEMENT_OUTCOMES",
        "mode": "qgr1_supplement", "admitted_scales": sorted(admitted),
        "single_native_process": True,
        "source_force_on_decision": str(decision_path),
        "source_force_on_decision_sha256": _sha256(decision_path),
        "tasks": tasks,
    }
    output = run_root / "matched_qgr1_supplement_execution.freeze.json"
    _write_once(output, payload)
    print(json.dumps({
        "admitted_scales": sorted(admitted), "tasks": len(tasks), "output": str(output)
    }, indent=2))
    return 0


def _write_once(path, payload):
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != encoded:
        raise SystemExit(f"immutable V3 QGR1 supplement schedule differs:{path}")
    if not path.exists(): path.write_text(encoded, encoding="utf-8")


def _load(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def _sha256(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__": raise SystemExit(main())
