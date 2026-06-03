"""Timed-trip pricing for the BPC_future v1 model."""

from __future__ import annotations

from dataclasses import dataclass
import itertools
import math
import time
import weakref

from BPC_future.core.branching import BranchConstraint, partial_sequence_allowed, trip_allowed_by_branch
from BPC_future.core.columns import TimedTrip, candidate_start_times_for_trip, evaluate_timed_trip, rounded
from BPC_future.core.cuts import FutureCut
from BPC_future.core.data import ArcOption, FutureData
from BPC_future.master.rmp import FutureDuals, manual_reduced_cost


@dataclass
class PricingResult:
    trips: list[TimedTrip]
    exhausted: bool
    best_reduced_cost: float | None
    generated_sequences: int
    evaluated_timed_trips: int
    negative_trips: int
    false_candidate_trips: int = 0
    dominance_pruned: int = 0
    diverse_selected: int = 0
    cache_hits: int = 0


@dataclass(frozen=True)
class PricingConfig:
    time_bucket_size: float = 1.0
    max_tasks_per_trip: int = 0
    max_sequences: int = 0
    max_timed_evaluations: int = 0
    max_returned_trips: int = 100
    eps: float = 1.0e-6
    heuristic: bool = False
    heuristic_top_tasks: int = 8
    time_limit: float = 0.0
    start_time_step: float = 5.0
    selection_mode: str = "reduced_cost"
    max_path_combinations_per_sequence: int = 0
    path_dominance_enabled: bool = False
    start_optimization_enabled: bool = False
    best_start_per_path_profile_enabled: bool = False
    early_stop_negative_per_sequence_enabled: bool = False
    stop_after_negative_trips: int = 0
    max_negative_trips_per_sequence: int = 1
    max_negative_starts_per_profile: int = 0
    generalized_partial_dominance_enabled: bool = False


@dataclass(frozen=True)
class _FixedNoWaitingTripProfile:
    lower_start: float
    upper_start: float
    end_offset: float
    cost: float
    energy: float


@dataclass(frozen=True)
class _StartCandidateProfile:
    start: float
    occupancy: tuple[tuple[int, float], ...] = tuple()


@dataclass(frozen=True)
class _OptimizedArcProfile:
    arc_options: tuple[ArcOption, ...]
    profile: _FixedNoWaitingTripProfile
    starts: tuple[_StartCandidateProfile, ...]


@dataclass(frozen=True)
class _PartialNoWaitingPathProfile:
    arc_options: tuple[ArcOption, ...]
    lower_start: float
    upper_start: float
    offset: float
    travel_cost: float
    travel_energy: float
    service_cost: float
    service_energy: float


class _PricingTimeout(Exception):
    pass


@dataclass
class _SequenceResourcePrecheckCache:
    task_load: dict[int, float]
    task_service_time: dict[int, float]
    task_service_energy: dict[int, float]
    min_arc_energy: dict[tuple[int, int], float]
    min_arc_time: dict[tuple[int, int], float]
    result_by_sequence: dict[tuple[int, ...], bool]
    hits: int = 0
    misses: int = 0
    clears: int = 0


_RESOURCE_PRECHECK_CACHE: dict[int, tuple[weakref.ReferenceType[FutureData], _SequenceResourcePrecheckCache]] = {}
_RESOURCE_PRECHECK_MAX_ENTRIES_PER_DATA = 300000


def _clear_sequence_resource_precheck_cache() -> None:
    _RESOURCE_PRECHECK_CACHE.clear()


def _sequence_resource_precheck_cache_stats(data: FutureData) -> dict[str, int]:
    entry = _RESOURCE_PRECHECK_CACHE.get(id(data))
    if entry is None or entry[0]() is not data:
        return {"entries": 0, "hits": 0, "misses": 0, "clears": 0}
    cache = entry[1]
    return {
        "entries": len(cache.result_by_sequence),
        "hits": int(cache.hits),
        "misses": int(cache.misses),
        "clears": int(cache.clears),
    }


def _sequence_resource_precheck_cache(data: FutureData) -> _SequenceResourcePrecheckCache:
    key = id(data)
    entry = _RESOURCE_PRECHECK_CACHE.get(key)
    if entry is not None and entry[0]() is data:
        return entry[1]
    cache = _SequenceResourcePrecheckCache(
        task_load={int(task): float(data.task_value(int(task), "d")) for task in data.tasks},
        task_service_time={int(task): float(data.task_value(int(task), "sigma")) for task in data.tasks},
        task_service_energy={int(task): float(data.task_value(int(task), "g")) for task in data.tasks},
        min_arc_energy={
            (int(origin), int(destination)): min(float(option.energy) for option in options)
            for (origin, destination), options in data.arc_options.items()
            if options
        },
        min_arc_time={
            (int(origin), int(destination)): min(float(option.tau) for option in options)
            for (origin, destination), options in data.arc_options.items()
            if options
        },
        result_by_sequence={},
    )
    _RESOURCE_PRECHECK_CACHE[key] = (weakref.ref(data), cache)
    return cache


def _check_pricing_deadline(deadline: float | None) -> None:
    if deadline is not None and time.perf_counter() > float(deadline):
        raise _PricingTimeout


