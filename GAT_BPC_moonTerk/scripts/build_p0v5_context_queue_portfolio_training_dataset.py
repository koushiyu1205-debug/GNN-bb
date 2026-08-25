#!/usr/bin/env python3
"""Bind median arm outcomes to action-time portfolio features."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.exact.bpc.pricing.backends.base import BackendPricingRequest  # noqa: E402
from lunar_ice_bpc.exact.core.branching import branch_context_from_payload  # noqa: E402
from lunar_ice_bpc.exact.core.cuts import cut_context_from_payload  # noqa: E402
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals  # noqa: E402
from lunar_ice_bpc.guidance.context_queue_portfolio_gates import (  # noqa: E402
    collapse_matched_matrix,
)
from lunar_ice_bpc.guidance.context_queue_portfolio_v1 import (  # noqa: E402
    PORTFOLIO_ARMS, build_portfolio_features,
)
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import (  # noqa: E402
    verify_portfolio_freezes,
)


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_context_queue_portfolio_v1_20260807_r1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outcomes", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    _verify_freezes(run_root)
    config = _load(run_root / "config.freeze.json")
    corpus = _load(run_root / "corpus.freeze.json")
    admission = _load(run_root / "qgr1_force_on.decision.json")["decision"]
    arm_scale_mask = {
        str(arm): {int(value) for value in scales}
        for arm, scales in dict(admission["arm_scale_mask"]).items()
    }
    outcome_path = args.outcomes.resolve()
    outcome_payload = _load(outcome_path)
    outcomes = collapse_matched_matrix(
        outcome_payload["rows"],
        caps_by_scale=config["execution"]["replay_caps_sec"],
        required_repeats=config["execution"]["blocked_fresh_process_repeats"],
    )
    by_context_arm = {(row.context_id, row.arm): row for row in outcomes}
    rows = []
    for context in corpus["rows"]:
        if context["partition"] not in {"train", "calibration"}:
            continue
        snapshot = _load(Path(context["snapshot_path"]))
        request = _request(context, snapshot)
        features = build_portfolio_features(request)
        targets = {}
        for arm in PORTFOLIO_ARMS:
            outcome = by_context_arm.get((context["context_id"], arm))
            admitted = int(context["scale"]) in arm_scale_mask.get(arm, set())
            determined = bool(admitted and outcome is not None and outcome.determined)
            ratio = float(outcome.ratio) if determined else None
            targets[arm] = {
                "admitted_for_scale": admitted,
                "determined": determined,
                "ratio": ratio,
                "benefit": bool(determined and ratio <= 0.98),
                "positive_gain": max(0.0, 1.0 - ratio) if determined else 0.0,
                "adverse": bool(outcome is not None and outcome.adverse),
                "correctness_redlines": (
                    list(outcome.correctness_redlines) if outcome else []
                ),
            }
        rows.append({
            "context_id": context["context_id"],
            "instance_hash": context["instance_content_hash"],
            "scale": context["scale"],
            "partition": context["partition"],
            "state_hash": context["state_hash"],
            "features": _feature_payload(features),
            "targets": targets,
        })
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_training_dataset.v1",
        "unit": "context_with_three_repeats_already_collapsed",
        "instance_balanced_required": True,
        "selector_heldout_outcomes_included": False,
        "formal_outcomes_included": False,
        "corpus_freeze_sha256": _sha256(run_root / "corpus.freeze.json"),
        "source_outcomes": str(outcome_path),
        "source_outcomes_sha256": _sha256(outcome_path),
        "arm_scale_mask": {
            arm: sorted(scales) for arm, scales in arm_scale_mask.items()
        },
        "rows": rows,
    }
    output = (
        args.output.resolve() if args.output
        else run_root / "portfolio_training_dataset.freeze.json"
    )
    _write_once(output, payload)
    print(json.dumps({
        "output": str(output), "context_count": len(rows),
        "instance_count": len({row["instance_hash"] for row in rows}),
    }, ensure_ascii=False, indent=2))
    return 0


def _request(context, snapshot):
    data = load_lunar_ice_data(_load(Path(context["instance_path"])))
    if data.instance_content_hash != context["instance_content_hash"]:
        raise SystemExit("instance content hash drift")
    duals = dict(snapshot.get("true_duals") or {})
    trajectory = dict(snapshot.get("trajectory_features") or {})
    previous_policy = str(trajectory.get("previous_queue_policy_id") or "")
    return BackendPricingRequest(
        data=data,
        true_duals=JourneyDuals(
            cover=dict(duals.get("task_duals") or duals.get("cover") or {}),
            fleet_limit=float(duals.get("fleet_dual") if duals.get("fleet_dual") is not None else duals.get("fleet_limit") or 0.0),
            cuts=dict(duals.get("cut_duals") or duals.get("cuts") or {}),
        ),
        mode="exact_proof", objective_mode="official",
        pricing_lifecycle_scope=str(snapshot.get("pricing_lifecycle_scope") or "root_cg"),
        branch_context=branch_context_from_payload(snapshot.get("branch_context") or {}),
        cut_context=cut_context_from_payload(snapshot.get("cut_context") or {}),
        proof_queue_policy_id="Q0", proof_tail_fallback_context=True,
        proof_tail_active_column_count=_optional_int(snapshot.get("active_column_count")),
        proof_tail_active_task_sets=(
            None if snapshot.get("active_task_sets") is None else
            tuple(tuple(str(v) for v in row) for row in snapshot["active_task_sets"])
        ),
        proof_tail_active_column_signature_hashes=(
            None if snapshot.get("active_column_signature_hashes") is None else
            tuple(str(v) for v in snapshot["active_column_signature_hashes"])
        ),
        proof_tail_round_index=_optional_int(snapshot.get("round")),
        proof_tail_previous_queue_policy_id=previous_policy,
        proof_tail_previous_proof_wall_sec=_optional_float(trajectory.get("previous_proof_pass_wall_time")),
        proof_tail_previous_processed_labels=_optional_int(trajectory.get("previous_proof_processed_labels")),
        proof_tail_previous_dominance_candidate_checks=_optional_int(trajectory.get("previous_dominance_candidate_checks")),
        proof_tail_previous_dominance_wall_sec=_optional_float(trajectory.get("previous_dominance_wall_sec")),
        proof_tail_previous_max_visited_bucket_size=_optional_int(trajectory.get("previous_max_visited_bucket_size")),
        proof_tail_dual_delta_l1=_optional_float(trajectory.get("dual_l1_delta_from_previous")),
        proof_tail_v5_midpoint_wall_sec=_optional_float(snapshot.get("bidirectional_midpoint_prepass_wall_sec")),
        proof_tail_v5_midpoint_reason=str(snapshot.get("bidirectional_midpoint_fallback_reason") or "snapshot_replay"),
        instance_hash=data.instance_content_hash,
        config_hash=str(snapshot["config_hash"]), engine_hash=str(snapshot["engine_hash"]),
        rmp_iteration_id=str(snapshot.get("rmp_iteration_id") or ""),
        cut_lineage_hash=str(dict(snapshot.get("cut_lineage") or {}).get("cut_lineage_hash") or ""),
        live_cut_policy_hash=str(snapshot.get("live_cut_policy_hash") or ""),
        separator_policy_version=str(snapshot.get("separator_policy_version") or ""),
    )


def _feature_payload(features):
    return {
        "schema_version": features.schema_version,
        "instance_content_hash": features.instance_content_hash,
        "task_ids": list(features.task_ids),
        "arc_candidate_ids": list(features.arc_candidate_ids),
        "node_features": [list(row) for row in features.node_features],
        "edge_index": [list(row) for row in features.edge_index],
        "edge_features": [list(row) for row in features.edge_features],
        "context_features": list(features.context_features),
    }


def _optional_int(value):
    return None if value is None else int(value)


def _optional_float(value):
    return None if value is None else float(value)


def _verify_freezes(run_root):
    try:
        verify_portfolio_freezes(run_root, ROOT)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_once(path, payload):
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if Path(path).exists() and Path(path).read_text(encoding="utf-8") != text:
        raise SystemExit(f"immutable artifact drift:{path}")
    if not Path(path).exists():
        Path(path).write_text(text, encoding="utf-8")


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
