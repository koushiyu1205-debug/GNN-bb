#!/usr/bin/env python3
"""V3 14-instance/11+3 adapter for the conservative QGR1 ranker."""

from __future__ import annotations

import hashlib
from pathlib import Path
import json
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
import scripts.train_p0v5_qgr1_residual_gat_v2 as v2  # noqa: E402
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.guidance.qgr1_residual_supervision_v2 import (  # noqa: E402
    build_qgr1_residual_pairs,
)


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_interaction_gat_queue_selector_v3_20260814"


def main() -> int:
    v2.DEFAULT_RUN_ROOT = DEFAULT_RUN_ROOT
    v2.REPORT_SCHEMA = "lunar_ice_bpc.p0v5_qgr1_residual_gat_training.v3"
    v2._examples = _examples_v3
    v2._inner_split = _inner_split_v3
    original_payload = v2.qg2_v3_checkpoint_payload

    def checkpoint_payload(model, *, normalization, metadata):
        metadata["inner_split"] = "per_scale_11_train_3_validation.v3"
        metadata["outer_train_instances_per_scale"] = 14
        return original_payload(model, normalization=normalization, metadata=metadata)

    v2.qg2_v3_checkpoint_payload = checkpoint_payload
    v2._record_qgr1_veto = _record_qgr1_veto_v3
    return int(v2.main())


def _examples_v3(corpus, *, seed, maximum):
    examples = []
    for source in corpus.get("rows") or ():
        if str(source.get("partition")) != "train":
            continue
        instance_path = Path(source["instance_path"]).resolve()
        snapshot_path = Path(source["snapshot_path"]).resolve()
        trace_path = Path(source["q0_trace_path"]).resolve()
        for path, name in (
            (instance_path, "instance"), (snapshot_path, "snapshot"),
            (trace_path, "q0_trace"),
        ):
            if v2._sha256(path) != str(source[f"{name}_sha256"]):
                raise SystemExit("QGR1 V3 corpus file hash drift")
        data = load_lunar_ice_data(v2._load(instance_path))
        snapshot = v2._load(snapshot_path)
        trace = v2._load(trace_path)
        if (
            data.instance_content_hash != str(source["instance_hash"])
            or str(snapshot["state_hash"]) != str(source["state_hash"])
            or str(trace.get("policy") or "") != "Q0"
            or not bool(trace.get("milestone_reached"))
        ):
            raise SystemExit("QGR1 V3 corpus binding mismatch")
        telemetry = dict(trace.get("proof_telemetry") or {})
        labels = {
            int(row["label_id"]): dict(row)
            for row in telemetry.get("proof_queue_label_state_trace") or ()
        }
        supervised, neutral, supervision = build_qgr1_residual_pairs(
            trace, labels, seed=seed, maximum=maximum
        )
        if (
            not supervised or not neutral
            or not bool(supervision.get("all_admitted_routes_represented"))
        ):
            raise SystemExit(
                "QGR1 V3 requires supervised/neutral pairs and every admitted route"
            )
        examples.append({
            "instance_hash": data.instance_content_hash,
            "state_hash": str(snapshot["state_hash"]), "scale": int(data.scale),
            "features": v2.legacy._features(data, snapshot), "labels": labels,
            "pairs": supervised, "neutral_pairs": neutral,
            "supervision": supervision,
            "supervision_hash": v2._stable_hash(supervision),
        })
    for scale in (30, 50):
        count = len({row["instance_hash"] for row in examples if row["scale"] == scale})
        if count != 14:
            raise SystemExit(f"QGR1 V3 scale{scale} outer train instances != 14")
    return examples


def _inner_split_v3(examples):
    result = {}
    for scale in (30, 50):
        instances = sorted(
            {row["instance_hash"] for row in examples if row["scale"] == scale},
            key=lambda value: hashlib.sha256(f"61635:{value}".encode()).hexdigest(),
        )
        result.update({value: "train" for value in instances[:11]})
        result.update({value: "validation" for value in instances[11:]})
    return result


def _record_qgr1_veto_v3(run_root, violations, report):
    decision = {
        "schema_version": "lunar_ice_bpc.p0v5_qgr1_surrogate_veto.v3",
        "admitted": False, "hard_veto": True, "force_on_executed": False,
        "veto_scales": [30, 50], "violations": list(violations),
        "training_report": report,
        "qgr1_hyperparameter_reselection_forbidden": True,
    }
    v2._write_once(Path(run_root) / "qgr1_surrogate_veto.decision.json", decision)
    state_path = Path(run_root) / "state.json"
    state = v2._load(state_path)
    state.update({"current_stage": "CONTEXT_GAT_TRAINING", "status": "READY"})
    state_path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