def price_timed_trips(
    data: FutureData,
    duals: FutureDuals,
    branch_constraints: tuple[BranchConstraint, ...],
    *,
    vehicle: int,
    config: PricingConfig,
    cuts: tuple[FutureCut, ...] = tuple(),
    true_duals: FutureDuals | None = None,
    phase: str = "phase2",
    trip_cache: dict[tuple, tuple[tuple[TimedTrip, ...], int, int]] | None = None,
) -> PricingResult:
    started = time.perf_counter()
    max_tasks = _max_tasks_per_trip(data, config.max_tasks_per_trip)
    task_order = _task_order(data, duals, vehicle, config)
    candidates_by_signature: dict[tuple[tuple[int, ...], tuple[str, ...], float], tuple[float, TimedTrip]] = {}
    generated_sequences = 0
    timed_evaluations = 0
    best_rc: float | None = None
    exhausted = True
    false_candidates = 0
    dominance_pruned = 0
    cache_hits = 0
    max_sequences = int(config.max_sequences)
    max_timed = int(config.max_timed_evaluations)
    time_limit = float(config.time_limit)
    deadline = None if time_limit <= 0.0 else started + time_limit

    try:
        for size in range(1, max_tasks + 1):
            for sequence in itertools.permutations(task_order, size):
                _check_pricing_deadline(deadline)
                if time_limit > 0.0 and time.perf_counter() - started > time_limit:
                    exhausted = False
                    break
                if not partial_sequence_allowed(tuple(sequence), vehicle, branch_constraints):
                    continue
                if not _sequence_resource_precheck(data, tuple(sequence)):
                    dominance_pruned += 1
                    continue
                generated_sequences += 1
                if max_sequences > 0 and generated_sequences > max_sequences:
                    exhausted = False
                    break
                sequence_lb = _sequence_reduced_cost_lower_bound(
                    data,
                    tuple(sequence),
                    vehicle,
                    duals,
                    branch_constraints,
                    cuts,
                    phase,
                )
                if sequence_lb >= -float(config.eps):
                    dominance_pruned += 1
                    continue
                representative_time = _time_duals_zero(duals, vehicle, config.eps)
                dominance_safe = _time_duals_nonpositive(duals, vehicle, config.eps)
                sequence_candidates, sequence_best_rc, evals, pruned, cache_hit, sequence_false, partial_sequence_scan = _priced_timed_trips_for_sequence(
                    data,
                    tuple(sequence),
                    vehicle,
                    duals,
                    branch_constraints,
                    config,
                    cuts,
                    phase,
                    trip_cache,
                    true_duals,
                    representative_time,
                    dominance_safe,
                    deadline,
                )
                timed_evaluations += evals
                dominance_pruned += pruned
                cache_hits += int(cache_hit)
                false_candidates += sequence_false
                if (not config.heuristic) and pruned > 0 and not dominance_safe:
                    exhausted = False
                if partial_sequence_scan:
                    exhausted = False
                if max_timed > 0 and timed_evaluations > max_timed:
                    exhausted = False
                    break
                if sequence_best_rc is not None:
                    best_rc = sequence_best_rc if best_rc is None else min(best_rc, sequence_best_rc)
                for rc, trip in sequence_candidates:
                    old = candidates_by_signature.get(trip.signature)
                    if old is None or rc < old[0] - 1.0e-9:
                        candidates_by_signature[trip.signature] = (rc, trip)
                if config.stop_after_negative_trips > 0 and len(candidates_by_signature) >= int(config.stop_after_negative_trips):
                    exhausted = False
                    break
            if not exhausted:
                break
    except _PricingTimeout:
        exhausted = False

    candidates = sorted(candidates_by_signature.values(), key=lambda item: item[0])
    selected_pairs = _select_candidates(candidates, int(config.max_returned_trips), config.selection_mode)
    selected = [trip for _rc, trip in selected_pairs]
    if config.max_returned_trips > 0:
        selected = selected[: int(config.max_returned_trips)]
    return PricingResult(
        trips=selected,
        exhausted=exhausted,
        best_reduced_cost=best_rc,
        generated_sequences=generated_sequences,
        evaluated_timed_trips=timed_evaluations,
        negative_trips=len(selected),
        false_candidate_trips=false_candidates,
        dominance_pruned=dominance_pruned,
        diverse_selected=len(selected) if config.selection_mode == "diverse" else 0,
        cache_hits=cache_hits,
    )


def _priced_timed_trips_for_sequence(
    data: FutureData,
    sequence: tuple[int, ...],
    vehicle: int,
    duals: FutureDuals,
    branch_constraints: tuple[BranchConstraint, ...],
    config: PricingConfig,
    cuts: tuple[FutureCut, ...],
    phase: str,
    trip_cache: dict[tuple, tuple[tuple[TimedTrip, ...], int, int]] | None,
    true_duals: FutureDuals | None,
    representative_time: bool,
    dominance_safe: bool,
    deadline: float | None = None,
) -> tuple[list[tuple[float, TimedTrip]], float | None, int, int, bool, int, bool]:
    if (
        not config.heuristic
        and bool(config.start_optimization_enabled)
        and not branch_constraints
        and _pricing_cuts_start_independent(cuts)
        and not bool(data.instance.get("scheduling", {}).get("task_waiting_allowed", True))
    ):
        return _priced_timed_trips_for_sequence_with_start_optimization(
            data,
            sequence,
            vehicle,
            duals,
            config,
            cuts,
            phase,
            trip_cache,
            dominance_safe,
            deadline,
        )
    best_rc: float | None = None
    trips, evaluations, pruned, cache_hit = _timed_trips_for_sequence(
        data,
        sequence,
        config,
        trip_cache,
        representative_time=representative_time,
        dominance_safe=dominance_safe,
        deadline=deadline,
    )
    negative: list[tuple[float, TimedTrip]] = []
    false_candidates = 0
    for trip in trips:
        rc = manual_reduced_cost(trip, vehicle, duals, branch_constraints, cuts, phase=phase)
        if best_rc is None or rc < best_rc - 1.0e-9:
            best_rc = rc
        if rc >= -float(config.eps):
            continue
        if not trip_allowed_by_branch(trip, vehicle, branch_constraints):
            continue
        if true_duals is not None:
            true_rc = manual_reduced_cost(trip, vehicle, true_duals, branch_constraints, cuts, phase=phase)
            if true_rc >= -float(config.eps):
                false_candidates += 1
                continue
            rc = true_rc
        negative.append((rc, trip))
    negative.sort(key=lambda item: (item[0], item[1].start_time, item[1].arc_option_ids))
    partial = False
    limit = int(config.max_negative_trips_per_sequence)
    if limit > 0 and len(negative) > limit:
        partial = True
        negative = negative[:limit]
    return negative, best_rc, evaluations, pruned, cache_hit, false_candidates, partial


