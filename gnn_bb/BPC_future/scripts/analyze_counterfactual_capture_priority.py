#!/usr/bin/env python3
"""Prioritize exact-context capture targets for selector calibration.

This script is diagnostic-only.  It reads existing replay candidate manifests
and target coverage summaries, then ranks which exact contexts should be
captured next to improve selector calibration coverage.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


DEFAULT_CANDIDATES = Path(
    "BPC_future/results/root_cause_counterfactual_replay_candidates_20260613/"
    "candidates.csv"
)
DEFAULT_CANDIDATE_SUMMARY = Path(
    "BPC_future/results/root_cause_counterfactual_replay_candidates_20260613/"
    "summary.json"
)
DEFAULT_TARGET_COVERAGE = Path(
    "BPC_future/results/root_cause_counterfactual_capture_target_coverage_20260613/"
    "summary.json"
)
DEFAULT_DATASET_STRUCTURE = Path(
    "BPC_future/results/root_cause_counterfactual_replay_dataset_structure_20260613/"
    "summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_counterfactual_capture_priority_20260613"
)


def _as_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


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


def _read_candidates(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _coverage_maps(coverage: dict[str, Any]) -> dict[str, Any]:
    covered_candidate_ids: set[str] = set()
    uncovered_candidate_ids: set[str] = set()
    covered_context_keys: set[str] = set()
    uncovered_target_rows: list[dict[str, Any]] = []
    for target in coverage.get("target_results", []):
        candidate_id = str(target.get("candidate_id", ""))
        context = target.get("context", {}) or {}
        context_key = "|".join(str(item) for item in context.get("raw_context_key", []))
        covered = bool(target.get("covered_by_replay_ready_exact_capture"))
        if covered:
            covered_candidate_ids.add(candidate_id)
            if context_key:
                covered_context_keys.add(context_key)
        else:
            uncovered_candidate_ids.add(candidate_id)
            uncovered_target_rows.append(target)
    return {
        "covered_candidate_ids": covered_candidate_ids,
        "uncovered_candidate_ids": uncovered_candidate_ids,
        "covered_context_keys": covered_context_keys,
        "uncovered_target_rows": uncovered_target_rows,
    }


def _candidate_priority(
    row: dict[str, str],
    *,
    recommended_ids: set[str],
    covered_candidate_ids: set[str],
    uncovered_candidate_ids: set[str],
    covered_context_keys: set[str],
) -> dict[str, Any]:
    candidate_id = row["candidate_id"]
    context_key = row["context_key"]
    recommended = candidate_id in recommended_ids
    exact_candidate_covered = candidate_id in covered_candidate_ids
    exact_candidate_uncovered = candidate_id in uncovered_candidate_ids
    context_covered = context_key in covered_context_keys
    risk = row.get("candidate_risk", "")
    if exact_candidate_uncovered and recommended:
        tier = 0
        reason = "recommended_target_uncovered"
    elif not context_covered and risk == "low_context_noise":
        tier = 1
        reason = "uncovered_low_context_noise_candidate"
    elif not context_covered:
        tier = 2
        reason = "uncovered_mixed_context_candidate"
    elif not exact_candidate_covered:
        tier = 3
        reason = "covered_context_additional_descriptor_candidate"
    else:
        tier = 4
        reason = "already_exact_covered"
    priority_score = (
        -1000.0 * tier
        + (100.0 if recommended else 0.0)
        + _as_float(row.get("replay_priority_score"))
        + min(_as_int(row.get("context_rows")), 20) / 20.0
    )
    return {
        "candidate_id": candidate_id,
        "context_key": context_key,
        "candidate_risk": risk,
        "recommended_for_first_replay_batch": recommended,
        "exact_candidate_covered": exact_candidate_covered,
        "context_covered": context_covered,
        "priority_tier": tier,
        "priority_reason": reason,
        "capture_priority_score": round(priority_score, 6),
        "replay_priority_score": _as_float(row.get("replay_priority_score")),
        "context_rows": _as_int(row.get("context_rows")),
        "context_label_counts": row.get("context_label_counts", ""),
        "improved_rows": _as_int(row.get("improved_rows")),
        "worsened_rows": _as_int(row.get("worsened_rows")),
        "improved_best_rc": row.get("improved_best_rc", ""),
        "worsened_best_rc": row.get("worsened_best_rc", ""),
        "improved_returned_count": _as_int(row.get("improved_returned_count")),
        "worsened_returned_count": _as_int(row.get("worsened_returned_count")),
    }


def analyze_capture_priority(
    *,
    candidates_path: Path,
    candidate_summary_path: Path,
    target_coverage_path: Path,
    dataset_structure_path: Path,
    top_n: int,
) -> dict[str, Any]:
    candidates = _read_candidates(candidates_path)
    candidate_summary = json.loads(candidate_summary_path.read_text(encoding="utf-8"))
    target_coverage = json.loads(target_coverage_path.read_text(encoding="utf-8"))
    dataset_structure = json.loads(dataset_structure_path.read_text(encoding="utf-8"))
    recommended_ids = set(candidate_summary.get("recommended_candidate_ids") or [])
    coverage = _coverage_maps(target_coverage)
    priorities = [
        _candidate_priority(
            row,
            recommended_ids=recommended_ids,
            covered_candidate_ids=coverage["covered_candidate_ids"],
            uncovered_candidate_ids=coverage["uncovered_candidate_ids"],
            covered_context_keys=coverage["covered_context_keys"],
        )
        for row in candidates
    ]
    priorities.sort(
        key=lambda item: (
            item["priority_tier"],
            -item["capture_priority_score"],
            item["candidate_id"],
        )
    )
    top_priorities = priorities[: max(0, int(top_n))]
    group_summaries = dataset_structure.get("group_summaries", {}) or {}
    dataset_summary = group_summaries.get("impact_dataset", {}) or {}
    context_summary = group_summaries.get("context_hash", {}) or {}
    checks = {
        "has_uncovered_recommended_target": any(
            item["priority_reason"] == "recommended_target_uncovered"
            for item in priorities
        ),
        "top_priority_is_uncovered_recommended_target": bool(
            top_priorities
            and top_priorities[0]["priority_reason"] == "recommended_target_uncovered"
        ),
        "has_additional_uncovered_candidates": any(
            item["priority_tier"] in {1, 2} for item in priorities
        ),
        "dataset_structure_still_needs_dual_label_coverage": (
            int(dataset_summary.get("mixed_label_group_count", 0)) < 2
            or float(context_summary.get("single_label_row_share", 0.0) or 0.0) > 0.5
        ),
        "priority_is_calibration_only": True,
    }
    return {
        "schema_version": "counterfactual_capture_priority_v1",
        "inputs": {
            "candidates": str(candidates_path),
            "candidate_summary": str(candidate_summary_path),
            "target_coverage": str(target_coverage_path),
            "dataset_structure": str(dataset_structure_path),
        },
        "candidate_count": len(candidates),
        "recommended_candidate_ids": sorted(recommended_ids),
        "covered_recommended_candidate_ids": sorted(
            recommended_ids.intersection(coverage["covered_candidate_ids"])
        ),
        "uncovered_recommended_candidate_ids": sorted(
            recommended_ids.intersection(coverage["uncovered_candidate_ids"])
        ),
        "covered_context_count": len(coverage["covered_context_keys"]),
        "dataset_mixed_label_group_count": int(
            dataset_summary.get("mixed_label_group_count", 0)
        ),
        "context_mixed_label_group_count": int(
            context_summary.get("mixed_label_group_count", 0)
        ),
        "context_single_label_row_share": float(
            context_summary.get("single_label_row_share", 0.0) or 0.0
        ),
        "top_priorities": top_priorities,
        "checks": checks,
        "all_checks_pass": all(bool(value) for value in checks.values()),
        "interpretation": (
            "The next useful evidence step is targeted exact-context capture, "
            "starting with uncovered recommended targets and uncovered candidate "
            "contexts. These priorities are not optimization evidence."
        ),
    }


def _write_priority_csv(path: Path, priorities: list[dict[str, Any]]) -> None:
    fieldnames = (
        "candidate_id",
        "priority_reason",
        "priority_tier",
        "capture_priority_score",
        "candidate_risk",
        "recommended_for_first_replay_batch",
        "exact_candidate_covered",
        "context_covered",
        "context_key",
        "context_rows",
        "context_label_counts",
        "improved_rows",
        "worsened_rows",
        "improved_best_rc",
        "worsened_best_rc",
        "improved_returned_count",
        "worsened_returned_count",
    )
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in priorities:
            writer.writerow({key: item.get(key, "") for key in fieldnames})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument(
        "--candidate-summary", type=Path, default=DEFAULT_CANDIDATE_SUMMARY
    )
    parser.add_argument("--target-coverage", type=Path, default=DEFAULT_TARGET_COVERAGE)
    parser.add_argument(
        "--dataset-structure", type=Path, default=DEFAULT_DATASET_STRUCTURE
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--top-n", type=int, default=10)
    args = parser.parse_args()

    result = analyze_capture_priority(
        candidates_path=args.candidates,
        candidate_summary_path=args.candidate_summary,
        target_coverage_path=args.target_coverage,
        dataset_structure_path=args.dataset_structure,
        top_n=args.top_n,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    _write_priority_csv(args.output_dir / "top_priorities.csv", result["top_priorities"])
    print(json.dumps(result, sort_keys=True))
    return 0 if result["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
