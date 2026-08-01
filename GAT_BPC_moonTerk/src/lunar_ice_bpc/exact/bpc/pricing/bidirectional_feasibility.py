"""Exact depot-meet primitives for the P0V4 bidirectional feasibility gate.

This module is deliberately not a pricing backend.  It supplies the
mathematical state needed by a future Native backward labelling kernel and
keeps the feasibility prototype fail-closed: joined routes are rebuilt by the
frozen forward timing semantics, and no no-negative certificate is emitted.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import inf, isfinite
from typing import Iterable

from lunar_ice_bpc.exact.core.branching import (
    BranchContext,
    journey_satisfies_branch_context,
)
from lunar_ice_bpc.exact.core.columns import TimedSortie, build_timed_sortie
from lunar_ice_bpc.exact.core.cuts import CutContext
from lunar_ice_bpc.exact.core.data import LunarIceData
from lunar_ice_bpc.exact.core.journey import (
    JourneyColumn,
    build_journey_column,
)
from lunar_ice_bpc.exact.core.objective import (
    additive_objective_value,
    operating_cost_value,
)
from lunar_ice_bpc.exact.master.journey_rmp import (
    JourneyDuals,
    manual_journey_reduced_cost,
)


BIDIRECTIONAL_FEASIBILITY_POLICY_ID = (
    "p0v4_frozen_dual_depot_meet_max_plus_v1"
)
_EPS = 1.0e-9


@dataclass(frozen=True)
class StaticSortieTransform:
    """Start-time-independent exact summary of one sortie skeleton."""

    sequence: tuple[str, ...]
    path_types: tuple[str, ...]
    release_time: float
    latest_departure: float
    duration: float
    science_weight: float
    weighted_completion_offset: float
    operating_cost: float
    risk_integral: float
    task_set: frozenset[str]

    @property
    def structurally_feasible(self) -> bool:
        return bool(
            self.sequence
            and len(self.path_types) == len(self.sequence) + 1
            and self.release_time <= self.latest_departure + _EPS
        )

    def departure_time(self, available_time: float) -> float:
        return max(float(available_time), float(self.release_time))

    def can_start_at(self, available_time: float) -> bool:
        return bool(
            self.structurally_feasible
            and self.departure_time(available_time)
            <= self.latest_departure + _EPS
        )

    def end_time(self, available_time: float) -> float:
        return self.departure_time(available_time) + float(self.duration)

    def weighted_completion(self, available_time: float) -> float:
        return (
            float(self.science_weight)
            * self.departure_time(available_time)
            + float(self.weighted_completion_offset)
        )

    def materialize(
        self,
        data: LunarIceData,
        *,
        available_time: float,
    ) -> TimedSortie:
        sortie = build_timed_sortie(
            data,
            self.sequence,
            self.path_types,
            start_time=float(available_time),
        )
        if not sortie.feasible:
            raise ValueError(
                "static sortie transform accepted an infeasible materialization"
            )
        if (
            abs(float(sortie.start_time) - self.departure_time(available_time))
            > 2.0e-6
            or abs(float(sortie.end_time) - self.end_time(available_time))
            > 2.0e-6
            or abs(
                float(sortie.discovery_completion_term)
                - self.weighted_completion(available_time)
            )
            > 2.0e-5
        ):
            raise ValueError(
                "static sortie transform drifted from frozen P0V4 timing"
            )
        return sortie


@dataclass(frozen=True)
class BackwardSuffixSummary:
    """Exact boundary summary for a suffix joined at a depot."""

    transforms: tuple[StaticSortieTransform, ...]
    task_set: frozenset[str]
    latest_input_time: float
    structurally_feasible: bool

    def accepts(self, prefix_end_time: float) -> bool:
        return bool(
            self.structurally_feasible
            and float(prefix_end_time)
            <= float(self.latest_input_time) + _EPS
        )


@dataclass(frozen=True)
class BidirectionalJoinAudit:
    """Audited result of one forward-prefix/backward-suffix join."""

    status: str
    feasible: bool
    branch_feasible: bool
    task_sets_disjoint: bool
    suffix_boundary_feasible: bool
    journey: JourneyColumn | None
    true_reduced_cost: float | None
    cut_coefficients: dict[str, float]
    static_objective: float | None
    objective_drift: float | None
    weighted_completion_drift: float | None
    policy_id: str = BIDIRECTIONAL_FEASIBILITY_POLICY_ID
    can_certify_no_negative: bool = False
    certificate_scope: str = "DIAGNOSTIC_BIDIRECTIONAL_FEASIBILITY_ONLY"


def build_static_sortie_transform(
    data: LunarIceData,
    sequence: Iterable[str],
    path_types: Iterable[str],
) -> StaticSortieTransform:
    """Build the exact max-plus transform used by backward suffix labels."""

    ordered = tuple(str(task_id) for task_id in sequence)
    paths = tuple(str(path_type) for path_type in path_types)
    if not ordered:
        raise ValueError("bidirectional sortie transform requires a task")
    if len(paths) != len(ordered) + 1:
        raise ValueError(
            "bidirectional sortie transform requires one path per leg"
        )
    if len(set(ordered)) != len(ordered):
        raise ValueError(
            "bidirectional sortie transform requires elementary task order"
        )
    if len(ordered) > int(data.max_tasks_per_trip):
        return _infeasible_transform(ordered, paths)

    current = "depot"
    elapsed = 0.0
    release = 0.0
    latest = float(data.horizon)
    weight = 0.0
    completion_offset = 0.0
    distance = 0.0
    energy = 0.0
    risk = 0.0
    demand = 0.0
    shadow = 0.0
    service_cost = 0.0
    for index, task_id in enumerate(ordered):
        option = data.option(current, task_id, paths[index])
        elapsed += float(option.travel_time_min)
        distance += float(option.distance_km)
        energy += float(option.energy_proxy)
        risk += float(option.risk_integral)
        shadow += float(option.shadow_exposure_min)
        task = data.tasks[task_id]
        release = max(
            release,
            float(task.ready_time) - elapsed,
        )
        latest = min(
            latest,
            float(task.due_time) - float(task.service_time) - elapsed,
        )
        completion_offset += float(task.science_weight) * (
            elapsed + float(task.service_time)
        )
        weight += float(task.science_weight)
        elapsed += float(task.service_time)
        energy += float(task.service_energy)
        risk += (
            float(task.local_thermal_risk)
            * float(task.service_time)
            * 0.01
        )
        shadow += (
            float(task.local_shadow_score) * float(task.service_time)
        )
        demand += float(task.demand)
        service_cost += float(task.service_cost)
        current = task_id

    back = data.option(current, "depot", paths[-1])
    elapsed += float(back.travel_time_min)
    distance += float(back.distance_km)
    energy += float(back.energy_proxy)
    risk += float(back.risk_integral)
    shadow += float(back.shadow_exposure_min)
    recharge = float(data.dock_overhead_min) + energy / max(
        _EPS,
        float(data.recharge_power_proxy_per_min),
    )
    duration = elapsed + recharge
    latest = min(latest, float(data.horizon) - duration)
    resources_feasible = bool(
        demand <= float(data.capacity) + _EPS
        and energy <= float(data.energy_limit) + _EPS
        and shadow
        <= float(data.max_shadow_exposure_per_sortie) + _EPS
    )
    if not resources_feasible:
        latest = -inf
    operating = operating_cost_value(
        service_cost=service_cost,
        distance_km=distance,
        energy_proxy=energy,
    )
    return StaticSortieTransform(
        sequence=ordered,
        path_types=paths,
        release_time=float(release),
        latest_departure=float(latest),
        duration=float(duration),
        science_weight=float(weight),
        weighted_completion_offset=float(completion_offset),
        operating_cost=float(operating),
        risk_integral=float(risk),
        task_set=frozenset(ordered),
    )


def summarize_backward_suffix(
    transforms: Iterable[StaticSortieTransform],
) -> BackwardSuffixSummary:
    """Return the exact latest depot time from which a suffix is feasible."""

    rows = tuple(transforms)
    seen: set[str] = set()
    structurally_feasible = True
    for row in rows:
        if not row.structurally_feasible or seen.intersection(row.task_set):
            structurally_feasible = False
        seen.update(row.task_set)
    latest_input = inf
    for row in reversed(rows):
        cap = float(row.latest_departure)
        if isfinite(latest_input):
            cap = min(cap, latest_input - float(row.duration))
        if float(row.release_time) > cap + _EPS:
            structurally_feasible = False
        latest_input = cap
    return BackwardSuffixSummary(
        transforms=rows,
        task_set=frozenset(seen),
        latest_input_time=float(latest_input),
        structurally_feasible=bool(structurally_feasible),
    )


def join_at_depot(
    data: LunarIceData,
    *,
    forward_transforms: Iterable[StaticSortieTransform],
    backward_suffix: BackwardSuffixSummary,
    true_duals: JourneyDuals,
    branch_context: BranchContext | None = None,
    cut_context: CutContext | None = None,
) -> BidirectionalJoinAudit:
    """Join two exact halves and replay the complete route under P0V4."""

    forward = tuple(forward_transforms)
    prefix_tasks = frozenset(
        task_id
        for transform in forward
        for task_id in transform.task_set
    )
    prefix_elementary = sum(
        len(transform.task_set) for transform in forward
    ) == len(prefix_tasks)
    disjoint = bool(
        prefix_elementary
        and prefix_tasks.isdisjoint(backward_suffix.task_set)
    )
    current_time = 0.0
    materialized: list[TimedSortie] = []
    try:
        for transform in forward:
            if not transform.can_start_at(current_time):
                raise ValueError("forward prefix is not time feasible")
            sortie = transform.materialize(
                data,
                available_time=current_time,
            )
            materialized.append(sortie)
            current_time = float(sortie.end_time)
    except (KeyError, ValueError):
        return _failed_join(
            "FORWARD_PREFIX_INFEASIBLE",
            task_sets_disjoint=disjoint,
            suffix_boundary_feasible=False,
        )
    suffix_boundary = backward_suffix.accepts(current_time)
    if not disjoint or not suffix_boundary:
        return _failed_join(
            (
                "TASK_SET_OVERLAP"
                if not disjoint
                else "BACKWARD_SUFFIX_BOUNDARY_INFEASIBLE"
            ),
            task_sets_disjoint=disjoint,
            suffix_boundary_feasible=suffix_boundary,
        )
    try:
        for transform in backward_suffix.transforms:
            sortie = transform.materialize(
                data,
                available_time=current_time,
            )
            materialized.append(sortie)
            current_time = float(sortie.end_time)
        journey = build_journey_column(data, tuple(materialized))
    except (KeyError, ValueError):
        return _failed_join(
            "JOIN_REPLAY_INFEASIBLE",
            task_sets_disjoint=disjoint,
            suffix_boundary_feasible=suffix_boundary,
        )
    active_branch = branch_context or BranchContext()
    branch_feasible = journey_satisfies_branch_context(
        journey,
        active_branch,
    )
    if not branch_feasible:
        return BidirectionalJoinAudit(
            status="BRANCH_CONTEXT_INFEASIBLE",
            feasible=False,
            branch_feasible=False,
            task_sets_disjoint=True,
            suffix_boundary_feasible=True,
            journey=journey,
            true_reduced_cost=None,
            cut_coefficients={},
            static_objective=None,
            objective_drift=None,
            weighted_completion_drift=None,
        )
    active_cuts = cut_context or CutContext()
    cut_coefficients = active_cuts.coefficients_for(journey)
    true_rc = manual_journey_reduced_cost(
        journey,
        true_duals,
        cut_coefficients=cut_coefficients,
    )
    static_operating = sum(
        transform.operating_cost
        for transform in (*forward, *backward_suffix.transforms)
    )
    static_risk = sum(
        transform.risk_integral
        for transform in (*forward, *backward_suffix.transforms)
    )
    static_completion = 0.0
    static_time = 0.0
    for transform in (*forward, *backward_suffix.transforms):
        static_completion += transform.weighted_completion(static_time)
        static_time = transform.end_time(static_time)
    static_objective = additive_objective_value(
        data,
        operating_cost=static_operating,
        risk_integral=static_risk,
        weighted_completion_time=static_completion,
    )
    objective_drift = abs(
        float(static_objective) - float(journey.objective)
    )
    completion_drift = abs(
        float(static_completion)
        - float(journey.discovery_completion_term)
    )
    if objective_drift > 2.0e-6 or completion_drift > 2.0e-5:
        return BidirectionalJoinAudit(
            status="OBJECTIVE_RECOMPOSITION_MISMATCH",
            feasible=False,
            branch_feasible=True,
            task_sets_disjoint=True,
            suffix_boundary_feasible=True,
            journey=journey,
            true_reduced_cost=true_rc,
            cut_coefficients=cut_coefficients,
            static_objective=float(static_objective),
            objective_drift=float(objective_drift),
            weighted_completion_drift=float(completion_drift),
        )
    return BidirectionalJoinAudit(
        status="FEASIBLE_JOIN_DIAGNOSTIC_ONLY",
        feasible=True,
        branch_feasible=True,
        task_sets_disjoint=True,
        suffix_boundary_feasible=True,
        journey=journey,
        true_reduced_cost=float(true_rc),
        cut_coefficients=cut_coefficients,
        static_objective=float(static_objective),
        objective_drift=float(objective_drift),
        weighted_completion_drift=float(completion_drift),
    )


def split_and_rejoin_journey(
    data: LunarIceData,
    journey: JourneyColumn,
    *,
    split_sortie_index: int,
    true_duals: JourneyDuals,
    branch_context: BranchContext | None = None,
    cut_context: CutContext | None = None,
) -> BidirectionalJoinAudit:
    """Differential helper for an already legal frozen-P0V4 route."""

    split = int(split_sortie_index)
    if split < 0 or split > len(journey.sorties):
        raise ValueError("split sortie index is outside the journey")
    transforms = tuple(
        build_static_sortie_transform(
            data,
            sortie.tasks,
            tuple(leg.path_type for leg in sortie.legs),
        )
        for sortie in journey.sorties
    )
    suffix = summarize_backward_suffix(transforms[split:])
    return join_at_depot(
        data,
        forward_transforms=transforms[:split],
        backward_suffix=suffix,
        true_duals=true_duals,
        branch_context=branch_context,
        cut_context=cut_context,
    )


def _infeasible_transform(
    sequence: tuple[str, ...],
    path_types: tuple[str, ...],
) -> StaticSortieTransform:
    return StaticSortieTransform(
        sequence=sequence,
        path_types=path_types,
        release_time=inf,
        latest_departure=-inf,
        duration=inf,
        science_weight=0.0,
        weighted_completion_offset=0.0,
        operating_cost=inf,
        risk_integral=inf,
        task_set=frozenset(sequence),
    )


def _failed_join(
    status: str,
    *,
    task_sets_disjoint: bool,
    suffix_boundary_feasible: bool,
) -> BidirectionalJoinAudit:
    return BidirectionalJoinAudit(
        status=str(status),
        feasible=False,
        branch_feasible=False,
        task_sets_disjoint=bool(task_sets_disjoint),
        suffix_boundary_feasible=bool(suffix_boundary_feasible),
        journey=None,
        true_reduced_cost=None,
        cut_coefficients={},
        static_objective=None,
        objective_drift=None,
        weighted_completion_drift=None,
    )