def _priced_timed_trips_for_sequence_with_start_optimization(
    data: FutureData,
    sequence: tuple[int, ...],
    vehicle: int,
    duals: FutureDuals,
    config: PricingConfig,
    cuts: tuple[FutureCut, ...],
    phase: str,
    trip_cache: dict[tuple, tuple[tuple[TimedTrip, ...], int, int]] | None,
    dominance_safe: bool,
    deadline: float | None = None,
) -> tuple[list[tuple[float, TimedTrip]], float | None, int, int, bool, int, bool]:
    """Price a no-waiting sequence by optimizing start time before building columns.

    For fixed task order and fixed path-option tuple, all non-time reduced-cost
    terms are constant and the time-occupation term is piecewise linear in the
    start time. Its breakpoints are exactly where the trip start or trip end
    crosses a time bucket boundary, so checking those points is enough for the
    configured trip-time master. We still build real TimedTrip objects only for
    starts that have negative true reduced cost.
    """

    bucket = float(config.time_bucket_size)
    time_duals = {
        int(bucket_index): float(value)
        for (r, bucket_index), value in duals.time_occupation.items()
        if int(r) == int(vehicle) and abs(float(value)) > 1.0e-12
    }
    point_cut_duals = _point_capacity_cut_duals(cuts, duals, vehicle)
    representative_start_only = not time_duals and not point_cut_duals
    arc_profiles, pruned, cache_hit = _optimized_arc_profiles_for_sequence(
        data,
        sequence,
        config,
        trip_cache,
        dominance_safe,
        cuts,
        vehicle,
        representative_start_only,
        deadline=deadline,
    )
    best_rc: float | None = None
    evaluations = 0
    negative: list[tuple[float, TimedTrip]] = []
    partial = False
    limit = int(config.max_negative_trips_per_sequence)
    profile_limit = int(config.max_negative_starts_per_profile)
    early_stop_sequence = bool(config.early_stop_negative_per_sequence_enabled) and limit > 0
    for arc_profile in arc_profiles:
        _check_pricing_deadline(deadline)
        profile = arc_profile.profile
        base_rc = _fixed_trip_base_reduced_cost(
            data,
            sequence,
            vehicle,
            profile,
            duals,
            cuts,
            phase,
        )
        if not bool(config.best_start_per_path_profile_enabled):
            profile_negative: list[tuple[float, TimedTrip]] = []
            for start_profile in arc_profile.starts:
                _check_pricing_deadline(deadline)
                rc = _reduced_cost_at_start(
                    base_rc,
                    start_profile.occupancy,
                    start_profile.start,
                    profile.end_offset,
                    time_duals,
                    point_cut_duals,
                    bucket,
                    data.horizon,
                )
                evaluations += 1
                if best_rc is None or rc < best_rc - 1.0e-9:
                    best_rc = rc
                if rc >= -float(config.eps):
                    continue
                trip = evaluate_timed_trip(
                    data,
                    sequence,
                    start_profile.start,
                    time_bucket_size=bucket,
                    arc_options=arc_profile.arc_options,
                    include_physical_paths=False,
                )
                if trip is None:
                    continue
                true_rc = manual_reduced_cost(trip, vehicle, duals, tuple(), cuts, phase=phase)
                if true_rc < -float(config.eps):
                    profile_negative.append((true_rc, trip))
                    if early_stop_sequence and len(negative) + len(profile_negative) >= limit:
                        partial = True
                        negative.extend(profile_negative)
                        negative.sort(key=lambda item: (item[0], item[1].start_time, item[1].arc_option_ids))
                        return negative[:limit], best_rc, evaluations, pruned, cache_hit, 0, partial
            profile_negative.sort(key=lambda item: (item[0], item[1].start_time, item[1].arc_option_ids))
            if profile_limit > 0 and len(profile_negative) > profile_limit:
                partial = True
                profile_negative = profile_negative[:profile_limit]
            negative.extend(profile_negative)
            continue
        best_start_rc: float | None = None
        best_start_profile: _StartCandidateProfile | None = None
        for start_profile in arc_profile.starts:
            _check_pricing_deadline(deadline)
            rc = _reduced_cost_at_start(
                base_rc,
                start_profile.occupancy,
                start_profile.start,
                profile.end_offset,
                time_duals,
                point_cut_duals,
                bucket,
                data.horizon,
            )
            evaluations += 1
            if best_rc is None or rc < best_rc - 1.0e-9:
                best_rc = rc
            if best_start_rc is None or rc < best_start_rc - 1.0e-9:
                best_start_rc = rc
                best_start_profile = start_profile
        if best_start_rc is None or best_start_profile is None:
            continue
        if best_start_rc >= -float(config.eps):
            continue
        trip = evaluate_timed_trip(
            data,
            sequence,
            best_start_profile.start,
            time_bucket_size=bucket,
            arc_options=arc_profile.arc_options,
            include_physical_paths=False,
        )
        if trip is None:
            continue
        true_rc = manual_reduced_cost(trip, vehicle, duals, tuple(), cuts, phase=phase)
        if true_rc < -float(config.eps):
            negative.append((true_rc, trip))
            if early_stop_sequence and len(negative) >= limit:
                partial = True
                negative.sort(key=lambda item: (item[0], item[1].start_time, item[1].arc_option_ids))
                return negative[:limit], best_rc, evaluations, pruned, cache_hit, 0, partial
    negative.sort(key=lambda item: (item[0], item[1].start_time, item[1].arc_option_ids))
    if limit > 0 and len(negative) > limit:
        partial = True
        negative = negative[:limit]
    return negative, best_rc, evaluations, pruned, cache_hit, 0, partial


def _timed_trips_for_sequence(
    data: FutureData,
    sequence: tuple[int, ...],
    config: PricingConfig,
    trip_cache: dict[tuple, tuple[tuple[TimedTrip, ...], int, int]] | None,
    *,
    representative_time: bool = False,
    dominance_safe: bool = False,
    deadline: float | None = None,
) -> tuple[tuple[TimedTrip, ...], int, int, bool]:
    bucket = float(config.time_bucket_size)
    start_step = max(float(config.start_time_step), bucket)
    combo_limit = config.max_path_combinations_per_sequence if config.heuristic else 0
    combo_dominance = bool(config.path_dominance_enabled) and (bool(config.heuristic) or bool(dominance_safe))
    cache_key = (
        str(data.instance_path),
        tuple(int(task) for task in sequence),
        round(bucket, 9),
        round(start_step, 9),
        int(combo_limit),
        bool(combo_dominance),
        bool(representative_time),
    )
    if trip_cache is not None and cache_key in trip_cache:
        trips, _evaluations, pruned = trip_cache[cache_key]
        return trips, 0, pruned, True
    evaluations = 0
    feasible: list[TimedTrip] = []
    arc_combinations, pruned = _path_option_combinations(
        data,
        sequence,
        max_combinations=combo_limit,
        dominance_enabled=combo_dominance,
        deadline=deadline,
    )
    for arc_options in arc_combinations:
        _check_pricing_deadline(deadline)
        starts = candidate_start_times_for_trip(data, sequence, arc_options, start_step=start_step)
        if representative_time and starts:
            starts = (starts[0],)
        for start in starts:
            _check_pricing_deadline(deadline)
            trip = evaluate_timed_trip(
                data,
                sequence,
                start,
                time_bucket_size=bucket,
                arc_options=arc_options,
                include_physical_paths=False,
            )
            evaluations += 1
            if trip is not None:
                feasible.append(trip)
    trips = tuple(feasible)
    if trip_cache is not None:
        trip_cache[cache_key] = (trips, evaluations, pruned)
    return trips, evaluations, pruned, False


