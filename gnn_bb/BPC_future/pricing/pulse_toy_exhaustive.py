"""Toy exhaustive Pulse enumerator used by sharded final-judge tests.

The default mode is the Phase-3B root-only exhaustive search: no pruning,
dominance, resume, parallelism, branch compiler, or harvesting.  Later guarded
features are opt-in and remain exact-safe/fail-open.
"""

from __future__ import annotations

from dataclasses import dataclass
import itertools
import time
from typing import Iterable, Iterator

from BPC_future.core.cuts import FutureCut
from BPC_future.core.data import ArcOption, FutureData
from BPC_future.core.journey import JourneyColumn
from BPC_future.master.journey_rmp import JourneyDuals
from BPC_future.pricing.journey_harvesting import harvest_support_aware_negative_journeys
from BPC_future.pricing.pulse_archive import (
    PulseArchiveRecord,
    PulseStructuralKey,
    StructuralKeyDominanceArchive,
)
from BPC_future.pricing.pulse_materialization import (
    PulseLeafCandidate,
    PulseSortieTrace,
    materialize_pulse_leaf_candidate,
    materialize_pulse_sortie,
)


@dataclass(frozen=True)
class ToyPulseExhaustiveResult:
    candidates: tuple[PulseLeafCandidate, ...]
    exhausted: bool
    status: str
    reason: str
    generated_sortie_traces: int
    generated_leaves: int
    materialized_sorties: int
    materialized_journey_leaves: int
    materialized_journeys: int
    infeasible_leaves: int
    recursions: int
    expanded_states: int
    pulse_return_pruned: int
    pulse_time_window_pruned: int
    pulse_resource_pruned: int
    pulse_bound_pruned: int
    pulse_archive_pruned: int
    pulse_depot_ready_pruned: int
    pulse_negative_found: bool
    pulse_harvested_count: int
    harvested_journeys: tuple[JourneyColumn, ...]
    harvest_diagnostics: dict[str, object]
    best_true_reduced_cost: float | None
    negative_leaves: tuple[PulseLeafCandidate, ...]
    shard_first_task: int | None = None

    @property
    def found_negative(self) -> bool:
        return bool(self.negative_leaves)

    @property
    def journeys(self) -> tuple[JourneyColumn, ...]:
        return tuple(candidate.journey for candidate in self.candidates)

    @property
    def journey_signatures(self) -> tuple[tuple, ...]:
        return tuple(candidate.journey.signature for candidate in self.candidates)


