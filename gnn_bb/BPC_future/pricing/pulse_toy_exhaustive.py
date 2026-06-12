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

from BPC_future.core.branching import BranchConstraint
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
    pulse_branch_pruned: int
    pulse_negative_found: bool
    pulse_harvested_count: int
    pulse_negative_pool_size: int
    pulse_harvested_new_task_set_count: int
    pulse_harvested_support_changing_count: int
    pulse_harvested_replacement_count: int
    harvested_journeys: tuple[JourneyColumn, ...]
    harvest_diagnostics: dict[str, object]
    best_true_reduced_cost: float | None
    negative_leaves: tuple[PulseLeafCandidate, ...]
    shard_first_task: int | None = None
    pulse_capacity_pruned: int = 0
    pulse_energy_pruned: int = 0

    @property
    def found_negative(self) -> bool:
        return bool(self.negative_leaves)

    @property
    def journeys(self) -> tuple[JourneyColumn, ...]:
        return tuple(candidate.journey for candidate in self.candidates)

    @property
    def journey_signatures(self) -> tuple[tuple, ...]:
        return tuple(candidate.journey.signature for candidate in self.candidates)

    @property
    def transition_time_window_pruned(self) -> int:
        return int(self.pulse_time_window_pruned)

    @property
    def transition_energy_pruned(self) -> int:
        return int(self.pulse_energy_pruned)

    @property
    def transition_return_pruned(self) -> int:
        return int(self.pulse_return_pruned)


def _harvest_diagnostic_int(diagnostics: dict[str, object], key: str) -> int:
    value = diagnostics.get(key, 0)
    if value is None:
        return 0
    return int(value)


def _harvest_replacement_count(diagnostics: dict[str, object]) -> int:
    explicit = _harvest_diagnostic_int(diagnostics, "selected_replacement_task_set_count")
    if explicit:
        return explicit
    return _harvest_diagnostic_int(
        diagnostics, "selected_strong_replacement_count"
    ) + _harvest_diagnostic_int(diagnostics, "selected_weak_replacement_count")


def _select_negative_leaf_harvest(
    negative_leaves: tuple[PulseLeafCandidate, ...],
    *,
    duals: JourneyDuals,
    cuts: tuple[FutureCut, ...],
    eps: float,
    harvest_after_negative_enabled: bool,
    support_aware_harvesting_enabled: bool,
    negative_harvest_limit: int,
    active_masks: tuple[object, ...],
    pool_masks: tuple[object, ...],
    forbidden_signatures: tuple[object, ...],
) -> tuple[tuple[JourneyColumn, ...], dict[str, object]]:
    if not bool(harvest_after_negative_enabled) or not negative_leaves:
        return tuple(), {}
    forbidden = {tuple(signature) for signature in (forbidden_signatures or tuple())}
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
        return tuple(harvest.selected), dict(harvest.diagnostics)
    harvested_journeys = tuple(candidate.journey for candidate in harvest_source[:harvest_limit])
    return harvested_journeys, {
        "candidate_negative_count": len(negative_leaves),
        "selected_count": len(harvested_journeys),
        "selected_new_mask_count": len(harvested_journeys),
        "selected_new_task_set_count": len(harvested_journeys),
        "selected_support_changing_count": len(harvested_journeys),
        "selected_replacement_task_set_count": 0,
    }