def _time_duals_zero(duals: FutureDuals, vehicle: int, eps: float) -> bool:
    threshold = max(1.0e-9, float(eps))
    for (r, _bucket), value in duals.time_occupation.items():
        if int(r) == int(vehicle) and abs(float(value)) > threshold:
            return False
    return True


def _time_duals_nonpositive(duals: FutureDuals, vehicle: int, eps: float) -> bool:
    threshold = max(1.0e-9, float(eps))
    for (r, _bucket), value in duals.time_occupation.items():
        if int(r) == int(vehicle) and float(value) > threshold:
            return False
    return True


def _fixed_no_waiting_trip_profile(
    data: FutureData,
    sequence: tuple[int, ...],
    arc_options: tuple[ArcOption, ...],
) -> _FixedNoWaitingTripProfile | None:
    if len(arc_options) != len(sequence) + 1:
        return None
    load = sum(data.task_value(task, "d") for task in sequence)
    if load > data.capacity + 1.0e-9:
        return None

    lower = 0.0
    upper = float(data.horizon)
    offset = 0.0
    travel_energy = 0.0
    travel_cost = 0.0
    service_energy = 0.0
    service_cost = 0.0
    for leg_index, task in enumerate(sequence):
        option = arc_options[leg_index]
        travel_energy += float(option.energy)
        travel_cost += float(option.cost)
        arrival_offset = offset + float(option.tau)
        service = data.task_value(task, "sigma")
        lower = max(lower, data.task_value(task, "r") - arrival_offset)
        upper = min(upper, data.task_value(task, "D") - service - arrival_offset)
        offset = arrival_offset + service
        service_energy += data.task_value(task, "g")
        service_cost += data.task_value(task, "c_srv")

    back = arc_options[-1]
    travel_energy += float(back.energy)
    travel_cost += float(back.cost)
    return_offset = offset + float(back.tau)
    survival_energy = float(data.survival_energy_rate) * return_offset
    total_energy = travel_energy + service_energy + survival_energy
    if total_energy > data.energy_limit + 1.0e-9:
        return None
    recharge_time = total_energy / max(1.0e-9, float(data.rho))
    end_offset = return_offset + recharge_time
    upper = min(upper, float(data.horizon) - end_offset)
    lower = max(0.0, lower)
    if upper < lower - 1.0e-9:
        return None
    return _FixedNoWaitingTripProfile(
        lower_start=rounded(lower),
        upper_start=rounded(upper),
        end_offset=rounded(end_offset),
        cost=rounded(travel_cost + service_cost),
        energy=rounded(total_energy),
    )


def _fixed_trip_base_reduced_cost(
    data: FutureData,
    sequence: tuple[int, ...],
    vehicle: int,
    profile: _FixedNoWaitingTripProfile,
    duals: FutureDuals,
    cuts: tuple[FutureCut, ...],
    phase: str,
) -> float:
    rc = 0.0 if phase == "phase1" else float(profile.cost)
    for task in set(sequence):
        rc -= float(duals.cover.get(int(task), 0.0))
        rc -= float(duals.task_vehicle.get((int(task), int(vehicle)), 0.0))
    rc -= float(duals.sortie_count.get(int(vehicle), 0.0))
    for cut_index, cut in enumerate(cuts):
        if getattr(cut, "kind", "") == "time_point_capacity":
            continue
        coeff = _sequence_cut_coefficient(cut, sequence, vehicle)
        if coeff != 0.0:
            rc -= float(duals.cuts.get(int(cut_index), 0.0)) * coeff
    return rc


def _optimized_arc_profiles_for_sequence(
    data: FutureData,
    sequence: tuple[int, ...],
    config: PricingConfig,
    trip_cache: dict[tuple, tuple[tuple[TimedTrip, ...], int, int]] | None,
    dominance_safe: bool,
    cuts: tuple[FutureCut, ...],
    vehicle: int,
    representative_start_only: bool,
    deadline: float | None = None,
) -> tuple[tuple[_OptimizedArcProfile, ...], int, bool]:
    _check_pricing_deadline(deadline)
    bucket = float(config.time_bucket_size)
    combo_limit = config.max_path_combinations_per_sequence if config.heuristic else 0
    time_points = _time_points_from_cuts(cuts, vehicle)
    combo_dominance = (
        bool(config.path_dominance_enabled)
        and (bool(config.heuristic) or bool(dominance_safe))
        and not time_points
    )
    cache_key = (
        "optimized_profiles_v2",
        str(data.instance_path),
        tuple(int(task) for task in sequence),
        round(bucket, 9),
        int(combo_limit),
        bool(combo_dominance),
        tuple(round(point, 6) for point in time_points),
        bool(representative_start_only),
    )
    if trip_cache is not None and cache_key in trip_cache:
        cached_profiles, _evaluations, pruned = trip_cache[cache_key]  # type: ignore[assignment]
        return cached_profiles, pruned, True  # type: ignore[return-value]

    if not bool(data.instance.get("scheduling", {}).get("task_waiting_allowed", True)):
        profile_bases, pruned = _no_waiting_arc_profiles_for_sequence(
            data,
            sequence,
            max_profiles=combo_limit,
            dominance_enabled=combo_dominance,
            generalized_partial_dominance=bool(config.generalized_partial_dominance_enabled),
            deadline=deadline,
        )
    else:
        arc_combinations, pruned = _path_option_combinations(
            data,
            sequence,
            max_combinations=combo_limit,
            dominance_enabled=combo_dominance,
            deadline=deadline,
        )
        profile_bases = tuple(
            _OptimizedArcProfile(arc_options=arc_options, profile=profile, starts=tuple())
            for arc_options in arc_combinations
            for profile in (_fixed_no_waiting_trip_profile(data, sequence, arc_options),)
            if profile is not None
        )

    profiles: list[_OptimizedArcProfile] = []
    for profile_base in profile_bases:
        _check_pricing_deadline(deadline)
        profile = profile_base.profile
        start_values = _start_breakpoint_candidates(
            profile.lower_start,
            profile.upper_start,
            profile.end_offset,
            bucket,
            data.horizon,
            time_points,
        )
        if representative_start_only and start_values:
            start_values = (start_values[0],)
        starts = tuple(
            _StartCandidateProfile(start=start)
            for start in start_values
        )
        if starts:
            profiles.append(_OptimizedArcProfile(arc_options=profile_base.arc_options, profile=profile, starts=starts))
    stored = tuple(profiles)
    if trip_cache is not None:
        trip_cache[cache_key] = (stored, 0, pruned)  # type: ignore[assignment]
    return stored, pruned, False


