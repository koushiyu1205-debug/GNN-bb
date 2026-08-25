#!/usr/bin/env python3
"""Run the gated real-map V4 GAT-first pipeline through formal full20."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs/p0v5_qg2_v4_realmap_gat_first_20260806"
BUILD = ROOT / "build/native-spprc-bidirectional-feasibility-v1"
COLLECTION_STATE = RUN / "realmap_v4_collection_state.json"
INDEX = RUN / "realmap_v4_snapshot_index.json"
FREEZE = RUN / "realmap_v4_oracle_execution_freeze.json"
SPLIT = RUN / "realmap_v4_instance_split.json"
ORACLE_DIR = RUN / "oracle_realmap_v4"
ORACLE = RUN / "oracle_realmap_v4.json"
TRAIN_GATE = RUN / "realmap_v4_training_gate.json"
AUTHORIZED_ORACLE = RUN / "oracle_realmap_v4_training_view.json"
RANKER_DIR = RUN / "ranker_gat_v4"
RANKER = RANKER_DIR / "training_report.json"
ATTRIBUTION = RUN / "ranker_gat_v4_attribution.json"
FORCE_SCREEN_DIR = RUN / "force_on_train_screen_v4"
FORCE_TRAIN = FORCE_SCREEN_DIR / "force_on_train.json"
FORCE_CALIBRATION_DIR = RUN / "force_on_calibration_v4"
FORCE_CALIBRATION = FORCE_CALIBRATION_DIR / "force_on_calibration.json"
FORCE_HELDOUT_DIR = RUN / "force_on_heldout_v4"
FORCE_HELDOUT = FORCE_HELDOUT_DIR / "force_on_heldout.json"
MATCHED_DIR = RUN / "matched_arms_v4"
MATCHED = MATCHED_DIR / "matched_arms.json"
SELECTOR_DIR = RUN / "selector_gat_v4"
SELECTOR = SELECTOR_DIR / "training_report.json"
SELECTOR_ATTRIBUTION = RUN / "selector_gat_v4_attribution.json"
FRESH_CAL_DIR = RUN / "selector_gat_fresh_calibration_v4"
FRESH_CAL = FRESH_CAL_DIR / "fresh_calibration.json"
FRESH_HELDOUT_DIR = RUN / "selector_gat_fresh_heldout_v4"
FRESH_HELDOUT = FRESH_HELDOUT_DIR / "fresh_heldout.json"
STATE = RUN / "realmap_v4_gat_first_state.json"
EVENTS = RUN / "realmap_v4_pipeline_events.jsonl"
SCHEDULED_ORACLE_CONTEXTS = 120
SCHEDULED_ORACLE_CONTEXTS_PER_SCALE = 60
COLLECTION_PREFLIGHT_READY_STATUSES = frozenset({
    "ORACLE_PREFLIGHT_READY",
    "ORACLE_PREFLIGHT_READY_AFTER_TREE_SUPPLEMENT",
})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--oracle-contexts", type=int, default=SCHEDULED_ORACLE_CONTEXTS
    )
    parser.add_argument(
        "--oracle-contexts-per-scale", type=int,
        default=SCHEDULED_ORACLE_CONTEXTS_PER_SCALE,
    )
    args = parser.parse_args()
    _validate_collection()
    _validate_scheduled_oracle_budget(
        contexts=int(args.oracle_contexts),
        contexts_per_scale=int(args.oracle_contexts_per_scale),
    )
    env = _environment()

    _state("RUNNING_BOUNDED_ORACLE")
    if not ORACLE.is_file():
        result = _run([
            sys.executable, str(ROOT / "scripts/run_p0v5_qg2_bounded_oracle.py"),
            "--state-index", str(INDEX),
            "--instance-split", str(SPLIT),
            "--output-dir", str(ORACLE_DIR),
            "--output", str(ORACLE),
            "--execution-freeze", str(FREEZE),
            "--max-contexts", str(int(args.oracle_contexts)),
            "--max-contexts-per-scale", str(int(args.oracle_contexts_per_scale)),
            "--repeats", "3",
            "--scale30-wall-sec", "300",
            "--scale50-wall-sec", "600",
            "--memory-limit-gb", "10.867",
        ], env=env, accepted={0, 2})
        if result not in {0, 2} or not ORACLE.is_file():
            return _stop("ORACLE_EXECUTION_FAILED", result)

    _state("RUNNING_TRAINING_ONLY_AUTHORITY")
    if not AUTHORIZED_ORACLE.is_file():
        result = _run([
            sys.executable,
            str(ROOT / "scripts/authorize_p0v5_qg2_realmap_v4_training.py"),
            "--oracle-summary", str(ORACLE),
            "--instance-split", str(SPLIT),
            "--gate-output", str(TRAIN_GATE),
            "--authorized-oracle-output", str(AUTHORIZED_ORACLE),
        ], env=env, accepted={0, 2})
        if result != 0 or not AUTHORIZED_ORACLE.is_file():
            return _stop("TRAINING_DATA_GATE_FAILED", result)

    _state("TRAINING_LABEL_GAT")
    if not RANKER.is_file():
        result = _run([
            sys.executable, str(ROOT / "scripts/train_p0v5_qg2_v3_rankers.py"),
            "--oracle-summary", str(AUTHORIZED_ORACLE),
            "--instance-split", str(SPLIT),
            "--output-dir", str(RANKER_DIR),
            "--models", "gat",
            "--epochs", "40",
            "--early-stopping-patience", "8",
        ], env=env)
        if result != 0 or not RANKER.is_file():
            return _stop("LABEL_GAT_TRAINING_FAILED", result)

    _state("RUNNING_LABEL_GAT_ATTRIBUTION")
    if not ATTRIBUTION.is_file():
        result = _run([
            sys.executable,
            str(ROOT / "scripts/analyze_p0v5_qg2_v3_gat_attribution.py"),
            "--training-report", str(RANKER),
            "--oracle-summary", str(AUTHORIZED_ORACLE),
            "--output", str(ATTRIBUTION),
            "--partitions", "calibration",
        ], env=env)
        if result != 0:
            return _stop("LABEL_GAT_ATTRIBUTION_FAILED", result)

    _state("RUNNING_LABEL_GAT_FORCE_ON_TRAIN_SCREEN")
    if not FORCE_TRAIN.is_file():
        result = _run_force(
            partition="train", output_dir=FORCE_SCREEN_DIR,
            output=FORCE_TRAIN, maximum_per_scale=5, env=env,
        )
        if result != 0:
            return _stop("LABEL_GAT_FORCE_SCREEN_FAILED", result)
    force_train_report = _load(FORCE_TRAIN)
    expand_qg2_train = _qg2_train_screen_warrants_expansion(
        force_train_report
    )
    qg2_positive = False
    force_reports = [FORCE_TRAIN]
    if expand_qg2_train:
        _state("EXPANDING_SIGNAL_BEARING_QG2_FORCE_ON_TRAIN")
        result = _run_force(
            partition="train", output_dir=FORCE_SCREEN_DIR,
            output=FORCE_TRAIN, maximum_per_scale=0, env=env,
        )
        if result != 0:
            return _stop("QG2_TRAIN_FORCE_EXPANSION_FAILED", result)
        qg2_positive = _qg2_train_support(_load(FORCE_TRAIN))
    if qg2_positive:
        _state("EXPANDING_TRAIN_SUPPORTED_QG2_EVALUATION_MATRIX")
        for partition, directory, output in (
            ("calibration", FORCE_CALIBRATION_DIR, FORCE_CALIBRATION),
            ("heldout", FORCE_HELDOUT_DIR, FORCE_HELDOUT),
        ):
            if not output.is_file():
                result = _run_force(
                    partition=partition, output_dir=directory,
                    output=output, maximum_per_scale=0, env=env,
                )
                if result != 0:
                    return _stop(f"QG2_{partition.upper()}_FORCE_FAILED", result)
            force_reports.append(output)

    _state("RUNNING_REPLICATED_QD1_QB1_MATRIX", qg2_positive=qg2_positive)
    if not MATCHED.is_file():
        result = _run([
            sys.executable,
            str(ROOT / "scripts/collect_p0v5_qg2_realmap_v4_matched_arms.py"),
            "--oracle-summary", str(AUTHORIZED_ORACLE),
            "--instance-split", str(SPLIT),
            "--output-dir", str(MATCHED_DIR),
            "--output", str(MATCHED),
            "--repeats", "3",
            "--scale30-wall-sec", "300",
            "--scale50-wall-sec", "600",
            "--memory-limit-gb", "10.867",
        ], env=env)
        if result != 0 or not MATCHED.is_file():
            return _stop("MATCHED_ARM_MATRIX_FAILED", result)

    _state("TRAINING_CONTEXT_GAT", qg2_positive=qg2_positive)
    if not SELECTOR.is_file():
        command = [
            sys.executable,
            str(ROOT / "scripts/train_p0v5_qg2_v3_gat_arm_selector.py"),
            "--oracle-summary", str(AUTHORIZED_ORACLE),
            "--ranker-training-report", str(RANKER),
            "--matched-arm-report", str(MATCHED),
            "--output-dir", str(SELECTOR_DIR),
            "--model-kind", "gat",
            "--epochs", "200",
            "--early-stopping-patience", "25",
        ]
        for report in force_reports:
            command.extend(("--qg2-force-on-report", str(report)))
        result = _run(command, env=env)
        if result != 0 or not SELECTOR.is_file():
            return _stop("CONTEXT_GAT_TRAINING_FAILED", result)

    _state("RUNNING_CONTEXT_GAT_ATTRIBUTION", qg2_positive=qg2_positive)
    if not SELECTOR_ATTRIBUTION.is_file():
        result = _run([
            sys.executable,
            str(ROOT / "scripts/analyze_p0v5_qg2_v3_selector_attribution.py"),
            "--selector-training-report", str(SELECTOR),
            "--output", str(SELECTOR_ATTRIBUTION),
            "--partitions", "calibration",
        ], env=env)
        if result != 0:
            return _stop("CONTEXT_GAT_ATTRIBUTION_FAILED", result)

    for partition, directory, output in (
        ("calibration", FRESH_CAL_DIR, FRESH_CAL),
        ("heldout", FRESH_HELDOUT_DIR, FRESH_HELDOUT),
    ):
        _state(f"RUNNING_CONTEXT_GAT_FRESH_{partition.upper()}")
        if not output.is_file():
            result = _run([
                sys.executable,
                str(ROOT / "scripts/evaluate_p0v5_qg2_v3_gat_selector_fresh.py"),
                "--selector-training-report", str(SELECTOR),
                "--output-dir", str(directory),
                "--output", str(output),
                "--partition", partition,
                "--repeats", "3",
                "--scale30-wall-sec", "300",
                "--scale50-wall-sec", "600",
                "--memory-limit-gb", "10.867",
            ], env=env, accepted={0, 3})
            if result not in {0, 3} or not output.is_file():
                return _stop(f"FRESH_{partition.upper()}_FAILED", result)

    heldout = _load(FRESH_HELDOUT)
    overall = dict((heldout.get("summary") or {}).get("overall") or {})
    heldout30 = dict((heldout.get("summary") or {}).get("scale30") or {})
    heldout50 = dict((heldout.get("summary") or {}).get("scale50") or {})
    passed = bool(
        overall.get("all_safe")
        and int(overall.get("activated_count") or 0) > 0
        and float(overall.get("net_geomean_ratio") or 1.0) < 1.0
        and float(heldout30.get("net_geomean_ratio") or 1.0) <= 1.0
        and float(heldout50.get("net_geomean_ratio") or 1.0) <= 1.0
    )
    if not passed:
        _state(
            "GAT_FRESH_NOT_POSITIVE_STOP_BEFORE_CONTROLS",
            qg2_positive=qg2_positive,
            heldout_summary=heldout.get("summary"),
            controls_started=False,
        )
        return 2

    # Persist the GAT conclusion before starting either control.  This makes
    # the GAT result immediately observable and keeps MLP/Linear from delaying
    # or influencing the decision to continue the GAT candidate.
    _state(
        "GAT_FRESH_POSITIVE_RUNNING_POST_GAT_CONTROLS",
        qg2_positive=qg2_positive,
        heldout_summary=heldout.get("summary"),
        controls_started=True,
    )
    controls = _run([
        sys.executable,
        str(ROOT / "scripts/run_p0v5_qg2_realmap_v4_controls_after_gat.py"),
        "--scale30-wall-sec", "300",
        "--scale50-wall-sec", "600",
        "--memory-limit-gb", "10.867",
    ], env=env)
    if controls != 0:
        return _stop("POST_GAT_CONTROLS_FAILED", controls)
    _state(
        "GAT_AND_CONTROLS_COMPLETE_RUNNING_DEVELOPMENT_E2E",
        qg2_positive=qg2_positive,
        heldout_summary=heldout.get("summary"),
        controls_started=True,
        controls_complete=True,
    )
    e2e = _run([
        sys.executable,
        str(ROOT / "scripts/run_p0v5_qg2_realmap_v4_development_e2e.py"),
    ], env=env)
    if e2e != 0:
        return _stop("DEVELOPMENT_E2E_FAILED", e2e)
    _state(
        "DEVELOPMENT_E2E_PASSED_RUNNING_FORMAL_FULL20",
        qg2_positive=qg2_positive,
        heldout_summary=heldout.get("summary"),
        controls_complete=True,
    )
    formal = _run([
        sys.executable,
        str(ROOT / "scripts/run_p0v5_qg2_realmap_v4_formal_full20.py"),
    ], env=env)
    if formal != 0:
        return _stop("FORMAL_FULL20_FAILED", formal)
    _state(
        "FORMAL_FULL20_PASSED_RUNNING_FINAL_CANDIDATE_AUDIT",
        qg2_positive=qg2_positive,
        heldout_summary=heldout.get("summary"),
        controls_complete=True,
        production_switch_performed=False,
    )
    audit = _run([
        sys.executable,
        str(ROOT / "scripts/audit_p0v5_qg2_realmap_v4_completion.py"),
    ], env=env)
    if audit != 0:
        return _stop("FINAL_CANDIDATE_AUDIT_FAILED", audit)
    finalized = _run([
        sys.executable,
        str(ROOT / "scripts/finalize_p0v5_qg2_realmap_v4_candidate.py"),
    ], env=env)
    if finalized != 0:
        return _stop("FINAL_CANDIDATE_FREEZE_FAILED", finalized)
    _state(
        "P0V5_QG2_V4_FINAL_CANDIDATE_FROZEN",
        qg2_positive=qg2_positive,
        heldout_summary=heldout.get("summary"),
        controls_complete=True,
        production_switch_performed=False,
    )
    return 0


def _run_force(*, partition, output_dir, output, maximum_per_scale, env):
    return _run([
        sys.executable,
        str(ROOT / "scripts/calibrate_p0v5_qg2_v3_gat_force_on.py"),
        "--training-report", str(RANKER),
        "--oracle-summary", str(AUTHORIZED_ORACLE),
        "--output-dir", str(output_dir),
        "--output", str(output),
        "--partition", partition,
        "--repeats", "3",
        "--maximum-contexts-per-scale", str(int(maximum_per_scale)),
        "--scale30-wall-sec", "300",
        "--scale50-wall-sec", "600",
        "--memory-limit-gb", "10.867",
    ], env=env)


def _qg2_train_support(report):
    rows = _qg2_train_rows(report)
    beneficial = sum(_qg2_row_is_beneficial(row) for row in rows)
    return len(rows) >= 5 and beneficial >= 2


def _qg2_train_screen_warrants_expansion(report):
    """Allow one bounded full-train expansion after any positive signal."""

    return any(
        _qg2_row_is_beneficial(row) for row in _qg2_train_rows(report)
    )


def _qg2_train_rows(report):
    return [
        row for row in report.get("records") or ()
        if str(row.get("partition") or "") == "train"
        and bool(row.get("safe")) and bool(row.get("action_eligible"))
        and str(row.get("comparison_class") or "") not in {
            "both_censored", "literal_q0_veto", "replicate_class_disagreement",
        }
    ]


def _qg2_row_is_beneficial(row):
    return bool(row.get("beneficial")) or str(
        row.get("comparison_class") or ""
    ) == "gat_beneficial_censor"


def _validate_collection():
    required = (COLLECTION_STATE, INDEX, FREEZE, SPLIT)
    if any(not path.is_file() for path in required):
        raise SystemExit("real-map V4 collection/preflight is incomplete")
    state = _load(COLLECTION_STATE)
    if str(state.get("status") or "") not in (
        COLLECTION_PREFLIGHT_READY_STATUSES
    ):
        raise SystemExit("real-map V4 collection has not reached Oracle preflight")


def _validate_scheduled_oracle_budget(*, contexts, contexts_per_scale):
    """Refuse an invocation that differs from the pre-outcome V4 schedule."""

    freeze = _load(FREEZE)
    frozen_contexts = int(freeze.get("scheduled_oracle_contexts") or 0)
    frozen_per_scale = int(
        freeze.get("scheduled_oracle_contexts_per_scale") or 0
    )
    if not bool(freeze.get("oracle_schedule_must_match_exactly")):
        raise SystemExit("real-map V4 Oracle schedule is not exact-bound")
    if (frozen_contexts, frozen_per_scale) != (
        SCHEDULED_ORACLE_CONTEXTS,
        SCHEDULED_ORACLE_CONTEXTS_PER_SCALE,
    ):
        raise SystemExit("real-map V4 frozen Oracle schedule drift")
    if (int(contexts), int(contexts_per_scale)) != (
        frozen_contexts, frozen_per_scale
    ):
        raise SystemExit("real-map V4 Oracle invocation budget drift")


def _run(command, *, env, accepted={0}):
    completed = subprocess.run(command, cwd=ROOT, env=env, check=False)
    return completed.returncode if completed.returncode in accepted else completed.returncode


def _stop(status, returncode):
    _state(status, returncode=returncode)
    return int(returncode or 2)


def _environment():
    env = dict(os.environ)
    for key in (
        "LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST",
        "LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE",
        "LUNAR_ICE_P0V5_QG2_V3_SELECTOR_MANIFEST",
        "LUNAR_ICE_P0V5_QG2_V3_SELECTOR_EVALUATION_MODE",
        "LUNAR_ICE_P0V5_QG2_FALLBACK_SNAPSHOT_DIR",
    ):
        env.pop(key, None)
    env["PYTHONPATH"] = f"{ROOT / 'src'}:{BUILD}"
    return env


def _state(status, **extra):
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_realmap_v4_gat_first_state.v1",
        "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": status,
        **extra,
    }
    _write(STATE, payload)
    with EVENTS.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


if __name__ == "__main__":
    raise SystemExit(main())