def toy_root_exhaustive_pulse(
    data: FutureData,
    duals: JourneyDuals,
    *,
    cuts: tuple[FutureCut, ...] = tuple(),
    time_bucket_size: float,
    eps: float = 1.0e-6,
    max_tasks_per_sortie: int = 0,
    max_sorties: int | None = None,
    root_start_time: float = 0.0,
    first_task_shard: int | None = None,
    second_action_shard: int | str | None = None,
    deadline: float | None = None,
    max_recursions: int = 0,
    exact_safe_pruning_enabled: bool = False,
    return_feasibility_pruning_enabled: bool = True,
    time_window_pruning_enabled: bool = True,
    resource_pruning_enabled: bool = True,
    bound_pruning_enabled: bool = False,
    archive_dominance_enabled: bool = False,
    archive_max_records_per_key: int = 32,
    harvest_after_negative_enabled: bool = False,
    support_aware_harvesting_enabled: bool = False,
    negative_harvest_limit: int = 0,
    active_masks: tuple[object, ...] = tuple(),
    pool_masks: tuple[object, ...] = tuple(),
    forbidden_signatures: tuple[object, ...] = tuple(),
    include_physical_paths: bool = True,
) -> ToyPulseExhaustiveResult:
    """Enumerate a finite root-only toy Pulse search space.

    The search is intentionally small and deterministic.  It starts at the
    depot, opens sorties sequentially, and materializes every completed leaf
    through the Phase-3A helper contract.
    """

    task_order = tuple(int(task) for task in data.tasks)
    max_tasks = _toy_max_tasks_per_sortie(data, int(max_tasks_per_sortie))
    sortie_limit = int(data.sortie_limit if max_sorties is None else max_sorties)
    sortie_limit = max(0, min(int(data.sortie_limit), sortie_limit))
    shard_task = None if first_task_shard is None else int(first_task_shard)
    second_shard = _normalize_second_action_shard(second_action_shard)
    forbidden = {tuple(signature) for signature in (forbidden_signatures or tuple())}

    candidates_by_signature: dict[tuple, PulseLeafCandidate] = {}
    generated_sortie_traces = 0
    materialized_sorties = 0
    materialized_journey_leaves = 0
    infeasible_leaves = 0
    recursions = 0
    expanded_states = 0
    pulse_return_pruned = 0
    pulse_time_window_pruned = 0
    pulse_resource_pruned = 0
    pulse_bound_pruned = 0
    pulse_archive_pruned = 0
    pulse_depot_ready_pruned = 0
    stop_status: str | None = None
    stop_reason: str | None = None
    task_to_bit = {int(task): index for index, task in enumerate(task_order)}
    waiting_allowed = bool(data.instance.get("scheduling", {}).get("task_waiting_allowed", True))
    archive = (
        StructuralKeyDominanceArchive(max_records_per_key=int(archive_max_records_per_key))
        if bool(archive_dominance_enabled)
        else None
    )

    def stop_requested() -> bool:
        nonlocal stop_status, stop_reason
        if stop_status is not None:
            return True
        if deadline is not None and time.perf_counter() >= float(deadline):
            stop_status = "TIME_LIMIT"
            stop_reason = "deadline"
            return True
        return False

    def dfs(
        traces: tuple[PulseSortieTrace, ...],
        remaining_tasks: tuple[int, ...],
        next_start_time: float,
        prefix_reduced_cost: float,
        prefix_energy: float,
    ) -> None:
        nonlocal generated_sortie_traces, materialized_sorties, materialized_journey_leaves
        nonlocal infeasible_leaves, recursions, stop_status, stop_reason, expanded_states
        nonlocal pulse_return_pruned, pulse_time_window_pruned, pulse_resource_pruned, pulse_bound_pruned
        nonlocal pulse_archive_pruned, pulse_depot_ready_pruned
        if stop_requested():
            return
        recursions += 1
        if int(max_recursions) > 0 and recursions > int(max_recursions):
            stop_status = "RECURSION_LIMIT"
            stop_reason = "max_recursions"
            return
        if len(traces) >= sortie_limit:
            return
        if archive is not None:
            key = PulseStructuralKey(
                phase="depot_ready",
                last_node=0,
                visited_task_mask=_toy_visited_mask(task_order, remaining_tasks, task_to_bit),
                current_sortie_task_mask=0,
                sorties_used=len(traces),
                branch_state_key=tuple(),
            )
            decision = archive.consider(
                key,
                PulseArchiveRecord(
                    partial_reduced_cost_lb=float(prefix_reduced_cost),
                    exact_prefix_cost=float(prefix_reduced_cost),
                    current_time=float(next_start_time),
                    energy_used=float(prefix_energy),
                    load_used=0.0,
                    trace_summary=tuple(trace.sequence for trace in traces),
                    proof_mode=True,
                ),
                waiting_allowed=waiting_allowed,
            )
            if decision.dominated:
                pulse_archive_pruned += 1
                pulse_depot_ready_pruned += 1
                return
        expanded_states += 1
        for sequence in _toy_task_sequences_iter(remaining_tasks, max_tasks):
            if stop_requested():
                return
            if shard_task is not None and not traces and int(sequence[0]) != shard_task:
                continue
            if shard_task is not None and second_shard is not None and not traces:
                if second_shard == "return":
                    if len(sequence) != 1:
                        continue
                elif len(sequence) < 2 or int(sequence[1]) != int(second_shard):
                    continue
            for arc_options in _toy_arc_option_combinations_iter(data, sequence):
                if stop_requested():
                    return
                generated_sortie_traces += 1
                trace = PulseSortieTrace(
                    sequence=sequence,
                    start_time=float(next_start_time),
                    arc_options=arc_options,
                )
                if bool(exact_safe_pruning_enabled):
                    prune_reason = _toy_exact_safe_sortie_prune_reason(
                        data,
                        trace.sequence,
                        trace.start_time,
                        trace.arc_options,
                        return_feasibility_enabled=bool(return_feasibility_pruning_enabled),
                        time_window_enabled=bool(time_window_pruning_enabled),
                        resource_enabled=bool(resource_pruning_enabled),
                    )
                    if prune_reason == "return":
                        pulse_return_pruned += 1
                        continue
                    if prune_reason == "time_window":
                        pulse_time_window_pruned += 1
                        continue
                    if prune_reason == "resource":
                        pulse_resource_pruned += 1
                        continue
                if bool(bound_pruning_enabled):
                    # Bound pruning is intentionally fail-open until every
                    # row/cut/fleet contribution has a safe prefix lower bound.
                    pulse_bound_pruned += 0
                trip = materialize_pulse_sortie(
                    data,
                    trace.sequence,
                    trace.start_time,
                    arc_options=trace.arc_options,
                    time_bucket_size=float(time_bucket_size),
                    include_physical_paths=bool(include_physical_paths),
                )
                if trip is None:
                    infeasible_leaves += 1
                    continue
                materialized_sorties += 1
                next_traces = traces + (trace,)
                candidate = materialize_pulse_leaf_candidate(
                    data,
                    next_traces,
                    duals,
                    cuts=cuts,
                    time_bucket_size=float(time_bucket_size),
                    eps=float(eps),
                    include_physical_paths=bool(include_physical_paths),
                )
                if candidate is not None:
                    materialized_journey_leaves += 1
                    candidates_by_signature.setdefault(candidate.journey.signature, candidate)
                else:
                    infeasible_leaves += 1
                used = frozenset(sequence)
                if len(next_traces) < sortie_limit:
                    dfs(
                        next_traces,
                        tuple(task for task in remaining_tasks if task not in used),
                        float(trip.end_time),
                        float(prefix_reduced_cost)
                        + float(trip.cost)
                        - sum(float(duals.cover.get(int(task), 0.0)) for task in sequence),
                        float(prefix_energy) + float(trip.energy),
                    )

    if sortie_limit > 0 and not stop_requested():
        dfs(tuple(), task_order, float(root_start_time), 0.0, 0.0)

    candidates = tuple(
        candidates_by_signature[signature]
        for signature in sorted(candidates_by_signature, key=repr)
    )
    negative_leaves = tuple(
        candidate for candidate in candidates if candidate.true_reduced_cost < -float(eps)
    )
    harvested_journeys: tuple[JourneyColumn, ...] = tuple()
    harvest_diagnostics: dict[str, object] = {}
    if bool(harvest_after_negative_enabled) and negative_leaves:
        harvest_limit = int(negative_harvest_limit) if int(negative_harvest_limit) > 0 else len(negative_leaves)
        harvest_source = tuple(
            candidate for candidate in negative_leaves if tuple(candidate.journey.signature) not in forbidden
        )
        if bool(support_aware_harvesting_enabled) and harvest_limit > 0 and harvest_source:
            harvest = harvest_support_aware_negative_journeys(
                (candidate.journey for candidate in harvest_source),
                true_duals=duals,
                cuts=cuts,
                active_masks=active_masks,
                pool_masks=pool_masks,
                forbidden_signatures=forbidden,
                eps=float(eps),
                max_columns=harvest_limit,
                min_new_masks=0,
                replacement_cap=harvest_limit,
                top_k_strongest=harvest_limit,
                max_jaccard_selected=1.0,
                max_jaccard_active=1.0,
                max_containment=1.0,
            )
            harvested_journeys = tuple(harvest.selected)
            harvest_diagnostics = dict(harvest.diagnostics)
        else:
            harvested_journeys = tuple(candidate.journey for candidate in harvest_source[:harvest_limit])
            harvest_diagnostics = {
                "candidate_negative_count": len(negative_leaves),
                "selected_count": len(harvested_journeys),
            }
    best_true_reduced_cost = (
        min(float(candidate.true_reduced_cost) for candidate in candidates)
        if candidates
        else None
    )
    status = "OPTIMAL" if stop_status is None else str(stop_status)
    reason = "exhausted" if stop_reason is None else str(stop_reason)
    exhausted = stop_status is None
    if bool(harvest_after_negative_enabled) and negative_leaves:
        exhausted = False
        status = "FOUND_NEGATIVE_HARVESTED" if harvested_journeys else "FOUND_NEGATIVE"
        reason = "harvest_after_negative"
    return ToyPulseExhaustiveResult(
        candidates=candidates,
        exhausted=exhausted,
        status=status,
        reason=reason,
        generated_sortie_traces=int(generated_sortie_traces),
        generated_leaves=int(materialized_journey_leaves),
        materialized_sorties=int(materialized_sorties),
        materialized_journey_leaves=int(materialized_journey_leaves),
        materialized_journeys=int(materialized_journey_leaves),
        infeasible_leaves=int(infeasible_leaves),
        recursions=int(recursions),
        expanded_states=int(expanded_states),
        pulse_return_pruned=int(pulse_return_pruned),
        pulse_time_window_pruned=int(pulse_time_window_pruned),
        pulse_resource_pruned=int(pulse_resource_pruned),
        pulse_bound_pruned=int(pulse_bound_pruned),
        pulse_archive_pruned=int(pulse_archive_pruned),
        pulse_depot_ready_pruned=int(pulse_depot_ready_pruned),
        pulse_negative_found=bool(negative_leaves),
        pulse_harvested_count=len(harvested_journeys),
        harvested_journeys=harvested_journeys,
        harvest_diagnostics=harvest_diagnostics,
        best_true_reduced_cost=best_true_reduced_cost,
        negative_leaves=negative_leaves,
        shard_first_task=shard_task,
    )


