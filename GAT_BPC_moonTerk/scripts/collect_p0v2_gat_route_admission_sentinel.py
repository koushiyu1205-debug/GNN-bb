#!/usr/bin/env python3
"""Collect unbiased route-admission opportunity rows from frozen P0 traces.

This collector does not manufacture a counterfactual by changing P0's batch
size.  A route promotion is considered behaviorally effective only when the
number of addable routes exceeds the actual P0 admission limit.  Contexts in
which every addable route fits are structural zeroes: the master stores a set
and deterministically sorts semantic signatures before the next RMP.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from lunar_ice_bpc.exact.core.cuts import stable_payload_hash
from lunar_ice_bpc.exact.core.objective import OBJECTIVE_SPEC_ID
from lunar_ice_bpc.guidance.opportunity_gate import (
    OPPORTUNITY_OBSERVATION_SCHEMA_V1,
    validate_opportunity_observation,
)
from lunar_ice_bpc.guidance.route_admission import (
    ROUTE_ADMISSION_LEXICOGRAPHIC_OBJECTIVE_SPEC_V2,
    ROUTE_ADMISSION_OBJECTIVE_SPEC_V1,
    validate_route_admission_snapshot,
)


SENTINEL_SCHEMA = "lunar_ice_bpc.gat_sentinel_manifest.v1"
COLLECTION_SCHEMA = (
    "lunar_ice_bpc.route_admission_sentinel_collection.v1"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sentinel-manifest", required=True)
    parser.add_argument("--training-rows-dir", required=True)
    parser.add_argument("--output-jsonl", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument(
        "--b0-results-jsonl",
        default="",
        help=(
            "Optional frozen same-code B0 outcomes used only to audit whether "
            "effective contexts can support complete-exact paired timing."
        ),
    )
    parser.add_argument("--scales", default="20,30")
    parser.add_argument(
        "--p0-admission-limit-by-scale",
        default="5=8,10=16,20=32,30=64",
        help="Comma-separated scale=limit map from the frozen P0 profile.",
    )
    parser.add_argument(
        "--model-call-wall-sec-upper-bound",
        type=float,
        default=0.001,
    )
    args = parser.parse_args()

    selected_scales = {
        int(value)
        for value in str(args.scales).split(",")
        if value.strip()
    }
    if not selected_scales or not selected_scales.issubset(
        {5, 10, 20, 30, 50, 100}
    ):
        raise SystemExit("unsupported --scales")
    admission_limit_by_scale = {}
    for token in str(args.p0_admission_limit_by_scale).split(","):
        scale_text, separator, limit_text = token.partition("=")
        if not separator:
            raise SystemExit("invalid --p0-admission-limit-by-scale")
        admission_limit_by_scale[int(scale_text)] = int(limit_text)
    if any(
        admission_limit_by_scale.get(scale, 0) <= 0
        for scale in selected_scales
    ):
        raise SystemExit("every selected scale needs a positive P0 limit")
    model_cost = float(args.model_call_wall_sec_upper_bound)
    if model_cost < 0.0:
        raise SystemExit("model cost upper bound must be nonnegative")

    manifest_path = Path(args.sentinel_manifest)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if str(manifest.get("schema_version") or "") != SENTINEL_SCHEMA:
        raise SystemExit("sentinel manifest schema mismatch")
    manifest_hash = stable_payload_hash(
        {
            key: value
            for key, value in manifest.items()
            if key != "manifest_hash"
        }
    )
    if str(manifest.get("manifest_hash") or "") != manifest_hash:
        raise SystemExit("sentinel manifest content hash mismatch")
    selected = {
        str(row["instance_content_hash"]): row
        for row in manifest.get("instances", ())
        if bool(row.get("selected"))
        and int(row.get("scale") or 0) in selected_scales
    }
    if not selected:
        raise SystemExit("no selected sentinel instances")

    by_context: dict[tuple[str, str], dict] = {}
    source_root = Path(args.training_rows_dir)
    for source in sorted(source_root.glob("*/*/harvest.json")):
        source_bytes = source.read_bytes()
        payload = json.loads(source_bytes)
        instance_hash = str(payload.get("instance_content_hash") or "")
        manifest_row = selected.get(instance_hash)
        if manifest_row is None:
            continue
        scale = int(payload.get("scale") or 0)
        if scale != int(manifest_row["scale"]):
            raise SystemExit("training row/sentinel scale mismatch")
        context_hash = str(payload.get("rmp_context_hash") or "")
        if not context_hash:
            raise SystemExit("harvest row lacks canonical RMP context hash")
        key = (instance_hash, context_hash)
        # Training rows are already canonical JSON.  Hash their immutable
        # transport bytes instead of serializing multi-megabyte feature
        # tensors a second time during a metadata-only opportunity scan.
        source_hash = hashlib.sha256(source_bytes).hexdigest()
        previous = by_context.get(key)
        if previous is not None:
            if previous["source_hash"] != source_hash:
                raise SystemExit(
                    "conflicting duplicate harvest context: "
                    f"{instance_hash}/{context_hash}"
                )
            continue
        grades = tuple(float(value) for value in payload.get(
            "harvest_grades", ()
        ))
        admission_limit = int(admission_limit_by_scale[scale])
        addable_count = sum(value >= 3.0 for value in grades)
        candidate_count = len(grades)
        effective_action_count = max(
            0, addable_count - admission_limit
        )
        candidate_ids = tuple(
            str(value)
            for value in payload.get("harvest_candidate_ids", ())
        )
        p0_selected_ids = tuple(
            str(value)
            for value in payload.get(
                "harvest_p0_selected_candidate_ids", ()
            )
        )
        p0_batch_identity_available = bool(
            len(candidate_ids) == candidate_count
            and len(candidate_ids) == len(set(candidate_ids))
            and len(p0_selected_ids)
            == min(admission_limit, addable_count)
            and set(p0_selected_ids).issubset(candidate_ids)
        )
        route_snapshot_path = source.with_name(
            "route_admission_snapshot.json"
        )
        lookahead_replay_ready = False
        route_snapshot_error = ""
        if route_snapshot_path.exists():
            try:
                route_snapshot = validate_route_admission_snapshot(
                    json.loads(
                        route_snapshot_path.read_text(encoding="utf-8")
                    )
                )
                lookahead_replay_ready = bool(
                    str(route_snapshot["instance_content_hash"])
                    == instance_hash
                    and str(route_snapshot["binding_hash"])
                    == context_hash
                )
                if not lookahead_replay_ready:
                    route_snapshot_error = (
                        "snapshot_harvest_context_identity_mismatch"
                    )
            except Exception as exc:
                route_snapshot_error = repr(exc)
        by_context[key] = {
            "source": source,
            "source_hash": source_hash,
            "scale": int(manifest_row["scale"]),
            "selection_probability": float(
                manifest_row["selection_probability"]
            ),
            "candidate_count": candidate_count,
            "addable_count": addable_count,
            "effective_action_count": effective_action_count,
            "admission_limit": admission_limit,
            "p0_batch_identity_available": (
                p0_batch_identity_available
            ),
            "route_snapshot_path": route_snapshot_path,
            "lookahead_replay_ready": lookahead_replay_ready,
            "route_snapshot_error": route_snapshot_error,
        }

    sequence_by_instance: dict[str, int] = {}
    output_rows = []
    for (instance_hash, context_hash), item in sorted(
        by_context.items()
    ):
        sequence = sequence_by_instance.get(instance_hash, 0)
        sequence_by_instance[instance_hash] = sequence + 1
        effective_count = int(item["effective_action_count"])
        addable_count = int(item["addable_count"])
        if addable_count < 2:
            status = "STRUCTURAL_ZERO_NO_LEGAL_ACTION"
        elif effective_count == 0:
            status = "STRUCTURAL_ZERO_ACTION_EQUIVALENT"
        else:
            status = "CENSORED_RESOURCE_OR_DISCOVERY"
        cheap_gate_eligible = effective_count > 0
        row = {
            "schema_version": OPPORTUNITY_OBSERVATION_SCHEMA_V1,
            "observation_id": stable_payload_hash(
                {
                    "selection_manifest_hash": manifest_hash,
                    "instance_content_hash": instance_hash,
                    "rmp_context_hash": context_hash,
                    "action_family": "route_admission",
                }
            ),
            "instance_content_hash": instance_hash,
            "rmp_context_hash": context_hash,
            "scale": int(item["scale"]),
            "sampling_stream": "sentinel",
            "selection_probability": float(
                item["selection_probability"]
            ),
            "selection_manifest_hash": manifest_hash,
            "selection_decision_pre_action": True,
            "target_condition_used_for_selection": False,
            "context_sequence_id": sequence,
            "solver_elapsed_sec": 0.0,
            "executed_objective_spec_id": OBJECTIVE_SPEC_ID,
            "cheap_gate_policy_version": (
                "p0_admission_pressure_preimport_v1"
            ),
            "cheap_gate_eligible": cheap_gate_eligible,
            # Zero is deliberately optimistic: the futility audit gives the
            # action family a free perfect pre-import gate.
            "cheap_gate_wall_sec": 0.0,
            "legal_action_count": max(1, addable_count),
            "route_admission_limit": int(item["admission_limit"]),
            "route_admission_addable_candidate_count": addable_count,
            "route_admission_effective_action_count": effective_count,
            "route_admission_structural_zero": effective_count == 0,
            "route_admission_p0_batch_identity_available": bool(
                item["p0_batch_identity_available"]
            ),
            "route_admission_lookahead_replay_ready": bool(
                item["lookahead_replay_ready"]
            ),
            "route_admission_target_objective_spec_id": (
                ROUTE_ADMISSION_LEXICOGRAPHIC_OBJECTIVE_SPEC_V2
            ),
            "route_admission_snapshot_path": (
                str(item["route_snapshot_path"].resolve())
                if item["route_snapshot_path"].exists()
                else ""
            ),
            "route_admission_snapshot_error": str(
                item["route_snapshot_error"]
            ),
            "rollout_attempted": False,
            "formal_label_available": False,
            "opportunity_outcome_status": status,
            "action_value_identifiable": False,
            "oracle_solver_gain": 0.0,
            "oracle_solver_gain_unit": "matched_end_to_end_wall_sec",
            "oracle_solver_time_saved_sec_lcb": None,
            "time_benefit_source": "",
            "model_would_be_invoked": cheap_gate_eligible,
            "model_call_wall_sec_upper_bound": (
                model_cost if cheap_gate_eligible else 0.0
            ),
            "model_cost_source": (
                "frozen_budget_upper_bound"
                if cheap_gate_eligible
                else ""
            ),
            "startup_cost_share_sec": 0.0,
            "censored_reason": (
                "matched_end_to_end_pair_not_collected"
                if effective_count > 0
                else ""
            ),
            "source_harvest_row": str(item["source"].resolve()),
            "source_harvest_row_hash": item["source_hash"],
            "calibration_used": False,
            "protected_final_test_used": False,
        }
        output_rows.append(validate_opportunity_observation(row))

    target = Path(args.output_jsonl)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in output_rows
        ),
        encoding="utf-8",
    )
    b0_by_instance = {}
    if str(args.b0_results_jsonl).strip():
        b0_path = Path(args.b0_results_jsonl)
        for line in b0_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                b0_row = json.loads(line)
                b0_by_instance[
                    str(b0_row.get("instance_content_hash") or "")
                ] = b0_row
    scale_reports = {}
    for scale in sorted(selected_scales):
        rows = [row for row in output_rows if int(row["scale"]) == scale]
        scale_reports[str(scale)] = {
            "selected_sentinel_instance_count": len(
                {
                    row["instance_content_hash"]
                    for row in rows
                }
            ),
            "unique_canonical_context_count": len(rows),
            "structural_zero_context_count": sum(
                bool(row["route_admission_structural_zero"])
                for row in rows
            ),
            "effective_action_context_count": sum(
                int(row["route_admission_effective_action_count"]) > 0
                for row in rows
            ),
            "effective_action_instance_count": len(
                {
                    row["instance_content_hash"]
                    for row in rows
                    if int(
                        row["route_admission_effective_action_count"]
                    )
                    > 0
                }
            ),
            "effective_action_p0_batch_identity_context_count": sum(
                int(row["route_admission_effective_action_count"]) > 0
                and bool(
                    row[
                        "route_admission_p0_batch_identity_available"
                    ]
                )
                for row in rows
            ),
            "effective_action_lookahead_replay_ready_context_count": sum(
                int(row["route_admission_effective_action_count"]) > 0
                and bool(
                    row["route_admission_lookahead_replay_ready"]
                )
                for row in rows
            ),
            "matched_end_to_end_pair_count": 0,
            "effective_action_exact_complete_instance_count": len(
                {
                    row["instance_content_hash"]
                    for row in rows
                    if int(
                        row["route_admission_effective_action_count"]
                    )
                    > 0
                    and bool(
                        b0_by_instance.get(
                            row["instance_content_hash"], {}
                        ).get("bpc_tree_optimal")
                    )
                    and str(
                        b0_by_instance.get(
                            row["instance_content_hash"], {}
                        ).get("algorithm_status")
                        or ""
                    )
                    == "BPC_OPTIMAL"
                }
            ),
            "effective_action_b0_status_counts": _status_counts(
                b0_by_instance.get(row["instance_content_hash"], {}).get(
                    "algorithm_status"
                )
                for row in rows
                if int(row["route_admission_effective_action_count"]) > 0
            ),
        }
    report = {
        "schema_version": COLLECTION_SCHEMA,
        "sentinel_manifest": str(manifest_path.resolve()),
        "sentinel_manifest_hash": manifest_hash,
        "training_rows_dir": str(source_root.resolve()),
        "b0_results_jsonl": (
            str(Path(args.b0_results_jsonl).resolve())
            if str(args.b0_results_jsonl).strip()
            else ""
        ),
        "output_jsonl": str(target.resolve()),
        "executed_objective_spec_id": OBJECTIVE_SPEC_ID,
        "p0_admission_limit_by_scale": {
            str(scale): int(admission_limit_by_scale[scale])
            for scale in sorted(selected_scales)
        },
        "context_identity": (
            "instance_content_hash+rmp_context_hash"
        ),
        "duplicate_contexts_counted_as_samples": False,
        "fixed_pool_single_column_rollouts_used": False,
        "route_admission_target_objective_spec_id": (
            ROUTE_ADMISSION_LEXICOGRAPHIC_OBJECTIVE_SPEC_V2
        ),
        "route_admission_snapshot_replay_spec_id": (
            ROUTE_ADMISSION_OBJECTIVE_SPEC_V1
        ),
        "legacy_four_coefficient_cost_used": False,
        "cross_context_cost_normalization_used": False,
        "scale_reports": scale_reports,
        "minimum_unique_sentinel_instances_per_scale": 20,
        "sentinel_sample_threshold_reached": all(
            int(scale_reports[str(scale)][
                "selected_sentinel_instance_count"
            ])
            >= 20
            for scale in selected_scales
        ),
        "matched_end_to_end_sample_threshold_reached": False,
        "perfect_policy_net_gain_ucb95_sec_per_context": None,
        "route_admission_decision": (
            "BLOCK_LINEAR_MATCHED_END_TO_END_UNIDENTIFIABLE"
        ),
        "linear_training_authorized": False,
    }
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    print(str(report_path.resolve()))
    return 0


def _status_counts(values) -> dict[str, int]:
    counts = {}
    for value in values:
        key = str(value or "MISSING")
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


if __name__ == "__main__":
    raise SystemExit(main())