@dataclass(frozen=True)
class PrefixReducedCostLedger:
    """Proof-side prefix reduced-cost ledger for transition Pulse.

    exact_prefix_rc contains only contributions already fixed by the trace:
    fixed/fleet once per journey, traversed arc costs, service costs, and
    covered-task dual rewards.  lb_prefix_rc is the safe value used by bound
    pruning; Phase 7E keeps it equal to exact_prefix_rc and only combines it
    with fail-open lower bounds that do not include cuts.
    """

    exact_prefix_rc: float = 0.0
    lb_prefix_rc: float = 0.0
    covered_tasks: frozenset[int] = frozenset()
    fixed_fleet_charged: bool = False

    @classmethod
    def root(cls) -> "PrefixReducedCostLedger":
        return cls()

    def extend_task(
        self,
        data: FutureData,
        duals: JourneyDuals,
        *,
        task: int,
        arc_cost: float,
        starts_journey: bool,
    ) -> "PrefixReducedCostLedger":
        task = int(task)
        if task in self.covered_tasks:
            raise ValueError(f"task {task} already covered in prefix ledger")
        fixed_fleet = 0.0
        fixed_charged = bool(self.fixed_fleet_charged)
        if bool(starts_journey):
            if fixed_charged:
                raise ValueError("fixed/fleet contribution already charged")
            fixed_fleet = float(data.fixed_vehicle_cost) - float(duals.fleet_limit)
            fixed_charged = True
        contribution = (
            float(fixed_fleet)
            + float(arc_cost)
            + float(data.task_value(task, "c_srv"))
            - float(duals.cover.get(task, 0.0))
        )
        return PrefixReducedCostLedger(
            exact_prefix_rc=float(self.exact_prefix_rc) + float(contribution),
            lb_prefix_rc=float(self.lb_prefix_rc) + float(contribution),
            covered_tasks=frozenset((*self.covered_tasks, task)),
            fixed_fleet_charged=fixed_charged,
        )

    def return_to_depot(self, *, return_cost: float) -> "PrefixReducedCostLedger":
        return PrefixReducedCostLedger(
            exact_prefix_rc=float(self.exact_prefix_rc) + float(return_cost),
            lb_prefix_rc=float(self.lb_prefix_rc) + float(return_cost),
            covered_tasks=frozenset(self.covered_tasks),
            fixed_fleet_charged=bool(self.fixed_fleet_charged),
        )


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
    harvested_journeys, harvest_diagnostics = _select_negative_leaf_harvest(
        negative_leaves,
        duals=duals,
        cuts=cuts,
        eps=float(eps),
        harvest_after_negative_enabled=bool(harvest_after_negative_enabled),
        support_aware_harvesting_enabled=bool(support_aware_harvesting_enabled),
        negative_harvest_limit=int(negative_harvest_limit),
        active_masks=active_masks,
        pool_masks=pool_masks,
        forbidden_signatures=forbidden_signatures,
    )
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
        pulse_branch_pruned=0,
        pulse_negative_found=bool(negative_leaves),
        pulse_harvested_count=len(harvested_journeys),
        pulse_negative_pool_size=len(negative_leaves),
        pulse_harvested_new_task_set_count=_harvest_diagnostic_int(
            harvest_diagnostics, "selected_new_task_set_count"
        )
        or _harvest_diagnostic_int(harvest_diagnostics, "selected_new_mask_count"),
        pulse_harvested_support_changing_count=_harvest_diagnostic_int(
            harvest_diagnostics, "selected_support_changing_count"
        ),
        pulse_harvested_replacement_count=_harvest_replacement_count(harvest_diagnostics),
        harvested_journeys=harvested_journeys,
        harvest_diagnostics=harvest_diagnostics,
        best_true_reduced_cost=best_true_reduced_cost,
        negative_leaves=negative_leaves,
        shard_first_task=shard_task,
        pulse_capacity_pruned=0,
        pulse_energy_pruned=0,
    )


@dataclass(frozen=True)
class _TransitionPulseState:
    phase: str
    traces: tuple[PulseSortieTrace, ...]
    remaining_tasks: tuple[int, ...]
    last_node: int
    current_sequence: tuple[int, ...]
    current_arc_options: tuple[ArcOption, ...]
    visited_task_mask: int
    current_sortie_task_mask: int
    sorties_used: int
    sortie_start_time: float
    current_time: float
    travel_energy: float
    service_energy: float
    load_used: float
    partial_exact_prefix_rc: float
    partial_lb_prefix_rc: float
    pending_same_mask: int