def _toy_max_tasks_per_sortie(data: FutureData, configured: int) -> int:
    if configured > 0:
        return min(int(configured), len(data.tasks))
    min_demand = max(1.0e-9, min(data.task_value(task, "d") for task in data.tasks))
    return min(len(data.tasks), max(1, int(data.capacity // min_demand)))


def _toy_visited_mask(
    task_order: tuple[int, ...],
    remaining_tasks: tuple[int, ...],
    task_to_bit: dict[int, int],
) -> int:
    remaining = frozenset(int(task) for task in remaining_tasks)
    mask = 0
    for task in task_order:
        if int(task) not in remaining:
            mask |= 1 << int(task_to_bit[int(task)])
    return mask


def _toy_task_sequences_iter(tasks: tuple[int, ...], max_tasks: int) -> Iterator[tuple[int, ...]]:
    limit = min(int(max_tasks), len(tasks))
    for size in range(1, limit + 1):
        yield from (tuple(int(task) for task in sequence) for sequence in itertools.permutations(tasks, size))


def _toy_arc_option_combinations_iter(
    data: FutureData,
    sequence: tuple[int, ...],
) -> Iterator[tuple[ArcOption, ...]]:
    legs: list[tuple[ArcOption, ...]] = []
    current = 0
    for task in sequence:
        options = _safe_options(data, current, int(task))
        if not options:
            return
        legs.append(options)
        current = int(task)
    options = _safe_options(data, current, 0)
    if not options:
        return
    legs.append(options)
    for combo in itertools.product(*legs):
        yield tuple(combo)


def _safe_options(data: FutureData, source: int, target: int) -> tuple[ArcOption, ...]:
    try:
        return tuple(data.options(int(source), int(target)))
    except KeyError:
        return tuple()


def _normalize_second_action_shard(value: int | str | None) -> int | str | None:
    if value is None:
        return None
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"return", "depot", "return-after-first-task"}:
            return "return"
        return int(normalized)
    return int(value)


def _toy_exact_safe_sortie_prune_reason(
    data: FutureData,
    sequence: tuple[int, ...],
    start_time: float,
    arc_options: tuple[ArcOption, ...],
    *,
    return_feasibility_enabled: bool,
    time_window_enabled: bool,
    resource_enabled: bool,
) -> str | None:
    """Return a safe prune reason for this fixed completed sortie trace."""

    if len(arc_options) != len(sequence) + 1:
        return None
    current_time = float(start_time)
    travel_energy = 0.0
    service_energy = 0.0
    task_waiting_allowed = bool(data.instance.get("scheduling", {}).get("task_waiting_allowed", True))

    if resource_enabled:
        load = sum(float(data.task_value(task, "d")) for task in sequence)
        service_energy = sum(float(data.task_value(task, "g")) for task in sequence)
        if load > float(data.capacity) + 1.0e-9:
            return "resource"

    for leg_index, task in enumerate(sequence):
        option = arc_options[leg_index]
        travel_energy += float(option.energy)
        arrival = current_time + float(option.tau)
        ready_time = float(data.task_value(task, "r"))
        if task_waiting_allowed:
            service_start = max(ready_time, arrival)
        else:
            if time_window_enabled and arrival < ready_time - 1.0e-9:
                return "time_window"
            service_start = arrival
        finish_service = service_start + float(data.task_value(task, "sigma"))
        if time_window_enabled and finish_service > float(data.task_value(task, "D")) + 1.0e-9:
            return "time_window"
        current_time = finish_service

    return_option = arc_options[-1]
    travel_energy += float(return_option.energy)
    return_time = current_time + float(return_option.tau)
    elapsed_before_recharge = max(0.0, return_time - float(start_time))
    survival_energy = float(data.survival_energy_rate) * elapsed_before_recharge
    total_energy = travel_energy + service_energy + survival_energy
    if resource_enabled and total_energy > float(data.energy_limit) + 1.0e-9:
        return "resource"
    if return_feasibility_enabled:
        recharge_time = total_energy / float(data.rho)
        end_time = return_time + recharge_time
        if end_time > float(data.horizon) + 1.0e-9:
            return "return"
    return None


__all__ = [
    "ToyPulseExhaustiveResult",
    "toy_root_exhaustive_pulse",
]
