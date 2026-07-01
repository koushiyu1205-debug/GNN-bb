"""B2 pricing-tail profiling counters."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PruningCounter:
    labels_generated: int = 0
    labels_extended: int = 0
    labels_pruned_by_resource: int = 0
    labels_pruned_by_time_window: int = 0
    labels_pruned_by_dominance: int = 0
    labels_pruned_by_completion_bound: int = 0
    labels_pruned_by_branch: int = 0
    labels_pruned_by_cut: int = 0
    check_time_by_filter: dict[str, float] = field(default_factory=dict)
    dominance_time: float = 0.0
    bound_time: float = 0.0
    queue_time: float = 0.0
    candidate_addability_time: float = 0.0
    candidate_duplicate_count: int = 0
    candidate_addable_count: int = 0

    def merge_completion_payload(self, payload: dict) -> None:
        completion = payload.get("completion_bound") if isinstance(payload, dict) else {}
        if not isinstance(completion, dict):
            return
        self.labels_pruned_by_completion_bound += int(completion.get("pruned_label_count") or 0)
        self.labels_generated += int(completion.get("evaluated_label_count") or 0)

    def to_payload(self) -> dict:
        return {
            "labels_generated": int(self.labels_generated),
            "labels_extended": int(self.labels_extended),
            "labels_pruned_by_resource": int(self.labels_pruned_by_resource),
            "labels_pruned_by_time_window": int(self.labels_pruned_by_time_window),
            "labels_pruned_by_dominance": int(self.labels_pruned_by_dominance),
            "labels_pruned_by_completion_bound": int(self.labels_pruned_by_completion_bound),
            "labels_pruned_by_branch": int(self.labels_pruned_by_branch),
            "labels_pruned_by_cut": int(self.labels_pruned_by_cut),
            "check_time_by_filter": dict(self.check_time_by_filter),
            "dominance_time": float(self.dominance_time),
            "bound_time": float(self.bound_time),
            "queue_time": float(self.queue_time),
            "candidate_addability_time": float(self.candidate_addability_time),
            "candidate_duplicate_count": int(self.candidate_duplicate_count),
            "candidate_addable_count": int(self.candidate_addable_count),
        }

