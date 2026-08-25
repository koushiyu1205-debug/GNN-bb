#!/usr/bin/env python3
"""Freeze V2 QGR1 force-on or full train/calibration matched execution."""

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
from lunar_ice_bpc.guidance.context_queue_portfolio_gates import (  # noqa: E402
    rotate_blocked_arm_order,
)


PREDICTOR = ROOT / "scripts/predict_p0v5_qgr1_residual_potential_v2.py"
DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_interaction_gat_queue_selector_v2_20260807"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("force_on", "full_matrix"))
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--training-report", type=Path)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    try:
        verify_portfolio_freezes(run_root, ROOT)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    if bool(_load(run_root / "state.json").get("terminal")):
        raise SystemExit("terminal chain forbids QGR1 execution freeze")
    config = _load(run_root / "config.freeze.json")
    corpus = _load(run_root / "corpus.freeze.json")
    report_path = (
        args.training_report.resolve() if args.training_report
        else run_root / "qgr1_training/training_report.json"
    )
    report = _load(report_path)
    checkpoint = _validate_training_report(report, report_path)
    admission = _load(run_root / "arm_admission.decision.json")["decision"]
    if bool(admission.get("correctness_chain_redline")):
        raise SystemExit("QGR1 execution forbidden after correctness redline")
    if args.mode == "full_matrix":
        force = _load(run_root / "qgr1_force_on.decision.json")["decision"]
        if not bool(force.get("admitted")):
            raise SystemExit("QGR1 full matrix forbidden because force-on failed")
    contexts = _contexts(corpus["rows"], args.mode)
    potentials_dir = run_root / "qgr1_residual_potentials_v2"
    potentials_dir.mkdir(parents=True, exist_ok=True)
    by_state_hash = {}
    potential_rows = []
    for context in contexts:
        output = potentials_dir / f"{context['state_hash']}.json"
        if not output.is_file():
            completed = subprocess.run([
                sys.executable, str(PREDICTOR),
                "--instance", str(context["instance_path"]),
                "--snapshot", str(context["snapshot_path"]),
                "--checkpoint", str(checkpoint),
                "--output", str(output),
                "--run-root", str(run_root),
            ], cwd=ROOT, check=False)
            if completed.returncode != 0:
                _record_potential_veto(
                    run_root,
                    reason="QGR1_POTENTIAL_ZERO_NONFINITE_OR_EXPORT_FAILED",
                    context=context,
                )
                return 2
        potential = _load(output)
        if (
            str(potential.get("source_state_hash")) != str(context["state_hash"])
            or float(potential.get("guidance_bucket_width") or 0.0) != 1.0e-4
            or str(potential.get("checkpoint_sha256")) != _sha256(checkpoint)
            or dict(potential.get("hard_zero_thresholds") or {})
            != dict(report["hard_zero_thresholds"])
        ):
            raise SystemExit("QGR1 V2 potential binding drift")
        by_state_hash[str(context["state_hash"])] = str(output)
        potential_rows.append({
            "context_id": context["context_id"],
            "state_hash": context["state_hash"],
            "potential_path": str(output),
            "potential_sha256": _sha256(output),
        })
    stem = f"qgr1_{args.mode}"
    index_path = run_root / f"{stem}_potential_index.freeze.json"
    _write_once(index_path, {
        "schema_version": "lunar_ice_bpc.p0v5_qgr1_potential_index.v1",
        "mode": args.mode,
        "frozen_before_corresponding_outcomes": True,
        "training_report": str(report_path),
        "training_report_sha256": _sha256(report_path),
        "checkpoint_sha256": _sha256(checkpoint),
        "hard_zero_thresholds": report["hard_zero_thresholds"],
        "by_state_hash": dict(sorted(by_state_hash.items())),
        "rows": potential_rows,
    })
    schedule = _schedule(contexts, config, mode=args.mode)
    schedule.update({
        "corpus_freeze": str(run_root / "corpus.freeze.json"),
        "corpus_freeze_sha256": _sha256(run_root / "corpus.freeze.json"),
        "potential_index": str(index_path),
        "potential_index_sha256": _sha256(index_path),
        "training_report_sha256": _sha256(report_path),
        "checkpoint_sha256": _sha256(checkpoint),
    })
    schedule_path = run_root / f"{stem}_execution.freeze.json"
    _write_once(schedule_path, schedule)
    _update_state(
        run_root,
        "QGR1_FORCE_ON_MATRIX" if args.mode == "force_on" else "QGR1_FULL_MATRIX",
    )
    print(json.dumps({
        "mode": args.mode,
        "context_count": len(contexts),
        "instance_count": len({row["instance_content_hash"] for row in contexts}),
        "task_count": len(schedule["tasks"]),
        "schedule": str(schedule_path),
        "potential_index": str(index_path),
    }, ensure_ascii=False, indent=2))
    return 0


