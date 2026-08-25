#!/usr/bin/env python3
"""Run the clean Q0-trace -> Label-GAT -> force-on pipeline."""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs/p0v5_qg2_v5_trace_first_20260807"
SOURCE_RUN = ROOT / "runs/p0v5_qg2_v4_realmap_gat_first_20260806"
INDEX = SOURCE_RUN / "realmap_v4_snapshot_index.json"
SPLIT = SOURCE_RUN / "realmap_v4_instance_split.json"
EXACT_FREEZE = SOURCE_RUN / "realmap_v4_oracle_execution_freeze.json"
SOURCE_ORACLE_DIR = SOURCE_RUN / "oracle_realmap_v4"
TRACE_DIR = RUN / "trace_corpus"
TRACE_CORPUS = RUN / "trace_supervision_corpus.json"
TRAINING_VIEW = RUN / "trace_training_view.json"
SELECTION_FREEZE = RUN / "trace_selection_freeze.json"
SMOKE_DIR = RUN / "label_gat_smoke"
SMOKE_REPORT = SMOKE_DIR / "training_report.json"
TRAINING_FREEZE = RUN / "label_gat_training_freeze.json"
GAT_DIR = RUN / "label_gat"
GAT_REPORT = GAT_DIR / "training_report.json"
ATTRIBUTION = RUN / "label_gat_attribution.json"
FORCE_DIR = RUN / "label_gat_force_on_train_screen"
FORCE_REPORT = FORCE_DIR / "force_on_train.json"
STATE = RUN / "PIPELINE_STATE.json"
EVENTS = RUN / "events.jsonl"

COLLECTOR = ROOT / "scripts/collect_p0v5_qg2_v5_trace_corpus.py"
TRAINER = ROOT / "scripts/train_p0v5_qg2_v5_label_gat.py"
ATTRIBUTION_SCRIPT = (
    ROOT / "scripts/analyze_p0v5_qg2_v4_instance_balanced_gat_attribution.py"
)
FORCE_SCRIPT = (
    ROOT / "scripts/calibrate_p0v5_qg2_v4_instance_balanced_gat_force_on.py"
)


def main() -> int:
    RUN.mkdir(parents=True, exist_ok=True)
    if not TRACE_CORPUS.is_file() or not TRAINING_VIEW.is_file():
        _state("COLLECTING_Q0_TRACE_SUPERVISION")
        result = _run([
            sys.executable, str(COLLECTOR),
            "--state-index", str(INDEX),
            "--instance-split", str(SPLIT),
            "--execution-freeze", str(EXACT_FREEZE),
            "--source-oracle-dir", str(SOURCE_ORACLE_DIR),
            "--output-dir", str(TRACE_DIR),
            "--output", str(TRACE_CORPUS),
            "--training-view-output", str(TRAINING_VIEW),
            "--selection-freeze", str(SELECTION_FREEZE),
            "--scale30-contexts", "33",
            "--scale50-contexts", "20",
            "--scale30-wall-sec", "300",
            "--scale50-wall-sec", "600",
            "--memory-limit-gb", "10.867",
        ], accepted={0})
        if result != 0:
            return _stop("TRACE_SUPERVISION_COLLECTION_FAILED", result)

    _state("RUNNING_ONE_EPOCH_LABEL_GAT_SMOKE")
    result = _run([
        sys.executable, str(TRAINER),
        "--trace-corpus", str(TRACE_CORPUS),
        "--training-view", str(TRAINING_VIEW),
        "--instance-split", str(SPLIT),
        "--output-dir", str(SMOKE_DIR),
        "--epochs", "1",
        "--early-stopping-patience", "1",
        "--max-pairs-per-context", "256",
        "--seed", "20260807",
    ], accepted={0})
    if result != 0 or not SMOKE_REPORT.is_file():
        return _stop("LABEL_GAT_SMOKE_FAILED", result)

    _ensure_training_freeze()
    _validate_training_freeze()
    _state("TRAINING_LABEL_GAT_FORMAL")
    result = _run([
        sys.executable, str(TRAINER),
        "--trace-corpus", str(TRACE_CORPUS),
        "--training-view", str(TRAINING_VIEW),
        "--instance-split", str(SPLIT),
        "--output-dir", str(GAT_DIR),
        "--epochs", "40",
        "--early-stopping-patience", "8",
        "--max-pairs-per-context", "4096",
        "--learning-rate", "0.002",
        "--seed", "20260807",
    ], accepted={0})
    _validate_training_freeze()
    if result != 0 or not GAT_REPORT.is_file():
        return _stop("LABEL_GAT_FORMAL_TRAINING_FAILED", result)

    _state("RUNNING_LABEL_GAT_ATTRIBUTION")
    if not ATTRIBUTION.is_file():
        result = _run([
            sys.executable, str(ATTRIBUTION_SCRIPT),
            "--training-report", str(GAT_REPORT),
            "--oracle-summary", str(TRAINING_VIEW),
            "--output", str(ATTRIBUTION),
            "--partitions", "calibration",
        ], accepted={0})
        if result != 0:
            return _stop("LABEL_GAT_ATTRIBUTION_FAILED", result)

    _state("RUNNING_LABEL_GAT_FORCE_ON_TRAIN_SCREEN")
    if not FORCE_REPORT.is_file():
        result = _run([
            sys.executable, str(FORCE_SCRIPT),
            "--training-report", str(GAT_REPORT),
            "--oracle-summary", str(TRAINING_VIEW),
            "--output-dir", str(FORCE_DIR),
            "--output", str(FORCE_REPORT),
            "--partition", "train",
            "--repeats", "3",
            "--maximum-contexts-per-scale", "5",
            "--scale30-wall-sec", "300",
            "--scale50-wall-sec", "600",
            "--memory-limit-gb", "10.867",
        ], accepted={0})
        if result != 0:
            return _stop("LABEL_GAT_FORCE_ON_SCREEN_FAILED", result)

    _state(
        "LABEL_GAT_FORCE_ON_SCREEN_COMPLETE",
        next_action=(
            "evaluate_cross_instance_qg2_signal_then_collect_qd1_qb1_matrix"
        ),
        mlp_or_linear_started=False,
    )
    return 0


