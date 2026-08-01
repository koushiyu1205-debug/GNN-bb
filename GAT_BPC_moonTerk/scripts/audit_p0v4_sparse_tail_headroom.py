#!/usr/bin/env python3
"""Audit the two fixed sparse-tail pilots without expanding the evidence set."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


SCHEMA_VERSION = "lunar_ice_bpc.sparse_tail_headroom_gate.v1"
FIXED_PILOTS = (
    (30, "scale30_instance003_round049_S1_margin3e6.json"),
    (50, "scale50_instance001_round091_S1_margin3e6.json"),
)


def _audit_row(path: Path, expected_scale: int) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    safety = dict(payload.get("safety") or {})
    reconstruction = dict(payload.get("reconstruction_audit") or {})
    source_wall = float(payload.get("source_round_proof_wall_sec") or 0.0)
    action_wall = float(payload.get("fresh_process_wall_sec") or 0.0)
    issues: list[str] = []
    if payload.get("status") != "SAFE_REPLAY_COMPLETE":
        issues.append("replay_not_safe_complete")
    if int(payload.get("scale") or 0) != int(expected_scale):
        issues.append("scale_mismatch")
    if payload.get("action") != "S1":
        issues.append("unexpected_action")
    if not bool(payload.get("negative_escape_triggered")):
        issues.append("negative_escape_not_triggered")
    if bool(payload.get("frontier_empty")):
        issues.append("partial_action_frontier_unexpectedly_empty")
    if bool(payload.get("search_exhaustive")):
        issues.append("partial_action_unexpectedly_exhaustive")
    if bool(payload.get("backend_can_enter_certificate_audit")):
        issues.append("partial_action_entered_certificate_audit")
    if int(reconstruction.get("true_negative_column_count") or 0) < 1:
        issues.append("no_audited_true_negative")
    best_rc = payload.get("best_found_rc")
    official_eps = float(payload.get("official_negative_eps") or 0.0)
    if best_rc is None or float(best_rc) >= -official_eps:
        issues.append("best_column_not_officially_negative")
    if list(safety.get("issues") or []):
        issues.append("replay_safety_issues_present")
    for key in (
        "legal_candidate_universe_mutated",
        "reduced_cost_definition_mutated",
        "dominance_or_bound_mutated",
        "pruning_path_mutated",
        "certificate_path_mutated",
        "can_certify_from_replay",
    ):
        if bool(safety.get(key)):
            issues.append(key)
    if safety.get("replay_certificate_authority") != "none":
        issues.append("replay_certificate_authority_not_none")
    if safety.get("next_round_policy") != "restore_frozen_v5":
        issues.append("next_round_does_not_restore_frozen_v5")
    if source_wall <= 0.0 or action_wall <= 0.0:
        issues.append("invalid_wall_time")
    ratio = action_wall / source_wall if source_wall > 0.0 else None
    gain = 1.0 - ratio if ratio is not None else None
    return {
        "scale": int(expected_scale),
        "artifact": str(path.resolve()),
        "artifact_status": str(payload.get("status") or ""),
        "source_round": int(payload.get("source_round") or 0),
        "source_proof_wall_sec": source_wall,
        "sparse_action_wall_sec": action_wall,
        "action_to_source_wall_ratio": ratio,
        "action_call_wall_gain_fraction": gain,
        "best_found_true_rc": best_rc,
        "audited_true_negative_count": int(
            reconstruction.get("true_negative_column_count") or 0
        ),
        "host_peak_rss_bytes": int(
            payload.get("host_peak_rss_bytes") or 0
        ),
        "certificate_authority": str(
            safety.get("replay_certificate_authority") or ""
        ),
        "next_round_policy": str(
            safety.get("next_round_policy") or ""
        ),
        "issues": issues,
        "safety_pass": not issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pilot-dir",
        type=Path,
        default=Path(
            "runs/p0v4_v5_sparse_tail_headroom_pilot_20260801"
        ),
    )
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    rows = [
        _audit_row(args.pilot_dir / filename, scale)
        for scale, filename in FIXED_PILOTS
    ]
    gate_threshold = 0.08
    gate_pass = all(
        bool(row["safety_pass"])
        and float(row["action_call_wall_gain_fraction"] or 0.0)
        >= gate_threshold
        for row in rows
    )
    output = args.output or args.pilot_dir / "headroom_gate.json"
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": (
            "SPARSE_TAIL_ACTION_HEADROOM_GATE_PASSED"
            if gate_pass
            else "SPARSE_TAIL_ACTION_HEADROOM_GATE_FAILED"
        ),
        "evidence_scope": (
            "two_pre_registered_mathematical_context_replays_only"
        ),
        "context_expansion_authorized": False,
        "action_call_headroom_threshold_fraction": gate_threshold,
        "rows": rows,
        "development_model_prototype_authorized": gate_pass,
        "formal_gat_training_authorized": False,
        "deployment_authorized": False,
        "formal_training_blockers": [
            "only_two_counterfactual_contexts",
            "end_to_end_cg_round_debt_unmeasured",
            "no_held_out_instance_level_gain_measurement",
        ],
        "next_step": (
            "run_one_bounded_end_to_end_shadow_oracle_pilot_with_the_"
            "opt_in_once_per_root_runtime; do_not expand the route-promotion_"
            "census"
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if gate_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
