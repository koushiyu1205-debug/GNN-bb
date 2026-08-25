#!/usr/bin/env python3
"""Train V4 QGR1 only from complete stratified literal-Q0 traces."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
import scripts.train_p0v5_qgr1_residual_gat_v2 as base  # noqa: E402
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.guidance.qgr1_residual_supervision_v2 import (  # noqa: E402
    build_qgr1_residual_pairs,
)


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_residual_gat_censor_aware_selector_v4_20260815"


def main() -> int:
    base.DEFAULT_RUN_ROOT = DEFAULT_RUN_ROOT
    base.REPORT_SCHEMA = "lunar_ice_bpc.p0v5_qgr1_residual_gat_training.v4"
    base.legacy._validate_corpus = _validate_v4_corpus
    base._examples = _examples_v4
    base._inner_split = _inner_split_v4
    original_payload = base.qg2_v3_checkpoint_payload

    def checkpoint_payload(model, *, normalization, metadata):
        metadata.update({
            "inner_split": "per_scale_11_train_3_validation.v4",
            "outer_train_instances_per_scale": 14,
            "trace_sampling_mode": "qgr1_stratified_reservoir_v1",
            "trace_incomplete_contexts_used": 0,
        })
        return original_payload(model, normalization=normalization, metadata=metadata)

    base.qg2_v3_checkpoint_payload = checkpoint_payload
    base._record_qgr1_veto = _record_qgr1_veto
    return int(base.main())


def _validate_v4_corpus(corpus):
    if corpus.get("schema_version") != "lunar_ice_bpc.p0v5_qgr1_stratified_trace_corpus.v4":
        raise SystemExit("QGR1 V4 trace corpus schema mismatch")
    if not bool(corpus.get("literal_q0_future_trace_only")):
        raise SystemExit("QGR1 V4 requires literal-Q0 future traces")
    if bool(corpus.get("performance_outcomes_used")):
        raise SystemExit("QGR1 V4 trace corpus leaked performance outcomes")


def _examples_v4(corpus, *, seed, maximum):
    examples = []
    represented = {30: set(), 50: set()}
    for source in corpus.get("rows") or ():
        if str(source.get("partition")) != "train":
            continue
        paths = {
            name: Path(source[f"{name}_path"]).resolve()
            for name in ("instance", "snapshot", "q0_trace")
        }
        for name, path in paths.items():
            if base._sha256(path) != str(source[f"{name}_sha256"]):
                raise SystemExit("QGR1 V4 corpus hash drift")
        data = load_lunar_ice_data(base._load(paths["instance"]))
        snapshot = base._load(paths["snapshot"])
        trace = base._load(paths["q0_trace"])
        telemetry = dict(trace.get("proof_telemetry") or {})
        if (
            data.instance_content_hash != str(source["instance_hash"])
            or str(snapshot["state_hash"]) != str(source["state_hash"])
            or str(trace.get("policy") or "") != "Q0"
            or not bool(trace.get("milestone_reached"))
            or str(telemetry.get("proof_queue_label_trace_sampling_mode"))
            != "qgr1_stratified_reservoir_v1"
            or bool(telemetry.get("proof_queue_label_trace_incomplete"))
            or bool(telemetry.get("proof_queue_label_trace_truncated"))
            or int(telemetry.get("proof_queue_label_trace_final_rows") or 0) > 100_000
        ):
            raise SystemExit("QGR1 V4 trace binding/capacity contract failed")
        labels = {int(row["label_id"]): dict(row)
                  for row in telemetry.get("proof_queue_label_state_trace") or ()}
        supervised, neutral, supervision = build_qgr1_residual_pairs(
            trace, labels, seed=seed, maximum=maximum
        )
        if (
            not supervised or not neutral
            or not bool(supervision.get("all_admitted_routes_represented"))
        ):
            raise SystemExit("QGR1 V4 mandatory witness/pair family coverage failed")
        examples.append({
            "instance_hash": data.instance_content_hash,
            "state_hash": str(snapshot["state_hash"]), "scale": int(data.scale),
            "features": base.legacy._features(data, snapshot), "labels": labels,
            "pairs": supervised, "neutral_pairs": neutral,
            "supervision": supervision,
            "supervision_hash": base._stable_hash(supervision),
        })
        represented[int(data.scale)].add(data.instance_content_hash)
    for scale in (30, 50):
        if len(represented[scale]) < 11:
            raise SystemExit(f"QGR1 V4 scale{scale} trace-complete instances < 11")
        if len(represented[scale]) != 14:
            raise SystemExit(
                f"QGR1 V4 fixed 11/3 inner split requires 14 represented scale{scale} instances"
            )
    return examples


def _inner_split_v4(examples):
    result = {}
    for scale in (30, 50):
        instances = sorted(
            {row["instance_hash"] for row in examples if row["scale"] == scale},
            key=lambda value: hashlib.sha256(f"61635:v4:{value}".encode()).hexdigest(),
        )
        result.update({value: "train" for value in instances[:11]})
        result.update({value: "validation" for value in instances[11:]})
    return result


def _record_qgr1_veto(run_root, violations, report):
    decision = {
        "schema_version": "lunar_ice_bpc.p0v5_qgr1_surrogate_veto.v4",
        "admitted": False, "hard_veto": True, "force_on_executed": False,
        "veto_scales": [30, 50], "violations": list(violations),
        "training_report": report,
        "qgr1_hyperparameter_reselection_forbidden": True,
    }
    base._write_once(Path(run_root) / "qgr1_surrogate_veto.decision.json", decision)
    state_path = Path(run_root) / "state.json"
    state = base._load(state_path)
    state.update({"current_stage": "FINAL_PORTFOLIO_ORACLE", "status": "READY"})
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2,
                                     sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