def _ensure_training_freeze() -> None:
    if not TRAINING_FREEZE.is_file() and GAT_REPORT.exists():
        raise SystemExit(
            "formal Label-GAT output exists before the training freeze"
        )
    source_paths = (
        Path(__file__).resolve(), COLLECTOR, TRAINER,
        ROOT / "scripts/train_p0v5_qg2_v4_instance_balanced_rankers.py",
        ROOT / "scripts/train_p0v5_qg2_v3_rankers.py",
        ROOT / "src/lunar_ice_bpc/guidance/instance_balanced_learning.py",
        ROOT / "src/lunar_ice_bpc/guidance/proof_queue_label_state_gat_v3.py",
        ROOT / "src/lunar_ice_bpc/guidance/qg2_admission_supervision_v3.py",
        ATTRIBUTION_SCRIPT, FORCE_SCRIPT,
        ROOT / "tests/test_p0v5_qg2_v5_trace_first.py",
        ROOT / "scripts/finalize_p0v5_qg2_v5_bounded_trace_corpus.py",
    )
    artifacts = (
        TRACE_CORPUS, TRAINING_VIEW, SELECTION_FREEZE, SPLIT, EXACT_FREEZE,
        SMOKE_REPORT,
        SMOKE_DIR / "training_curve.jsonl",
    )
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_label_gat_training_freeze.v1",
        "created_after_one_epoch_smoke": True,
        "created_before_formal_training": True,
        "development_only": True,
        "deployable": False,
        "model_order": ["label_gat", "context_gat", "mlp", "linear"],
        "random_or_leaked_qo2_on_critical_path": False,
        "source_sha256": {str(path): _sha256(path) for path in source_paths},
        "artifact_sha256": {str(path): _sha256(path) for path in artifacts},
        "production_switch_authorized": False,
    }
    if TRAINING_FREEZE.is_file():
        if _load(TRAINING_FREEZE) != payload:
            raise SystemExit("Label-GAT training freeze drift")
    else:
        _atomic_write(TRAINING_FREEZE, payload)


def _validate_training_freeze() -> None:
    payload = _load(TRAINING_FREEZE)
    if (
        payload.get("schema_version")
        != "lunar_ice_bpc.p0v5_qg2_label_gat_training_freeze.v1"
        or not bool(payload.get("created_after_one_epoch_smoke"))
        or bool(payload.get("deployable"))
        or list(payload.get("model_order") or ())[:2]
        != ["label_gat", "context_gat"]
    ):
        raise SystemExit("Label-GAT training freeze contract failed")
    for key in ("source_sha256", "artifact_sha256"):
        for raw, expected in dict(payload.get(key) or {}).items():
            path = Path(raw)
            if not path.is_file() or _sha256(path) != str(expected):
                raise SystemExit(f"Label-GAT training freeze drift:{path}")


def _run(command, *, accepted: set[int]) -> int:
    completed = subprocess.run(
        command, cwd=ROOT, env=_environment(), check=False
    )
    if int(completed.returncode) not in accepted:
        return int(completed.returncode)
    return int(completed.returncode)


def _environment() -> dict[str, str]:
    env = dict(os.environ)
    build = ROOT / "build/native-spprc-bidirectional-feasibility-v1"
    env["PYTHONPATH"] = f"{ROOT / 'src'}:{build}"
    for key in (
        "LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST",
        "LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE",
        "LUNAR_ICE_P0V5_QG2_V3_SELECTOR_MANIFEST",
        "LUNAR_ICE_P0V5_QG2_V3_SELECTOR_EVALUATION_MODE",
    ):
        env.pop(key, None)
    return env


def _state(status: str, **extra) -> None:
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_v5_trace_first_state.v1",
        "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": status,
        "trace_progress": _load_optional(TRACE_DIR / "progress.json"),
        "trace_corpus_ready": TRACE_CORPUS.is_file(),
        "label_gat_smoke_ready": SMOKE_REPORT.is_file(),
        "label_gat_ready": GAT_REPORT.is_file(),
        "force_on_screen_ready": FORCE_REPORT.is_file(),
        "mlp_or_linear_started": False,
        "production_switch_performed": False,
        **extra,
    }
    _atomic_write(STATE, payload)
    with EVENTS.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        stream.flush()


def _stop(status: str, returncode: int) -> int:
    _state(status, returncode=int(returncode))
    return int(returncode) if int(returncode) != 0 else 2


def _load_optional(path: Path):
    return _load(path) if path.is_file() else None


def _load(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _atomic_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
