#!/usr/bin/env python3
"""Freeze QGR1 force-on or post-admission supplement execution before outcomes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import (  # noqa: E402
    verify_portfolio_freezes,
)
PREDICTOR = ROOT / "scripts/predict_p0v5_qgr1_potential.py"
DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_context_queue_portfolio_v1_20260807_r1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("force_on", "supplement"))
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--training-report", type=Path)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    _verify_freezes(run_root)
    config = _load(run_root / "config.freeze.json")
    corpus = _load(run_root / "corpus.freeze.json")
    report_path = (
        args.training_report.resolve() if args.training_report
        else run_root / "qgr1_training/training_report.json"
    )
    report = _load(report_path)
    _validate_training_report(report, report_path)
    arm_admission = _load(run_root / "arm_admission.decision.json")["decision"]
    if bool(arm_admission.get("correctness_chain_redline")):
        raise SystemExit("QGR1 execution forbidden after correctness redline")
    if args.mode == "supplement":
        decision = _load(run_root / "qgr1_force_on.decision.json")["decision"]
        if not bool(decision.get("admitted")):
            raise SystemExit("QGR1 supplement forbidden because force-on did not pass")

    contexts = _selected_contexts(corpus["rows"], mode=args.mode, run_root=run_root)
    potentials_dir = run_root / "qgr1_potentials"
    potentials_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = Path(report["checkpoint_path"]).resolve()
    by_state_hash = {}
    potential_rows = []
    for context in contexts:
        target = potentials_dir / f"{context['state_hash']}.json"
        if not target.is_file():
            completed = subprocess.run([
                sys.executable, str(PREDICTOR),
                "--instance", str(context["instance_path"]),
                "--snapshot", str(context["snapshot_path"]),
                "--checkpoint", str(checkpoint),
                "--output", str(target),
                "--run-root", str(run_root),
            ], cwd=ROOT, check=False)
            if completed.returncode != 0:
                raise SystemExit(f"QGR1 potential export failed:{context['state_hash']}")
        potential = _load(target)
        if (
            str(potential.get("source_state_hash")) != str(context["state_hash"])
            or float(potential.get("guidance_bucket_width")) != 1.0e-4
            or str(potential.get("checkpoint_sha256")) != _sha256(checkpoint)
        ):
            raise SystemExit("QGR1 potential binding drift")
        by_state_hash[str(context["state_hash"])] = str(target)
        potential_rows.append({
            "context_id": context["context_id"],
            "state_hash": context["state_hash"],
            "potential_path": str(target),
            "potential_sha256": _sha256(target),
        })

    index_name = f"qgr1_{args.mode}_potential_index.freeze.json"
    index = {
        "schema_version": "lunar_ice_bpc.p0v5_qgr1_potential_index.v1",
        "mode": args.mode,
        "frozen_before_corresponding_outcomes": True,
        "training_report": str(report_path),
        "training_report_sha256": _sha256(report_path),
        "checkpoint_sha256": _sha256(checkpoint),
        "by_state_hash": dict(sorted(by_state_hash.items())),
        "rows": potential_rows,
    }
    _write_once(run_root / index_name, index)
    schedule = _schedule(contexts, config, mode=args.mode)
    schedule.update({
        "corpus_freeze": str(run_root / "corpus.freeze.json"),
        "corpus_freeze_sha256": _sha256(run_root / "corpus.freeze.json"),
        "potential_index": str(run_root / index_name),
        "potential_index_sha256": _sha256(run_root / index_name),
        "checkpoint_sha256": _sha256(checkpoint),
    })
    schedule_name = f"qgr1_{args.mode}_execution.freeze.json"
    _write_once(run_root / schedule_name, schedule)
    _update_state(
        run_root,
        "QGR1_FORCE_ON_MATRIX" if args.mode == "force_on" else "QGR1_SUPPLEMENT_MATRIX",
    )
    print(json.dumps({
        "mode": args.mode,
        "context_count": len(contexts),
        "instance_count": len({row["instance_content_hash"] for row in contexts}),
        "task_count": len(schedule["tasks"]),
        "schedule": str(run_root / schedule_name),
        "potential_index": str(run_root / index_name),
    }, ensure_ascii=False, indent=2))
    return 0


def _selected_contexts(rows, *, mode, run_root):
    eligible = [
        dict(row) for row in rows
        if row["partition"] in {"train", "calibration"}
    ]
    if mode == "force_on":
        selected = []
        for scale in (30, 50):
            by_instance = {}
            for row in eligible:
                if int(row["scale"]) == scale and row["partition"] == "calibration":
                    by_instance.setdefault(row["instance_content_hash"], []).append(row)
            if len(by_instance) != 4:
                raise SystemExit(f"QGR1 force-on scale{scale} calibration instances != 4")
            for instance_hash, values in sorted(by_instance.items()):
                values.sort(key=lambda row: hashlib.sha256(
                    f"qgr1-force:{row['state_hash']}".encode()
                ).hexdigest())
                selected.append(values[0])
        if len(selected) != 8:
            raise SystemExit("QGR1 force-on must freeze exactly eight contexts")
        return selected
    force = _load(run_root / "qgr1_force_on_execution.freeze.json")
    force_ids = {str(task["context_id"]) for task in force["tasks"]}
    return [row for row in eligible if str(row["context_id"]) not in force_ids]


def _schedule(contexts, config, *, mode):
    repeats = int(config["execution"]["blocked_fresh_process_repeats"])
    tasks = []
    for context in contexts:
        arms = ("Q0", "QGR1") if mode == "force_on" else ("QGR1",)
        for block in range(repeats):
            order = sorted(arms, key=lambda arm: hashlib.sha256(
                f"{context['state_hash']}:{block}:{arm}".encode()
            ).hexdigest())
            for ordinal, arm in enumerate(order):
                tasks.append({
                    "context_id": context["context_id"],
                    "instance_content_hash": context["instance_content_hash"],
                    "scale": context["scale"],
                    "partition": context["partition"],
                    "state_hash": context["state_hash"],
                    "block": block,
                    "ordinal_in_block": ordinal,
                    "arm": arm,
                    "cap_sec": float(config["execution"]["replay_caps_sec"][str(context["scale"])]),
                    "memory_limit_gb": float(config["execution"]["memory_limit_gb"]),
                    "fresh_process": True,
                })
    return {
        "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_matched_execution.v1",
        "mode": f"qgr1_{mode}",
        "frozen_before_corresponding_outcomes": True,
        "single_native_process": True,
        "same_prefrozen_q0_milestone_required": True,
        "tasks": tasks,
    }


def _validate_training_report(report, path):
    checkpoint = Path(str(report.get("checkpoint_path") or "")).resolve()
    if (
        report.get("schema_version") != "lunar_ice_bpc.p0v5_qgr1_label_gat_training.v1"
        or not bool(dict(report.get("smoke_gate") or {}).get("passed"))
        or bool(report.get("activation_authority"))
        or not checkpoint.is_file()
        or _sha256(checkpoint) != str(report.get("checkpoint_sha256") or "")
    ):
        raise SystemExit(f"QGR1 training smoke/binding invalid:{path}")


def _verify_freezes(run_root):
    try:
        verify_portfolio_freezes(run_root, ROOT)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc


def _update_state(run_root, stage):
    path = run_root / "state.json"
    payload = _load(path)
    if bool(payload.get("terminal")):
        raise SystemExit("experiment chain is already terminal")
    payload.update({"current_stage": stage, "status": "READY"})
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_once(path, payload):
    path = Path(path)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != text:
        raise SystemExit(f"immutable QGR1 execution artifact drift:{path}")
    if not path.exists():
        path.write_text(text, encoding="utf-8")


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