def _no_waiting_arc_profiles_for_sequence(
    data: FutureData,
    sequence: tuple[int, ...],
    *,
    max_profiles: int = 0,
    dominance_enabled: bool = False,
    generalized_partial_dominance: bool = False,
    deadline: float | None = None,
) -> tuple[tuple[_OptimizedArcProfile, ...], int]:
    _check_pricing_deadline(deadline)
    if not sequence:
        return tuple(), 0
    load = sum(data.task_value(task, "d") for task in sequence)
    if load > data.capacity + 1.0e-9:
        return tuple(), 0
    legs = _path_option_legs(data, sequence)
    if not legs:
        return tuple(), 0

    pruned = 0
    partials = (
        _PartialNoWaitingPathProfile(
            arc_options=tuple(),
            lower_start=0.0,
            upper_start=float(data.horizon),
            offset=0.0,
            travel_cost=0.0,
            travel_energy=0.0,
            service_cost=0.0,
            service_energy=0.0,
        ),
    )
    for depth, options in enumerate(legs[:-1]):
        _check_pricing_deadline(deadline)
        next_partials: list[_PartialNoWaitingPathProfile] = []
        for partial in partials:
            _check_pricing_deadline(deadline)
            for option in options:
                _check_pricing_deadline(deadline)
                extended = _extend_no_waiting_partial(data, sequence, depth, partial, option)
                if extended is not None:
                    next_partials.append(extended)
        if dominance_enabled and next_partials:
            before = len(next_partials)
            next_partials = _pareto_filter_partial_profiles(
                next_partials,
                generalized=bool(generalized_partial_dominance),
            )
            pruned += max(0, before - len(next_partials))
        partials = tuple(next_partials)
        if not partials:
            return tuple(), pruned

    completed: list[_OptimizedArcProfile] = []
    for partial in partials:
        _check_pricing_deadline(deadline)
        for option in legs[-1]:
            _check_pricing_deadline(deadline)
            base = _complete_no_waiting_partial(data, partial, option)
            if base is not None:
                completed.append(base)
    if dominance_enabled and completed:
        before = len(completed)
        completed = _pareto_filter_optimized_profiles(completed)
        pruned += max(0, before - len(completed))

    completed.sort(key=_optimized_arc_profile_sort_key)
    if max_profiles > 0:
        pruned += max(0, len(completed) - int(max_profiles))
        completed = completed[: int(max_profiles)]
    return tuple(completed), pruned


def _path_option_legs(data: FutureData, sequence: tuple[int, ...]) -> tuple[tuple[ArcOption, ...], ...]:
    legs: list[tuple[ArcOption, ...]] = []
    current = 0
    for task in sequence:
        options = data.options(current, int(task))
        if not options:
            return tuple()
        legs.append(options)
        current = int(task)
    options = data.options(current, 0)
    if not options:
        return tuple()
    legs.append(options)
    return tuple(legs)


def _extend_no_waiting_partial(
    data: FutureData,
    sequence: tuple[int, ...],
    depth: int,
    partial: _PartialNoWaitingPathProfile,
    option: ArcOption,
) -> _PartialNoWaitingPathProfile | None:
    task = int(sequence[int(depth)])
    arrival_offset = float(partial.offset) + float(option.tau)
    service = data.task_value(task, "sigma")
    lower = max(float(partial.lower_start), data.task_value(task, "r") - arrival_offset)
    upper = min(float(partial.upper_start), data.task_value(task, "D") - service - arrival_offset)
    if upper < lower - 1.0e-9:
        return None
    offset = arrival_offset + service
    travel_energy = float(partial.travel_energy) + float(option.energy)
    service_energy = float(partial.service_energy) + data.task_value(task, "g")
    if travel_energy + service_energy > data.energy_limit + 1.0e-9:
        return None
    return _PartialNoWaitingPathProfile(
        arc_options=partial.arc_options + (option,),
        lower_start=rounded(max(0.0, lower)),
        upper_start=rounded(upper),
        offset=rounded(offset),
        travel_cost=rounded(float(partial.travel_cost) + float(option.cost)),
        travel_energy=rounded(travel_energy),
        service_cost=rounded(float(partial.service_cost) + data.task_value(task, "c_srv")),
        service_energy=rounded(service_energy),
    )


def _complete_no_waiting_partial(
    data: FutureData,
    partial: _PartialNoWaitingPathProfile,
    option: ArcOption,
) -> _OptimizedArcProfile | None:
    travel_energy = float(partial.travel_energy) + float(option.energy)
    return_offset = float(partial.offset) + float(option.tau)
    survival_energy = float(data.survival_energy_rate) * return_offset
    total_energy = travel_energy + float(partial.service_energy) + survival_energy
    if total_energy > data.energy_limit + 1.0e-9:
        return None
    recharge_time = total_energy / max(1.0e-9, float(data.rho))
    end_offset = return_offset + recharge_time
    lower = max(0.0, float(partial.lower_start))
    upper = min(float(partial.upper_start), float(data.horizon) - end_offset)
    if upper < lower - 1.0e-9:
        return None
    profile = _FixedNoWaitingTripProfile(
        lower_start=rounded(lower),
        upper_start=rounded(upper),
        end_offset=rounded(end_offset),
        cost=rounded(float(partial.travel_cost) + float(option.cost) + float(partial.service_cost)),
        energy=rounded(total_energy),
    )
    return _OptimizedArcProfile(arc_options=partial.arc_options + (option,), profile=profile, starts=tuple())


def _pareto_filter_partial_profiles(
    profiles: list[_PartialNoWaitingPathProfile],
    *,
    generalized: bool = False,
) -> list[_PartialNoWaitingPathProfile]:
    if not bool(generalized):
        grouped: dict[float, list[_PartialNoWaitingPathProfile]] = {}
        for profile in profiles:
            grouped.setdefault(round(float(profile.offset), 9), []).append(profile)
        filtered: list[_PartialNoWaitingPathProfile] = []
        for group in grouped.values():
            filtered.extend(_pareto_filter_partial_profile_group(group, generalized=False))
        filtered.sort(key=_partial_profile_sort_key)
        return filtered

    return _pareto_filter_partial_profile_group(profiles, generalized=True)


def _pareto_filter_partial_profile_group(
    profiles: list[_PartialNoWaitingPathProfile],
    *,
    generalized: bool,
) -> list[_PartialNoWaitingPathProfile]:
    filtered: list[_PartialNoWaitingPathProfile] = []
    skyline: list[_PartialNoWaitingPathProfile] = []
    for profile in sorted(profiles, key=_partial_profile_sort_key):
        if any(_dominates_partial_profile(other, profile, generalized=generalized) for other in skyline):
            continue
        skyline = [other for other in skyline if not _dominates_partial_profile(profile, other, generalized=generalized)]
        skyline.append(profile)
    filtered.extend(skyline)
    filtered.sort(key=_partial_profile_sort_key)
    return filtered