def transition_root_only_pulse(
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
    branch_constraints: tuple[BranchConstraint, ...] = tuple(),
    deadline: float | None = None,
    max_recursions: int = 0,
    archive_dominance_enabled: bool = False,
    archive_max_records_per_key: int = 32,
    bound_pruning_enabled: bool = False,
    harvest_after_negative_enabled: bool = False,
    support_aware_harvesting_enabled: bool = False,
    negative_harvest_limit: int = 0,
    active_masks: tuple[object, ...] = tuple(),
    pool_masks: tuple[object, ...] = tuple(),
    forbidden_signatures: tuple[object, ...] = tuple(),
    include_physical_paths: bool = True,
) -> ToyPulseExhaustiveResult:
    """Phase-7A root-only Pulse core with transition-level feasibility checks.

    This test-only core keeps the Phase-3A leaf contract: every completed
    sortie/journey is still materialized through the existing evaluator.
    """

    unsupported_branch = tuple(
        constraint for constraint in branch_constraints if constraint.kind not in {"same_vehicle", "separate_vehicle"}
    )
    if unsupported_branch:
        return _empty_transition_result(
            status="UNSUPPORTED",
            reason="unsupported_branch",
            shard_first_task=None if first_task_shard is None else int(first_task_shard),
        )

    task_order = tuple(int(task) for task in data.tasks)
    max_tasks = _toy_max_tasks_per_sortie(data, int(max_tasks_per_sortie))
    sortie_limit = int(data.sortie_limit if max_sorties is None else max_sorties)
    sortie_limit = max(0, min(int(data.sortie_limit), sortie_limit))
    shard_task = None if first_task_shard is None else int(first_task_shard)
    second_shard = _normalize_second_action_shard(second_action_shard)
    task_to_bit = {int(task): index for index, task in enumerate(task_order)}
    waiting_allowed = bool(data.instance.get("scheduling", {}).get("task_waiting_allowed", True))
    archive = (
        StructuralKeyDominanceArchive(max_records_per_key=int(archive_max_records_per_key))
        if bool(archive_dominance_enabled)
        else None
    )

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
    pulse_branch_pruned = 0
    pulse_capacity_pruned = 0
    pulse_energy_pruned = 0
    stop_status: str | None = None
    stop_reason: str | None = None
    prefix_bound_pruning_supported = _prefix_rc_bound_pruning_supported(data, cuts)

    def stop_requested() -> bool:
        nonlocal stop_status, stop_reason
        if stop_status is not None:
            return True
        if deadline is not None and time.perf_counter() >= float(deadline):
            stop_status = "TIME_LIMIT"
            stop_reason = "deadline"
            return True
        return False

    def count_recursion() -> bool:
        nonlocal recursions, stop_status, stop_reason
        if stop_requested():
            return False
        recursions += 1
        if int(max_recursions) > 0 and recursions > int(max_recursions):
            stop_status = "RECURSION_LIMIT"
            stop_reason = "max_recursions"
            return False
        return True

    def search_depot(
        traces: tuple[PulseSortieTrace, ...],
        remaining_tasks: tuple[int, ...],
        next_start_time: float,
        visited_mask: int,
        sorties_used: int,
        pending_same_mask: int,
        partial_exact_prefix_rc: float,
        partial_lb_prefix_rc: float,
    ) -> None:
        nonlocal expanded_states, pulse_branch_pruned, pulse_archive_pruned, pulse_depot_ready_pruned
        nonlocal pulse_bound_pruned
        if not count_recursion():
            return
        if int(sorties_used) >= int(sortie_limit):
            return
        if not remaining_tasks:
            return
        if pending_same_mask and not _pending_same_possible(pending_same_mask, remaining_tasks, task_to_bit):
            pulse_branch_pruned += 1
            return
        if archive is not None:
            key = PulseStructuralKey(
                phase="depot_ready",
                last_node=0,
                visited_task_mask=int(visited_mask),
                current_sortie_task_mask=0,
                sorties_used=int(sorties_used),
                branch_state_key=_transition_archive_branch_state_key(
                    int(pending_same_mask),
                    waiting_allowed=waiting_allowed,
                    current_time=float(next_start_time),
                ),
            )
            decision = archive.consider(
                key,
                PulseArchiveRecord(
                    partial_reduced_cost_lb=float(partial_lb_prefix_rc),
                    exact_prefix_cost=float(partial_exact_prefix_rc),
                    current_time=float(next_start_time),
                    energy_used=0.0,
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
        if bool(bound_pruning_enabled) and bool(prefix_bound_pruning_supported) and traces:
            remaining_lb = _depot_remaining_reduced_cost_lower_bound(
                data,
                duals,
                remaining_tasks=remaining_tasks,
                fixed_fleet_charged=True,
            )
            if remaining_lb is not None and float(partial_lb_prefix_rc) + float(remaining_lb) >= -float(eps):
                pulse_bound_pruned += 1
                return
        expanded_states += 1
        for task in remaining_tasks:
            task = int(task)
            if shard_task is not None and not traces and task != int(shard_task):
                continue
            for option in _safe_options(data, 0, task):
                state = _TransitionPulseState(
                    phase="open_sortie",
                    traces=traces,
                    remaining_tasks=remaining_tasks,
                    last_node=0,
                    current_sequence=tuple(),
                    current_arc_options=tuple(),
                    visited_task_mask=int(visited_mask),
                    current_sortie_task_mask=0,
                    sorties_used=int(sorties_used),
                    sortie_start_time=float(next_start_time),
                    current_time=float(next_start_time),
                    travel_energy=0.0,
                    service_energy=0.0,
                    load_used=0.0,
                    partial_exact_prefix_rc=float(partial_exact_prefix_rc),
                    partial_lb_prefix_rc=float(partial_lb_prefix_rc),
                    pending_same_mask=int(pending_same_mask),
                )
                next_state = try_extend_task(state, task, option)
                if next_state is not None:
                    search_open(next_state)

    def search_open(state: _TransitionPulseState) -> None:
        nonlocal expanded_states, pulse_branch_pruned, pulse_archive_pruned, pulse_bound_pruned
        if not count_recursion():
            return
        if archive is not None:
            survival_so_far = float(data.survival_energy_rate) * max(
                0.0,
                float(state.current_time) - float(state.sortie_start_time),
            )
            key = PulseStructuralKey(
                phase="open_sortie",
                last_node=int(state.last_node),
                visited_task_mask=int(state.visited_task_mask),
                current_sortie_task_mask=int(state.current_sortie_task_mask),
                sorties_used=int(state.sorties_used),
                branch_state_key=_transition_archive_branch_state_key(
                    int(state.pending_same_mask),
                    waiting_allowed=waiting_allowed,
                    current_time=float(state.current_time),
                ),
            )
            decision = archive.consider(
                key,
                PulseArchiveRecord(
                    partial_reduced_cost_lb=float(state.partial_lb_prefix_rc),
                    exact_prefix_cost=float(state.partial_exact_prefix_rc),
                    current_time=float(state.current_time) if waiting_allowed else None,
                    start_interval=None
                    if waiting_allowed
                    else (float(state.current_time), float(state.current_time)),
                    energy_used=float(state.travel_energy)
                    + float(state.service_energy)
                    + float(survival_so_far),
                    load_used=float(state.load_used),
                    trace_summary=tuple(trace.sequence for trace in state.traces)
                    + (tuple(state.current_sequence),),
                    proof_mode=True,
                ),
                waiting_allowed=waiting_allowed,
            )
            if decision.dominated:
                pulse_archive_pruned += 1
                return
        expanded_states += 1
        can_return_now = _second_action_allows_return(state, second_shard)
        if can_return_now:
            complete_sortie_by_return(state)
        elif _is_first_sortie_second_action_point(state):
            pulse_branch_pruned += 1
        remaining_after_current = tuple(
            int(task)
            for task in state.remaining_tasks
            if not (int(state.visited_task_mask) & (1 << int(task_to_bit[int(task)])))
        )
        if bool(bound_pruning_enabled) and bool(prefix_bound_pruning_supported):
            remaining_lb = _open_sortie_remaining_reduced_cost_lower_bound(
                data,
                duals,
                current_node=int(state.last_node),
                remaining_tasks=remaining_after_current,
            )
            if remaining_lb is not None and float(state.partial_lb_prefix_rc) + float(remaining_lb) >= -float(eps):
                pulse_bound_pruned += 1
                return
        if len(state.current_sequence) >= int(max_tasks):
            return
        for task in remaining_after_current:
            task = int(task)
            if not _second_action_allows_task(state, task, second_shard):
                pulse_branch_pruned += 1
                continue
            for option in _safe_options(data, int(state.last_node), task):
                next_state = try_extend_task(state, task, option)
                if next_state is not None:
                    search_open(next_state)

    def try_extend_task(
        state: _TransitionPulseState,
        task: int,
        option: ArcOption,
    ) -> _TransitionPulseState | None:
        nonlocal pulse_time_window_pruned, pulse_resource_pruned, pulse_return_pruned, pulse_branch_pruned
        nonlocal pulse_capacity_pruned, pulse_energy_pruned
        task = int(task)
        bit = 1 << int(task_to_bit[int(task)])
        if int(state.visited_task_mask) & bit:
            pulse_branch_pruned += 1
            return None
        branch_update = _transition_branch_update(
            int(state.visited_task_mask),
            int(state.pending_same_mask),
            task,
            branch_constraints,
            task_to_bit,
        )
        if branch_update is None:
            pulse_branch_pruned += 1
            return None
        next_visited_mask, next_pending_mask = branch_update
        remaining_after = tuple(int(item) for item in state.remaining_tasks if int(item) != task)
        if next_pending_mask and not _pending_same_possible(next_pending_mask, remaining_after, task_to_bit):
            pulse_branch_pruned += 1
            return None
        next_load = float(state.load_used) + float(data.task_value(task, "d"))
        if next_load > float(data.capacity) + 1.0e-9:
            pulse_resource_pruned += 1
            pulse_capacity_pruned += 1
            return None
        arrival = float(state.current_time) + float(option.tau)
        ready_time = float(data.task_value(task, "r"))
        if waiting_allowed:
            service_start = max(ready_time, arrival)
        else:
            if arrival < ready_time - 1.0e-9:
                pulse_time_window_pruned += 1
                return None
            service_start = arrival
        finish_service = service_start + float(data.task_value(task, "sigma"))
        if finish_service > float(data.task_value(task, "D")) + 1.0e-9:
            pulse_time_window_pruned += 1
            return None
        next_travel_energy = float(state.travel_energy) + float(option.energy)
        next_service_energy = float(state.service_energy) + float(data.task_value(task, "g"))
        survival_so_far = float(data.survival_energy_rate) * max(
            0.0,
            float(finish_service) - float(state.sortie_start_time),
        )
        if next_travel_energy + next_service_energy + survival_so_far > float(data.energy_limit) + 1.0e-9:
            pulse_resource_pruned += 1
            pulse_energy_pruned += 1
            return None
        if not _future_return_lower_bound_possible(
            data,
            current_time=float(finish_service),
            sortie_start_time=float(state.sortie_start_time),
            travel_energy=float(next_travel_energy),
            service_energy=float(next_service_energy),
            candidate_return_nodes=(task,) + remaining_after,
        ):
            pulse_return_pruned += 1
            return None
        next_sequence = tuple(state.current_sequence) + (task,)
        next_arc_options = tuple(state.current_arc_options) + (option,)
        next_ledger = _ledger_from_transition_state(
            state,
            task_order=task_order,
            task_to_bit=task_to_bit,
        ).extend_task(
            data,
            duals,
            task=task,
            arc_cost=float(option.cost),
            starts_journey=not state.traces and not state.current_sequence,
        )
        return _TransitionPulseState(
            phase="open_sortie",
            traces=state.traces,
            remaining_tasks=remaining_after,
            last_node=task,
            current_sequence=next_sequence,
            current_arc_options=next_arc_options,
            visited_task_mask=int(next_visited_mask),
            current_sortie_task_mask=int(state.current_sortie_task_mask) | bit,
            sorties_used=int(state.sorties_used),
            sortie_start_time=float(state.sortie_start_time),
            current_time=float(finish_service),
            travel_energy=float(next_travel_energy),
            service_energy=float(next_service_energy),
            load_used=float(next_load),
            partial_exact_prefix_rc=float(next_ledger.exact_prefix_rc),
            partial_lb_prefix_rc=float(next_ledger.lb_prefix_rc),
            pending_same_mask=int(next_pending_mask),
        )

    def complete_sortie_by_return(state: _TransitionPulseState) -> None:
        nonlocal generated_sortie_traces, materialized_sorties, materialized_journey_leaves
        nonlocal infeasible_leaves, pulse_return_pruned, pulse_branch_pruned
        if not state.current_sequence:
            return
        return_options = _safe_options(data, int(state.last_node), 0)
        if not return_options:
            pulse_return_pruned += 1
            return
        for return_option in return_options:
            if not _direct_return_option_feasible(
                data,
                current_time=float(state.current_time),
                sortie_start_time=float(state.sortie_start_time),
                travel_energy=float(state.travel_energy),
                service_energy=float(state.service_energy),
                return_option=return_option,
            ):
                pulse_return_pruned += 1
                continue
            trace = PulseSortieTrace(
                sequence=tuple(state.current_sequence),
                start_time=float(state.sortie_start_time),
                arc_options=tuple(state.current_arc_options) + (return_option,),
            )
            generated_sortie_traces += 1
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
            next_traces = tuple(state.traces) + (trace,)
            if int(state.pending_same_mask) == 0:
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
            elif int(state.sorties_used) + 1 >= int(sortie_limit):
                pulse_branch_pruned += 1
            if int(state.sorties_used) + 1 < int(sortie_limit) and state.remaining_tasks:
                if state.pending_same_mask and not _pending_same_possible(
                    int(state.pending_same_mask),
                    state.remaining_tasks,
                    task_to_bit,
                ):
                    pulse_branch_pruned += 1
                    continue
                returned_ledger = _ledger_from_transition_state(
                    state,
                    task_order=task_order,
                    task_to_bit=task_to_bit,
                ).return_to_depot(return_cost=float(return_option.cost))
                search_depot(
                    next_traces,
                    tuple(state.remaining_tasks),
                    float(trip.end_time),
                    int(state.visited_task_mask),
                    int(state.sorties_used) + 1,
                    int(state.pending_same_mask),
                    float(returned_ledger.exact_prefix_rc),
                    float(returned_ledger.lb_prefix_rc),
                )

    if sortie_limit > 0 and not stop_requested():
        search_depot(
            tuple(),
            task_order,
            float(root_start_time),
            0,
            0,
            0,
            0.0,
            0.0,
        )

    candidates = tuple(
        candidates_by_signature[signature]
        for signature in sorted(candidates_by_signature, key=repr)
    )
    negative_leaves = tuple(
        candidate for candidate in candidates if candidate.true_reduced_cost < -float(eps)
    )
    harvested_journeys, harvest_diagnostics = _select_negative_leaf_harvest(
        negative_leaves,
        duals=duals,
        cuts=cuts,
        eps=float(eps),
        harvest_after_negative_enabled=bool(harvest_after_negative_enabled),
        support_aware_harvesting_enabled=bool(support_aware_harvesting_enabled),
        negative_harvest_limit=int(negative_harvest_limit),
        active_masks=active_masks,
        pool_masks=pool_masks,
        forbidden_signatures=forbidden_signatures,
    )
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
        pulse_branch_pruned=int(pulse_branch_pruned),
        pulse_negative_found=bool(negative_leaves),
        pulse_harvested_count=len(harvested_journeys),
        pulse_negative_pool_size=len(negative_leaves),
        pulse_harvested_new_task_set_count=_harvest_diagnostic_int(
            harvest_diagnostics, "selected_new_task_set_count"
        )
        or _harvest_diagnostic_int(harvest_diagnostics, "selected_new_mask_count"),
        pulse_harvested_support_changing_count=_harvest_diagnostic_int(
            harvest_diagnostics, "selected_support_changing_count"
        ),
        pulse_harvested_replacement_count=_harvest_replacement_count(harvest_diagnostics),
        harvested_journeys=harvested_journeys,
        harvest_diagnostics=harvest_diagnostics,
        best_true_reduced_cost=best_true_reduced_cost,
        negative_leaves=negative_leaves,
        shard_first_task=shard_task,
        pulse_capacity_pruned=int(pulse_capacity_pruned),
        pulse_energy_pruned=int(pulse_energy_pruned),
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


def _empty_transition_result(
    *,
    status: str,
    reason: str,
    shard_first_task: int | None,
) -> ToyPulseExhaustiveResult:
    return ToyPulseExhaustiveResult(
        candidates=tuple(),
        exhausted=False,
        status=str(status),
        reason=str(reason),
        generated_sortie_traces=0,
        generated_leaves=0,
        materialized_sorties=0,
        materialized_journey_leaves=0,
        materialized_journeys=0,
        infeasible_leaves=0,
        recursions=0,
        expanded_states=0,
        pulse_return_pruned=0,
        pulse_time_window_pruned=0,
        pulse_resource_pruned=0,
        pulse_bound_pruned=0,
        pulse_archive_pruned=0,
        pulse_depot_ready_pruned=0,
        pulse_branch_pruned=0,
        pulse_negative_found=False,
        pulse_harvested_count=0,
        pulse_negative_pool_size=0,
        pulse_harvested_new_task_set_count=0,
        pulse_harvested_support_changing_count=0,
        pulse_harvested_replacement_count=0,
        harvested_journeys=tuple(),
        harvest_diagnostics={},
        best_true_reduced_cost=None,
        negative_leaves=tuple(),
        shard_first_task=shard_first_task,
        pulse_capacity_pruned=0,
        pulse_energy_pruned=0,
    )


def _ledger_from_transition_state(
    state: _TransitionPulseState,
    *,
    task_order: tuple[int, ...],
    task_to_bit: dict[int, int],
) -> PrefixReducedCostLedger:
    return PrefixReducedCostLedger(
        exact_prefix_rc=float(state.partial_exact_prefix_rc),
        lb_prefix_rc=float(state.partial_lb_prefix_rc),
        covered_tasks=_tasks_from_mask(int(state.visited_task_mask), task_order, task_to_bit),
        fixed_fleet_charged=bool(state.traces or state.current_sequence),
    )


def _tasks_from_mask(
    mask: int,
    task_order: tuple[int, ...],
    task_to_bit: dict[int, int],
) -> frozenset[int]:
    return frozenset(
        int(task)
        for task in task_order
        if int(mask) & (1 << int(task_to_bit[int(task)]))
    )


def _prefix_rc_bound_pruning_supported(data: FutureData, cuts: tuple[FutureCut, ...]) -> bool:
    if cuts:
        return False
    for task in data.tasks:
        if float(data.task_value(int(task), "c_srv")) < -1.0e-9:
            return False
    for options in data.arc_options.values():
        for option in options:
            if float(option.cost) < -1.0e-9:
                return False
    return True


def _positive_cover_reward_bound(duals: JourneyDuals, tasks: tuple[int, ...]) -> float:
    return sum(max(0.0, float(duals.cover.get(int(task), 0.0))) for task in tasks)


def _min_arc_option_cost(data: FutureData, source: int, target: int) -> float | None:
    options = _safe_options(data, int(source), int(target))
    if not options:
        return None
    return min(float(option.cost) for option in options)


def _min_return_cost_lower_bound(data: FutureData, candidate_return_nodes: tuple[int, ...]) -> float | None:
    costs = [
        float(cost)
        for node in candidate_return_nodes
        for cost in (_min_arc_option_cost(data, int(node), 0),)
        if cost is not None
    ]
    if not costs:
        return None
    return min(costs)


def _depot_remaining_reduced_cost_lower_bound(
    data: FutureData,
    duals: JourneyDuals,
    *,
    remaining_tasks: tuple[int, ...],
    fixed_fleet_charged: bool,
) -> float | None:
    if not remaining_tasks:
        return None
    outbound_costs = [
        float(cost)
        for task in remaining_tasks
        for cost in (_min_arc_option_cost(data, 0, int(task)),)
        if cost is not None
    ]
    return_costs = [
        float(cost)
        for task in remaining_tasks
        for cost in (_min_arc_option_cost(data, int(task), 0),)
        if cost is not None
    ]
    if not outbound_costs or not return_costs:
        return None
    fixed_fleet = 0.0 if bool(fixed_fleet_charged) else float(data.fixed_vehicle_cost) - float(duals.fleet_limit)
    return (
        float(fixed_fleet)
        + min(outbound_costs)
        + min(return_costs)
        - _positive_cover_reward_bound(duals, remaining_tasks)
    )


def _open_sortie_remaining_reduced_cost_lower_bound(
    data: FutureData,
    duals: JourneyDuals,
    *,
    current_node: int,
    remaining_tasks: tuple[int, ...],
) -> float | None:
    candidate_return_nodes = (int(current_node),) + tuple(int(task) for task in remaining_tasks)
    return_lb = _min_return_cost_lower_bound(data, candidate_return_nodes)
    if return_lb is None:
        return None
    return float(return_lb) - _positive_cover_reward_bound(duals, remaining_tasks)


def _future_return_lower_bound_possible(
    data: FutureData,
    *,
    current_time: float,
    sortie_start_time: float,
    travel_energy: float,
    service_energy: float,
    candidate_return_nodes: tuple[int, ...],
) -> bool:
    """Optimistic exact-safe check that some future return could still fit."""

    best_return_time: float | None = None
    best_return_energy: float | None = None
    for node in candidate_return_nodes:
        for option in _safe_options(data, int(node), 0):
            best_return_time = float(option.tau) if best_return_time is None else min(best_return_time, float(option.tau))
            best_return_energy = (
                float(option.energy)
                if best_return_energy is None
                else min(best_return_energy, float(option.energy))
            )
    if best_return_time is None or best_return_energy is None:
        return False
    optimistic_return_time = float(current_time) + float(best_return_time)
    optimistic_survival = float(data.survival_energy_rate) * max(
        0.0,
        float(optimistic_return_time) - float(sortie_start_time),
    )
    optimistic_energy = (
        float(travel_energy)
        + float(service_energy)
        + float(best_return_energy)
        + float(optimistic_survival)
    )
    if optimistic_energy > float(data.energy_limit) + 1.0e-9:
        return False
    optimistic_end_time = float(optimistic_return_time) + optimistic_energy / float(data.rho)
    return optimistic_end_time <= float(data.horizon) + 1.0e-9


def _direct_return_option_feasible(
    data: FutureData,
    *,
    current_time: float,
    sortie_start_time: float,
    travel_energy: float,
    service_energy: float,
    return_option: ArcOption,
) -> bool:
    return_time = float(current_time) + float(return_option.tau)
    survival_energy = float(data.survival_energy_rate) * max(
        0.0,
        float(return_time) - float(sortie_start_time),
    )
    total_energy = (
        float(travel_energy)
        + float(return_option.energy)
        + float(service_energy)
        + float(survival_energy)
    )
    if total_energy > float(data.energy_limit) + 1.0e-9:
        return False
    end_time = float(return_time) + total_energy / float(data.rho)
    return end_time <= float(data.horizon) + 1.0e-9


def _transition_branch_update(
    visited_mask: int,
    pending_same_mask: int,
    task: int,
    constraints: tuple[BranchConstraint, ...],
    task_to_bit: dict[int, int],
) -> tuple[int, int] | None:
    task_bit_index = task_to_bit.get(int(task))
    if task_bit_index is None:
        return None
    new_visited = int(visited_mask) | (1 << int(task_bit_index))
    new_pending = int(pending_same_mask)
    for constraint in constraints:
        if constraint.task_j is None:
            return None
        left_bit_index = task_to_bit.get(int(constraint.task_i))
        right_bit_index = task_to_bit.get(int(constraint.task_j))
        if left_bit_index is None or right_bit_index is None:
            continue
        left_bit = 1 << int(left_bit_index)
        right_bit = 1 << int(right_bit_index)
        left = bool(new_visited & left_bit)
        right = bool(new_visited & right_bit)
        if constraint.kind == "separate_vehicle":
            if left and right:
                return None
        elif constraint.kind == "same_vehicle":
            if left and right:
                new_pending &= ~left_bit
                new_pending &= ~right_bit
            elif left:
                new_pending |= right_bit
            elif right:
                new_pending |= left_bit
        else:
            return None
    return int(new_visited), int(new_pending)


def _transition_archive_branch_state_key(
    pending_same_mask: int,
    *,
    waiting_allowed: bool,
    current_time: float,
) -> tuple[object, ...]:
    if bool(waiting_allowed):
        return (int(pending_same_mask),)
    return (int(pending_same_mask), "exact_time", round(float(current_time), 9))


def _pending_same_possible(
    pending_same_mask: int,
    remaining_tasks: tuple[int, ...],
    task_to_bit: dict[int, int],
) -> bool:
    remaining_mask = 0
    for task in remaining_tasks:
        bit_index = task_to_bit.get(int(task))
        if bit_index is not None:
            remaining_mask |= 1 << int(bit_index)
    return (int(pending_same_mask) & ~int(remaining_mask)) == 0


def _is_first_sortie_second_action_point(state: _TransitionPulseState) -> bool:
    return not state.traces and len(state.current_sequence) == 1


def _second_action_allows_return(
    state: _TransitionPulseState,
    second_shard: int | str | None,
) -> bool:
    if second_shard is None:
        return True
    if not _is_first_sortie_second_action_point(state):
        return True
    return second_shard == "return"


def _second_action_allows_task(
    state: _TransitionPulseState,
    task: int,
    second_shard: int | str | None,
) -> bool:
    if second_shard is None:
        return True
    if not _is_first_sortie_second_action_point(state):
        return True
    return second_shard != "return" and int(task) == int(second_shard)


__all__ = [
    "ToyPulseExhaustiveResult",
    "transition_root_only_pulse",
    "toy_root_exhaustive_pulse",
]
