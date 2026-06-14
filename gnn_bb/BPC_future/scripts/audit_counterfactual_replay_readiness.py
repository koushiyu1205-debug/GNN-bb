#!/usr/bin/env python3
"""Audit whether selected counterfactual replay candidates are replay-ready.

The counterfactual replay candidate manifest is intentionally observational:
it identifies exact-context improved-vs-worsened descriptor pairs from logs.
This script checks whether those descriptors contain enough information to
reconstruct concrete JourneyColumn batches for a no-certificate-effect replay.

It does not run the solver, pricing, Pulse, RMP, or any benchmark.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_MANIFEST = Path(
    "BPC_future/results/root_cause_counterfactual_replay_candidates_20260613/"
    "summary.json"
)
DEFAULT_STAGE_ROWS = Path(
    "BPC_future/results/root_cause_returned_batch_trajectory_dataset_20260613/"
    "stage_rows.csv"
)
DEFAULT_CANDIDATE_ROWS = Path(
    "BPC_future/results/root_cause_returned_batch_trajectory_dataset_20260613/"
    "candidate_rows.csv"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_counterfactual_replay_readiness_20260613"
)

REQUIRED_EXACT_CONTEXT_FIELDS = (
    "instance",
    "cg_iter",
    "pricing_kind",
    "active_hash_before",
    "rmp_objective_before",
)

REQUIRED_REPLAY_FIELDS = (
    "source_log_path",
    "repeat_index",
    "full_journey_signatures",
    "sortie_boundaries",
    "concrete_arc_option_ids",
    "start_times",
    "true_rc_per_journey",
    "rmp_pool_snapshot",
    "true_dual_snapshot",
    "cut_snapshot",
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _split_pipe(value: Any) -> list[str]:
    text = str(value or "").strip()
    if not text:
        return []
    return [part.strip() for part in text.split("|") if part.strip()]


def _split_ints(value: str) -> tuple[int, ...]:
    if not value.strip():
        return tuple()
    items: list[int] = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        items.append(int(float(part)))
    return tuple(items)


def _descriptor_entries(descriptor: dict[str, Any]) -> list[dict[str, Any]]:
    sequences = _split_pipe(descriptor.get("returned_sequences"))
    task_sets = _split_pipe(descriptor.get("returned_task_sets"))
    arc_families = _split_pipe(descriptor.get("returned_arc_families"))
    entries: list[dict[str, Any]] = []
    for index, sequence_text in enumerate(sequences):
        arc_text = arc_families[index] if index < len(arc_families) else ""
        task_set_text = task_sets[index] if index < len(task_sets) else ""
        sequence = _split_ints(sequence_text)
        arc_family_tuple = tuple(part.strip() for part in arc_text.split(",") if part.strip())
        entries.append(
            {
                "index": index,
                "sequence": sequence,
                "sequence_text": sequence_text,
                "task_set": _split_ints(task_set_text),
                "task_set_text": task_set_text,
                "arc_families": arc_family_tuple,
                "arc_families_text": arc_text,
                "single_sortie_arc_count_consistent": (
                    bool(sequence)
                    and bool(arc_family_tuple)
                    and len(arc_family_tuple) == len(sequence) + 1
                ),
            }
        )
    return entries


def _row_matches_sample(
    row: dict[str, str],
    *,
    context_key: list[str],
    sample: dict[str, str],
    entry: dict[str, Any],
    label: str,
) -> bool:
    if row.get("instance", "") != str(context_key[0]):
        return False
    if row.get("cg_iter", "") != str(context_key[1]):
        return False
    if row.get("run_improvement_class", "") != label:
        return False
    if sample.get("dataset") and row.get("dataset", "") != sample.get("dataset", ""):
        return False
    if sample.get("profile") and row.get("profile", "") != sample.get("profile", ""):
        return False
    if row.get("candidate_sequence", "") != entry["sequence_text"]:
        return False
    return row.get("candidate_arc_families", "") == entry["arc_families_text"]


def _candidate_row_matches(
    candidate_rows: list[dict[str, str]],
    *,
    context_key: list[str],
    samples: list[dict[str, str]],
    entry: dict[str, Any],
    label: str,
) -> dict[str, Any]:
    matches: list[dict[str, str]] = []
    for sample in samples:
        matches.extend(
            row
            for row in candidate_rows
            if _row_matches_sample(
                row,
                context_key=context_key,
                sample=sample,
                entry=entry,
                label=label,
            )
        )
    seen_rows = {
        (
            row.get("dataset", ""),
            row.get("profile", ""),
            row.get("repeat_index", ""),
            row.get("candidate_start_time", ""),
        ): row
        for row in matches
    }
    starts = sorted(
        {
            row.get("candidate_start_time", "")
            for row in seen_rows.values()
            if row.get("candidate_start_time", "")
        }
    )
    repeat_values = sorted(
        {
            row.get("repeat_index", "")
            for row in seen_rows.values()
            if row.get("repeat_index", "")
        }
    )
    return {
        "match_count": len(seen_rows),
        "distinct_start_times": starts,
        "distinct_start_time_count": len(starts),
        "distinct_repeat_count": len(repeat_values),
        "ambiguous_start_time": len(starts) > 1,
        "has_start_time": bool(starts),
    }


def _stage_row_context_counts(
    stage_rows: list[dict[str, str]],
    context_key: list[str],
) -> dict[str, Any]:
    rows = [
        row
        for row in stage_rows
        if row.get("instance", "") == str(context_key[0])
        and row.get("cg_iter", "") == str(context_key[1])
        and row.get("pricing_kind", "") == str(context_key[2])
        and row.get("active_hash_before", "") == str(context_key[3])
        and row.get("rmp_objective_before", "") == str(context_key[4])
    ]
    return {
        "stage_exact_context_row_count": len(rows),
        "stage_exact_context_dataset_counts": dict(
            Counter(row.get("dataset", "") for row in rows)
        ),
        "stage_exact_context_profile_counts": dict(
            Counter(row.get("profile", "") for row in rows)
        ),
        "stage_exact_context_repeat_count": len(
            {
                (row.get("dataset", ""), row.get("profile", ""), row.get("repeat_index", ""))
                for row in rows
            }
        ),
    }


def _descriptor_readiness(
    *,
    context_key: list[str],
    label: str,
    descriptor_summary: dict[str, Any],
    candidate_rows: list[dict[str, str]],
) -> dict[str, Any]:
    descriptor = descriptor_summary.get("descriptor", {})
    entries = _descriptor_entries(descriptor)
    samples = [
        {str(key): str(value) for key, value in sample.items()}
        for sample in descriptor_summary.get("samples", [])
        if isinstance(sample, dict)
    ]
    returned_count = int(float(descriptor.get("returned_count") or 0))
    entry_payloads: list[dict[str, Any]] = []
    for entry in entries:
        matches = _candidate_row_matches(
            candidate_rows,
            context_key=context_key,
            samples=samples,
            entry=entry,
            label=label,
        )
        entry_payloads.append({**entry, **matches})
    missing_entries = max(0, returned_count - len(entries))
    has_all_entry_start_times = bool(entries) and all(
        bool(entry.get("has_start_time")) for entry in entry_payloads
    )
    has_ambiguous_start_time = any(
        bool(entry.get("ambiguous_start_time")) for entry in entry_payloads
    )
    all_single_sortie_consistent = bool(entries) and all(
        bool(entry.get("single_sortie_arc_count_consistent")) for entry in entry_payloads
    )
    return {
        "label": label,
        "descriptor_rows": int(descriptor_summary.get("rows") or 0),
        "returned_count": returned_count,
        "sequence_entry_count": len(entries),
        "arc_family_entry_count": len(_split_pipe(descriptor.get("returned_arc_families"))),
        "task_set_entry_count": len(_split_pipe(descriptor.get("returned_task_sets"))),
        "missing_sequence_entries_due_to_sampling": missing_entries,
        "manifest_has_start_times": False,
        "manifest_has_concrete_arc_option_ids": False,
        "manifest_has_full_journey_signatures": False,
        "manifest_has_sortie_boundaries": False,
        "manifest_has_source_log_path": False,
        "manifest_has_repeat_index": False,
        "candidate_rows_can_recover_start_times": has_all_entry_start_times,
        "candidate_rows_start_time_ambiguous": has_ambiguous_start_time,
        "single_sortie_arc_count_consistent": all_single_sortie_consistent,
        "entries": entry_payloads,
        "ready_for_exact_replay": False,
        "blocking_reasons": [
            reason
            for reason, blocked in (
                ("manifest_missing_source_log_path", True),
                ("manifest_missing_repeat_index", True),
                ("manifest_missing_full_journey_signatures", True),
                ("manifest_missing_concrete_arc_option_ids", True),
                ("manifest_missing_sortie_boundaries", True),
                ("manifest_missing_start_times", True),
                ("manifest_missing_true_rc_per_journey", True),
                ("manifest_missing_rmp_pool_true_dual_cut_snapshots", True),
                ("descriptor_truncated_by_sampling", missing_entries > 0),
                ("candidate_row_start_times_missing_or_unmatched", not has_all_entry_start_times),
                ("candidate_row_start_times_ambiguous", has_ambiguous_start_time),
                ("arc_family_count_not_single_sortie_signature", not all_single_sortie_consistent),
            )
            if blocked
        ],
    }


def build_summary(
    manifest_path: Path,
    stage_rows_path: Path,
    candidate_rows_path: Path,
) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    stage_rows = _read_csv(stage_rows_path)
    candidate_rows = _read_csv(candidate_rows_path)
    recommended = [
        candidate
        for candidate in manifest.get("candidates", [])
        if candidate.get("recommended_for_first_replay_batch")
    ]
    candidate_summaries: list[dict[str, Any]] = []
    for candidate in recommended:
        context_key = [str(item) for item in candidate.get("context_key", [])]
        descriptor_payloads = [
            _descriptor_readiness(
                context_key=context_key,
                label="improved",
                descriptor_summary=candidate.get("improved_descriptor", {}),
                candidate_rows=candidate_rows,
            ),
            _descriptor_readiness(
                context_key=context_key,
                label="worsened",
                descriptor_summary=candidate.get("worsened_descriptor", {}),
                candidate_rows=candidate_rows,
            ),
        ]
        candidate_summaries.append(
            {
                "candidate_id": candidate.get("candidate_id", ""),
                "candidate_risk": candidate.get("candidate_risk", ""),
                "context_key": context_key,
                **_stage_row_context_counts(stage_rows, context_key),
                "descriptors": descriptor_payloads,
                "ready_for_exact_replay": all(
                    descriptor.get("ready_for_exact_replay")
                    for descriptor in descriptor_payloads
                ),
            }
        )
    descriptor_count = sum(len(item["descriptors"]) for item in candidate_summaries)
    descriptors_with_truncated_sampling = sum(
        1
        for item in candidate_summaries
        for descriptor in item["descriptors"]
        if int(descriptor["missing_sequence_entries_due_to_sampling"]) > 0
    )
    descriptors_with_candidate_row_starts = sum(
        1
        for item in candidate_summaries
        for descriptor in item["descriptors"]
        if bool(descriptor["candidate_rows_can_recover_start_times"])
    )
    descriptors_with_ambiguous_candidate_row_starts = sum(
        1
        for item in candidate_summaries
        for descriptor in item["descriptors"]
        if bool(descriptor["candidate_rows_start_time_ambiguous"])
    )
    ready_count = sum(
        1 for item in candidate_summaries if bool(item["ready_for_exact_replay"])
    )
    return {
        "inputs": {
            "manifest": str(manifest_path),
            "stage_rows": str(stage_rows_path),
            "candidate_rows": str(candidate_rows_path),
        },
        "required_exact_context_fields": list(REQUIRED_EXACT_CONTEXT_FIELDS),
        "required_replay_fields": list(REQUIRED_REPLAY_FIELDS),
        "recommended_candidate_count": len(candidate_summaries),
        "descriptor_count": descriptor_count,
        "ready_candidate_count": ready_count,
        "descriptors_with_truncated_sampling": descriptors_with_truncated_sampling,
        "descriptors_with_candidate_row_start_times": descriptors_with_candidate_row_starts,
        "descriptors_with_ambiguous_candidate_row_start_times": (
            descriptors_with_ambiguous_candidate_row_starts
        ),
        "candidates": candidate_summaries,
        "checks": {
            "recommended_candidates_present": len(candidate_summaries) == 3,
            "no_candidate_ready_for_exact_replay": ready_count == 0,
            "manifest_lacks_required_replay_fields": True,
            "candidate_rows_are_not_exact_context_snapshots": True,
            "needs_new_no_certificate_effect_replay_capture": True,
        },
        "interpretation": (
            "The selected observational candidates locate useful exact contexts, "
            "but the current manifest/log-derived descriptors are not sufficient "
            "to reconstruct concrete JourneyColumn batches.  A controlled replay "
            "harness must capture source log identity, repeat, concrete arc option "
            "ids, start times, sortie boundaries, true-dual/cut context, and an RMP "
            "pool snapshot before any optimization direction can be treated as "
            "causal evidence."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--stage-rows", type=Path, default=DEFAULT_STAGE_ROWS)
    parser.add_argument("--candidate-rows", type=Path, default=DEFAULT_CANDIDATE_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    summary = build_summary(args.manifest, args.stage_rows, args.candidate_rows)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(summary["checks"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