def _pareto_filter_optimized_profiles(
    profiles: list[_OptimizedArcProfile],
) -> list[_OptimizedArcProfile]:
    skyline: list[_OptimizedArcProfile] = []
    for profile in sorted(profiles, key=_optimized_arc_profile_sort_key):
        if any(_dominates_optimized_profile(other, profile) for other in skyline):
            continue
        skyline = [other for other in skyline if not _dominates_optimized_profile(profile, other)]
        skyline.append(profile)
    return skyline


def _dominates_partial_profile(
    left: _PartialNoWaitingPathProfile,
    right: _PartialNoWaitingPathProfile,
    *,
    generalized: bool = False,
) -> bool:
    if bool(generalized):
        left_current_low = float(left.lower_start) + float(left.offset)
        left_current_high = float(left.upper_start) + float(left.offset)
        right_current_low = float(right.lower_start) + float(right.offset)
        right_current_high = float(right.upper_start) + float(right.offset)
        interval_no_worse = (
            left_current_low <= right_current_low + 1.0e-9
            and left_current_high >= right_current_high - 1.0e-9
            and float(left.offset) <= float(right.offset) + 1.0e-9
        )
        interval_strict = (
            left_current_low < right_current_low - 1.0e-9
            or left_current_high > right_current_high + 1.0e-9
            or float(left.offset) < float(right.offset) - 1.0e-9
        )
    else:
        same_offset = abs(float(left.offset) - float(right.offset)) <= 1.0e-9
        if not same_offset:
            return False
        interval_no_worse = (
            float(left.lower_start) <= float(right.lower_start) + 1.0e-9
            and float(left.upper_start) >= float(right.upper_start) - 1.0e-9
        )
        interval_strict = (
            float(left.lower_start) < float(right.lower_start) - 1.0e-9
            or float(left.upper_start) > float(right.upper_start) + 1.0e-9
        )
    no_worse = (
        interval_no_worse
        and float(left.travel_cost) <= float(right.travel_cost) + 1.0e-9
        and float(left.travel_energy) <= float(right.travel_energy) + 1.0e-9
        and float(left.service_cost) <= float(right.service_cost) + 1.0e-9
        and float(left.service_energy) <= float(right.service_energy) + 1.0e-9
    )
    strict = (
        interval_strict
        or float(left.travel_cost) < float(right.travel_cost) - 1.0e-9
        or float(left.travel_energy) < float(right.travel_energy) - 1.0e-9
        or float(left.service_cost) < float(right.service_cost) - 1.0e-9
        or float(left.service_energy) < float(right.service_energy) - 1.0e-9
    )
    return bool(no_worse and strict)


def _dominates_optimized_profile(left: _OptimizedArcProfile, right: _OptimizedArcProfile) -> bool:
    a = left.profile
    b = right.profile
    no_worse = (
        float(a.lower_start) <= float(b.lower_start) + 1.0e-9
        and float(a.upper_start) >= float(b.upper_start) - 1.0e-9
        and float(a.end_offset) <= float(b.end_offset) + 1.0e-9
        and float(a.cost) <= float(b.cost) + 1.0e-9
    )
    strict = (
        float(a.lower_start) < float(b.lower_start) - 1.0e-9
        or float(a.upper_start) > float(b.upper_start) + 1.0e-9
        or float(a.end_offset) < float(b.end_offset) - 1.0e-9
        or float(a.cost) < float(b.cost) - 1.0e-9
    )
    return bool(no_worse and strict)


def _partial_profile_sort_key(profile: _PartialNoWaitingPathProfile) -> tuple[float, float, float, float, float, tuple[str, ...]]:
    return (
        round(float(profile.travel_cost), 9),
        round(float(profile.offset), 9),
        round(float(profile.travel_energy), 9),
        round(float(profile.lower_start), 9),
        round(-float(profile.upper_start), 9),
        tuple(option.option_id for option in profile.arc_options),
    )


def _optimized_arc_profile_sort_key(profile: _OptimizedArcProfile) -> tuple[float, float, float, float, float, tuple[str, ...]]:
    return (
        round(float(profile.profile.cost), 9),
        round(float(profile.profile.end_offset), 9),
        round(float(profile.profile.energy), 9),
        round(float(profile.profile.lower_start), 9),
        round(-float(profile.profile.upper_start), 9),
        tuple(option.option_id for option in profile.arc_options),
    )


def _start_breakpoint_candidates(
    lower: float,
    upper: float,
    end_offset: float,
    bucket_size: float,
    horizon: float,
    time_points: tuple[float, ...] = tuple(),
) -> tuple[float, ...]:
    if upper < lower - 1.0e-9:
        return tuple()
    bucket = max(1.0e-9, float(bucket_size))
    candidates = {rounded(lower), rounded(upper)}

    first_start_boundary = int(math.floor(lower / bucket)) - 1
    last_start_boundary = int(math.ceil(upper / bucket)) + 1
    for bucket_index in range(first_start_boundary, last_start_boundary + 1):
        start = bucket_index * bucket
        if lower - 1.0e-9 <= start <= upper + 1.0e-9:
            candidates.add(rounded(start))

    end_lower = lower + float(end_offset)
    end_upper = min(float(horizon), upper + float(end_offset))
    first_end_boundary = int(math.floor(end_lower / bucket)) - 1
    last_end_boundary = int(math.ceil(end_upper / bucket)) + 1
    for bucket_index in range(first_end_boundary, last_end_boundary + 1):
        start = bucket_index * bucket - float(end_offset)
        if lower - 1.0e-9 <= start <= upper + 1.0e-9:
            candidates.add(rounded(start))

    epsilon = min(1.0e-5, bucket * 1.0e-6)
    for point in time_points:
        for boundary in (float(point), float(point) - float(end_offset)):
            for start in (boundary - epsilon, boundary, boundary + epsilon):
                if lower - 1.0e-9 <= start <= upper + 1.0e-9:
                    candidates.add(rounded(max(lower, min(upper, start))))

    return tuple(sorted(candidates))


