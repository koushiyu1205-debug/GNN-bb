#!/usr/bin/env python3
"""Freeze one fresh-validated QG2 V3 selector for development E2E."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.guidance.qg2_v3_selector_runtime import (  # noqa: E402
    QG2_V3_SELECTOR_MANIFEST_SCHEMA,
    QG2_V3_SELECTOR_RUNTIME_POLICY_ID,
    qg2_v3_selector_runtime_implementation_hash,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selector-training-report", required=True)
    parser.add_argument("--fresh-report", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--backend-id",
        default="native_rcspp_bidirectional_root_partial_hybrid_v3",
    )
    parser.add_argument(
        "--native-build-dir",
        default="build/native-spprc-bidirectional-feasibility-v1",
    )
    args = parser.parse_args()

    training_path = _resolve(args.selector_training_report)
    fresh_path = _resolve(args.fresh_report)
    training = _load(training_path)
    fresh = _load(fresh_path)
    if str(training.get("trained_model") or "") != "gat":
        raise SystemExit("development candidate must use the GAT-first winner")
    if str(fresh.get("selector_training_report_sha256") or "") != _sha256(
        training_path
    ):
        raise SystemExit("fresh report is not bound to selector training report")
    if str(fresh.get("checkpoint_sha256") or "") != str(
        training.get("checkpoint_sha256") or ""
    ):
        raise SystemExit("fresh report checkpoint hash mismatch")
    if str(fresh.get("partition") or "") != "heldout" or int(
        fresh.get("repeat_count") or 0
    ) < 3:
        raise SystemExit("fresh heldout must contain at least three repeats")
    overall = dict((fresh.get("summary") or {}).get("overall") or {})
    per30 = dict((fresh.get("summary") or {}).get("scale30") or {})
    per50 = dict((fresh.get("summary") or {}).get("scale50") or {})
    if not (
        bool(overall.get("all_safe"))
        and int(overall.get("activated_count") or 0) > 0
        and 0.0 < float(overall.get("net_geomean_ratio") or 1.0) < 1.0
        and float(per30.get("net_geomean_ratio") or 1.0) <= 1.0
        and float(per50.get("net_geomean_ratio") or 1.0) <= 1.0
    ):
        raise SystemExit("fresh GAT selector did not pass development E2E gate")
    trainable_arms = set(training.get("trainable_arms") or ())
    qg2_enabled = "QG2" in trainable_arms
    allowed_actions = {"Q0", "QD1", "QB1"}
    if qg2_enabled:
        allowed_actions.add("QG2")
    if any(
        not bool(row.get("safe"))
        or str(row.get("selected_action") or "") not in allowed_actions
        for row in fresh.get("records") or ()
    ):
        raise SystemExit("fresh selector record violates action/safety contract")

    checkpoint_path = _resolve(training["checkpoint_path"])
    ranker = _load(_resolve(training["ranker_training_report"]))
    feature_envelope_path = _resolve(ranker["feature_envelope_path"])
    feature_envelope = _load(feature_envelope_path)
    oracle_path = _resolve(training["oracle_summary"])
    oracle = _load(oracle_path)
    policy_hashes = sorted({
        str(row.get("source_exact_action_policy_hash") or "")
        for row in oracle.get("initial_rows") or ()
        if row.get("compliant_context")
        and str(row.get("source_exact_action_policy_hash") or "")
    })
    source_engines = sorted({
        str(row.get("source_engine_hash") or "")
        for row in oracle.get("initial_rows") or ()
        if row.get("compliant_context")
        and str(row.get("source_engine_hash") or "")
    })
    build_dir = _resolve(args.native_build_dir)
    sys.path.insert(0, str(build_dir))
    from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import (
        spprc_engine_build_hash,
    )
    candidate_engine_hash = spprc_engine_build_hash(str(args.backend_id))
    thresholds = dict(fresh["thresholds"])
    expected_veto = set() if qg2_enabled else {"QG2"}
    if set(thresholds.get("forced_veto_arms") or ()) != expected_veto:
        raise SystemExit("fresh selector QG2 action/veto contract mismatch")
    thresholds = {
        key: value for key, value in thresholds.items()
        if key != "forced_veto_arms"
    }
    action_universe = ["Q0", "QD1", "QB1"]
    qg2_fields = {}
    if qg2_enabled:
        ranker_models = [
            dict(row) for row in ranker.get("models") or ()
            if str(row.get("model_kind") or "") == "gat"
        ]
        if len(ranker_models) != 1:
            raise SystemExit("QG2-enabled selector requires one label GAT")
        ranker_checkpoint = _resolve(ranker_models[0]["checkpoint_path"])
        action_universe.insert(1, "QG2")
        qg2_fields = {
            "qg2_ranker_checkpoint_path": str(ranker_checkpoint),
            "qg2_ranker_checkpoint_sha256": _sha256(ranker_checkpoint),
            "qg2_ranker_model_kind": "gat",
            "qg2_guidance_bucket_width": float(
                oracle["frozen_guidance_bucket_width"]
            ),
            "qg2_label_state_schema_version": (
                "lunar_spprc.qg2_label_state.v1"
            ),
        }
    payload = {
        "schema_version": QG2_V3_SELECTOR_MANIFEST_SCHEMA,
        "development_only": True,
        "deployable": False,
        "runtime_policy_id": QG2_V3_SELECTOR_RUNTIME_POLICY_ID,
        "runtime_implementation_hash": (
            qg2_v3_selector_runtime_implementation_hash()
        ),
        "model_kind": "gat",
        "action_universe": action_universe,
        "forced_veto_arms": sorted(expected_veto),
        "fallback_action": "Q0",
        "checkpoint_path": str(checkpoint_path),
        "checkpoint_sha256": _sha256(checkpoint_path),
        "selector_training_report": str(training_path),
        "selector_training_report_sha256": _sha256(training_path),
        "fresh_report": str(fresh_path),
        "fresh_report_sha256": _sha256(fresh_path),
        "feature_envelope_path": str(feature_envelope_path),
        "feature_envelope_sha256": _sha256(feature_envelope_path),
        "feature_envelope": feature_envelope,
        "thresholds": thresholds,
        "allowed_scales": [30, 50],
        "allowed_exact_engine_hashes": [candidate_engine_hash],
        "allowed_exact_action_policy_hashes": policy_hashes,
        "training_source_exact_engine_hashes_diagnostic_only": source_engines,
        "backend_id": str(args.backend_id),
        "torch_num_threads": 1,
        "fresh_heldout_summary": fresh["summary"],
        "fresh_harmful_actions_are_reported_not_a_pre_e2e_veto": True,
        "qg2_label_state_arm_status": (
            "enabled_by_realmap_train_force_on"
            if qg2_enabled else "hard_vetoed_by_realmap_train_force_on"
        ),
        **qg2_fields,
        "development_e2e_authorized": True,
        "deployment_authorized": False,
        "production_switch_authorized": False,
    }
    output = _resolve(args.output)
    _write(output, payload)
    print(json.dumps({
        "output": str(output),
        "model_kind": "gat",
        "candidate_engine_hash": candidate_engine_hash,
        "thresholds": thresholds,
        "fresh_heldout_summary": fresh["summary"],
        "development_e2e_authorized": True,
        "deployment_authorized": False,
    }, sort_keys=True))
    return 0


def _resolve(value):
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
