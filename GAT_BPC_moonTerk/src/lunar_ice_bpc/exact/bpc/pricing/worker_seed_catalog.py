"""Worker seed catalog updated only by diagnostics."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class WorkerSeedCatalog:
    rows: list[dict] = field(default_factory=list)

    def record_hidden_negative_audit(self, audit: dict) -> None:
        for row in audit.get("rows", []) or []:
            self.rows.append(
                {
                    "task_set": tuple(str(task_id) for task_id in row.get("hidden_task_set", [])),
                    "ordered_task_sequences": tuple(
                        tuple(str(task_id) for task_id in sequence)
                        for sequence in row.get("hidden_sequence", [])
                    ),
                    "path_signature": tuple(tuple(item) for item in row.get("hidden_path_signature", [])),
                    "source": "hidden_negative_audit",
                    "true_reduced_cost": row.get("hidden_true_rc"),
                    "miss_reason": row.get("miss_reason") or "unknown",
                    "replacement_or_new_task_set": row.get("replacement_or_new_task_set") or "",
                    "worker_priced_candidate_source_match": row.get(
                        "worker_priced_candidate_source_match"
                    )
                    or "none",
                    "worker_priced_candidate_seed_sources": tuple(
                        str(source)
                        for source in row.get("worker_priced_candidate_seed_sources", [])
                    ),
                }
            )

    def to_payload(self) -> dict:
        refinement_counts = _refinement_coverage_counts(self.rows)
        refinement_exact = int(refinement_counts.get("exact") or 0)
        refinement_superset = int(refinement_counts.get("superset") or 0)
        refinement_uncovered = int(refinement_counts.get("uncovered") or 0)
        return {
            "schema_version": "lunar_ice_bpc.b2_worker_seed_catalog.v1",
            "seed_count": len(self.rows),
            "task_count_counts": _task_count_counts(self.rows),
            "miss_reason_counts": _field_counts(self.rows, "miss_reason", default="unknown"),
            "source_match_counts": _field_counts(
                self.rows,
                "worker_priced_candidate_source_match",
                default="none",
            ),
            "seed_source_counts": _seed_source_counts(self.rows),
            "refinement_coverage_counts": refinement_counts,
            "refinement_exact_count": refinement_exact,
            "refinement_superset_count": refinement_superset,
            "refinement_covered_count": refinement_exact + refinement_superset,
            "refinement_uncovered_count": refinement_uncovered,
            "rows": [
                {
                    "task_set": list(row["task_set"]),
                    "ordered_task_sequences": [
                        list(sequence)
                        for sequence in row.get("ordered_task_sequences", tuple())
                    ],
                    "path_signature": [list(item) for item in row["path_signature"]],
                    "source": row["source"],
                    "true_reduced_cost": row["true_reduced_cost"],
                    "miss_reason": row.get("miss_reason") or "unknown",
                    "replacement_or_new_task_set": row.get("replacement_or_new_task_set") or "",
                    "worker_priced_candidate_source_match": row.get(
                        "worker_priced_candidate_source_match"
                    )
                    or "none",
                    "worker_priced_candidate_seed_sources": list(
                        row.get("worker_priced_candidate_seed_sources") or []
                    ),
                }
                for row in self.rows
            ],
            "mutates_certificate": False,
        }


def _task_count_counts(rows: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        key = str(len(row.get("task_set") or ()))
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _field_counts(rows: list[dict], key: str, *, default: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or default)
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _seed_source_counts(rows: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        sources = tuple(row.get("worker_priced_candidate_seed_sources") or ("unknown",))
        for source in sources or ("unknown",):
            source_key = str(source)
            counts[source_key] = counts.get(source_key, 0) + 1
    return dict(sorted(counts.items()))


def _refinement_coverage_counts(rows: list[dict]) -> dict[str, int]:
    counts = {"exact": 0, "superset": 0, "uncovered": 0}
    for row in rows:
        match = str(row.get("worker_priced_candidate_source_match") or "none")
        sources = tuple(str(source) for source in row.get("worker_priced_candidate_seed_sources") or tuple())
        from_refinement = any(source.startswith("hidden_negative_refinement") for source in sources)
        if from_refinement and match in {"exact", "superset"}:
            counts[match] += 1
        else:
            counts["uncovered"] += 1
    return {key: value for key, value in counts.items() if value > 0}