def _reduced_cost_at_start(
    base_rc: float,
    occupancy: tuple[tuple[int, float], ...],
    start: float,
    end_offset: float,
    time_duals: dict[int, float],
    point_cut_duals: tuple[tuple[float, float], ...],
    bucket_size: float | None = None,
    horizon: float | None = None,
) -> float:
    rc = float(base_rc)
    if time_duals:
        if occupancy:
            for bucket, coeff in occupancy:
                dual = time_duals.get(int(bucket), 0.0)
                if dual != 0.0:
                    rc -= dual * float(coeff)
        elif bucket_size is not None and horizon is not None:
            rc -= _time_dual_overlap_value(float(start), float(end_offset), float(bucket_size), float(horizon), time_duals)
    if point_cut_duals:
        end = float(start) + float(end_offset)
        for point, dual in point_cut_duals:
            if float(start) <= point + 1.0e-9 and point < end - 1.0e-9:
                rc -= dual
    return round(rc, 9)


def _time_dual_overlap_value(
    start: float,
    end_offset: float,
    bucket_size: float,
    horizon: float,
    time_duals: dict[int, float],
) -> float:
    end = float(start) + float(end_offset)
    if end <= start + 1.0e-12:
        return 0.0
    first = max(0, int(math.floor(start / bucket_size)))
    last = min(int(math.ceil(float(horizon) / bucket_size)) - 1, int(math.floor((end - 1.0e-12) / bucket_size)))
    value = 0.0
    for bucket in range(first, last + 1):
        dual = float(time_duals.get(int(bucket), 0.0))
        if dual == 0.0:
            continue
        left = bucket * bucket_size
        right = min(float(horizon), (bucket + 1) * bucket_size)
        overlap = max(0.0, min(end, right) - max(start, left))
        if overlap > 1.0e-9:
            value += dual * rounded(overlap / bucket_size)
    return value


def _occupancy_profile(
    start: float,
    end_offset: float,
    bucket_size: float,
    horizon: float,
) -> tuple[tuple[int, float], ...]:
    start = float(start)
    end = start + float(end_offset)
    if end <= start + 1.0e-12:
        return tuple()
    bucket_size = float(bucket_size)
    first = max(0, int(math.floor(start / bucket_size)))
    last = min(int(math.ceil(float(horizon) / bucket_size)) - 1, int(math.floor((end - 1.0e-12) / bucket_size)))
    occupancy: list[tuple[int, float]] = []
    for bucket in range(first, last + 1):
        left = bucket * bucket_size
        right = min(float(horizon), (bucket + 1) * bucket_size)
        overlap = max(0.0, min(end, right) - max(start, left))
        if overlap > 1.0e-9:
            occupancy.append((int(bucket), rounded(overlap / bucket_size)))
    return tuple(occupancy)


def _point_capacity_cut_duals(
    cuts: tuple[FutureCut, ...],
    duals: FutureDuals,
    vehicle: int,
) -> tuple[tuple[float, float], ...]:
    points: list[tuple[float, float]] = []
    for cut_index, cut in enumerate(cuts):
        if getattr(cut, "kind", "") != "time_point_capacity":
            continue
        if int(getattr(cut, "vehicle", -1)) != int(vehicle):
            continue
        dual = float(duals.cuts.get(int(cut_index), 0.0))
        if abs(dual) <= 1.0e-12:
            continue
        points.append((round(float(getattr(cut, "time_point")), 6), dual))
    return tuple(sorted(points))


def _time_points_from_cuts(cuts: tuple[FutureCut, ...], vehicle: int) -> tuple[float, ...]:
    points = {
        round(float(getattr(cut, "time_point")), 6)
        for cut in cuts
        if getattr(cut, "kind", "") == "time_point_capacity"
        and int(getattr(cut, "vehicle", -1)) == int(vehicle)
    }
    return tuple(sorted(points))


def _pricing_cuts_start_independent(cuts: tuple[FutureCut, ...]) -> bool:
    supported = {
        "fleet_lower_bound",
        "fleet_upper_bound",
        "fleet_prefix_disable",
        "sortie_lower_bound",
        "subset_row",
        "time_point_capacity",
    }
    return all(getattr(cut, "kind", "") in supported for cut in cuts)


def _path_option_combinations(
    data: FutureData,
    sequence: tuple[int, ...],
    *,
    max_combinations: int = 0,
    dominance_enabled: bool = False,
    deadline: float | None = None,
) -> tuple[tuple[tuple[ArcOption, ...], ...], int]:
    _check_pricing_deadline(deadline)
    legs: list[tuple[ArcOption, ...]] = []
    current = 0
    for task in sequence:
        legs.append(data.options(current, int(task)))
        current = int(task)
    legs.append(data.options(current, 0))
    if any(not options for options in legs):
        return tuple(), 0
    combos = []
    for combo in itertools.product(*legs):
        _check_pricing_deadline(deadline)
        combos.append(tuple(combo))
    original_count = len(combos)
    if dominance_enabled:
        combos = _pareto_filter_arc_combinations(combos)
    combos.sort(key=_arc_combination_sort_key)
    if max_combinations > 0:
        combos = combos[: int(max_combinations)]
    return tuple(combos), max(0, original_count - len(combos))


def _arc_combination_sort_key(combo: tuple[ArcOption, ...]) -> tuple[float, float, float, float, tuple[str, ...]]:
    return (
        round(sum(option.cost for option in combo), 9),
        round(sum(option.tau for option in combo), 9),
        round(sum(option.energy for option in combo), 9),
        round(sum(option.risk for option in combo), 9),
        tuple(option.option_id for option in combo),
    )


def _pareto_filter_arc_combinations(combos: list[tuple[ArcOption, ...]]) -> list[tuple[ArcOption, ...]]:
    skyline: list[tuple[tuple[float, float, float, float], tuple[ArcOption, ...]]] = []
    ordered = sorted(((_arc_combination_metrics(combo), combo) for combo in combos), key=lambda item: item[0])
    for metrics, combo in ordered:
        if any(_dominates_metrics(other_metrics, metrics) for other_metrics, _other in skyline):
            continue
        skyline = [
            (other_metrics, other)
            for other_metrics, other in skyline
            if not _dominates_metrics(metrics, other_metrics)
        ]
        skyline.append((metrics, combo))
    return [combo for _metrics, combo in skyline]


def _arc_combination_metrics(combo: tuple[ArcOption, ...]) -> tuple[float, float, float]:
    return (
        sum(option.cost for option in combo),
        sum(option.tau for option in combo),
        sum(option.energy for option in combo),
    )


def _dominates_metrics(left: tuple[float, ...], right: tuple[float, ...]) -> bool:
    return all(a <= b + 1.0e-9 for a, b in zip(left, right)) and any(a < b - 1.0e-9 for a, b in zip(left, right))


