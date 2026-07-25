#!/usr/bin/env python3
"""Compare P0, linear, MLP, and GAT ordering on immutable snapshots."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from math import log1p
from pathlib import Path
from statistics import mean, median
from time import perf_counter

import torch

from lunar_ice_bpc.exact.bpc.guidance.replay import (
    load_pricing_snapshot,
    replay_pricing_ordering,
)
from lunar_ice_bpc.exact.bpc.pricing.backends import BackendPricingRequest
from lunar_ice_bpc.exact.core.branching import branch_context_from_payload
from lunar_ice_bpc.exact.core.cuts import cut_context_from_payload
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals
from lunar_ice_bpc.guidance.models import load_checkpoint
from lunar_ice_bpc.guidance.tensorization import (
    build_static_graph_features,
    dynamic_node_features,
    encode_queue_policy_id,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot-dir", required=True)
    parser.add_argument("--development-manifest", required=True)
    parser.add_argument("--split-manifest", required=True)
    parser.add_argument("--checkpoint", action="append", default=[])
    parser.add_argument("--fold", type=int, required=True)
    parser.add_argument("--output-jsonl", required=True)
    parser.add_argument("--torch-threads", type=int, default=2)
    args = parser.parse_args()
    torch.set_num_threads(max(1, int(args.torch_threads)))

    split = json.loads(
        Path(args.split_manifest).read_text(encoding="utf-8")
    )
    if not bool((split.get("audit") or {}).get("passed")):
        raise SystemExit("split manifest audit did not pass")
    fold = int(args.fold)
    if fold not in range(int(split["fold_count"])):
        raise SystemExit(f"invalid fold {fold}")
    validation_hashes = {
        str(row["instance_content_hash"])
        for row in split.get("development", ())
        if int(row["fold"]) == fold
    }
    forbidden_hashes = {
        str(row["instance_content_hash"])
        for partition in ("calibration", "protected_final_test")
        for row in split.get(partition, ())
    }
    development = json.loads(
        Path(args.development_manifest).read_text(encoding="utf-8")
    )
    instance_paths = {
        str(row["instance_content_hash"]): Path(row["path"])
        for row in development.get("instances", ())
    }

    checkpoints = []
    for raw_path in args.checkpoint:
        started = perf_counter()
        model, metadata = load_checkpoint(raw_path, map_location="cpu")
        if int(metadata.get("fold", -1)) != fold:
            raise SystemExit(
                f"checkpoint fold mismatch for {raw_path}: "
                f"{metadata.get('fold')} != {fold}"
            )
        if str(metadata.get("split_manifest_hash") or "") != str(
            split.get("manifest_hash") or ""
        ):
            raise SystemExit(
                f"checkpoint split manifest mismatch for {raw_path}"
            )
        checkpoints.append(
            {
                "path": str(Path(raw_path).resolve()),
                "model": model,
                "metadata": metadata,
                "model_kind": str(model.kind),
                "checkpoint_id": str(metadata["checkpoint_id"]),
                "load_sec": perf_counter() - started,
            }
        )

    output = Path(args.output_jsonl)
    output.parent.mkdir(parents=True, exist_ok=True)
    results = []
    seen = set()
    for snapshot_path in sorted(Path(args.snapshot_dir).rglob("*.json")):
        content_hint = snapshot_path.parent.name
        if (
            content_hint in forbidden_hashes
            or content_hint not in validation_hashes
        ):
            # Snapshot storage is content-hash partitioned, so forbidden
            # partitions can be skipped without deserializing their context.
            continue
        snapshot = load_pricing_snapshot(snapshot_path)
        content_hash = snapshot.instance_content_hash
        if content_hash in forbidden_hashes:
            raise SystemExit(
                f"forbidden calibration/protected snapshot encountered: "
                f"{content_hash}"
            )
        if content_hash not in validation_hashes:
            continue
        context_key = (content_hash, snapshot.binding.binding_hash)
        if context_key in seen:
            continue
        seen.add(context_key)
        instance_path = instance_paths.get(content_hash)
        if instance_path is None:
            raise SystemExit(f"instance path missing for {content_hash}")
        data = load_lunar_ice_data(
            json.loads(instance_path.read_text(encoding="utf-8"))
        )
        request = _request_from_snapshot(snapshot, data)
        static = build_static_graph_features(data)
        dynamic = dynamic_node_features(request)
        raw_node = torch.tensor(
            [
                list(static_row) + list(dynamic_row)
                for static_row, dynamic_row in zip(
                    static.node_features, dynamic, strict=True
                )
            ],
            dtype=torch.float32,
        )
        raw_edge = torch.tensor(
            static.arc_features, dtype=torch.float32
        )
        common = {
            "snapshot_hash": snapshot.snapshot_hash,
            "binding_hash": snapshot.binding.binding_hash,
            "instance_content_hash": content_hash,
            "scale": data.scale,
            "fold": fold,
            "censored": snapshot.censored,
        }
        p0_result = replay_pricing_ordering(snapshot, priorities={}, enabled=False)
        results.append(
            {
                **common,
                "ranker": "P0_deterministic",
                "checkpoint_id": "",
                "model_kind": "deterministic",
                "inference_sec": 0.0,
                **_ranking_metrics(snapshot, p0_result["replay_ordering"]),
                "legal_universe_preserved": (
                    p0_result["ordering_audit"][
                        "legal_action_universe_hash_before_sort"
                    ]
                    == p0_result["ordering_audit"][
                        "legal_action_universe_hash_after_sort"
                    ]
                ),
            }
        )
        for checkpoint in checkpoints:
            inference_started = perf_counter()
            priorities = _checkpoint_priorities(
                checkpoint,
                snapshot=snapshot,
                static=static,
                raw_node=raw_node,
                raw_edge=raw_edge,
            )
            replay = replay_pricing_ordering(
                snapshot,
                priorities=priorities,
                expected_binding_hash=snapshot.binding.binding_hash,
            )
            results.append(
                {
                    **common,
                    "ranker": checkpoint["checkpoint_id"],
                    "checkpoint_id": checkpoint["checkpoint_id"],
                    "model_kind": checkpoint["model_kind"],
                    "inference_sec": perf_counter() - inference_started,
                    **_ranking_metrics(
                        snapshot, replay["replay_ordering"]
                    ),
                    "legal_universe_preserved": (
                        replay["ordering_audit"][
                            "legal_action_universe_hash_before_sort"
                        ]
                        == replay["ordering_audit"][
                            "legal_action_universe_hash_after_sort"
                        ]
                    ),
                }
            )

    if not results:
        raise SystemExit("no validation-fold snapshots found")
    output.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in results
        ),
        encoding="utf-8",
    )
    by_ranker = defaultdict(list)
    for row in results:
        by_ranker[row["ranker"]].append(row)
    report = {
        "schema_version": "lunar_ice_bpc.gat_snapshot_model_replay.v1",
        "split_manifest_hash": split.get("manifest_hash"),
        "partition": "development_validation_fold_only",
        "fold": fold,
        "context_count": len(seen),
        "calibration_used": False,
        "protected_final_test_used": False,
        "all_legal_universes_preserved": all(
            row["legal_universe_preserved"] for row in results
        ),
        "checkpoint_load_sec": {
            row["checkpoint_id"]: row["load_sec"] for row in checkpoints
        },
        "ranker_summary": {
            ranker: _ranker_summary(rows)
            for ranker, rows in sorted(by_ranker.items())
        },
        "result_semantics_changed": False,
        "can_certify": False,
    }
    report_path = output.with_suffix(output.suffix + ".report.json")
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    print(str(report_path.resolve()))
    return 0


def _request_from_snapshot(snapshot, data) -> BackendPricingRequest:
    return BackendPricingRequest(
        data=data,
        true_duals=JourneyDuals(
            cover=dict(snapshot.true_duals.get("cover") or {}),
            fleet_limit=_optional_float_default(
                snapshot.true_duals.get("fleet_limit"), 0.0
            ),
            cuts=dict(snapshot.true_duals.get("cuts") or {}),
        ),
        mode=snapshot.pricing_mode,
        objective_mode=snapshot.objective_mode,
        branch_context=branch_context_from_payload(snapshot.branch_context),
        cut_context=cut_context_from_payload(snapshot.full_cut_context),
        wall_time_limit_sec=snapshot.wall_time_budget_sec,
        memory_limit_gb=snapshot.memory_limit_gb,
        instance_hash=snapshot.binding.instance_hash,
        config_hash=snapshot.binding.config_hash,
        engine_hash=snapshot.binding.engine_hash,
        dual_binding_hash=snapshot.binding.mathematical_dual_hash,
        cut_lineage_hash=snapshot.binding.cut_lineage_hash,
        live_cut_policy_hash=snapshot.binding.live_cut_policy_hash,
        rmp_iteration_id=snapshot.binding.rmp_iteration_id,
        separator_policy_version=snapshot.binding.separator_policy_version,
    )


def _checkpoint_priorities(
    checkpoint,
    *,
    snapshot,
    static,
    raw_node,
    raw_edge,
) -> dict[str, float]:
    metadata = checkpoint["metadata"]
    node_mean = torch.tensor(
        metadata["node_feature_mean"], dtype=torch.float32
    )
    node_std = torch.tensor(
        metadata["node_feature_std"], dtype=torch.float32
    ).clamp_min(1.0e-8)
    edge_mean = torch.tensor(
        metadata["edge_feature_mean"], dtype=torch.float32
    )
    edge_std = torch.tensor(
        metadata["edge_feature_std"], dtype=torch.float32
    ).clamp_min(1.0e-8)
    if (
        raw_node.shape[1] != node_mean.numel()
        or raw_edge.shape[1] != edge_mean.numel()
    ):
        raise ValueError("snapshot/checkpoint feature width mismatch")
    inputs = {
        "node_features": (raw_node - node_mean) / node_std,
        "edge_index": torch.tensor(
            (static.arc_sources, static.arc_targets), dtype=torch.long
        ),
        "edge_features": (raw_edge - edge_mean) / edge_std,
        "task_node_indices": torch.arange(
            1, len(static.node_ids), dtype=torch.long
        ),
        "resource_context": torch.tensor(
            (
                log1p(
                    max(0.0, snapshot.memory_limit_gb) * (1024.0**3)
                ),
                log1p(
                    0.0
                    if snapshot.wall_time_budget_sec is None
                    else max(0.0, snapshot.wall_time_budget_sec)
                ),
                1.0 if snapshot.pricing_mode == "exact_proof" else 0.0,
                encode_queue_policy_id(snapshot.queue_policy_id),
            ),
            dtype=torch.float32,
        ),
    }
    with torch.inference_mode():
        prediction = checkpoint["model"](**inputs)
    task_scores = [
        float(value) for value in prediction["task_scores"]
    ]
    arc_scores = [float(value) for value in prediction["arc_scores"]]
    return {
        **dict(zip(static.node_ids[1:], task_scores, strict=True)),
        **dict(
            zip(static.arc_candidate_ids, arc_scores, strict=True)
        ),
    }


def _ranking_metrics(snapshot, ordering: list[str]) -> dict:
    by_id = {
        str(row["candidate_id"]): row for row in snapshot.candidate_rows
    }
    observed_positive = {
        candidate_id
        for candidate_id, row in by_id.items()
        if bool(row.get("training_observed"))
        and float(row.get("training_grade") or 0.0) >= 3.0
    }
    first_rank = next(
        (
            index
            for index, candidate_id in enumerate(ordering, start=1)
            if candidate_id in observed_positive
        ),
        None,
    )
    top5 = set(ordering[:5])
    return {
        "observed_positive_count": len(observed_positive),
        "first_observed_negative_candidate_rank": first_rank,
        "observed_top5_recall": (
            0.0
            if not observed_positive
            else len(top5.intersection(observed_positive))
            / len(observed_positive)
        ),
    }


def _ranker_summary(rows: list[dict]) -> dict:
    evaluable_ranks = [
        int(row["first_observed_negative_candidate_rank"])
        for row in rows
        if row["first_observed_negative_candidate_rank"] is not None
    ]
    return {
        "context_count": len(rows),
        "observed_negative_evaluable_context_count": len(evaluable_ranks),
        "first_observed_negative_candidate_rank_p50": (
            None if not evaluable_ranks else median(evaluable_ranks)
        ),
        "observed_top5_recall_mean": mean(
            row["observed_top5_recall"] for row in rows
        ),
        "inference_sec_mean": mean(
            row["inference_sec"] for row in rows
        ),
        "not_a_stage_b_first_addable_metric": True,
    }


def _optional_float_default(value, default: float) -> float:
    return float(default) if value is None else float(value)


if __name__ == "__main__":
    raise SystemExit(main())
