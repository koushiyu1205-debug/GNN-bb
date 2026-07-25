#!/usr/bin/env python3
"""Replay route-level harvest ranking on one development validation fold.

This is an offline discovery diagnostic.  It never mutates a solver, never
touches calibration/final-test rows, and cannot certify an online H promotion.
Legacy v1 rows did not record active-task-set membership, so they support an
exact comparison of the pre-selector candidate ordering only.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from math import log2
from pathlib import Path
from statistics import mean, median
from time import perf_counter

import torch

from lunar_ice_bpc.exact.core.cuts import stable_payload_hash
from lunar_ice_bpc.guidance.models import load_checkpoint
from lunar_ice_bpc.guidance.tensorization import (
    HARVEST_MODEL_CONTEXT_SCHEMA_V2,
    learned_harvest_context,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records-jsonl", required=True)
    parser.add_argument("--split-manifest", required=True)
    parser.add_argument("--static-cache-dir", required=True)
    parser.add_argument("--checkpoint", required=True)
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

    load_started = perf_counter()
    model, metadata = load_checkpoint(args.checkpoint, map_location="cpu")
    checkpoint_load_sec = perf_counter() - load_started
    if int(metadata.get("fold", -1)) != fold:
        raise SystemExit(
            f"checkpoint fold mismatch: {metadata.get('fold')} != {fold}"
        )
    if str(metadata.get("split_manifest_hash") or "") != str(
        split.get("manifest_hash") or ""
    ):
        raise SystemExit("checkpoint split manifest mismatch")
    model.eval()
    if str(
        metadata.get("harvest_model_context_schema_version") or ""
    ) != HARVEST_MODEL_CONTEXT_SCHEMA_V2:
        raise SystemExit(
            "checkpoint uses an obsolete/leaky harvest model context"
        )

    cache_dir = Path(args.static_cache_dir)
    static_cache: dict[str, dict] = {}
    results: list[dict] = []
    seen_contexts: set[tuple[str, str]] = set()
    legacy_context_count = 0
    input_line_count = 0
    with Path(args.records_jsonl).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            input_line_count += 1
            row = json.loads(line)
            if str(row.get("head") or "") != "harvest":
                continue
            content_hash = str(row["instance_content_hash"])
            if content_hash in forbidden_hashes:
                raise SystemExit(
                    "calibration/protected harvest row supplied to replay: "
                    f"{content_hash}"
                )
            if content_hash not in validation_hashes:
                continue
            context_key = (
                content_hash,
                str(row.get("rmp_context_hash") or ""),
            )
            if context_key in seen_contexts:
                raise SystemExit(f"duplicate harvest context: {context_key}")
            seen_contexts.add(context_key)

            static = _load_static_sidecar(
                row, cache_dir=cache_dir, cache=static_cache
            )
            raw_node = _node_features(row, static=static)
            raw_edge = torch.tensor(
                static["edge_features"], dtype=torch.float32
            )
            masks = torch.tensor(
                row["harvest_task_masks"], dtype=torch.float32
            )
            contexts = torch.tensor(
                row["harvest_context"], dtype=torch.float32
            )
            model_contexts = torch.tensor(
                [
                    learned_harvest_context(values)
                    for values in row["harvest_context"]
                ],
                dtype=torch.float32,
            )
            grades = [float(value) for value in row["harvest_grades"]]
            candidate_count = len(grades)
            if (
                masks.shape[0] != candidate_count
                or contexts.shape != (candidate_count, 4)
            ):
                raise SystemExit("harvest candidate tensor length mismatch")

            inference_started = perf_counter()
            with torch.inference_mode():
                prediction = model(
                    node_features=_normalize(
                        raw_node,
                        metadata["node_feature_mean"],
                        metadata["node_feature_std"],
                    ),
                    edge_index=torch.tensor(
                        static["edge_index"], dtype=torch.long
                    ),
                    edge_features=_normalize(
                        raw_edge,
                        metadata["edge_feature_mean"],
                        metadata["edge_feature_std"],
                    ),
                    task_node_indices=torch.tensor(
                        static["task_node_indices"], dtype=torch.long
                    ),
                    resource_context=torch.tensor(
                        row["resource_context"], dtype=torch.float32
                    ),
                    harvest_task_masks=masks,
                    harvest_context=model_contexts,
                )
            inference_sec = perf_counter() - inference_started
            scores = [
                float(value)
                for value in prediction["harvest_scores"].tolist()
            ]
            descriptors = _candidate_descriptors(row)
            universe_hash = _universe_hash(descriptors)
            p0_order = sorted(
                range(candidate_count),
                key=lambda index: (
                    float(contexts[index, 0]),
                    descriptors[index]["task_indices"],
                    index,
                ),
            )
            learned_order = sorted(
                range(candidate_count),
                key=lambda index: (
                    -scores[index],
                    float(contexts[index, 0]),
                    descriptors[index]["task_indices"],
                    index,
                ),
            )
            learned_universe_hash = _universe_hash(
                [descriptors[index] for index in learned_order]
            )
            schema = str(row.get("schema_version") or "")
            selector_context_exact = (
                schema.endswith(".v2")
                and list(row.get("harvest_context_schema") or ())
                == [
                    "true_reduced_cost",
                    "would_change_active_support",
                    "is_new_task_set",
                    "task_fraction",
                ]
            )
            if not selector_context_exact:
                legacy_context_count += 1
            common = {
                "instance_content_hash": content_hash,
                "rmp_context_hash": context_key[1],
                "scale": int(row["scale"]),
                "fold": fold,
                "candidate_count": candidate_count,
                "informative_grade_context": len(set(grades)) > 1,
                "selector_context_exact": selector_context_exact,
                "legal_action_universe_hash_before_sort": universe_hash,
            }
            results.extend(
                (
                    {
                        **common,
                        "ranker": "P0_deterministic",
                        "checkpoint_id": "",
                        "model_kind": "deterministic",
                        "inference_sec": 0.0,
                        "legal_action_universe_hash_after_sort": _universe_hash(
                            [descriptors[index] for index in p0_order]
                        ),
                        **_ranking_metrics(grades, p0_order),
                    },
                    {
                        **common,
                        "ranker": str(metadata["checkpoint_id"]),
                        "checkpoint_id": str(metadata["checkpoint_id"]),
                        "model_kind": str(model.kind),
                        "inference_sec": inference_sec,
                        "legal_action_universe_hash_after_sort": (
                            learned_universe_hash
                        ),
                        **_ranking_metrics(grades, learned_order),
                    },
                )
            )

    if not results:
        raise SystemExit("no validation-fold harvest rows found")
    for result in results:
        result["legal_universe_preserved"] = (
            result["legal_action_universe_hash_before_sort"]
            == result["legal_action_universe_hash_after_sort"]
        )
    output = Path(args.output_jsonl)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in results
        ),
        encoding="utf-8",
    )
    by_ranker = defaultdict(list)
    for result in results:
        by_ranker[result["ranker"]].append(result)
    report = {
        "schema_version": "lunar_ice_bpc.gat_harvest_row_replay.v1",
        "split_manifest_hash": split.get("manifest_hash"),
        "partition": "development_validation_fold_only",
        "fold": fold,
        "checkpoint": str(Path(args.checkpoint).resolve()),
        "checkpoint_id": str(metadata["checkpoint_id"]),
        "model_kind": str(model.kind),
        "harvest_model_context_schema_version": (
            HARVEST_MODEL_CONTEXT_SCHEMA_V2
        ),
        "checkpoint_load_sec": checkpoint_load_sec,
        "input_line_count": input_line_count,
        "context_count": len(seen_contexts),
        "legacy_v1_context_count": legacy_context_count,
        "selector_exact_replay": legacy_context_count == 0,
        "selector_replay_limitation": (
            ""
            if legacy_context_count == 0
            else (
                "v1 rows do not record active-task-set membership; metrics "
                "compare exact pre-selector candidate order only"
            )
        ),
        "calibration_used": False,
        "protected_final_test_used": False,
        "all_legal_universes_preserved": all(
            row["legal_universe_preserved"] for row in results
        ),
        "guidance_filter_count": 0,
        "ranker_summary": {
            ranker: _ranker_summary(rows)
            for ranker, rows in sorted(by_ranker.items())
        },
        "result_semantics_changed": False,
        "online_h_promotion_evidence": False,
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


def _load_static_sidecar(
    row: dict, *, cache_dir: Path, cache: dict[str, dict]
) -> dict:
    key = str(row.get("static_tensor_cache_key") or "")
    if not key or key != str(row.get("instance_content_hash") or ""):
        raise SystemExit("harvest row/static tensor identity mismatch")
    payload = cache.get(key)
    if payload is None:
        path = cache_dir / f"{key}.json"
        if not path.exists():
            raise SystemExit(f"static tensor sidecar missing: {key}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        observed_hash = str(
            payload.get("static_tensor_cache_hash") or ""
        )
        unsigned = dict(payload)
        unsigned.pop("static_tensor_cache_hash", None)
        if (
            str(payload.get("instance_content_hash") or "") != key
            or not observed_hash
            or stable_payload_hash(unsigned) != observed_hash
        ):
            raise SystemExit(f"stale static tensor sidecar rejected: {key}")
        cache[key] = payload
    if str(row.get("static_tensor_cache_hash") or "") != str(
        payload["static_tensor_cache_hash"]
    ):
        raise SystemExit("harvest row/static tensor hash mismatch")
    return payload


def _node_features(row: dict, *, static: dict) -> torch.Tensor:
    static_node = list(static["node_static_features"])
    dynamic = list(row.get("dynamic_node_features") or ())
    if len(static_node) != len(dynamic):
        raise SystemExit("harvest static/dynamic node count mismatch")
    return torch.tensor(
        [
            [*static_values, *dynamic_values]
            for static_values, dynamic_values in zip(
                static_node, dynamic, strict=True
            )
        ],
        dtype=torch.float32,
    )


def _normalize(
    values: torch.Tensor, mean_values: list, std_values: list
) -> torch.Tensor:
    feature_mean = torch.tensor(mean_values, dtype=torch.float32)
    feature_std = torch.tensor(
        std_values, dtype=torch.float32
    ).clamp_min(1.0e-8)
    if values.shape[1] != feature_mean.numel():
        raise SystemExit("harvest/checkpoint feature width mismatch")
    return (values - feature_mean) / feature_std


def _candidate_descriptors(row: dict) -> list[dict]:
    descriptors = []
    for index, (mask, context, grade) in enumerate(
        zip(
            row["harvest_task_masks"],
            row["harvest_context"],
            row["harvest_grades"],
            strict=True,
        )
    ):
        descriptors.append(
            {
                "candidate_sequence_id": index,
                "task_indices": tuple(
                    task_index
                    for task_index, value in enumerate(mask)
                    if float(value) > 0.5
                ),
                "true_reduced_cost": float(context[0]),
                "would_change_active_support": float(context[1]) > 0.5,
                "grade": float(grade),
            }
        )
    return descriptors


def _universe_hash(descriptors: list[dict]) -> str:
    # Hash a canonical multiset, not the current order.
    return stable_payload_hash(
        {
            "universe_kind": "offline_harvest_training_candidates",
            "members": sorted(
                (
                    {
                        **descriptor,
                        "task_indices": list(descriptor["task_indices"]),
                    }
                    for descriptor in descriptors
                ),
                key=lambda row: int(row["candidate_sequence_id"]),
            ),
        }
    )


def _ranking_metrics(grades: list[float], ordering: list[int]) -> dict:
    useful = {index for index, grade in enumerate(grades) if grade >= 4.0}
    addable = {index for index, grade in enumerate(grades) if grade >= 3.0}
    first_useful = next(
        (
            rank
            for rank, index in enumerate(ordering, start=1)
            if index in useful
        ),
        None,
    )
    top5 = set(ordering[:5])
    ideal = sorted(grades, reverse=True)
    return {
        "useful_candidate_count": len(useful),
        "addable_candidate_count": len(addable),
        "first_useful_candidate_rank": first_useful,
        "useful_top5_recall": (
            0.0 if not useful else len(top5 & useful) / len(useful)
        ),
        "useful_top5_precision": (
            0.0 if not ordering else len(top5 & useful) / min(5, len(ordering))
        ),
        "graded_ndcg_at_5": _dcg(
            [grades[index] for index in ordering[:5]]
        )
        / max(_dcg(ideal[:5]), 1.0e-12),
    }


def _dcg(values: list[float]) -> float:
    return sum(
        (2.0 ** float(value) - 1.0) / log2(rank + 1.0)
        for rank, value in enumerate(values, start=1)
    )


def _ranker_summary(rows: list[dict]) -> dict:
    ranks = [
        int(row["first_useful_candidate_rank"])
        for row in rows
        if row["first_useful_candidate_rank"] is not None
    ]
    informative = [
        row for row in rows if bool(row["informative_grade_context"])
    ]
    informative_ranks = [
        int(row["first_useful_candidate_rank"])
        for row in informative
        if row["first_useful_candidate_rank"] is not None
    ]
    return {
        "context_count": len(rows),
        "informative_grade_context_count": len(informative),
        "first_useful_candidate_rank_p50": (
            None if not ranks else median(ranks)
        ),
        "first_useful_candidate_rank_mean": (
            None if not ranks else mean(ranks)
        ),
        "informative_first_useful_rank_p50": (
            None if not informative_ranks else median(informative_ranks)
        ),
        "informative_first_useful_rank_mean": (
            None if not informative_ranks else mean(informative_ranks)
        ),
        "useful_top5_recall_mean": mean(
            row["useful_top5_recall"] for row in rows
        ),
        "useful_top5_precision_mean": mean(
            row["useful_top5_precision"] for row in rows
        ),
        "graded_ndcg_at_5_mean": mean(
            row["graded_ndcg_at_5"] for row in rows
        ),
        "inference_sec_mean": mean(
            row["inference_sec"] for row in rows
        ),
        "not_a_stage_b_first_addable_metric": True,
    }


if __name__ == "__main__":
    raise SystemExit(main())
