"""BPC-facing resource-constrained shortest-path labeling core.

This module is a thin, exact-safe interface over the existing lunar journey
resource-label routines.  It makes the pricing boundary explicit for branch
price-and-cut:

* exact full-space mode can support a no-negative certificate only when every
  nonempty task subset is covered and true-dual RC audit is performed by the
  caller;
* relaxed/ng-route and direct selected-set modes are worker searches only and
  never certify no-negative.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from time import perf_counter
from typing import Iterable

from lunar_ice_bpc.domain.scenario import PATH_TYPES
from lunar_ice_bpc.exact.core.columns import TimedSortie, build_timed_sortie
from lunar_ice_bpc.exact.core.branching import (
    DIFFERENT_JOURNEY,
    SAME_JOURNEY,
    BranchContext,
    journey_satisfies_branch_context,
)
from lunar_ice_bpc.exact.core.cuts import CutContext
from lunar_ice_bpc.exact.core.data import LunarIceData
from lunar_ice_bpc.exact.core.journey import JourneyColumn, build_journey_column
from lunar_ice_bpc.exact.core.objective import sortie_objective_value
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals
from lunar_ice_bpc.exact.pricing.journey_pricing import (
    DirectPricingCache,
    price_direct_journey_columns,
    price_direct_journey_columns_incremental,
    price_exhaustive_direct_journey_columns,
    price_full_universe_incremental_journey_columns,
)


RESOURCE_LABEL_CORE_SCHEMA_VERSION = "lunar_ice_bpc.resource_label_core.v1"
CORE_EXACT_ELEMENTARY_FULL_SPACE = "exact_elementary_full_space"
CORE_RELAXED_NG_ROUTE_WORKER = "relaxed_ng_route_worker"
CORE_DIRECT_SELECTED_SET_WORKER = "direct_selected_set_worker"
CORE_MODES = (
    CORE_EXACT_ELEMENTARY_FULL_SPACE,
    CORE_RELAXED_NG_ROUTE_WORKER,
    CORE_DIRECT_SELECTED_SET_WORKER,
)


@dataclass(frozen=True)
class _ResourceExtensionLabel:
    sequence: tuple[str, ...]
    task_set: tuple[str, ...]
    current_task: str
    sortie: TimedSortie
    reduced_proxy: float
    proxy_profile: str


_RESOURCE_EXTENSION_PROXY_PROFILES = (
    "balanced",
    "time",
    "energy",
    "risk",
    "distance",
    "cost",
)

_RESOURCE_EXTENSION_MAX_PATH_VARIANTS_PER_SEQUENCE = 18


_RESOURCE_EXTENSION_STAT_KEYS = (
    "label_attempt_count",
    "label_feasible_count",
    "label_infeasible_count",
    "label_unique_task_set_count",
    "label_task_set_representative_replacement_count",
    "label_frontier_accepted_count",
    "label_dominance_rejected_count",
    "label_dominance_replaced_count",
    "label_capacity_truncated_count",
    "label_returned_seed_count",
    "label_end_bucket_count",
    "label_path_variant_candidate_count",
    "label_path_variant_duplicate_count",
    "label_path_variant_feasible_count",
    "label_path_variant_infeasible_count",
    "label_time_limit_hit_count",
)


def _empty_resource_extension_stats() -> dict[str, int]:
    return {key: 0 for key in _RESOURCE_EXTENSION_STAT_KEYS}


def _accumulate_resource_extension_stats(total: dict[str, int], row: dict[str, int]) -> None:
    for key in _RESOURCE_EXTENSION_STAT_KEYS:
        total[key] = int(total.get(key) or 0) + int(row.get(key) or 0)


@dataclass(frozen=True)
class ResourceLabelCoreConfig:
    mode: str = CORE_RELAXED_NG_ROUTE_WORKER
    max_task_count: int = 12
    max_candidate_sets: int | None = 160
    wall_time_limit_sec: float | None = None
    negative_eps: float = 1.0e-6
    stop_at_first_negative: bool = False
    negative_harvest_target: int = 1
    run_direct_portfolio: bool = False
    completion_bound_enabled: bool = True
    exact_negative_harvest_target: int = 1
    active_task_sets_for_exact_harvest: tuple[tuple[str, ...], ...] = tuple()
    ng_neighborhood_size: int = 8
    ng_neighborhood_sizes: tuple[int, ...] | None = None
    resource_extension_seed_enabled: bool = True
    resource_extension_max_labels_per_task: int = 4
    protected_support_continuation_seed_count: int = 8

    def __post_init__(self) -> None:
        mode = str(self.mode)
        if mode not in CORE_MODES:
            raise ValueError(f"unsupported resource label core mode {mode!r}")
        object.__setattr__(self, "mode", mode)
        object.__setattr__(self, "max_task_count", max(1, int(self.max_task_count)))
        if self.max_candidate_sets is not None:
            object.__setattr__(self, "max_candidate_sets", max(0, int(self.max_candidate_sets)))
        if self.wall_time_limit_sec is not None:
            object.__setattr__(self, "wall_time_limit_sec", max(0.0, float(self.wall_time_limit_sec)))
        object.__setattr__(self, "negative_eps", abs(float(self.negative_eps)))
        object.__setattr__(
            self,
            "exact_negative_harvest_target",
            max(1, int(self.exact_negative_harvest_target)),
        )
        object.__setattr__(
            self,
            "negative_harvest_target",
            max(1, int(self.negative_harvest_target)),
        )
        object.__setattr__(
            self,
            "active_task_sets_for_exact_harvest",
            tuple(
                tuple(sorted(str(task_id) for task_id in row))
                for row in (self.active_task_sets_for_exact_harvest or tuple())
            ),
        )
        ng_size = max(1, int(self.ng_neighborhood_size))
        object.__setattr__(self, "ng_neighborhood_size", ng_size)
        object.__setattr__(
            self,
            "ng_neighborhood_sizes",
            _normalize_neighborhood_sizes(self.ng_neighborhood_sizes, fallback=ng_size),
        )
        object.__setattr__(
            self,
            "resource_extension_max_labels_per_task",
            max(1, int(self.resource_extension_max_labels_per_task)),
        )
        object.__setattr__(
            self,
            "protected_support_continuation_seed_count",
            max(0, int(self.protected_support_continuation_seed_count)),
        )

    @property
    def exact_full_space(self) -> bool:
        return self.mode == CORE_EXACT_ELEMENTARY_FULL_SPACE

    @property
    def worker_mode(self) -> bool:
        return self.mode in {CORE_RELAXED_NG_ROUTE_WORKER, CORE_DIRECT_SELECTED_SET_WORKER}


def run_resource_label_core(
    data: LunarIceData,
    duals: JourneyDuals,
    *,
    config: ResourceLabelCoreConfig,
    seed_task_sets: Iterable[Iterable[str]] = tuple(),
    seed_source_rows: Iterable[dict] = tuple(),
    branch_context: BranchContext | None = None,
    cut_context: CutContext | None = None,
    cache: DirectPricingCache | None = None,
) -> tuple[dict, tuple[JourneyColumn, ...]]:
    """Run resource-label pricing and return a certificate-aware payload."""

    started_at = perf_counter()
    deadline = (
        None
        if config.wall_time_limit_sec is None
        else started_at + max(0.0, float(config.wall_time_limit_sec))
    )
    branch = branch_context or BranchContext()
    cuts = cut_context or CutContext()
    seeds = tuple(tuple(str(task_id) for task_id in row) for row in seed_task_sets)
    extra_seed_source_rows = tuple(seed_source_rows or tuple())
    if config.mode == CORE_EXACT_ELEMENTARY_FULL_SPACE:
        if cuts.empty:
            payload, columns = price_full_universe_incremental_journey_columns(
                data,
                duals,
                negative_eps=config.negative_eps,
                max_direct_tasks=config.max_task_count,
                max_returned_columns=config.exact_negative_harvest_target,
                active_task_sets_for_harvest=config.active_task_sets_for_exact_harvest,
                completion_bound_enabled=bool(config.completion_bound_enabled),
                wall_time_limit_sec=config.wall_time_limit_sec,
                branch_context=branch,
                cut_context=cuts,
                stop_at_first_negative=bool(config.stop_at_first_negative),
            )
            payload["exact_pricing_engine_preference"] = "full_universe_incremental_label"
        else:
            payload, columns = price_exhaustive_direct_journey_columns(
                data,
                duals,
                negative_eps=config.negative_eps,
                max_direct_tasks=config.max_task_count,
                cache=cache,
                completion_bound_enabled=bool(config.completion_bound_enabled),
                wall_time_limit_sec=config.wall_time_limit_sec,
                branch_context=branch,
                cut_context=cuts,
            )
            payload["exact_pricing_engine_preference"] = "exhaustive_subset_pricing"
        payload = _core_payload(
            data,
            payload,
            mode=config.mode,
            search_space_complete=bool(payload.get("pricing_complete_for_all_task_subsets")),
            worker_only=False,
            branch_context=branch,
            cut_context=cuts,
        )
        return payload, tuple(columns)

    if config.mode == CORE_RELAXED_NG_ROUTE_WORKER:
        generated_by_size: dict[str, int] = {}
        resource_generated_by_size: dict[str, int] = {}
        generated_rows: list[tuple[str, ...]] = []
        resource_generated_rows: list[tuple[str, ...]] = []
        resource_label_columns: tuple[JourneyColumn, ...] = tuple()
        resource_extension_stats = _empty_resource_extension_stats()
        for ng_size in config.ng_neighborhood_sizes or (config.ng_neighborhood_size,):
            stage_seed_sets = _ng_route_seed_task_sets(
                data,
                duals,
                ng_neighborhood_size=int(ng_size),
                max_task_count=config.max_task_count,
                max_candidate_sets=None,
            )
            generated_by_size[str(int(ng_size))] = len(stage_seed_sets)
            generated_rows.extend(stage_seed_sets)
            if config.resource_extension_seed_enabled:
                resource_labels, resource_stats = _resource_extension_ng_labels_with_stats(
                    data,
                    duals,
                    ng_neighborhood_size=int(ng_size),
                    max_task_count=config.max_task_count,
                    max_candidate_sets=config.max_candidate_sets,
                    max_labels_per_task=config.resource_extension_max_labels_per_task,
                    deadline=deadline,
                )
                resource_seed_sets = tuple(label.task_set for label in resource_labels)
                resource_generated_by_size[str(int(ng_size))] = len(resource_seed_sets)
                resource_generated_rows.extend(resource_seed_sets)
                resource_label_columns = _dedupe_columns(
                    (
                        *resource_label_columns,
                        *(
                            column
                            for column in _resource_extension_label_columns(data, resource_labels)
                            if journey_satisfies_branch_context(column, branch)
                        ),
                    )
                )
                _accumulate_resource_extension_stats(resource_extension_stats, resource_stats)
            if _deadline_expired(deadline):
                resource_extension_stats["label_time_limit_hit_count"] += 1
                break
        raw_generated_seed_sets = _dedupe_task_sets(generated_rows)
        raw_resource_generated_seed_sets = _dedupe_task_sets(resource_generated_rows)
        branch_feasible_seeds = _branch_feasible_task_sets(seeds, branch)
        generated_seed_sets = _branch_feasible_task_sets(raw_generated_seed_sets, branch)
        resource_generated_seed_sets = _branch_feasible_task_sets(raw_resource_generated_seed_sets, branch)
        merged_generated_seed_sets = _dedupe_task_sets((*resource_generated_seed_sets, *generated_seed_sets))
        merged_seeds = _dedupe_task_sets((*branch_feasible_seeds, *merged_generated_seed_sets))
        protected_refinement_seed_sets = _protected_extra_seed_task_sets(
            extra_seed_source_rows,
            branch_feasible_seeds,
            source_prefix="hidden_negative_refinement",
        )
        protected_support_continuation_seed_sets = _protected_extra_seed_task_sets(
            extra_seed_source_rows,
            branch_feasible_seeds,
            source_prefix="support_continuation",
            limit=config.protected_support_continuation_seed_count,
        )
        active_seed_sets = _bounded_portfolio_seed_sets(
            input_seed_sets=branch_feasible_seeds,
            resource_extension_seed_sets=resource_generated_seed_sets,
            ng_seed_sets=generated_seed_sets,
            protected_seed_sets=(
                *protected_refinement_seed_sets,
                *protected_support_continuation_seed_sets,
            ),
            max_candidate_sets=config.max_candidate_sets,
        )
        active_seed_source_rows = _seed_source_rows(
            active_seed_sets,
            input_seed_sets=branch_feasible_seeds,
            resource_extension_seed_sets=resource_generated_seed_sets,
            ng_seed_sets=generated_seed_sets,
            extra_seed_source_rows=extra_seed_source_rows,
        )
        payload, columns = price_direct_journey_columns_incremental(
            data,
            duals,
            negative_eps=config.negative_eps,
            max_direct_tasks=config.max_task_count,
            seed_task_sets=active_seed_sets,
            max_candidate_sets=config.max_candidate_sets,
            wall_time_limit_sec=_remaining_wall_time(deadline),
            stop_at_first_negative=bool(config.stop_at_first_negative),
            negative_harvest_target=config.negative_harvest_target,
            branch_context=branch,
            cut_context=cuts,
        )
        columns = _dedupe_columns((*resource_label_columns, *columns))
        direct_negative_count = int(payload.get("negative_column_count") or 0)
        skip_direct_portfolio = bool(
            config.stop_at_first_negative
            and direct_negative_count >= int(config.negative_harvest_target)
        )
        if config.run_direct_portfolio and not skip_direct_portfolio:
            direct_payload, direct_columns = price_direct_journey_columns(
                data,
                duals,
                negative_eps=config.negative_eps,
                max_direct_tasks=config.max_task_count,
                allow_partial=True,
                seed_task_sets=active_seed_sets,
                max_candidate_sets=config.max_candidate_sets,
                completion_bound_enabled=False,
                wall_time_limit_sec=_remaining_wall_time(deadline),
                branch_context=branch,
                cut_context=cuts,
            )
            columns = _dedupe_columns((*columns, *direct_columns))
            payload = _merge_worker_payload(payload, direct_payload)
            payload["direct_seed_portfolio_column_count"] = len(direct_columns)
        elif skip_direct_portfolio:
            payload["direct_seed_portfolio_skipped_by_negative_harvest_target"] = True
            payload["direct_seed_portfolio_skip_reason"] = "negative_harvest_target_reached"
        payload = _core_payload(
            data,
            payload,
            mode=config.mode,
            search_space_complete=False,
            worker_only=True,
            branch_context=branch,
            cut_context=cuts,
        )
        resource_label_column_task_sets = _dedupe_task_sets(
            tuple(column.task_set for column in resource_label_columns)
        )
        priced_candidate_sets = _payload_task_sets(
            (*_payload_task_sets(payload.get("candidate_sets") or ()), *resource_label_column_task_sets)
        )
        direct_candidate_sets = _direct_only_candidate_sets(
            priced_candidate_sets,
            known_seed_sets=(*branch_feasible_seeds, *resource_generated_seed_sets, *generated_seed_sets),
        )
        candidate_seed_source_rows = _seed_source_rows(
            priced_candidate_sets,
            input_seed_sets=branch_feasible_seeds,
            resource_extension_seed_sets=resource_generated_seed_sets,
            ng_seed_sets=generated_seed_sets,
            direct_candidate_seed_sets=direct_candidate_sets,
            extra_seed_source_rows=extra_seed_source_rows,
        )
        payload["direct_seed_portfolio_enabled"] = bool(config.run_direct_portfolio)
        payload["negative_harvest_target"] = int(config.negative_harvest_target)
        payload["negative_harvest_early_stop_enabled"] = bool(config.stop_at_first_negative)
        payload["pricing_engine_role"] = "worker_candidate_search"
        payload["candidate_search_only"] = True
        payload["relaxed_candidate_search_can_certify_no_negative"] = False
        payload["no_column_certificate_allowed"] = False
        payload["ng_route_relaxation_kind"] = "seed_portfolio_task_set_neighborhood"
        payload["ng_route_relaxation_is_certificate_relaxation"] = False
        payload["relaxed_route_elementarity_proof_supported"] = False
        payload["dssr_refinement_status"] = "hidden_negative_seed_refinement_only"
        payload["exact_final_proof_required_after_worker"] = True
        payload["exact_final_proof_expected_mode"] = "exact_elementary_full_space"
        payload["ng_seed_task_set_count"] = len(generated_seed_sets)
        payload["raw_ng_seed_task_set_count"] = len(raw_generated_seed_sets)
        payload["resource_extension_seed_enabled"] = bool(config.resource_extension_seed_enabled)
        payload["resource_extension_seed_task_set_count"] = len(resource_generated_seed_sets)
        payload["raw_resource_extension_seed_task_set_count"] = len(raw_resource_generated_seed_sets)
        payload["resource_extension_label_stats"] = resource_extension_stats
        payload.update(
            {
                f"resource_extension_{key}": value
                for key, value in resource_extension_stats.items()
                if isinstance(value, int)
            }
        )
        payload["resource_extension_proxy_profiles"] = list(_RESOURCE_EXTENSION_PROXY_PROFILES)
        payload["resource_extension_proxy_profile_count"] = len(_RESOURCE_EXTENSION_PROXY_PROFILES)
        payload["resource_extension_time_limit_hit"] = bool(
            resource_extension_stats.get("label_time_limit_hit_count")
        )
        if payload["resource_extension_time_limit_hit"]:
            payload["pricing_timeout"] = True
            if not str(payload.get("timeout_stage") or ""):
                payload["timeout_stage"] = "resource_extension_seed_generation"
        payload["resource_extension_seed_task_set_count_by_size"] = resource_generated_by_size
        payload["resource_extension_label_column_worker_enabled"] = bool(
            config.resource_extension_seed_enabled
        )
        payload["resource_extension_label_column_count"] = len(resource_label_columns)
        payload["resource_extension_label_column_task_set_count"] = len(resource_label_column_task_sets)
        payload["resource_extension_label_column_task_sets"] = _task_sets_payload(
            resource_label_column_task_sets
        )
        payload["resource_extension_label_column_policy"] = (
            "feasible_resource_extension_physical_representatives_worker_only"
        )
        payload["resource_extension_label_columns_can_certify_no_negative"] = False
        payload["active_resource_extension_seed_task_set_count"] = _count_intersection(
            active_seed_sets,
            resource_generated_seed_sets,
        )
        payload["seed_task_set_count"] = len(branch_feasible_seeds)
        payload["raw_input_seed_task_set_count"] = len(_dedupe_task_sets(seeds))
        payload["merged_seed_task_set_count"] = len(merged_seeds)
        payload["branch_seed_filter_enabled"] = not branch.empty
        payload["branch_seed_filtered_input_count"] = max(0, len(_dedupe_task_sets(seeds)) - len(branch_feasible_seeds))
        payload["branch_seed_filtered_ng_count"] = max(0, len(raw_generated_seed_sets) - len(generated_seed_sets))
        payload["branch_seed_filtered_resource_extension_count"] = max(
            0,
            len(raw_resource_generated_seed_sets) - len(resource_generated_seed_sets),
        )
        payload["active_seed_task_set_count"] = len(active_seed_sets)
        payload["active_seed_task_set_sources"] = active_seed_source_rows
        payload["active_seed_task_set_source_counts"] = _seed_source_counts(active_seed_source_rows)
        payload["active_seed_task_set_source_task_count_counts"] = _seed_source_task_count_counts(
            active_seed_source_rows
        )
        payload["active_seed_selection_policy"] = (
            "protected_refinement_then_source_task_count_coverage_then_low_overlap_fill"
        )
        payload["protected_refinement_seed_task_set_count"] = len(protected_refinement_seed_sets)
        payload["active_protected_refinement_seed_task_set_count"] = _count_intersection(
            active_seed_sets,
            protected_refinement_seed_sets,
        )
        payload["protected_support_continuation_seed_budget"] = int(
            config.protected_support_continuation_seed_count
        )
        payload["protected_support_continuation_seed_task_set_count"] = len(
            protected_support_continuation_seed_sets
        )
        payload["active_protected_support_continuation_seed_task_set_count"] = _count_intersection(
            active_seed_sets,
            protected_support_continuation_seed_sets,
        )
        payload["protected_refinement_seed_task_set_count_by_size"] = _task_set_count_by_size(
            protected_refinement_seed_sets
        )
        payload["protected_support_continuation_seed_task_set_count_by_size"] = _task_set_count_by_size(
            protected_support_continuation_seed_sets
        )
        payload["protected_refinement_seed_budget_truncated_count"] = max(
            0,
            len(protected_refinement_seed_sets)
            - int(payload["active_protected_refinement_seed_task_set_count"]),
        )
        payload["protected_support_continuation_seed_budget_truncated_count"] = max(
            0,
            _count_extra_seed_source_prefix(
                extra_seed_source_rows,
                branch_feasible_seeds,
                source_prefix="support_continuation",
            )
            - len(protected_support_continuation_seed_sets),
        )
        payload["active_seed_task_set_count_by_size"] = _task_set_count_by_size(active_seed_sets)
        payload["priced_candidate_task_set_sources"] = candidate_seed_source_rows
        payload["priced_candidate_task_set_source_counts"] = _seed_source_counts(candidate_seed_source_rows)
        payload["priced_candidate_task_set_source_task_count_counts"] = _seed_source_task_count_counts(
            candidate_seed_source_rows
        )
        payload["direct_candidate_task_set_count"] = len(direct_candidate_sets)
        payload["candidate_seed_source_precedence"] = [
            "hidden_negative_refinement",
            "hidden_negative_refinement_expansion",
            "input_seed",
            "resource_extension",
            "ng_route",
            "direct_candidate",
        ]
        payload["active_ng_seed_task_set_count"] = _count_intersection(active_seed_sets, generated_seed_sets)
        payload["active_input_seed_task_set_count"] = _count_intersection(active_seed_sets, seeds)
        payload["generated_task_sets"] = _task_sets_payload(generated_seed_sets)
        payload["input_seed_task_sets"] = _task_sets_payload(branch_feasible_seeds)
        payload["merged_seed_task_sets"] = _task_sets_payload(merged_seeds)
        payload["active_seed_task_sets"] = _task_sets_payload(active_seed_sets)
        worker_column_task_sets = _column_task_sets_payload(columns)
        payload["worker_candidate_universe_task_sets"] = _task_sets_payload(active_seed_sets)
        payload["worker_seen_task_sets"] = worker_column_task_sets
        payload["worker_generated_column_task_sets"] = worker_column_task_sets
        payload["worker_generated_column_task_set_count"] = len(worker_column_task_sets)
        payload["ng_neighborhood_size"] = int(config.ng_neighborhood_size)
        payload["ng_neighborhood_sizes"] = [int(size) for size in config.ng_neighborhood_sizes or ()]
        payload["ng_neighborhood_stage_count"] = len(config.ng_neighborhood_sizes or ())
        payload["ng_seed_task_set_count_by_size"] = generated_by_size
        return payload, tuple(columns)

    branch_feasible_seeds = _branch_feasible_task_sets(seeds, branch)
    payload, columns = price_direct_journey_columns(
        data,
        duals,
        negative_eps=config.negative_eps,
        max_direct_tasks=config.max_task_count,
        allow_partial=True,
        seed_task_sets=branch_feasible_seeds,
        cache=cache,
        max_candidate_sets=config.max_candidate_sets,
        completion_bound_enabled=False,
        branch_context=branch,
        cut_context=cuts,
    )
    payload = _core_payload(
        data,
        payload,
        mode=config.mode,
        search_space_complete=False,
        worker_only=True,
        branch_context=branch,
        cut_context=cuts,
    )
    priced_candidate_sets = _payload_task_sets(payload.get("candidate_sets") or ())
    direct_candidate_sets = _direct_only_candidate_sets(
        priced_candidate_sets,
        known_seed_sets=branch_feasible_seeds,
    )
    payload["generated_task_sets"] = _task_sets_payload(branch_feasible_seeds)
    payload["input_seed_task_sets"] = _task_sets_payload(branch_feasible_seeds)
    payload["merged_seed_task_sets"] = _task_sets_payload(branch_feasible_seeds)
    payload["active_seed_task_sets"] = _task_sets_payload(branch_feasible_seeds)
    active_seed_source_rows = _seed_source_rows(
        branch_feasible_seeds,
        input_seed_sets=branch_feasible_seeds,
        resource_extension_seed_sets=tuple(),
        ng_seed_sets=tuple(),
        direct_candidate_seed_sets=tuple(),
        extra_seed_source_rows=extra_seed_source_rows,
    )
    candidate_seed_source_rows = _seed_source_rows(
        priced_candidate_sets,
        input_seed_sets=branch_feasible_seeds,
        resource_extension_seed_sets=tuple(),
        ng_seed_sets=tuple(),
        direct_candidate_seed_sets=direct_candidate_sets,
        extra_seed_source_rows=extra_seed_source_rows,
    )
    payload["active_seed_task_set_sources"] = active_seed_source_rows
    payload["active_seed_task_set_source_counts"] = _seed_source_counts(active_seed_source_rows)
    payload["active_seed_task_set_source_task_count_counts"] = _seed_source_task_count_counts(
        active_seed_source_rows
    )
    payload["priced_candidate_task_set_sources"] = candidate_seed_source_rows
    payload["priced_candidate_task_set_source_counts"] = _seed_source_counts(candidate_seed_source_rows)
    payload["priced_candidate_task_set_source_task_count_counts"] = _seed_source_task_count_counts(
        candidate_seed_source_rows
    )
    payload["direct_candidate_task_set_count"] = len(direct_candidate_sets)
    payload["candidate_seed_source_precedence"] = ["input_seed", "direct_candidate"]
    payload["branch_seed_filter_enabled"] = not branch.empty
    payload["branch_seed_filtered_input_count"] = max(0, len(_dedupe_task_sets(seeds)) - len(branch_feasible_seeds))
    worker_column_task_sets = _column_task_sets_payload(columns)
    payload["worker_candidate_universe_task_sets"] = _task_sets_payload(branch_feasible_seeds)
    payload["worker_seen_task_sets"] = worker_column_task_sets
    payload["worker_generated_column_task_sets"] = worker_column_task_sets
    payload["worker_generated_column_task_set_count"] = len(worker_column_task_sets)
    return payload, tuple(columns)


def _core_payload(
    data: LunarIceData,
    payload: dict,
    *,
    mode: str,
    search_space_complete: bool,
    worker_only: bool,
    branch_context: BranchContext,
    cut_context: CutContext,
) -> dict:
    result = dict(payload)
    result.update(
        {
            "schema_version": RESOURCE_LABEL_CORE_SCHEMA_VERSION,
            "resource_label_core_mode": str(mode),
            "resource_label_algorithm": _algorithm_name(mode),
            "pricing_engine_role": (
                "worker_candidate_search" if worker_only else "exact_full_space_oracle"
            ),
            "candidate_search_only": bool(worker_only),
            "no_column_certificate_allowed": False,
            "exact_final_proof_required_after_worker": bool(worker_only),
            "exact_final_proof_expected_mode": (
                "exact_elementary_full_space" if worker_only else ""
            ),
            "relaxed_candidate_search_can_certify_no_negative": False,
            "pricing_subproblem_kind": "resource_constrained_shortest_path_with_time_energy_risk_capacity",
            "resource_dimensions": [
                "time_window",
                "horizon",
                "energy",
                "capacity",
                "shadow_exposure",
                "risk",
                "weighted_completion",
            ],
            "dominance_policy": (
                "same_mask_end_time_and_reduced_base"
                if mode != CORE_EXACT_ELEMENTARY_FULL_SPACE
                else "same_mask_end_time_and_reduced_base_full_subset_space"
            ),
            "elementarity_policy": (
                "elementary_full_space"
                if mode == CORE_EXACT_ELEMENTARY_FULL_SPACE
                else "selected_elementary_candidate_sets_ng_route_worker"
            ),
            "ng_route_relaxation_enabled": mode == CORE_RELAXED_NG_ROUTE_WORKER,
            "ng_route_relaxation_kind": (
                "seed_portfolio_task_set_neighborhood"
                if mode == CORE_RELAXED_NG_ROUTE_WORKER
                else "none"
            ),
            "ng_route_relaxation_is_certificate_relaxation": False,
            "relaxed_route_elementarity_proof_supported": False,
            "dssr_refinement_status": (
                "hidden_negative_seed_refinement_only"
                if mode == CORE_RELAXED_NG_ROUTE_WORKER
                else "not_applicable"
            ),
            "worker_only": bool(worker_only),
            "search_space_complete": bool(search_space_complete),
            "certificate_eligible_after_true_dual_audit": bool(search_space_complete) and not bool(worker_only),
            "can_certify_no_negative": False,
            "uses_true_dual_bpc_certificate": False,
            "branch_context_active": not branch_context.empty,
            "branch_decision_count": len(branch_context.pair_decisions),
            "cut_context_active": not cut_context.empty,
            "cut_count": len(cut_context.cuts),
            "task_count": len(data.task_ids),
            "max_tasks_per_trip": int(data.max_tasks_per_trip),
            "certificate_boundary": (
                "search space is complete, but this core layer is not a certificate; "
                "caller must run true-dual RC audit before claiming no-negative"
                if not worker_only and search_space_complete
                else "worker/selected-set pricing only; no-column cannot certify"
            ),
        }
    )
    return result


def _algorithm_name(mode: str) -> str:
    if mode == CORE_EXACT_ELEMENTARY_FULL_SPACE:
        return "elementary_resource_labeling_exhaustive_task_subsets"
    if mode == CORE_RELAXED_NG_ROUTE_WORKER:
        return "ng_route_relaxed_resource_labeling"
    return "direct_selected_set_resource_labeling"


def _normalize_neighborhood_sizes(
    sizes: tuple[int, ...] | None,
    *,
    fallback: int,
) -> tuple[int, ...]:
    raw_sizes = (fallback,) if sizes is None else tuple(sizes)
    normalized: list[int] = []
    seen: set[int] = set()
    for value in raw_sizes:
        size = max(1, int(value))
        if size in seen:
            continue
        seen.add(size)
        normalized.append(size)
    if not normalized:
        normalized.append(max(1, int(fallback)))
    return tuple(normalized)


def _merge_worker_payload(left: dict, right: dict) -> dict:
    merged = dict(left)
    merged_candidate_sets = _dedupe_task_sets(
        (*_payload_task_sets(left.get("candidate_sets") or ()), *_payload_task_sets(right.get("candidate_sets") or ()))
    )
    merged.update(
        {
            "direct_seed_portfolio_status": right.get("status") or "",
            "direct_seed_portfolio_column_count": int(right.get("generated_journey_count") or 0),
            "direct_seed_portfolio_negative_column_count": int(right.get("negative_column_count") or 0),
            "direct_seed_portfolio_best_reduced_cost": right.get("best_reduced_cost"),
            "candidate_sets": [list(row) for row in merged_candidate_sets],
            "candidate_round_count": int(left.get("candidate_round_count") or 0)
            + int(right.get("candidate_round_count") or 0),
            "sortie_attempt_count": int(left.get("sortie_attempt_count") or 0)
            + int(right.get("sortie_attempt_count") or 0),
            "feasible_sortie_template_count": int(left.get("feasible_sortie_template_count") or 0)
            + int(right.get("feasible_sortie_template_count") or 0),
            "pareto_label_count": int(left.get("pareto_label_count") or 0)
            + int(right.get("pareto_label_count") or 0),
        }
    )
    return merged


def _dedupe_columns(columns: Iterable[JourneyColumn]) -> tuple[JourneyColumn, ...]:
    unique: list[JourneyColumn] = []
    seen = set()
    for column in columns:
        key = (
            tuple(sorted(str(task_id) for task_id in column.task_set)),
            tuple(
                (
                    tuple(sortie.tasks),
                    tuple((leg.source, leg.target, leg.path_type) for leg in sortie.legs),
                    float(sortie.start_time),
                )
                for sortie in column.sorties
            ),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(column)
    return tuple(unique)


def _bounded_interleaved_seed_sets(
    input_seed_sets: Iterable[Iterable[str]],
    ng_seed_sets: Iterable[Iterable[str]],
    *,
    max_candidate_sets: int | None,
) -> tuple[tuple[str, ...], ...]:
    input_rows = list(_dedupe_task_sets(input_seed_sets))
    ng_rows = list(_dedupe_task_sets(ng_seed_sets))
    limit = None if max_candidate_sets is None else max(0, int(max_candidate_sets))
    if limit == 0:
        return tuple()
    result: list[tuple[str, ...]] = []
    seen: set[tuple[str, ...]] = set()
    index = 0
    while index < max(len(input_rows), len(ng_rows)):
        for source in (input_rows, ng_rows):
            if index >= len(source):
                continue
            row = source[index]
            if row in seen:
                continue
            seen.add(row)
            result.append(row)
            if limit is not None and len(result) >= limit:
                return tuple(result)
        index += 1
    return tuple(result)


def _bounded_portfolio_seed_sets(
    *,
    input_seed_sets: Iterable[Iterable[str]],
    resource_extension_seed_sets: Iterable[Iterable[str]],
    ng_seed_sets: Iterable[Iterable[str]],
    protected_seed_sets: Iterable[Iterable[str]] = tuple(),
    max_candidate_sets: int | None,
) -> tuple[tuple[str, ...], ...]:
    """Select worker seed sets with source and task-count coverage.

    The relaxed worker is not a certificate routine, but its candidate budget is
    often the difference between finding a true negative column quickly and
    handing all work to the final judge.  A plain input/generated interleave can
    spend a tight budget before resource-extension or larger task-count seeds
    are tried.  This deterministic portfolio gives each source and task-count
    band an early chance, then fills the remainder with low-overlap task sets.
    This is worker-only diversification: it changes which candidates are tried
    first, not the exact proof boundary.
    """

    source_rows = (
        ("input_seed", list(_dedupe_task_sets(input_seed_sets))),
        ("resource_extension", list(_dedupe_task_sets(resource_extension_seed_sets))),
        ("ng_route", list(_dedupe_task_sets(ng_seed_sets))),
    )
    protected_rows = list(_dedupe_task_sets(protected_seed_sets))
    limit = None if max_candidate_sets is None else max(0, int(max_candidate_sets))
    if limit == 0:
        return tuple()
    if limit is None:
        return _dedupe_task_sets(
            (*protected_rows, *(row for _source, rows in source_rows for row in rows))
        )

    result: list[tuple[str, ...]] = []
    seen: set[tuple[str, ...]] = set()

    def add(row: tuple[str, ...]) -> bool:
        if row in seen or len(result) >= limit:
            return False
        seen.add(row)
        result.append(row)
        return True

    for row in protected_rows:
        add(row)
        if len(result) >= limit:
            return tuple(result)

    task_counts = sorted({len(row) for _source, rows in source_rows for row in rows})
    for task_count in task_counts:
        for _source, rows in source_rows:
            for row in rows:
                if len(row) == task_count and add(row):
                    break
        if len(result) >= limit:
            return tuple(result)

    while len(result) < limit:
        candidates: list[tuple[float, int, int, int, tuple[str, ...]]] = []
        candidate_seen: set[tuple[str, ...]] = set()
        for source_rank, (_source, rows) in enumerate(source_rows):
            for source_index, row in enumerate(rows):
                if row in seen or row in candidate_seen:
                    continue
                candidate_seen.add(row)
                candidates.append(
                    (
                        _seed_task_set_overlap_score(row, result),
                        len(row),
                        source_rank,
                        source_index,
                        row,
                    )
                )
        if not candidates:
            break
        _overlap, _length, _source_rank, _source_index, selected = min(candidates)
        add(selected)
    return tuple(result)


def _seed_task_set_overlap_score(
    task_set: tuple[str, ...],
    selected_task_sets: Iterable[tuple[str, ...]],
) -> float:
    selected_rows = tuple(selected_task_sets)
    if not selected_rows:
        return 0.0
    candidate = set(task_set)
    if not candidate:
        return 0.0
    return max(
        (
            len(candidate & set(row)) / len(candidate | set(row))
            for row in selected_rows
            if candidate | set(row)
        ),
        default=0.0,
    )


def _count_intersection(left: Iterable[Iterable[str]], right: Iterable[Iterable[str]]) -> int:
    right_set = set(_dedupe_task_sets(right))
    count = 0
    for row in _dedupe_task_sets(left):
        if row in right_set:
            count += 1
    return count


def _seed_source_rows(
    active_seed_sets: Iterable[Iterable[str]],
    *,
    input_seed_sets: Iterable[Iterable[str]],
    resource_extension_seed_sets: Iterable[Iterable[str]],
    ng_seed_sets: Iterable[Iterable[str]],
    direct_candidate_seed_sets: Iterable[Iterable[str]] = tuple(),
    extra_seed_source_rows: Iterable[dict] = tuple(),
) -> list[dict]:
    input_lookup = set(_dedupe_task_sets(input_seed_sets))
    resource_lookup = set(_dedupe_task_sets(resource_extension_seed_sets))
    ng_lookup = set(_dedupe_task_sets(ng_seed_sets))
    direct_lookup = set(_dedupe_task_sets(direct_candidate_seed_sets))
    extra_lookup = _extra_seed_source_lookup(extra_seed_source_rows)
    rows: list[dict] = []
    for task_set in _dedupe_task_sets(active_seed_sets):
        sources: list[str] = []
        if task_set in input_lookup:
            sources.append("input_seed")
        if task_set in resource_lookup:
            sources.append("resource_extension")
        if task_set in ng_lookup:
            sources.append("ng_route")
        if task_set in direct_lookup:
            sources.append("direct_candidate")
        for source in extra_lookup.get(task_set, tuple()):
            if source not in sources:
                sources.append(source)
        rows.append(
            {
                "task_set": list(task_set),
                "sources": sources or ["unknown"],
            }
        )
    return rows


def _protected_extra_seed_task_sets(
    source_rows: Iterable[dict],
    candidate_seed_sets: Iterable[Iterable[str]],
    *,
    source_prefix: str,
    limit: int | None = None,
) -> tuple[tuple[str, ...], ...]:
    candidate_lookup = set(_dedupe_task_sets(candidate_seed_sets))
    extra_lookup = _extra_seed_source_lookup(source_rows)
    protected: list[tuple[str, ...]] = []
    prefix = str(source_prefix)
    cap = None if limit is None else max(0, int(limit))
    for task_set, sources in extra_lookup.items():
        if cap is not None and len(protected) >= cap:
            break
        if task_set not in candidate_lookup:
            continue
        if any(str(source).startswith(prefix) for source in sources):
            protected.append(task_set)
    return _dedupe_task_sets(protected)


def _count_extra_seed_source_prefix(
    source_rows: Iterable[dict],
    candidate_seed_sets: Iterable[Iterable[str]],
    *,
    source_prefix: str,
) -> int:
    candidate_lookup = set(_dedupe_task_sets(candidate_seed_sets))
    extra_lookup = _extra_seed_source_lookup(source_rows)
    prefix = str(source_prefix)
    return sum(
        1
        for task_set, sources in extra_lookup.items()
        if task_set in candidate_lookup and any(str(source).startswith(prefix) for source in sources)
    )


def _extra_seed_source_lookup(source_rows: Iterable[dict]) -> dict[tuple[str, ...], tuple[str, ...]]:
    lookup: dict[tuple[str, ...], list[str]] = {}
    for raw_row in source_rows or tuple():
        if not isinstance(raw_row, dict):
            continue
        task_set = _normalize_seed_source_task_set(raw_row.get("task_set") or ())
        if not task_set:
            continue
        bucket = lookup.setdefault(task_set, [])
        for raw_source in raw_row.get("sources") or tuple():
            source = str(raw_source)
            if source and source not in bucket:
                bucket.append(source)
    return {task_set: tuple(sources) for task_set, sources in lookup.items()}


def _normalize_seed_source_task_set(raw: Iterable[object]) -> tuple[str, ...]:
    try:
        return tuple(sorted({str(task_id) for task_id in raw if str(task_id)}))
    except TypeError:
        return tuple()


def _seed_source_counts(source_rows: Iterable[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in source_rows:
        for source in row.get("sources") or ("unknown",):
            source_key = str(source)
            counts[source_key] = counts.get(source_key, 0) + 1
    return dict(sorted(counts.items()))


def _seed_source_task_count_counts(source_rows: Iterable[dict]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for row in source_rows:
        task_count = str(len(row.get("task_set") or ()))
        for source in row.get("sources") or ("unknown",):
            source_key = str(source)
            source_counts = counts.setdefault(source_key, {})
            source_counts[task_count] = source_counts.get(task_count, 0) + 1
    return {source: dict(sorted(size_counts.items())) for source, size_counts in sorted(counts.items())}


def _payload_task_sets(rows: Iterable[Iterable[str]]) -> tuple[tuple[str, ...], ...]:
    return _dedupe_task_sets(rows)


def _branch_feasible_task_sets(
    rows: Iterable[Iterable[str]],
    branch_context: BranchContext,
) -> tuple[tuple[str, ...], ...]:
    if branch_context.empty:
        return _dedupe_task_sets(rows)
    return tuple(
        row
        for row in _dedupe_task_sets(rows)
        if _candidate_universe_has_branch_feasible_subset(row, branch_context)
    )


def _candidate_universe_has_branch_feasible_subset(
    candidate_universe: Iterable[str],
    branch_context: BranchContext,
) -> bool:
    if branch_context.empty:
        return True
    tasks = {str(task_id) for task_id in candidate_universe}
    same_components = _same_journey_components(branch_context)
    for task_id in sorted(tasks):
        closure = _same_journey_closure(task_id, same_components)
        if not closure.issubset(tasks):
            continue
        if _task_group_violates_different_decision(closure, branch_context):
            continue
        return True
    return False


def _same_journey_components(branch_context: BranchContext) -> list[set[str]]:
    components: list[set[str]] = []
    for decision in branch_context.pair_decisions:
        if decision.sense != SAME_JOURNEY:
            continue
        pair = {str(decision.task_a), str(decision.task_b)}
        merged = set(pair)
        remaining: list[set[str]] = []
        for component in components:
            if component & merged:
                merged.update(component)
            else:
                remaining.append(component)
        remaining.append(merged)
        components = remaining
    return components


def _same_journey_closure(task_id: str, components: list[set[str]]) -> set[str]:
    task = str(task_id)
    for component in components:
        if task in component:
            return set(component)
    return {task}


def _task_group_violates_different_decision(
    task_group: set[str],
    branch_context: BranchContext,
) -> bool:
    for decision in branch_context.pair_decisions:
        if decision.sense != DIFFERENT_JOURNEY:
            continue
        if str(decision.task_a) in task_group and str(decision.task_b) in task_group:
            return True
    return False


def _task_set_count_by_size(rows: Iterable[Iterable[str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in _dedupe_task_sets(rows):
        key = str(len(row))
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: int(item[0])))


def _direct_only_candidate_sets(
    candidate_sets: Iterable[Iterable[str]],
    *,
    known_seed_sets: Iterable[Iterable[str]],
) -> tuple[tuple[str, ...], ...]:
    known = set(_dedupe_task_sets(known_seed_sets))
    return tuple(row for row in _dedupe_task_sets(candidate_sets) if row not in known)


def _task_sets_payload(rows: Iterable[Iterable[str]]) -> list[list[str]]:
    return [list(row) for row in _dedupe_task_sets(rows)]


def _column_task_sets_payload(columns: Iterable[JourneyColumn]) -> list[list[str]]:
    return _task_sets_payload(tuple(column.task_set for column in columns))


def _ng_route_seed_task_sets(
    data: LunarIceData,
    duals: JourneyDuals,
    *,
    ng_neighborhood_size: int,
    max_task_count: int,
    max_candidate_sets: int | None,
) -> tuple[tuple[str, ...], ...]:
    task_ids = tuple(data.task_ids)
    if not task_ids:
        return tuple()
    limit = max(1, min(int(max_task_count), int(ng_neighborhood_size), len(task_ids)))
    seed_sets: list[tuple[str, ...]] = []
    for task_id in task_ids:
        nearest = sorted(
            (other for other in task_ids if other != task_id),
            key=lambda other: (_task_distance(data, task_id, other), other),
        )
        seed_sets.append(tuple(sorted((task_id, *nearest[: limit - 1]))))
    dual_ranked = sorted(
        task_ids,
        key=lambda task_id: (-float(duals.cover.get(task_id, 0.0)), task_id),
    )
    for size in range(1, limit + 1):
        seed_sets.append(tuple(sorted(dual_ranked[:size])))
    for start in range(0, len(dual_ranked), limit):
        row = tuple(sorted(dual_ranked[start : start + limit]))
        if row:
            seed_sets.append(row)
    for size in range(2, min(4, limit) + 1):
        for combo in combinations(dual_ranked[: min(len(dual_ranked), limit + 3)], size):
            seed_sets.append(tuple(sorted(combo)))
            if max_candidate_sets is not None and len(seed_sets) >= int(max_candidate_sets):
                return _dedupe_task_sets(seed_sets)[: int(max_candidate_sets)]
    deduped = _dedupe_task_sets(seed_sets)
    if max_candidate_sets is not None:
        deduped = deduped[: int(max_candidate_sets)]
    return deduped


def _resource_extension_ng_seed_task_sets(
    data: LunarIceData,
    duals: JourneyDuals,
    *,
    ng_neighborhood_size: int,
    max_task_count: int,
    max_candidate_sets: int | None,
    max_labels_per_task: int,
    deadline: float | None = None,
) -> tuple[tuple[str, ...], ...]:
    rows, _stats = _resource_extension_ng_seed_task_sets_with_stats(
        data,
        duals,
        ng_neighborhood_size=ng_neighborhood_size,
        max_task_count=max_task_count,
        max_candidate_sets=max_candidate_sets,
        max_labels_per_task=max_labels_per_task,
        deadline=deadline,
    )
    return rows


def _resource_extension_ng_seed_task_sets_with_stats(
    data: LunarIceData,
    duals: JourneyDuals,
    *,
    ng_neighborhood_size: int,
    max_task_count: int,
    max_candidate_sets: int | None,
    max_labels_per_task: int,
    deadline: float | None = None,
) -> tuple[tuple[tuple[str, ...], ...], dict[str, int]]:
    labels, stats = _resource_extension_ng_labels_with_stats(
        data,
        duals,
        ng_neighborhood_size=ng_neighborhood_size,
        max_task_count=max_task_count,
        max_candidate_sets=max_candidate_sets,
        max_labels_per_task=max_labels_per_task,
        deadline=deadline,
    )
    return tuple(label.task_set for label in labels), stats


def _resource_extension_ng_labels_with_stats(
    data: LunarIceData,
    duals: JourneyDuals,
    *,
    ng_neighborhood_size: int,
    max_task_count: int,
    max_candidate_sets: int | None,
    max_labels_per_task: int,
    deadline: float | None = None,
) -> tuple[tuple[_ResourceExtensionLabel, ...], dict[str, int]]:
    """Build worker-only task-set seeds by ng-route resource label expansion.

    This is deliberately a candidate generator, not a certificate routine.  It
    uses a fixed portfolio of resource-proxy path choices per leg to find
    promising feasible prefixes.  The caller may pass these physical
    representatives through true-dual RC audit as worker columns, but no
    resource-extension no-column result can certify the pricing space.
    """

    task_ids = tuple(sorted(data.task_ids))
    limit = max(1, min(int(max_task_count), int(data.max_tasks_per_trip), len(task_ids)))
    stats = _empty_resource_extension_stats()
    if not task_ids or limit <= 0:
        return tuple(), stats
    if _deadline_expired(deadline):
        stats["label_time_limit_hit_count"] += 1
        return tuple(), stats
    neighborhood = _resource_ng_neighborhoods(
        data,
        duals,
        ng_neighborhood_size=max(1, int(ng_neighborhood_size)),
    )
    ranked_tasks = sorted(
        task_ids,
        key=lambda task_id: (
            -float(duals.cover.get(task_id, 0.0)),
            -float(data.tasks[task_id].science_weight),
            task_id,
        ),
    )
    rows_by_task_set: dict[tuple[str, ...], _ResourceExtensionLabel] = {}
    labels_by_end: dict[str, list[_ResourceExtensionLabel]] = {}
    frontier: list[_ResourceExtensionLabel] = []

    def add_label(label: _ResourceExtensionLabel) -> None:
        stats["label_feasible_count"] += 1
        old = rows_by_task_set.get(label.task_set)
        if old is None or _resource_label_sort_key(label) < _resource_label_sort_key(old):
            rows_by_task_set[label.task_set] = label
            if old is None:
                stats["label_unique_task_set_count"] += 1
            else:
                stats["label_task_set_representative_replacement_count"] += 1
        bucket = labels_by_end.setdefault(label.current_task, [])
        accepted, reason, replaced_count, truncated_count = _add_resource_extension_label(
            bucket,
            label,
            max_labels_per_task=max_labels_per_task,
        )
        stats["label_dominance_replaced_count"] += replaced_count
        stats["label_capacity_truncated_count"] += truncated_count
        if accepted:
            stats["label_frontier_accepted_count"] += 1
            frontier.append(label)
        elif reason == "dominated_by_existing":
            stats["label_dominance_rejected_count"] += 1

    for task_id in ranked_tasks:
        if _deadline_expired(deadline):
            stats["label_time_limit_hit_count"] += 1
            break
        for proxy_profile in _RESOURCE_EXTENSION_PROXY_PROFILES:
            if _deadline_expired(deadline):
                stats["label_time_limit_hit_count"] += 1
                break
            stats["label_attempt_count"] += 1
            labels, variant_stats = _build_resource_extension_label_variants(
                data,
                duals,
                (task_id,),
                proxy_profile=proxy_profile,
            )
            _accumulate_resource_extension_stats(stats, variant_stats)
            if labels:
                for label in labels:
                    add_label(label)
            else:
                stats["label_infeasible_count"] += 1

    for _depth in range(1, limit):
        if _deadline_expired(deadline):
            stats["label_time_limit_hit_count"] += 1
            break
        current_frontier = tuple(frontier)
        frontier = []
        for label in current_frontier:
            if _deadline_expired(deadline):
                stats["label_time_limit_hit_count"] += 1
                break
            if len(label.sequence) >= limit:
                continue
            allowed_next = _resource_extension_next_tasks(
                data,
                task_ids,
                label,
                neighborhood=neighborhood,
                duals=duals,
            )
            for task_id in allowed_next:
                if _deadline_expired(deadline):
                    stats["label_time_limit_hit_count"] += 1
                    break
                if task_id in label.task_set:
                    continue
                stats["label_attempt_count"] += 1
                next_labels, variant_stats = _build_resource_extension_label_variants(
                    data,
                    duals,
                    (*label.sequence, task_id),
                    proxy_profile=label.proxy_profile,
                )
                _accumulate_resource_extension_stats(stats, variant_stats)
                if next_labels:
                    for next_label in next_labels:
                        add_label(next_label)
                else:
                    stats["label_infeasible_count"] += 1
        if not frontier:
            break

    ordered = sorted(rows_by_task_set.values(), key=_resource_label_sort_key)
    if max_candidate_sets is not None:
        ordered = ordered[: max(0, int(max_candidate_sets))]
    stats["label_returned_seed_count"] = len(ordered)
    stats["label_end_bucket_count"] = len(labels_by_end)
    return tuple(ordered), stats


def _deadline_expired(deadline: float | None) -> bool:
    return bool(deadline is not None and perf_counter() >= float(deadline))


def _remaining_wall_time(deadline: float | None) -> float | None:
    if deadline is None:
        return None
    return max(0.0, float(deadline) - perf_counter())


def _resource_extension_label_columns(
    data: LunarIceData,
    labels: Iterable[_ResourceExtensionLabel],
) -> tuple[JourneyColumn, ...]:
    columns: list[JourneyColumn] = []
    for label in labels:
        if not label.sortie.feasible:
            continue
        try:
            columns.append(build_journey_column(data, (label.sortie,)))
        except ValueError:
            continue
    return _dedupe_columns(columns)


def _resource_ng_neighborhoods(
    data: LunarIceData,
    duals: JourneyDuals,
    *,
    ng_neighborhood_size: int,
) -> dict[str, tuple[str, ...]]:
    neighborhoods: dict[str, tuple[str, ...]] = {}
    for task_id in data.task_ids:
        ranked = sorted(
            (other for other in data.task_ids if other != task_id),
            key=lambda other: (
                _task_distance(data, task_id, other),
                -float(duals.cover.get(other, 0.0)),
                -float(data.tasks[other].science_weight),
                other,
            ),
        )
        neighborhoods[task_id] = tuple(ranked[: max(1, int(ng_neighborhood_size) - 1)])
    return neighborhoods


def _resource_extension_next_tasks(
    data: LunarIceData,
    task_ids: tuple[str, ...],
    label: _ResourceExtensionLabel,
    *,
    neighborhood: dict[str, tuple[str, ...]],
    duals: JourneyDuals,
) -> tuple[str, ...]:
    candidates = set(neighborhood.get(label.current_task, tuple()))
    candidates.update(
        task_id
        for task_id, _dual in sorted(
            ((task_id, float(duals.cover.get(task_id, 0.0))) for task_id in task_ids),
            key=lambda item: (-item[1], item[0]),
        )[:2]
    )
    return tuple(
        sorted(
            (task_id for task_id in candidates if task_id not in label.task_set),
            key=lambda task_id: (
                -float(duals.cover.get(task_id, 0.0)),
                _task_distance(data, label.current_task, task_id),
                task_id,
            ),
        )
    )


def _build_resource_extension_label(
    data: LunarIceData,
    duals: JourneyDuals,
    sequence: tuple[str, ...],
    *,
    proxy_profile: str = "balanced",
) -> _ResourceExtensionLabel | None:
    path_types = _proxy_path_types_for_sequence(data, sequence, proxy_profile=proxy_profile)
    sortie = build_timed_sortie(data, sequence, path_types, start_time=0.0)
    if not sortie.feasible:
        return None
    reduced_proxy = round(
        sortie_objective_value(data, sortie)
        - sum(float(duals.cover.get(task_id, 0.0)) for task_id in sortie.tasks),
        9,
    )
    return _ResourceExtensionLabel(
        sequence=tuple(sequence),
        task_set=tuple(sorted(sequence)),
        current_task=str(sequence[-1]),
        sortie=sortie,
        reduced_proxy=reduced_proxy,
        proxy_profile=str(proxy_profile),
    )


def _build_resource_extension_label_variants(
    data: LunarIceData,
    duals: JourneyDuals,
    sequence: tuple[str, ...],
    *,
    proxy_profile: str = "balanced",
) -> tuple[tuple[_ResourceExtensionLabel, ...], dict[str, int]]:
    assignments, duplicate_count = _resource_extension_path_type_assignments(
        data,
        sequence,
        proxy_profile=proxy_profile,
    )
    labels: list[_ResourceExtensionLabel] = []
    infeasible_count = 0
    for path_types in assignments:
        label = _build_resource_extension_label_for_path_types(
            data,
            duals,
            sequence,
            path_types=path_types,
            proxy_profile=proxy_profile,
        )
        if label is None:
            infeasible_count += 1
            continue
        labels.append(label)
    stats = _empty_resource_extension_stats()
    stats["label_path_variant_candidate_count"] = len(assignments)
    stats["label_path_variant_duplicate_count"] = int(duplicate_count)
    stats["label_path_variant_feasible_count"] = len(labels)
    stats["label_path_variant_infeasible_count"] = int(infeasible_count)
    return tuple(labels), stats


def _build_resource_extension_label_for_path_types(
    data: LunarIceData,
    duals: JourneyDuals,
    sequence: tuple[str, ...],
    *,
    path_types: tuple[str, ...],
    proxy_profile: str,
) -> _ResourceExtensionLabel | None:
    if len(path_types) != len(sequence) + 1:
        return None
    sortie = build_timed_sortie(data, sequence, path_types, start_time=0.0)
    if not sortie.feasible:
        return None
    reduced_proxy = round(
        sortie_objective_value(data, sortie)
        - sum(float(duals.cover.get(task_id, 0.0)) for task_id in sortie.tasks),
        9,
    )
    return _ResourceExtensionLabel(
        sequence=tuple(sequence),
        task_set=tuple(sorted(sequence)),
        current_task=str(sequence[-1]),
        sortie=sortie,
        reduced_proxy=reduced_proxy,
        proxy_profile=str(proxy_profile),
    )


def _resource_extension_path_type_assignments(
    data: LunarIceData,
    sequence: tuple[str, ...],
    *,
    proxy_profile: str = "balanced",
) -> tuple[tuple[tuple[str, ...], ...], int]:
    if not sequence:
        return tuple(), 0
    candidates: list[tuple[str, ...]] = []
    base = _proxy_path_types_for_sequence(data, sequence, proxy_profile=proxy_profile)
    candidates.append(base)
    for profile in _RESOURCE_EXTENSION_PROXY_PROFILES:
        if profile == proxy_profile:
            continue
        candidates.append(_proxy_path_types_for_sequence(data, sequence, proxy_profile=profile))

    current = "depot"
    arc_keys: list[tuple[str, str]] = []
    for task_id in sequence:
        arc_keys.append((str(current), str(task_id)))
        current = str(task_id)
    arc_keys.append((str(current), "depot"))
    for index, (source, target) in enumerate(arc_keys):
        for path_type in _resource_extension_nondominated_path_types(data, source, target):
            if path_type == base[index]:
                continue
            row = list(base)
            row[index] = path_type
            candidates.append(tuple(row))

    deduped: list[tuple[str, ...]] = []
    seen: set[tuple[str, ...]] = set()
    duplicate_count = 0
    for row in candidates:
        if row in seen:
            duplicate_count += 1
            continue
        seen.add(row)
        deduped.append(row)
        if len(deduped) >= _RESOURCE_EXTENSION_MAX_PATH_VARIANTS_PER_SEQUENCE:
            duplicate_count += max(0, len(candidates) - len(seen))
            break
    return tuple(deduped), duplicate_count


def _resource_extension_nondominated_path_types(
    data: LunarIceData,
    source: str,
    target: str,
) -> tuple[str, ...]:
    options = data.arcs[(str(source), str(target))]
    kept: list[str] = []
    for path_type in PATH_TYPES:
        option = options[str(path_type)]
        dominated = False
        for other_type in PATH_TYPES:
            if other_type == path_type:
                continue
            other = options[str(other_type)]
            weakly_better = (
                float(other.travel_time_min) <= float(option.travel_time_min) + 1.0e-9
                and float(other.distance_km) <= float(option.distance_km) + 1.0e-9
                and float(other.energy_proxy) <= float(option.energy_proxy) + 1.0e-9
                and float(other.risk_integral) <= float(option.risk_integral) + 1.0e-9
                and float(other.shadow_exposure_min) <= float(option.shadow_exposure_min) + 1.0e-9
            )
            strictly_better = (
                float(other.travel_time_min) < float(option.travel_time_min) - 1.0e-9
                or float(other.distance_km) < float(option.distance_km) - 1.0e-9
                or float(other.energy_proxy) < float(option.energy_proxy) - 1.0e-9
                or float(other.risk_integral) < float(option.risk_integral) - 1.0e-9
                or float(other.shadow_exposure_min) < float(option.shadow_exposure_min) - 1.0e-9
            )
            if weakly_better and strictly_better:
                dominated = True
                break
        if not dominated:
            kept.append(str(path_type))
    return tuple(kept)


def _proxy_path_types_for_sequence(
    data: LunarIceData,
    sequence: tuple[str, ...],
    *,
    proxy_profile: str = "balanced",
) -> tuple[str, ...]:
    current = "depot"
    path_types: list[str] = []
    for task_id in sequence:
        path_types.append(_proxy_path_type(data, current, task_id, proxy_profile=proxy_profile))
        current = task_id
    path_types.append(_proxy_path_type(data, current, "depot", proxy_profile=proxy_profile))
    return tuple(path_types)


def _proxy_path_type(
    data: LunarIceData,
    source: str,
    target: str,
    *,
    proxy_profile: str = "balanced",
) -> str:
    options = data.arcs[(str(source), str(target))]
    return min(
        options.values(),
        key=lambda option: _proxy_path_sort_key(option, proxy_profile=str(proxy_profile)),
    ).path_type


def _proxy_path_sort_key(option, *, proxy_profile: str) -> tuple[float, float, float, float, float, str]:
    travel = float(option.travel_time_min)
    energy = float(option.energy_proxy)
    risk = float(option.risk_integral)
    distance = float(option.distance_km)
    if proxy_profile == "time":
        primary = travel
    elif proxy_profile == "energy":
        primary = energy
    elif proxy_profile == "risk":
        primary = risk
    elif proxy_profile == "distance":
        primary = distance
    elif proxy_profile == "cost":
        primary = energy + distance
    else:
        primary = travel + 0.02 * energy + 0.02 * risk + 0.01 * distance
    return (primary, travel, energy, risk, distance, option.path_type)


def _add_resource_extension_label(
    labels: list[_ResourceExtensionLabel],
    candidate: _ResourceExtensionLabel,
    *,
    max_labels_per_task: int,
) -> tuple[bool, str, int, int]:
    kept: list[_ResourceExtensionLabel] = []
    replaced_count = 0
    for old in labels:
        same_task_set = old.task_set == candidate.task_set
        if same_task_set and _resource_label_dominates(old, candidate):
            return False, "dominated_by_existing", 0, 0
        if same_task_set and _resource_label_dominates(candidate, old):
            replaced_count += 1
            continue
        kept.append(old)
    label_cap = max(1, int(max_labels_per_task))
    kept.append(candidate)
    before_truncate = len(kept)
    kept = _truncate_resource_labels_by_task_count(kept, label_cap=label_cap)
    truncated_count = max(0, before_truncate - len(kept))
    labels[:] = kept
    accepted = candidate in labels
    return accepted, "accepted" if accepted else "capacity_truncated", replaced_count, truncated_count


def _truncate_resource_labels_by_task_count(
    labels: Iterable[_ResourceExtensionLabel],
    *,
    label_cap: int,
) -> list[_ResourceExtensionLabel]:
    """Keep a bounded deterministic label bucket for each task-count band.

    This is a worker-only recall safeguard.  Mature SPPRC labelers keep many
    incomparable labels per end node; a single global cap per end task can
    discard all larger task sets before they have a chance to extend.  We keep a
    small cap for every task-count band while preserving the existing
    reduced-cost/time ordering inside each band.
    """

    cap = max(1, int(label_cap))
    by_count: dict[int, list[_ResourceExtensionLabel]] = {}
    for label in labels:
        by_count.setdefault(len(label.task_set), []).append(label)
    kept: list[_ResourceExtensionLabel] = []
    for task_count in sorted(by_count):
        bucket = sorted(by_count[task_count], key=_resource_label_sort_key)
        kept.extend(bucket[:cap])
    kept.sort(key=_resource_label_sort_key)
    return kept


def _resource_label_dominates(
    left: _ResourceExtensionLabel,
    right: _ResourceExtensionLabel,
) -> bool:
    return bool(
        left.sortie.end_time <= right.sortie.end_time + 1.0e-9
        and left.sortie.energy_proxy <= right.sortie.energy_proxy + 1.0e-9
        and left.sortie.shadow_exposure_min <= right.sortie.shadow_exposure_min + 1.0e-9
        and left.reduced_proxy <= right.reduced_proxy + 1.0e-9
    )


def _resource_label_sort_key(label: _ResourceExtensionLabel) -> tuple[float, float, int, tuple[str, ...]]:
    return (
        float(label.reduced_proxy),
        float(label.sortie.end_time),
        len(label.task_set),
        label.task_set,
    )


def _dedupe_task_sets(rows: Iterable[Iterable[str]]) -> tuple[tuple[str, ...], ...]:
    seen: set[tuple[str, ...]] = set()
    result: list[tuple[str, ...]] = []
    for row in rows:
        normalized = tuple(sorted({str(task_id) for task_id in row}))
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return tuple(result)


def _task_distance(data: LunarIceData, left: str, right: str) -> float:
    a = data.tasks[str(left)].xy_km
    b = data.tasks[str(right)].xy_km
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5
