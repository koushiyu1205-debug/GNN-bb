#!/usr/bin/env python3
"""Train only the instance-balanced Label GAT from the Q0 trace corpus."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
TRAINER = ROOT / "scripts/train_p0v5_qg2_v4_instance_balanced_rankers.py"
TRACE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_trace_supervision_corpus.v1"
VIEW_SCHEMA = "lunar_ice_bpc.p0v5_qg2_bounded_oracle.v5"
REPORT_SCHEMA = "lunar_ice_bpc.p0v5_qg2_v3_ranker_training.v1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace-corpus", required=True)
    parser.add_argument("--training-view", required=True)
    parser.add_argument("--instance-split", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--early-stopping-patience", type=int, default=8)
    parser.add_argument("--max-pairs-per-context", type=int, default=4096)
    parser.add_argument("--learning-rate", type=float, default=0.002)
    parser.add_argument("--seed", type=int, default=20260807)
    args = parser.parse_args()

    corpus_path = _resolve(args.trace_corpus)
    view_path = _resolve(args.training_view)
    split_path = _resolve(args.instance_split)
    output_dir = _resolve(args.output_dir)
    corpus = _load(corpus_path)
    view = _load(view_path)
    if (
        corpus.get("schema_version") != TRACE_SCHEMA
        or not bool(dict(corpus.get("supervision_gate") or {}).get("passed"))
        or bool(corpus.get("performance_oracle"))
        or bool(corpus.get("random_or_leaked_qo2_outcomes_used"))
    ):
        raise SystemExit("Label-GAT trace corpus authority is invalid")
    if (
        view.get("schema_version") != VIEW_SCHEMA
        or str(view.get("compatibility_view_role") or "")
        != "label_gat_trace_supervision_only"
        or str(view.get("source_trace_corpus_sha256") or "")
        != _sha256(corpus_path)
        or bool(view.get("performance_oracle_gate_used"))
        or bool(view.get("random_or_leaked_qo2_outcomes_used"))
        or not bool(view.get("training_permitted"))
    ):
        raise SystemExit("Label-GAT compatibility view authority is invalid")
    if str(corpus.get("instance_split_sha256") or "") != _sha256(split_path):
        raise SystemExit("Label-GAT split binding drift")
    if output_dir.exists() and (output_dir / "training_report.json").is_file():
        _validate_report(
            output_dir / "training_report.json",
            corpus_path=corpus_path,
            view_path=view_path,
        )
        return 0

    command = [
        sys.executable,
        str(TRAINER),
        "--oracle-summary", str(view_path),
        "--instance-split", str(split_path),
        "--output-dir", str(output_dir),
        "--models", "gat",
        "--epochs", str(max(1, int(args.epochs))),
        "--early-stopping-patience", str(
            max(1, int(args.early_stopping_patience))
        ),
        "--max-pairs-per-context", str(
            max(1, int(args.max_pairs_per_context))
        ),
        "--learning-rate", str(float(args.learning_rate)),
        "--seed", str(int(args.seed)),
    ]
    completed = subprocess.run(command, cwd=ROOT, check=False)
    report_path = output_dir / "training_report.json"
    if completed.returncode != 0 or not report_path.is_file():
        raise SystemExit("instance-balanced Label GAT training failed")
    report = _load(report_path)
    report.update({
        "training_authority_kind": "action_reachable_q0_future_trace_only",
        "source_trace_corpus": str(corpus_path),
        "source_trace_corpus_sha256": _sha256(corpus_path),
        "source_training_view": str(view_path),
        "source_training_view_sha256": _sha256(view_path),
        "model_role": "label_state_queue_ordering_only",
        "trained_models_in_this_stage": ["gat"],
        "mlp_or_linear_control_started": False,
        "performance_oracle_gate_used": False,
        "random_or_leaked_qo2_outcomes_used": False,
        "next_performance_authority": "fresh_process_q0_vs_qg2_force_on",
        "deployment_authorized": False,
    })
    _atomic_write(report_path, report)
    _validate_report(
        report_path, corpus_path=corpus_path, view_path=view_path
    )
    return 0


def _validate_report(
    path: Path, *, corpus_path: Path, view_path: Path
) -> None:
    report = _load(path)
    models = [
        dict(row) for row in report.get("models") or ()
        if str(row.get("model_kind") or "") == "gat"
    ]
    if (
        report.get("schema_version") != REPORT_SCHEMA
        or len(models) != 1
        or str(report.get("source_trace_corpus_sha256") or "")
        != _sha256(corpus_path)
        or str(report.get("source_training_view_sha256") or "")
        != _sha256(view_path)
        or bool(report.get("mlp_or_linear_control_started"))
        or bool(report.get("deployment_authorized"))
    ):
        raise SystemExit("Label-GAT training report binding failed")
    checkpoint = _resolve(models[0].get("checkpoint_path") or "")
    curve = _resolve(report.get("training_curve_path") or "")
    if (
        not checkpoint.is_file()
        or _sha256(checkpoint) != str(models[0].get("checkpoint_sha256") or "")
        or not curve.is_file()
        or _sha256(curve) != str(report.get("training_curve_sha256") or "")
    ):
        raise SystemExit("Label-GAT checkpoint or curve drift")


def _resolve(value) -> Path:
    path = Path(str(value)).expanduser()
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _atomic_write(path: Path, payload: dict) -> None:
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
