#!/usr/bin/env python3
"""Audit partial materialization feasibility for replay candidate descriptors.

This read-only audit asks a narrower question than exact replay readiness:
given the current observational descriptor fields, can we resolve
sequence + arc-family + recovered start_time into a concrete TimedTrip?

Successful TimedTrip materialization is still not enough for controlled replay:
the replay harness also needs exact source-run identity, full JourneyColumn
signatures, sortie boundaries, true-dual/cut context, and an RMP pool snapshot.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from BPC_future.core.data import ArcOption, FutureData, load_future_data
from BPC_future.pricing.pulse_materialization import materialize_pulse_sortie


DEFAULT_MANIFEST = Path(
    "BPC_future/results/root_cause_counterfactual_replay_candidates_20260613/"
    "summary.json"
)
DEFAULT_CANDIDATE_ROWS = Path(
    "BPC_future/results/root_cause_returned_batch_trajectory_dataset_20260613/"
    "candidate_rows.csv"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_counterfactual_replay_materialization_20260613"
)

INSTANCE_ALIASES = {
    "tranq20_01": (
        "BPC_future/data/generated/moon_trek_60/logical_graphs/"
        "tranquillitatis_balmer_like_20km/tasks_20/"
        "tranquillitatis_balmer_like_20km_tasks20_01_seed21000_logical_graph.json"
    ),
    "mt20_greedy_apollo_01": (
        "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/"
        "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json"
    ),
    "mt20_greedy_tranq_01": (
        "BPC_future/logical_graph/tasks_020/greedy-anchor/"
        "tranquillitatis_balmer_like_20km/"
        "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json"
    ),
}


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
    return tuple(int(float(part.strip())) for part in value.split(",") if part.strip())


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
            }
        )
    return entries


def _candidate_row_matches(
    row: dict[str, str],
    *,
    context_key: list[str],
    sample: dict[str, Any],
    entry: dict[str, Any],
    label: str,
) -> bool:
    if row.get("instance", "") != str(context_key[0]):
        return False
    if row.get("cg_iter", "") != str(context_key[1]):
        return False
    if row.get("run_improvement_class", "") != label:
        return False
    for key in ("dataset", "profile", "repeat_index"):
        if sample.get(key) and row.get(key, "") != str(sample.get(key)):
            return False
    if row.get("candidate_sequence", "") != entry["sequence_text"]:
        return False
    return row.get("candidate_arc_families", "") == entry["arc_families_text"]


def _candidate_starts(
    candidate_rows: list[dict[str, str]],
    *,
    context_key: list[str],
    samples: list[dict[str, Any]],
    entry: dict[str, Any],
    label: str,
) -> list[float]:
    starts: set[float] = set()
    for sample in samples:
        for row in candidate_rows:
            if not _candidate_row_matches(
                row,
                context_key=context_key,
                sample=sample,
                entry=entry,
                label=label,
            ):
                continue
            raw = row.get("candidate_start_time", "")
            if raw == "":
                continue
            starts.add(float(raw))
    return sorted(starts)


def _option_matches_family(option: ArcOption, family: str) -> bool:
    family = str(family)
    return (
        str(option.path_type) == family
        or family in tuple(str(alias) for alias in option.aliases)
        or f":{family}:" in str(option.option_id)
    )


def _resolve_arc_options(
    data: FutureData,
    sequence: tuple[int, ...],
    families: tuple[str, ...],
) -> dict[str, Any]:
    if len(families) != len(sequence) + 1:
        return {
            "resolved": False,
            "reason": "arc_family_count_mismatch",
            "arc_match_counts": [],
            "arc_option_ids": [],
        }
    current = 0
    resolved: list[ArcOption] = []
    counts: list[int] = []
    for destination, family in zip((*sequence, 0), families):
        options = tuple(data.options(int(current), int(destination)))
        matches = tuple(option for option in options if _option_matches_family(option, family))
        counts.append(len(matches))
        if len(matches) != 1:
            return {
                "resolved": False,
                "reason": "arc_family_not_unique",
                "arc_match_counts": counts,
                "arc_option_ids": [option.option_id for option in resolved],
            }
        resolved.append(matches[0])
        current = int(destination)
    return {
        "resolved": True,
        "reason": "",
        "arc_match_counts": counts,
        "arc_option_ids": [option.option_id for option in resolved],
        "arc_options": tuple(resolved),
    }


def _load_candidate_data(instance: str) -> tuple[FutureData | None, str]:
    path = INSTANCE_ALIASES.get(str(instance))
    if not path:
        return None, "missing_instance_alias"
    if not Path(path).exists():
        return None, "instance_path_missing"
    return load_future_data(path, "."), ""


def _entry_materialization(
    data: FutureData | None,
    *,
    candidate_rows: list[dict[str, str]],
    context_key: list[str],
    label: str,
    samples: list[dict[str, Any]],
    entry: dict[str, Any],
    time_bucket_size: float,
) -> dict[str, Any]:
    starts = _candidate_starts(
        candidate_rows,
        context_key=context_key,
        samples=samples,
        entry=entry,
        label=label,
    )
    payload: dict[str, Any] = {
        "index": entry["index"],
        "sequence": list(entry["sequence"]),
        "arc_families": list(entry["arc_families"]),
        "recovered_start_times": starts,
        "recovered_start_time_count": len(starts),
        "arc_family_count_consistent": len(entry["arc_families"])
        == len(entry["sequence"]) + 1,
        "arc_options_resolved": False,
        "timed_trip_materialized": False,
    }
    if data is None:
        payload["blocking_reason"] = "instance_not_loaded"
        return payload
    resolved = _resolve_arc_options(
        data,
        tuple(entry["sequence"]),
        tuple(entry["arc_families"]),
    )
    payload.update(
        {
            "arc_options_resolved": bool(resolved["resolved"]),
            "arc_resolution_reason": str(resolved["reason"]),
            "arc_match_counts": list(resolved["arc_match_counts"]),
            "arc_option_ids": list(resolved["arc_option_ids"]),
        }
    )
    if not resolved["resolved"]:
        payload["blocking_reason"] = str(resolved["reason"])
        return payload
    if not starts:
        payload["blocking_reason"] = "missing_recovered_start_time"
        return payload
    materialized = 0
    signatures: list[str] = []
    for start in starts:
        trip = materialize_pulse_sortie(
            data,
            tuple(entry["sequence"]),
            float(start),
            arc_options=tuple(resolved["arc_options"]),
            time_bucket_size=float(time_bucket_size),
            include_physical_paths=False,
        )
        if trip is None:
            continue
        materialized += 1
        signatures.append(str(trip.signature))
    payload["timed_trip_materialized"] = materialized > 0
    payload["materialized_start_count"] = materialized
    payload["materialized_trip_signatures"] = signatures[:8]
    if materialized <= 0:
        payload["blocking_reason"] = "evaluate_timed_trip_rejected"
    return payload


def _descriptor_materialization(
    *,
    data: FutureData | None,
    candidate_rows: list[dict[str, str]],
    context_key: list[str],
    label: str,
    descriptor_summary: dict[str, Any],
    time_bucket_size: float,
) -> dict[str, Any]:
    descriptor = descriptor_summary.get("descriptor", {})
    entries = _descriptor_entries(descriptor)
    samples = [
        dict(sample)
        for sample in descriptor_summary.get("samples", [])
        if isinstance(sample, dict)
    ]
    returned_count = int(float(descriptor.get("returned_count") or 0))
    entry_payloads = [
        _entry_materialization(
            data,
            candidate_rows=candidate_rows,
            context_key=context_key,
            label=label,
            samples=samples,
            entry=entry,
            time_bucket_size=float(time_bucket_size),
        )
        for entry in entries
    ]
    resolved_entries = sum(1 for entry in entry_payloads if entry["arc_options_resolved"])
    materialized_entries = sum(
        1 for entry in entry_payloads if entry["timed_trip_materialized"]
    )
    return {
        "label": label,
        "returned_count": returned_count,
        "sequence_entry_count": len(entries),
        "missing_sequence_entries_due_to_sampling": max(0, returned_count - len(entries)),
        "arc_options_resolved_entries": resolved_entries,
        "timed_trip_materialized_entries": materialized_entries,
        "all_observed_entries_materialized": bool(entries)
        and materialized_entries == len(entries),
        "complete_descriptor_materialized": (
            returned_count == len(entries) and materialized_entries == returned_count
        ),
        "entries": entry_payloads,
    }


def build_summary(
    manifest_path: Path,
    candidate_rows_path: Path,
    *,
    time_bucket_size: float,
) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    candidate_rows = _read_csv(candidate_rows_path)
    candidates = [
        candidate
        for candidate in manifest.get("candidates", [])
        if candidate.get("recommended_for_first_replay_batch")
    ]
    payloads: list[dict[str, Any]] = []
    for candidate in candidates:
        context_key = [str(item) for item in candidate.get("context_key", [])]
        instance = context_key[0] if context_key else ""
        data, load_reason = _load_candidate_data(instance)
        descriptors = [
            _descriptor_materialization(
                data=data,
                candidate_rows=candidate_rows,
                context_key=context_key,
                label="improved",
                descriptor_summary=candidate.get("improved_descriptor", {}),
                time_bucket_size=float(time_bucket_size),
            ),
            _descriptor_materialization(
                data=data,
                candidate_rows=candidate_rows,
                context_key=context_key,
                label="worsened",
                descriptor_summary=candidate.get("worsened_descriptor", {}),
                time_bucket_size=float(time_bucket_size),
            ),
        ]
        payloads.append(
            {
                "candidate_id": candidate.get("candidate_id", ""),
                "context_key": context_key,
                "instance_path": INSTANCE_ALIASES.get(instance, ""),
                "instance_loaded": data is not None,
                "instance_load_blocking_reason": load_reason,
                "descriptors": descriptors,
                "all_observed_entries_materialized": all(
                    descriptor["all_observed_entries_materialized"]
                    for descriptor in descriptors
                ),
                "complete_descriptor_materialized": all(
                    descriptor["complete_descriptor_materialized"]
                    for descriptor in descriptors
                ),
            }
        )
    descriptor_count = sum(len(candidate["descriptors"]) for candidate in payloads)
    observed_descriptors_materialized = sum(
        1
        for candidate in payloads
        for descriptor in candidate["descriptors"]
        if descriptor["all_observed_entries_materialized"]
    )
    complete_descriptors_materialized = sum(
        1
        for candidate in payloads
        for descriptor in candidate["descriptors"]
        if descriptor["complete_descriptor_materialized"]
    )
    entry_count = sum(
        len(descriptor["entries"])
        for candidate in payloads
        for descriptor in candidate["descriptors"]
    )
    materialized_entry_count = sum(
        sum(1 for entry in descriptor["entries"] if entry["timed_trip_materialized"])
        for candidate in payloads
        for descriptor in candidate["descriptors"]
    )
    return {
        "inputs": {
            "manifest": str(manifest_path),
            "candidate_rows": str(candidate_rows_path),
        },
        "time_bucket_size": float(time_bucket_size),
        "recommended_candidate_count": len(payloads),
        "descriptor_count": descriptor_count,
        "entry_count": entry_count,
        "materialized_entry_count": materialized_entry_count,
        "observed_descriptors_materialized": observed_descriptors_materialized,
        "complete_descriptors_materialized": complete_descriptors_materialized,
        "candidates": payloads,
        "checks": {
            "recommended_candidates_present": len(payloads) == 3,
            "all_instances_loaded": all(candidate["instance_loaded"] for candidate in payloads),
            "all_observed_entries_materialized": (
                entry_count > 0 and materialized_entry_count == entry_count
            ),
            "not_all_complete_descriptors_materialized": (
                complete_descriptors_materialized < descriptor_count
            ),
            "still_not_exact_replay_payload": True,
        },
        "interpretation": (
            "The observed descriptor entries can be resolved to concrete arc "
            "options and materialized as TimedTrips for the selected candidates, "
            "but this remains partial.  At least one descriptor is sampling-"
            "truncated, and exact replay still requires full JourneyColumn "
            "signatures plus RMP/dual/cut snapshots."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--candidate-rows", type=Path, default=DEFAULT_CANDIDATE_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--time-bucket-size", type=float, default=10.0)
    args = parser.parse_args()

    summary = build_summary(
        args.manifest,
        args.candidate_rows,
        time_bucket_size=float(args.time_bucket_size),
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(summary["checks"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