def _contexts(rows, mode):
    eligible = [
        dict(row) for row in rows
        if row["partition"] in {"train", "calibration"}
    ]
    if mode == "full_matrix":
        return sorted(eligible, key=lambda row: (
            int(row["scale"]), str(row["instance_content_hash"]), str(row["state_hash"])
        ))
    selected = []
    for scale in (30, 50):
        by_instance = {}
        for row in eligible:
            if int(row["scale"]) == scale and row["partition"] == "calibration":
                by_instance.setdefault(row["instance_content_hash"], []).append(row)
        if len(by_instance) != 4:
            raise SystemExit(f"QGR1 V2 force-on scale{scale} calibration instances != 4")
        for instance_hash, values in sorted(by_instance.items()):
            values.sort(key=lambda row: hashlib.sha256(
                f"qgr1-v2-force:{row['state_hash']}".encode()
            ).hexdigest())
            selected.append(values[0])
    if len(selected) != 8 or len({row["instance_content_hash"] for row in selected}) != 8:
        raise SystemExit("QGR1 V2 force-on is not eight distinct instances")
    return selected


def _schedule(contexts, config, *, mode):
    tasks = []
    repeats = int(config["execution"]["blocked_fresh_process_repeats"])
    for context in contexts:
        for block, order in enumerate(rotate_blocked_arm_order(
            context["state_hash"], arms=("Q0", "QGR1"), repeats=repeats
        )):
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
        "v2_experiment_schema": "lunar_ice_bpc.p0v5_qgr1_residual_execution.v2",
        "mode": f"qgr1_{mode}",
        "frozen_before_corresponding_outcomes": True,
        "single_native_process": True,
        "same_prefrozen_q0_milestone_required": True,
        "tasks": tasks,
    }


def _validate_training_report(report, path):
    checkpoint = Path(str(report.get("checkpoint_path") or "")).resolve()
    if (
        report.get("schema_version") != "lunar_ice_bpc.p0v5_qgr1_residual_gat_training.v2"
        or not bool(dict(report.get("smoke_gate") or {}).get("passed"))
        or bool(report.get("activation_authority"))
        or not checkpoint.is_file()
        or _sha256(checkpoint) != str(report.get("checkpoint_sha256") or "")
        or dict(report.get("hard_zero_thresholds") or {}).get("quantile") != 0.75
    ):
        raise SystemExit(f"QGR1 V2 training smoke/binding invalid:{path}")
    return checkpoint


def _update_state(run_root, stage):
    path = run_root / "state.json"
    payload = _load(path)
    payload.update({"current_stage": stage, "status": "READY"})
    path.write_text(json.dumps(
        payload, ensure_ascii=False, indent=2, sort_keys=True
    ) + "\n", encoding="utf-8")


def _record_potential_veto(run_root, *, reason, context):
    admission = _load(run_root / "arm_admission.decision.json")["decision"]
    mask = dict(admission["arm_scale_mask"])
    mask["QGR1"] = []
    veto = {
        key: sorted(set((*values, "QGR1")))
        for key, values in admission["forced_veto_arms_by_scale"].items()
    }
    decision = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_qgr1_potential_veto.v2",
        "admitted": False,
        "hard_veto": True,
        "force_on_executed": False,
        "reason": str(reason),
        "failed_context_id": str(context["context_id"]),
        "arm_scale_mask": mask,
        "forced_veto_arms_by_scale": veto,
        "performance_failure_is_permanent_arm_veto": True,
        "qgr1_hyperparameter_reselection_forbidden": True,
        "correctness_redlines": [],
    }
    _write_once(run_root / "qgr1_force_on.decision.json", {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_qgr1_force_on_decision.v2",
        "stage": "qgr1_force_on",
        "decision": decision,
        "development_only": True,
        "deployment_authorized": False,
        "production_switch_authorized": False,
    })
    _update_state(run_root, "PORTFOLIO_ORACLE")


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_once(path, payload):
    path = Path(path)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != text:
        raise SystemExit(f"immutable QGR1 V2 execution drift:{path}")
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
