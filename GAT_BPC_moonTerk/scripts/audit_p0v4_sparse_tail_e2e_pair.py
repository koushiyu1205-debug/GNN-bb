#!/usr/bin/env python3
"""Audit the fixed NOOP/S1 cold-start sparse-tail pair."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "lunar_ice_bpc.sparse_tail_e2e_pair_gate.v1"
DEFAULT_PAIR_DIR = Path(
    "runs/p0v4_v5_sparse_tail_e2e_pilot_20260801"
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _stable_hash(value: object) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _without_keys(value: dict[str, Any], keys: set[str]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key not in keys}


def _all_zero(value: dict[str, Any]) -> bool:
    return all(int(item or 0) == 0 for item in value.values())


def _arm_payload(pair_dir: Path, arm: str) -> dict[str, Any]:
    arm_dir = pair_dir / arm
    summary = _load(arm_dir / "b4_2_cold_exact_summary.json")
    probe_path = (
        arm_dir
        / "pools/scale_030/instance_003/stage_001/probe.json"
    )
    probe = _load(probe_path)
    scale_row = dict((summary.get("by_scale") or {}).get("30") or {})
    history = [
        dict(row)
        for row in (probe.get("history") or [])
        if isinstance(row, dict)
    ]
    attempted_rows = [
        row
        for row in history
        if bool(row.get("one_deviation_sparse_tail_attempted"))
    ]
    final_row = history[-1] if history else {}
    return {
        "arm": arm,
        "summary_path": str(
            (arm_dir / "b4_2_cold_exact_summary.json").resolve()
        ),
        "probe_path": str(probe_path.resolve()),
        "summary": summary,
        "probe": probe,
        "scale_row": scale_row,
        "history": history,
        "attempted_rows": attempted_rows,
        "final_row": final_row,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pair-dir",
        type=Path,
        default=DEFAULT_PAIR_DIR,
    )
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    noop = _arm_payload(args.pair_dir, "NOOP")
    s1 = _arm_payload(args.pair_dir, "S1")
    issues: list[str] = []

    for arm in (noop, s1):
        scale_row = arm["scale_row"]
        summary = arm["summary"]
        probe = arm["probe"]
        if int(scale_row.get("exact_count") or 0) != 1:
            issues.append(f"{arm['arm'].lower()}_not_exact")
        if not _all_zero(dict(summary.get("redlines") or {})):
            issues.append(f"{arm['arm'].lower()}_summary_redline")
        if str(probe.get("pricing_state")) != "CERTIFIED_NO_NEGATIVE":
            issues.append(f"{arm['arm'].lower()}_root_not_certified")
        if int(probe.get("pricing_round_count") or 0) != 54:
            issues.append(f"{arm['arm'].lower()}_unexpected_round_count")

    noop_summary_config = _without_keys(
        dict(noop["summary"].get("config") or {}),
        {"model_id", "one_deviation_sparse_tail_fixed_action"},
    )
    s1_summary_config = _without_keys(
        dict(s1["summary"].get("config") or {}),
        {"model_id", "one_deviation_sparse_tail_fixed_action"},
    )
    if noop_summary_config != s1_summary_config:
        issues.append("summary_config_mismatch_beyond_arm")

    # The parent cold runner computes this child allowance after startup, so a
    # few milliseconds of difference are expected and are not an algorithm arm.
    noop_probe_config = _without_keys(
        dict(noop["probe"].get("config") or {}),
        {
            "one_deviation_sparse_tail_fixed_action",
            "wall_time_limit_sec",
        },
    )
    s1_probe_config = _without_keys(
        dict(s1["probe"].get("config") or {}),
        {
            "one_deviation_sparse_tail_fixed_action",
            "wall_time_limit_sec",
        },
    )
    if noop_probe_config != s1_probe_config:
        issues.append("probe_config_mismatch_beyond_arm_and_allowance")

    for key in (
        "instance_path",
        "instance_id",
        "root_engine",
        "worker_pricer_kind",
        "pricing_round_count",
        "added_column_count",
        "root_rmp_objective",
        "root_lp_bound",
    ):
        if noop["probe"].get(key) != s1["probe"].get(key):
            issues.append(f"probe_{key}_mismatch")

    noop_active_hash = _stable_hash(noop["probe"].get("active_columns") or [])
    s1_active_hash = _stable_hash(s1["probe"].get("active_columns") or [])
    if noop_active_hash != s1_active_hash:
        issues.append("final_active_column_order_mismatch")

    if noop["attempted_rows"]:
        issues.append("noop_unexpected_sparse_attempt")
    if len(s1["attempted_rows"]) != 1:
        issues.append("s1_sparse_attempt_count_not_one")
    s1_action_row = (
        s1["attempted_rows"][0] if s1["attempted_rows"] else {}
    )
    if bool(s1_action_row.get("one_deviation_sparse_tail_executed")):
        issues.append("s1_unexpected_positive_action")
    if s1_action_row.get("one_deviation_sparse_tail_fallback_reason") != (
        "no_official_true_negative_from_sparse_pass"
    ):
        issues.append("s1_unexpected_fallback_reason")
    if not bool(s1_action_row.get("can_certify_no_negative")):
        issues.append("s1_official_fallback_did_not_certify")
    if s1_action_row.get("one_deviation_sparse_tail_certificate_authority") != (
        "none"
    ):
        issues.append("s1_sparse_action_has_certificate_authority")

    noop_total = float(
        noop["scale_row"].get("mean_cold_start_total_sec") or 0.0
    )
    s1_total = float(
        s1["scale_row"].get("mean_cold_start_total_sec") or 0.0
    )
    noop_root = float(noop["scale_row"].get("mean_root_cg_sec") or 0.0)
    s1_root = float(s1["scale_row"].get("mean_root_cg_sec") or 0.0)
    noop_tree = float(noop["scale_row"].get("mean_tree_sec") or 0.0)
    s1_tree = float(s1["scale_row"].get("mean_tree_sec") or 0.0)
    total_gain_fraction = (
        (noop_total - s1_total) / noop_total if noop_total > 0.0 else None
    )
    harmful = bool(
        total_gain_fraction is not None and total_gain_fraction < 0.0
    )
    if not harmful:
        issues.append("s1_not_measured_harmful")

    audit_pass = not issues
    output_payload = {
        "schema_version": SCHEMA_VERSION,
        "status": (
            "FIXED_S1_E2E_GATE_FAILED_HARMFUL_CLOSURE_ACTION"
            if audit_pass and harmful
            else "FIXED_S1_E2E_AUDIT_INVALID"
        ),
        "evidence_scope": (
            "one_fixed_fully_cold_scale30_noop_s1_pair_only"
        ),
        "pair_valid": audit_pass,
        "exact_and_redlines_zero": audit_pass,
        "same_final_active_column_order": (
            noop_active_hash == s1_active_hash
        ),
        "final_active_column_sha256": noop_active_hash,
        "pricing_round_count": int(
            noop["probe"].get("pricing_round_count") or 0
        ),
        "added_column_count": int(
            noop["probe"].get("added_column_count") or 0
        ),
        "noop": {
            "total_sec": noop_total,
            "root_sec": noop_root,
            "tree_sec": noop_tree,
            "final_judge_wall_sec": float(
                noop["final_row"].get("final_judge_wall_time") or 0.0
            ),
            "official_proof_wall_sec": float(
                noop["final_row"].get(
                    "labeling_final_judge_proof_pass_wall_time"
                )
                or 0.0
            ),
        },
        "s1": {
            "total_sec": s1_total,
            "root_sec": s1_root,
            "tree_sec": s1_tree,
            "sparse_attempt_count": len(s1["attempted_rows"]),
            "sparse_action_round": int(s1_action_row.get("round") or 0),
            "sparse_action_wall_sec": float(
                s1_action_row.get(
                    "one_deviation_sparse_tail_pass_wall_time"
                )
                or 0.0
            ),
            "sparse_action_executed": bool(
                s1_action_row.get("one_deviation_sparse_tail_executed")
            ),
            "sparse_action_fallback_reason": str(
                s1_action_row.get(
                    "one_deviation_sparse_tail_fallback_reason"
                )
                or ""
            ),
            "final_judge_wall_sec": float(
                s1["final_row"].get("final_judge_wall_time") or 0.0
            ),
            "official_proof_wall_sec": float(
                s1["final_row"].get(
                    "labeling_final_judge_proof_pass_wall_time"
                )
                or 0.0
            ),
        },
        "paired_effect": {
            "total_gain_sec": noop_total - s1_total,
            "total_gain_fraction": total_gain_fraction,
            "root_gain_sec": noop_root - s1_root,
            "tree_gain_sec": noop_tree - s1_tree,
        },
        "issues": issues,
        "fixed_s1_deployment_authorized": False,
        "formal_gat_training_authorized": False,
        "development_gat_veto_prototype_authorized": audit_pass,
        "required_model_veto": (
            "no_negative_after_harvest_or_closure_likely_context"
        ),
        "required_runtime_guard": (
            "fail_closed_sparse_action_time_cap_then_official_proof"
        ),
        "next_step": (
            "stop_fixed_action_rollouts; train a conservative NOOP_S1_S4 "
            "context gate from existing positive and harmful action rows"
        ),
    }
    output = args.output or args.pair_dir / "paired_gate.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(output_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(output_payload, indent=2, sort_keys=True))
    return 0 if audit_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
