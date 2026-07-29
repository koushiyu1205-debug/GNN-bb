#!/usr/bin/env python3
"""One-shot single-child probe used only to choose a formal label horizon."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from run_p0_no_task_wait_v3_branch_child_trajectory import (  # noqa: E402
    _actionable_state_rows,
    _bind_exact_opportunity_control,
    _candidate_id,
    _configure_environment,
    _cut_context_from_payload,
    _cut_lineage_from_payload,
    _development_hashes,
    _extend_branch_context,
    _load_json,
    _node_probe_summary,
    _persist_child_continuation_snapshot,
    _probe_child,
    _probe_key,
    _sha256_json,
    _validated_parent_source,
    _write_json,
    BASELINE_ID,
    PROFILE_BY_SCALE,
)
from lunar_ice_bpc.domain.scenario import (  # noqa: E402
    SERVICE_TIMING_POLICY_ID,
)
from lunar_ice_bpc.exact.core.data import (  # noqa: E402
    load_lunar_ice_data,
)


SCHEMA_VERSION = (
    "lunar_ice_bpc.branch_single_child_horizon_probe.v1"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", required=True)
    parser.add_argument("--oracle-dir", required=True)
    parser.add_argument("--parent-snapshot", required=True)
    parser.add_argument("--split-manifest", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--rank-index", type=int, required=True)
    parser.add_argument(
        "--branch-sense",
        choices=("same_journey", "different_journey"),
        required=True,
    )
    parser.add_argument("--budget-sec", type=float, required=True)
    parser.add_argument("--max-rounds", type=int, default=16)
    parser.add_argument("--max-columns-per-round", type=int, default=128)
    args = parser.parse_args()

    if int(args.rank_index) not in {0, 1, 2}:
        raise SystemExit("rank index must be 0, 1, or 2")
    if float(args.budget_sec) <= 0.0:
        raise SystemExit("budget must be positive")
    instance_path = (ROOT / args.instance).resolve()
    oracle_dir = (ROOT / args.oracle_dir).resolve()
    parent_path = (ROOT / args.parent_snapshot).resolve()
    split_path = (ROOT / args.split_manifest).resolve()
    output_dir = (ROOT / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    data = load_lunar_ice_data(_load_json(instance_path))
    manifest = _load_json(split_path)
    split_hash = str(
        manifest.get("manifest_hash") or _sha256_json(manifest)
    )
    if data.instance_content_hash not in _development_hashes(manifest):
        raise SystemExit("single-child probe accepts development only")
    if data.service_timing_policy_id != SERVICE_TIMING_POLICY_ID:
        raise SystemExit("service-timing policy mismatch")
    profile = PROFILE_BY_SCALE.get(int(data.scale))
    if profile is None:
        raise SystemExit("single-child probe accepts scale20/30 only")
    _configure_environment(scale=int(data.scale), profile=profile)

    root_payload = _load_json(oracle_dir / "root_source.json")
    control = _load_json(oracle_dir / "control_rank0_tree.json")
    opportunity_path = oracle_dir / "branch_opportunity_report.json"
    opportunity = (
        _load_json(opportunity_path)
        if opportunity_path.is_file()
        else None
    )
    control, _ = _bind_exact_opportunity_control(control, opportunity)
    parent_source = _load_json(parent_path)
    parent_summary = parent_source.get("summary") or {}
    if (
        str(parent_source.get("instance_content_hash") or "")
        != data.instance_content_hash
        or str(parent_source.get("root_source_sha256") or "")
        != _sha256_json(root_payload)
        or str(parent_source.get("control_tree_sha256") or "")
        != _sha256_json(control)
        or not bool(parent_summary.get("exact_safe"))
    ):
        raise SystemExit("exact parent snapshot binding mismatch")

    states = _actionable_state_rows(control)
    if len(states) != 1:
        raise SystemExit("single-child probe requires one bound root state")
    state = states[0]
    if bool(
        parent_summary.get("fresh_reconstructed_shortlist_bound")
    ):
        state = {
            **state,
            "candidates": list(
                parent_summary.get("reconstructed_top3_candidates")
                or ()
            ),
        }
    if len(state["candidates"]) != 3:
        raise SystemExit("parent snapshot does not bind a top-3")
    try:
        _, parent_columns, validated_summary = (
            _validated_parent_source(
                data=data,
                state=state,
                source=parent_source,
            )
        )
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc

    cut_context = _cut_context_from_payload(state["cut_context"])
    cut_lineage = _cut_lineage_from_payload(state["cut_lineage"])
    candidate = state["candidates"][int(args.rank_index)]
    candidate_id = _candidate_id(candidate)
    context_key = (
        "same_child_context"
        if args.branch_sense == "same_journey"
        else "different_child_context"
    )
    child_context = _extend_branch_context(
        state["parent_branch_context"],
        candidate.get(context_key) or {},
    )
    raw, wall_sec = _probe_child(
        data=data,
        profile=profile,
        initial_columns=parent_columns,
        branch_context=child_context,
        cut_context=cut_context,
        cut_lineage=cut_lineage,
        depth=int(state["depth"]) + 1,
        ancestor_path=(str(state["node_id"]),),
        node_id=(
            f"horizon_probe_r{int(args.rank_index)}_"
            f"{args.branch_sense}"
        ),
        incumbent_objective=None,
        budget_sec=float(args.budget_sec),
        max_rounds=int(args.max_rounds),
        max_columns_per_round=int(args.max_columns_per_round),
    )
    child = _node_probe_summary(
        payload=raw,
        wall_sec=wall_sec,
        budget_sec=float(args.budget_sec),
        rank_index=int(args.rank_index),
        branch_sense=str(args.branch_sense),
        candidate_id=candidate_id,
    )
    probe_key = _probe_key(
        path_hash=state["path_hash"],
        rank_index=int(args.rank_index),
        branch_sense=str(args.branch_sense),
    )
    continuation = _persist_child_continuation_snapshot(
        output_dir=output_dir,
        data=data,
        raw=raw,
        initial_columns=parent_columns,
        probe_key=probe_key,
        path_hash=state["path_hash"],
        candidate_id=candidate_id,
        rank_index=int(args.rank_index),
        branch_sense=str(args.branch_sense),
        branch_context=child_context,
        cut_context=cut_context,
        cut_lineage=cut_lineage,
        observed_wall_sec=wall_sec,
        budget_sec=float(args.budget_sec),
    )
    if continuation is not None:
        child["continuation_column_source"] = continuation
    report = {
        "schema_version": SCHEMA_VERSION,
        "development_only": True,
        "deployable": False,
        "training_authorized": False,
        "formal_branch_training_label": False,
        "horizon_discovery_only": True,
        "one_shot_from_exact_parent_snapshot": True,
        "instance_id": data.instance_id,
        "instance_content_hash": data.instance_content_hash,
        "scale": int(data.scale),
        "baseline_id": BASELINE_ID,
        "split_manifest_hash": split_hash,
        "root_source_sha256": _sha256_json(root_payload),
        "control_tree_sha256": _sha256_json(control),
        "parent_snapshot_sha256": _sha256_json(parent_source),
        "parent_snapshot": validated_summary,
        "rank_index": int(args.rank_index),
        "branch_sense": str(args.branch_sense),
        "candidate_id": candidate_id,
        "budget_sec": float(args.budget_sec),
        "child": child,
        "guidance_filter_count": 0,
        "guidance_branch_pair_drop_count": 0,
    }
    _write_json(output_dir / "single_child_horizon_probe.json", report)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
