#!/usr/bin/env python3
"""Select controlled replay candidates from counterfactual coverage data.

This script does not run or modify the solver.  It expands pure
improved-vs-pure worsened descriptor groups inside exact contexts into a
candidate manifest for a later no-certificate-effect replay harness.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path(
    "BPC_future/results/root_cause_counterfactual_replay_coverage_20260613/"
    "summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_counterfactual_replay_candidates_20260613"
)

DESCRIPTOR_FIELDS = (
    "best_rc",
    "selected_count",
    "materialized_count",
    "returned_count",
    "returned_union_size",
    "returned_task_sets",
    "returned_sequences",
    "returned_arc_families",
)


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _as_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _descriptor_support(group: dict[str, Any]) -> int:
    return int(group.get("rows") or 0)


def _descriptor_summary(group: dict[str, Any]) -> dict[str, Any]:
    descriptor = group.get("descriptor", {})
    return {
        "rows": _descriptor_support(group),
        "label_counts": group.get("label_counts", {}),
        "profile_counts": group.get("profile_counts", {}),
        "dataset_counts": group.get("dataset_counts", {}),
        "descriptor": {field: descriptor.get(field, "") for field in DESCRIPTOR_FIELDS},
        "samples": group.get("samples", []),
    }


def _score_pair(
    context: dict[str, Any],
    improved: dict[str, Any],
    worsened: dict[str, Any],
) -> float:
    improved_desc = improved.get("descriptor", {})
    worsened_desc = worsened.get("descriptor", {})
    support = _descriptor_support(improved) + _descriptor_support(worsened)
    no_mixed_bonus = 3.0 if int(context.get("mixed_descriptor_count") or 0) == 0 else 0.0
    support_bonus = min(support, 6) / 2.0
    pair_context_bonus = min(int(context.get("pure_descriptor_pair_count") or 0), 18) / 18.0
    rc_gap = abs(_as_float(improved_desc.get("best_rc")) - _as_float(worsened_desc.get("best_rc")))
    rc_bonus = min(rc_gap / 50.0, 1.0)
    returned_count_gap = abs(
        _as_int(improved_desc.get("returned_count"))
        - _as_int(worsened_desc.get("returned_count"))
    )
    structure_bonus = min(returned_count_gap, 8) / 8.0
    mixed_penalty = min(int(context.get("mixed_descriptor_count") or 0), 5) * 0.25
    return round(
        no_mixed_bonus
        + support_bonus
        + pair_context_bonus
        + rc_bonus
        + structure_bonus
        - mixed_penalty,
        6,
    )


def build_manifest(input_path: Path, top_n: int) -> dict[str, Any]:
    coverage = json.loads(input_path.read_text(encoding="utf-8"))
    candidates: list[dict[str, Any]] = []
    for context in coverage["mixed_contexts"]:
        if not context.get("has_replay_candidate_pairs"):
            continue
        for improved_idx, improved in enumerate(context.get("pure_improved_samples", [])):
            for worsened_idx, worsened in enumerate(context.get("pure_worsened_samples", [])):
                improved_desc = improved.get("descriptor", {})
                worsened_desc = worsened.get("descriptor", {})
                candidate = {
                    "context_key": context["context_key"],
                    "context_rows": context["rows"],
                    "context_label_counts": context["label_counts"],
                    "context_descriptor_group_count": context["descriptor_group_count"],
                    "context_pure_improved_descriptor_count": context[
                        "pure_improved_descriptor_count"
                    ],
                    "context_pure_worsened_descriptor_count": context[
                        "pure_worsened_descriptor_count"
                    ],
                    "context_mixed_descriptor_count": context["mixed_descriptor_count"],
                    "context_pure_descriptor_pair_count": context[
                        "pure_descriptor_pair_count"
                    ],
                    "improved_descriptor_index": improved_idx,
                    "worsened_descriptor_index": worsened_idx,
                    "improved_descriptor": _descriptor_summary(improved),
                    "worsened_descriptor": _descriptor_summary(worsened),
                    "best_rc_delta_improved_minus_worsened": round(
                        _as_float(improved_desc.get("best_rc"))
                        - _as_float(worsened_desc.get("best_rc")),
                        9,
                    ),
                    "returned_count_delta_improved_minus_worsened": (
                        _as_int(improved_desc.get("returned_count"))
                        - _as_int(worsened_desc.get("returned_count"))
                    ),
                    "returned_union_delta_improved_minus_worsened": (
                        _as_int(improved_desc.get("returned_union_size"))
                        - _as_int(worsened_desc.get("returned_union_size"))
                    ),
                    "candidate_risk": (
                        "low_context_noise"
                        if int(context.get("mixed_descriptor_count") or 0) == 0
                        else "mixed_descriptor_context"
                    ),
                }
                candidate["replay_priority_score"] = _score_pair(
                    context, improved, worsened
                )
                candidates.append(candidate)
    candidates.sort(
        key=lambda item: (
            item["candidate_risk"] != "low_context_noise",
            -item["replay_priority_score"],
            -item["improved_descriptor"]["rows"],
            -item["worsened_descriptor"]["rows"],
            item["context_key"],
        )
    )
    for index, candidate in enumerate(candidates, start=1):
        candidate["candidate_id"] = f"replay_candidate_{index:03d}"
    low_noise = [item for item in candidates if item["candidate_risk"] == "low_context_noise"]
    mixed_context = [
        item for item in candidates if item["candidate_risk"] == "mixed_descriptor_context"
    ]
    selected: list[dict[str, Any]] = []
    selected_contexts: set[tuple[str, ...]] = set()
    for candidate in low_noise:
        context_key = tuple(candidate["context_key"])
        if context_key in selected_contexts:
            continue
        selected.append(candidate)
        selected_contexts.add(context_key)
        if len(selected) >= 2:
            break
    if len(selected) < min(2, len(low_noise)):
        for candidate in low_noise:
            if candidate in selected:
                continue
            selected.append(candidate)
            if len(selected) >= min(2, len(low_noise)):
                break
    if mixed_context:
        selected.append(mixed_context[0])
    for candidate in candidates:
        candidate["recommended_for_first_replay_batch"] = (
            candidate in selected[:top_n]
        )
    return {
        "input": str(input_path),
        "coverage_summary": {
            "rows": coverage["rows"],
            "mixed_context_count": coverage["mixed_context_count"],
            "pure_descriptor_pair_count": coverage["pure_descriptor_pair_count"],
            "replay_candidate_context_count": coverage["replay_candidate_context_count"],
            "mixed_descriptor_context_count": coverage["mixed_descriptor_context_count"],
        },
        "selection_policy": {
            "description": (
                "Prefer low-context-noise pairs first, then include one high-coverage "
                "mixed-descriptor context as a stress case. Candidates are not "
                "optimization evidence until controlled replay confirms them."
            ),
            "top_n": top_n,
        },
        "candidate_count": len(candidates),
        "low_context_noise_candidate_count": len(low_noise),
        "mixed_descriptor_context_candidate_count": len(mixed_context),
        "recommended_candidate_ids": [
            item["candidate_id"]
            for item in candidates
            if item.get("recommended_for_first_replay_batch")
        ],
        "candidates": candidates,
        "checks": {
            "has_manifest_candidates": len(candidates) == coverage["pure_descriptor_pair_count"],
            "has_low_context_noise_candidates": len(low_noise) >= 2,
            "has_mixed_context_stress_candidate": bool(mixed_context),
            "recommended_batch_is_small": 1 <= len(selected[:top_n]) <= top_n,
        },
    }


def _write_csv(path: Path, candidates: list[dict[str, Any]]) -> None:
    fieldnames = (
        "candidate_id",
        "recommended_for_first_replay_batch",
        "candidate_risk",
        "replay_priority_score",
        "context_key",
        "context_rows",
        "context_label_counts",
        "context_mixed_descriptor_count",
        "improved_rows",
        "worsened_rows",
        "improved_best_rc",
        "worsened_best_rc",
        "best_rc_delta_improved_minus_worsened",
        "improved_returned_count",
        "worsened_returned_count",
        "improved_returned_task_sets",
        "worsened_returned_task_sets",
        "improved_returned_sequences",
        "worsened_returned_sequences",
        "improved_returned_arc_families",
        "worsened_returned_arc_families",
    )
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in candidates:
            improved = item["improved_descriptor"]["descriptor"]
            worsened = item["worsened_descriptor"]["descriptor"]
            writer.writerow(
                {
                    "candidate_id": item["candidate_id"],
                    "recommended_for_first_replay_batch": item[
                        "recommended_for_first_replay_batch"
                    ],
                    "candidate_risk": item["candidate_risk"],
                    "replay_priority_score": item["replay_priority_score"],
                    "context_key": "|".join(item["context_key"]),
                    "context_rows": item["context_rows"],
                    "context_label_counts": json.dumps(
                        item["context_label_counts"],
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                    "context_mixed_descriptor_count": item[
                        "context_mixed_descriptor_count"
                    ],
                    "improved_rows": item["improved_descriptor"]["rows"],
                    "worsened_rows": item["worsened_descriptor"]["rows"],
                    "improved_best_rc": improved.get("best_rc", ""),
                    "worsened_best_rc": worsened.get("best_rc", ""),
                    "best_rc_delta_improved_minus_worsened": item[
                        "best_rc_delta_improved_minus_worsened"
                    ],
                    "improved_returned_count": improved.get("returned_count", ""),
                    "worsened_returned_count": worsened.get("returned_count", ""),
                    "improved_returned_task_sets": improved.get("returned_task_sets", ""),
                    "worsened_returned_task_sets": worsened.get("returned_task_sets", ""),
                    "improved_returned_sequences": improved.get("returned_sequences", ""),
                    "worsened_returned_sequences": worsened.get("returned_sequences", ""),
                    "improved_returned_arc_families": improved.get(
                        "returned_arc_families", ""
                    ),
                    "worsened_returned_arc_families": worsened.get(
                        "returned_arc_families", ""
                    ),
                }
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--top-n", type=int, default=3)
    args = parser.parse_args()

    manifest = build_manifest(args.input, args.top_n)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_csv(args.output_dir / "candidates.csv", manifest["candidates"])
    compact = {
        "candidate_count": manifest["candidate_count"],
        "low_context_noise_candidate_count": manifest[
            "low_context_noise_candidate_count"
        ],
        "mixed_descriptor_context_candidate_count": manifest[
            "mixed_descriptor_context_candidate_count"
        ],
        "recommended_candidate_ids": manifest["recommended_candidate_ids"],
        "checks": manifest["checks"],
    }
    print(json.dumps(compact, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
