#!/usr/bin/env python3
"""Build the bounded non-deployable sparse-tail GAT smoke dataset.

Two positive rows are mathematical-context S1 replays and are explicitly not
runtime-eligible.  The third row is the valid fully cold harmful closure pair.
The artifact exists to exercise feature/training/runtime plumbing only; it can
never authorize evaluation or deployment.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.exact.bpc.master.reduced_cost import (  # noqa: E402
    ReducedCostContext,
)
from lunar_ice_bpc.exact.core.cuts import stable_payload_hash  # noqa: E402
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.exact.core.journey import (  # noqa: E402
    journey_column_from_solution_payload,
)
from lunar_ice_bpc.guidance.sparse_tail_action import (  # noqa: E402
    SPARSE_TAIL_ACTIONS,
    build_sparse_tail_action_features,
    sparse_tail_feature_schema,
)


DATASET_SCHEMA = "lunar_ice_bpc.sparse_tail_gat_smoke_dataset.v1"
POSITIVE_REPLAYS = (
    ROOT
    / "runs/p0v4_v5_sparse_tail_headroom_pilot_20260801/"
    "scale30_instance003_round049_S1_margin3e6.json",
    ROOT
    / "runs/p0v4_v5_sparse_tail_headroom_pilot_20260801/"
    "scale50_instance001_round091_S1_margin3e6.json",
)
HARMFUL_PAIR = (
    ROOT / "runs/p0v4_v5_sparse_tail_e2e_pilot_20260801/paired_gate.json"
)
HARMFUL_PROBE = (
    ROOT
    / "runs/p0v4_v5_sparse_tail_e2e_pilot_20260801/S1/"
    "pools/scale_030/instance_003/stage_001/probe.json"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT
        / "runs/p0v4_v5_sparse_tail_gat_smoke_20260801/dataset",
    )
    args = parser.parse_args()
    output = _resolve(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)

    rows = []
    for index, replay_path in enumerate(POSITIVE_REPLAYS):
        replay = _load(replay_path)
        source_probe_path = Path(str(replay["source_probe"])).resolve()
        source_probe = _load(source_probe_path)
        round_index = int(replay["source_round"])
        history, round_row = _history_row(source_probe, round_index)
        context = _offline_context(
            instance_path=Path(str(replay["instance"])).resolve(),
            probe=source_probe,
            history=history,
            round_row=round_row,
            source_key={
                "replay_sha256": _sha256(replay_path),
                "source_probe_sha256": _sha256(source_probe_path),
                "round": round_index,
                "role": "mathematical_context_only",
            },
            runtime_eligible=False,
        )
        features = build_sparse_tail_action_features(context)
        source_wall = float(replay["source_round_proof_wall_sec"])
        action_wall = float(replay["fresh_process_wall_sec"])
        relative_gain = (source_wall - action_wall) / source_wall
        rows.append(
            _dataset_row(
                features=features,
                context_id=(
                    f"math_scale{int(replay['scale'])}_"
                    f"round{round_index:03d}"
                ),
                split="train" if index == 0 else "calibration",
                source_role="mathematical_context_only",
                runtime_eligible=False,
                beneficial=(True, False),
                observed_mask=(True, False),
                positive_relative_gain=(relative_gain, 0.0),
                delta_time_sec=(source_wall - action_wall, None),
                source_artifacts=(replay_path, source_probe_path),
                safety_issues=tuple(
                    (replay.get("safety") or {}).get("issues") or ()
                ),
            )
        )

    pair = _load(HARMFUL_PAIR)
    harmful_probe = _load(HARMFUL_PROBE)
    round_index = int(pair["s1"]["sparse_action_round"])
    history, round_row = _history_row(harmful_probe, round_index)
    context = _offline_context(
        instance_path=Path(str(harmful_probe["instance_path"])).resolve(),
        probe=harmful_probe,
        history=history,
        round_row=round_row,
        source_key={
            "paired_gate_sha256": _sha256(HARMFUL_PAIR),
            "probe_sha256": _sha256(HARMFUL_PROBE),
            "round": round_index,
            "role": "fully_cold_runtime_harmful",
        },
        runtime_eligible=True,
    )
    features = build_sparse_tail_action_features(context)
    rows.append(
        _dataset_row(
            features=features,
            context_id="runtime_scale30_round054_harmful",
            split="train",
            source_role="fully_cold_runtime_harmful",
            runtime_eligible=True,
            beneficial=(False, False),
            observed_mask=(True, False),
            positive_relative_gain=(0.0, 0.0),
            delta_time_sec=(
                float(pair["paired_effect"]["total_gain_sec"]),
                None,
            ),
            source_artifacts=(HARMFUL_PAIR, HARMFUL_PROBE),
            safety_issues=tuple(pair.get("issues") or ()),
        )
    )

    dataset_path = output / "sparse_tail_gat_smoke.jsonl"
    dataset_path.write_text(
        "".join(
            json.dumps(row, sort_keys=True) + "\n" for row in rows
        ),
        encoding="utf-8",
    )
    manifest = {
        "schema_version": DATASET_SCHEMA,
        "status": "ENGINEERING_SMOKE_DATASET_ONLY",
        "dataset": str(dataset_path.resolve()),
        "dataset_sha256": _sha256(dataset_path),
        "feature_schema": sparse_tail_feature_schema(),
        "feature_schema_hash": stable_payload_hash(
            sparse_tail_feature_schema()
        ),
        "row_count": len(rows),
        "runtime_eligible_row_count": sum(
            int(bool(row["runtime_eligible"])) for row in rows
        ),
        "mathematical_context_only_row_count": sum(
            int(row["source_role"] == "mathematical_context_only")
            for row in rows
        ),
        "observed_action_count": sum(
            sum(int(value) for value in row["observed_mask"])
            for row in rows
        ),
        "action_ids": list(SPARSE_TAIL_ACTIONS),
        "formal_training_authorized": False,
        "evaluation_authorized": False,
        "deployment_authorized": False,
        "blockers": [
            "only_one_runtime_eligible_context",
            "positive_rows_are_mathematical_context_replays",
            "no_instance_disjoint_harm_calibration_set",
        ],
        "rows": [
            {
                "context_id": row["context_id"],
                "split": row["split"],
                "source_role": row["source_role"],
                "runtime_eligible": row["runtime_eligible"],
                "feature_hash": row["feature_hash"],
            }
            for row in rows
        ],
    }
    manifest_path = output / "dataset_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


def _offline_context(
    *,
    instance_path: Path,
    probe: dict,
    history: list[dict],
    round_row: dict,
    source_key: dict,
    runtime_eligible: bool,
) -> dict:
    data = load_lunar_ice_data(_load(instance_path))
    dual = dict(round_row.get("dual_context") or {})
    reduced = ReducedCostContext(
        task_duals={
            str(key): float(value)
            for key, value in (dual.get("task_duals") or {}).items()
        },
        fleet_dual=float(dual.get("fleet_dual") or 0.0),
        cut_duals={
            str(key): float(value)
            for key, value in (dual.get("cut_duals") or {}).items()
        },
        dual_fingerprint=str(dual.get("dual_fingerprint") or ""),
        rmp_iteration_id=str(dual.get("rmp_iteration_id") or ""),
    )
    final_columns = tuple(
        journey_column_from_solution_payload(data, row)
        for row in (probe.get("active_columns") or ())
    )
    seed_count = len(final_columns) - sum(
        int(row.get("added_column_count") or 0)
        for row in history
    )
    prefix_count = max(
        0,
        seed_count
        + sum(
            int(row.get("added_column_count") or 0)
            for row in history
            if int(row.get("round") or 0) < int(round_row["round"])
        ),
    )
    master_columns = final_columns[:prefix_count]
    post_harvest = {
        "schema_version": (
            "lunar_ice_bpc.sparse_tail_post_harvest_context.v1"
        ),
        "node_id": str(round_row.get("node_id") or "root"),
        "harvest_pass_pricing_state": str(
            round_row.get("labeling_final_judge_harvest_pass_pricing_state")
            or "INCOMPLETE_LIMIT"
        ),
        "harvest_pass_status": "",
        "harvest_pass_wall_time_sec": float(
            round_row.get("labeling_final_judge_harvest_pass_wall_time")
            or 0.0
        ),
        "harvest_pass_processed_labels": int(
            round_row.get(
                "labeling_final_judge_harvest_pass_processed_labels"
            )
            or 0
        ),
        "harvest_pass_extended_labels": int(
            round_row.get("labels_extended") or 0
        ),
        "harvest_pass_raw_unique_negative_count": 0,
        "harvest_pass_true_audited_column_count": 0,
        "harvest_pass_best_true_rc": (
            round_row.get("final_judge_harvest_best_true_rc")
        ),
        "harvest_pass_search_exhaustive": False,
        "harvest_pass_frontier_empty": False,
        "harvest_pass_can_certify_no_negative": False,
        "audited_official_negative_column_count": 0,
    }
    if runtime_eligible:
        if not bool(
            round_row.get("one_deviation_sparse_tail_action_resolver_invoked")
            or round_row.get("one_deviation_sparse_tail_attempted")
        ):
            raise SystemExit("harmful runtime row lacks sparse-tail attempt")
    input_hash = stable_payload_hash(
        {
            "schema_version": "offline_sparse_tail_smoke_input.v1",
            **source_key,
        }
    )
    return {
        "data": data,
        "master_columns": master_columns,
        "master": SimpleNamespace(
            reduced_cost_context=reduced,
            objective=float(round_row.get("node_lp_bound") or 0.0),
        ),
        "round": int(round_row["round"]),
        "effective_harvest_target": int(
            round_row.get(
                "labeling_final_judge_effective_exact_harvest_target"
            )
            or probe.get("config", {}).get("batch_target")
            or 1
        ),
        "sparse_tail_time_cap_sec": 60.0,
        "prior_history": tuple(
            row
            for row in history
            if int(row.get("round") or 0) < int(round_row["round"])
        ),
        "post_harvest": post_harvest,
        "one_deviation_sparse_tail_decision_timing": (
            "after_empty_harvest_before_sparse_pass"
        ),
        "one_deviation_sparse_tail_input_hash": input_hash,
    }


def _dataset_row(
    *,
    features,
    context_id: str,
    split: str,
    source_role: str,
    runtime_eligible: bool,
    beneficial: tuple[bool, bool],
    observed_mask: tuple[bool, bool],
    positive_relative_gain: tuple[float, float],
    delta_time_sec: tuple[float | None, float | None],
    source_artifacts: tuple[Path, ...],
    safety_issues: tuple[str, ...],
) -> dict:
    feature_payload = features.payload()
    feature_schema_version = str(feature_payload.pop("schema_version"))
    row = {
        "schema_version": DATASET_SCHEMA,
        "feature_schema_version": feature_schema_version,
        "context_id": str(context_id),
        "split": str(split),
        "source_role": str(source_role),
        "runtime_eligible": bool(runtime_eligible),
        **feature_payload,
        "feature_hash": features.feature_hash,
        "beneficial": list(beneficial),
        "observed_mask": list(observed_mask),
        "positive_relative_gain": list(positive_relative_gain),
        "delta_time_sec": list(delta_time_sec),
        "memory_adverse_event": [False, False],
        "source_artifacts": [str(path.resolve()) for path in source_artifacts],
        "source_artifact_sha256": [
            _sha256(path) for path in source_artifacts
        ],
        "safety_issues": list(safety_issues),
        "certificate_authority": "none",
        "post_action_features_exposed_to_model": False,
    }
    if safety_issues:
        raise SystemExit(
            f"smoke source {context_id} has safety issues: {safety_issues}"
        )
    return row


def _history_row(probe: dict, round_index: int) -> tuple[list[dict], dict]:
    history = [dict(row) for row in (probe.get("history") or ())]
    matches = [
        row for row in history if int(row.get("round") or 0) == round_index
    ]
    if len(matches) != 1:
        raise SystemExit(f"round {round_index} is not unique in source probe")
    return history, matches[0]


def _load(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _resolve(path: Path) -> Path:
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


if __name__ == "__main__":
    raise SystemExit(main())