def _select_candidates(
    candidates: list[tuple[float, TimedTrip]],
    limit: int,
    mode: str,
) -> list[tuple[float, TimedTrip]]:
    if limit <= 0 or len(candidates) <= limit:
        return candidates
    if mode != "diverse":
        return candidates[:limit]
    selected: list[tuple[float, TimedTrip]] = []
    selected_signatures: set[tuple[tuple[int, ...], tuple[str, ...], float]] = set()

    def add(pair: tuple[float, TimedTrip]) -> None:
        if len(selected) >= limit:
            return
        signature = pair[1].signature
        if signature in selected_signatures:
            return
        selected.append(pair)
        selected_signatures.add(signature)

    for pair in candidates[: max(1, limit // 2)]:
        add(pair)
    task_seen: set[int] = set()
    for pair in candidates:
        if len(selected) >= limit:
            break
        if any(task not in task_seen for task in pair[1].tasks):
            add(pair)
            task_seen.update(pair[1].tasks)
    taskset_seen: set[frozenset[int]] = {pair[1].task_set for pair in selected}
    for pair in candidates:
        if len(selected) >= limit:
            break
        if pair[1].task_set not in taskset_seen:
            add(pair)
            taskset_seen.add(pair[1].task_set)
    for pair in candidates:
        if len(selected) >= limit:
            break
        add(pair)
    return selected


def _max_tasks_per_trip(data: FutureData, configured: int) -> int:
    if configured > 0:
        return min(int(configured), len(data.tasks))
    min_demand = max(1.0e-9, min(data.task_value(task, "d") for task in data.tasks))
    return min(len(data.tasks), max(1, int(data.capacity // min_demand)))


def _task_order(data: FutureData, duals: FutureDuals, vehicle: int, config: PricingConfig) -> tuple[int, ...]:
    tasks = sorted(
        data.tasks,
        key=lambda task: (
            -float(duals.cover.get(task, 0.0) + duals.task_vehicle.get((int(task), int(vehicle)), 0.0)),
            task,
        ),
    )
    if config.heuristic and config.heuristic_top_tasks > 0:
        return tuple(tasks[: int(config.heuristic_top_tasks)])
    return tuple(tasks)


def _sequence_resource_precheck(data: FutureData, sequence: tuple[int, ...]) -> bool:
    sequence = tuple(int(task) for task in sequence)
    cache = _sequence_resource_precheck_cache(data)
    cached = cache.result_by_sequence.get(sequence)
    if cached is not None:
        cache.hits += 1
        return bool(cached)
    cache.misses += 1
    if len(cache.result_by_sequence) >= _RESOURCE_PRECHECK_MAX_ENTRIES_PER_DATA:
        cache.result_by_sequence.clear()
        cache.clears += 1

    load = sum(cache.task_load[int(task)] for task in sequence)
    if load > data.capacity + 1.0e-9:
        cache.result_by_sequence[sequence] = False
        return False
    current = 0
    min_travel_energy = 0.0
    min_travel_time = 0.0
    for task in sequence:
        arc_key = (int(current), int(task))
        if arc_key not in cache.min_arc_energy or arc_key not in cache.min_arc_time:
            cache.result_by_sequence[sequence] = False
            return False
        min_travel_energy += float(cache.min_arc_energy[arc_key])
        min_travel_time += float(cache.min_arc_time[arc_key])
        min_travel_time += float(cache.task_service_time[int(task)])
        current = int(task)
    return_key = (int(current), 0)
    if return_key not in cache.min_arc_energy or return_key not in cache.min_arc_time:
        cache.result_by_sequence[sequence] = False
        return False
    min_travel_energy += float(cache.min_arc_energy[return_key])
    min_travel_time += float(cache.min_arc_time[return_key])
    service_energy = sum(cache.task_service_energy[int(task)] for task in sequence)
    survival = float(data.survival_energy_rate) * min_travel_time
    feasible = min_travel_energy + service_energy + survival <= data.energy_limit + 1.0e-9
    cache.result_by_sequence[sequence] = bool(feasible)
    return bool(feasible)


def _sequence_reduced_cost_lower_bound(
    data: FutureData,
    sequence: tuple[int, ...],
    vehicle: int,
    duals: FutureDuals,
    branch_constraints: tuple[BranchConstraint, ...],
    cuts: tuple[FutureCut, ...],
    phase: str,
) -> float:
    """Safe lower bound on reduced cost before path/start expansion.

    If this bound is nonnegative, no timed trip with this task order can have
    negative reduced cost. Branch rows are deliberately disabled here because
    their coefficients depend on branch semantics; branch nodes fall back to the
    full exact check.
    """

    if branch_constraints:
        return float("-inf")
    rc = 0.0
    if phase == "phase2":
        current = 0
        travel_cost_lb = 0.0
        for task in sequence:
            options = data.options(current, int(task))
            if not options:
                return float("inf")
            travel_cost_lb += min(option.cost for option in options)
            current = int(task)
        options = data.options(current, 0)
        if not options:
            return float("inf")
        travel_cost_lb += min(option.cost for option in options)
        service_cost = sum(data.task_value(task, "c_srv") for task in sequence)
        rc += float(travel_cost_lb + service_cost)

    for task in set(sequence):
        rc -= float(duals.cover.get(int(task), 0.0))
        rc -= float(duals.task_vehicle.get((int(task), int(vehicle)), 0.0))
    rc -= float(duals.sortie_count.get(int(vehicle), 0.0))

    for cut_index, cut in enumerate(cuts):
        if getattr(cut, "kind", "") == "time_point_capacity":
            if int(getattr(cut, "vehicle", -1)) == int(vehicle):
                rc += min(0.0, -float(duals.cuts.get(int(cut_index), 0.0)))
            continue
        coeff = _sequence_cut_coefficient(cut, sequence, vehicle)
        if coeff != 0.0:
            rc -= float(duals.cuts.get(int(cut_index), 0.0)) * coeff

    # Occupation rows have coefficients in [0, 1] for each bucket. This bound is
    # intentionally loose but sign-safe for any transformed dual sign.
    for (r, _bucket), dual in duals.time_occupation.items():
        if int(r) != int(vehicle):
            continue
        rc += min(0.0, -float(dual))
    return round(rc, 9)


def _sequence_cut_coefficient(cut: FutureCut, sequence: tuple[int, ...], vehicle: int) -> float:
    kind = getattr(cut, "kind", "")
    if kind == "sortie_lower_bound":
        return -1.0
    if kind == "subset_row":
        tasks = set(getattr(cut, "tasks", tuple()))
        k = int(getattr(cut, "k", 2))
        return float(len(tasks.intersection(sequence)) // k)
    if kind in {"fleet_lower_bound", "fleet_upper_bound", "fleet_prefix_disable"}:
        return 0.0
    return 0.0
