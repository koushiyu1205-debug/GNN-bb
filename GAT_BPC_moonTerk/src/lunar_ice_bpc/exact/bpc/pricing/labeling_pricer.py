"""Exact-safe resource-labeling pricing boundary for BPC.

This module is the BPC-facing wrapper around resource-constrained journey
labeling.  It deliberately separates candidate search from certification:

* relaxed/ng-route/stabilized modes may find columns, but never prove no-negative;
* every returned column is re-audited with the current true RMP dual;
* exact elementary certification is allowed only when the priced task-subset
  space is complete and the true-dual reduced-cost audit closes.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from time import perf_counter
from typing import Iterable

from lunar_ice_bpc.exact.bpc.cuts.cut_audit import (
    audit_cut_reduced_cost_consistency,
    build_cut_dominance_compatibility_report,
    cut_aware_column_signature_from_journey,
)
from lunar_ice_bpc.exact.bpc.pricing.dual_stabilization import (
    TAIL_DUAL_STABILIZATION_DEFAULT_ALPHA,
    TAIL_DUAL_STABILIZATION_DEFAULT_WINDOW,
    build_tail_dual_center,
    build_worker_duals_with_tail_center,
)
from lunar_ice_bpc.exact.bpc.pricing.resource_label_core import (
    CORE_EXACT_ELEMENTARY_FULL_SPACE,
    CORE_RELAXED_NG_ROUTE_WORKER,
    ResourceLabelCoreConfig,
    run_resource_label_core,
)
from lunar_ice_bpc.exact.bpc.pricing.status import PricingState
from lunar_ice_bpc.exact.core.branching import BranchContext, journey_satisfies_branch_context
from lunar_ice_bpc.exact.core.cuts import (
    CutContext,
    stable_payload_hash,
    true_dual_binding_hash,
)
from lunar_ice_bpc.exact.core.data import LunarIceData
from lunar_ice_bpc.exact.core.journey import JourneyColumn
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals, manual_journey_reduced_cost
from lunar_ice_bpc.exact.pricing.journey_pricing import DirectPricingCache


LABELING_PRICER_SCHEMA_VERSION = "lunar_ice_bpc.bpc_labeling_pricer.v1"
EXACT_ELEMENTARY_MODE = "exact_elementary"
RELAXED_NG_ROUTE_MODE = "relaxed_ng_route"
HEURISTIC_LABELING_MODE = "heuristic_labeling"
LABELING_PRICER_MODES = (EXACT_ELEMENTARY_MODE, RELAXED_NG_ROUTE_MODE, HEURISTIC_LABELING_MODE)
PROOF_KIND_NONE = "NONE"
PROOF_KIND_EXHAUSTIVE_FOUND_NEGATIVE = "EXHAUSTIVE_FOUND_NEGATIVE"
PROOF_KIND_EXHAUSTIVE_INCOMPLETE = "EXHAUSTIVE_INCOMPLETE"
PROOF_KIND_EXHAUSTIVE_NO_NEGATIVE = "EXHAUSTIVE_NO_NEGATIVE"
PROOF_KIND_RELAXED_WORKER_UNCERTIFIED = "RELAXED_WORKER_UNCERTIFIED"
CERTIFYING_PROOF_KINDS = frozenset(
    {
        PROOF_KIND_EXHAUSTIVE_NO_NEGATIVE,
        "FRONTIER_BOUND_NO_NEGATIVE",
    }
)
STATUS_SEMANTICS_CONTRACT_VERSION = "bpc_future_pricing_status_semantics_20260606"
NATIVE_EXACT_BACKEND_ENV = "LUNAR_ICE_SPPRC_EXACT_BACKEND"
DEFAULT_EXACT_BACKEND_ID = "native_rcspp_inprocess"
NATIVE_MEMORY_LIMIT_GB_ENV = "LUNAR_ICE_SPPRC_MEMORY_LIMIT_GB"
NATIVE_SHADOW_BACKEND_ENV = "LUNAR_ICE_SPPRC_SHADOW_BACKEND"
NATIVE_COMPLETION_BOUND_ENV = "LUNAR_ICE_SPPRC_COMPLETION_BOUND"
NATIVE_SUBSET_DOMINANCE_ENV = "LUNAR_ICE_SPPRC_SUBSET_DOMINANCE"
NATIVE_CUT_STATE_ENV = "LUNAR_ICE_SPPRC_CUT_STATE"


@dataclass(frozen=True)
class LabelingPricingConfig:
    """Configuration for exact-safe BPC labeling pricing.

    ``exact_elementary`` can certify only when ``len(data.task_ids)`` is within
    ``max_exact_tasks``.  The other modes are worker modes: they are allowed to
    use neighborhoods and stabilized duals to find columns, but no no-column
    result from those modes is a certificate.
    """

    mode: str = EXACT_ELEMENTARY_MODE
    max_exact_tasks: int = 10
    max_label_task_count: int = 12
    max_candidate_sets: int | None = 160
    harvest_target: int = 16
    exact_negative_harvest_target: int = 1
    completion_bound_enabled: bool = True
    ng_neighborhood_size: int = 8
    ng_neighborhood_sizes: tuple[int, ...] | None = (3, 5, 8)
    wall_time_limit_sec: float | None = None
    negative_eps: float = 1.0e-6
    dual_stabilization_enabled: bool = False
    dual_stabilization_alpha: float = TAIL_DUAL_STABILIZATION_DEFAULT_ALPHA
    dual_stabilization_window: int = TAIL_DUAL_STABILIZATION_DEFAULT_WINDOW
    stop_at_first_negative: bool = False
    support_aware_harvest_enabled: bool = True
    support_overlap_threshold: float = 0.6
    max_selected_jaccard: float = 0.5
    max_selected_containment: float = 0.8
    weak_replacement_cap: int = 8
    strong_replacement_threshold: float = -1.0e-4
    support_continuation_seed_enabled: bool = True
    support_continuation_max_seed_sets: int = 240
    support_continuation_max_neighbors: int = 4
    support_continuation_protected_seed_count: int = 8
    resource_extension_seed_enabled: bool = True
    active_task_sets_for_exact_harvest: tuple[tuple[str, ...], ...] = tuple()
    rmp_iteration_id: str = ""
    cut_lineage_hash: str = ""
    live_cut_policy_hash: str = ""
    separator_policy_version: str = ""

    def __post_init__(self) -> None:
        mode = str(self.mode)
        if mode not in LABELING_PRICER_MODES:
            raise ValueError(f"unsupported labeling pricing mode {mode!r}")
        object.__setattr__(self, "mode", mode)
        object.__setattr__(self, "max_exact_tasks", int(self.max_exact_tasks))
        object.__setattr__(self, "max_label_task_count", int(self.max_label_task_count))
        object.__setattr__(self, "harvest_target", max(1, int(self.harvest_target)))
        object.__setattr__(
            self,
            "exact_negative_harvest_target",
            max(1, int(self.exact_negative_harvest_target)),
        )
        ng_size = max(1, int(self.ng_neighborhood_size))
        object.__setattr__(self, "ng_neighborhood_size", ng_size)
        object.__setattr__(
            self,
            "ng_neighborhood_sizes",
            _normalize_neighborhood_sizes(self.ng_neighborhood_sizes, fallback=ng_size),
        )
        if self.max_candidate_sets is not None:
            object.__setattr__(self, "max_candidate_sets", max(0, int(self.max_candidate_sets)))
        if self.wall_time_limit_sec is not None:
            object.__setattr__(self, "wall_time_limit_sec", max(0.0, float(self.wall_time_limit_sec)))
        object.__setattr__(self, "negative_eps", abs(float(self.negative_eps)))
        object.__setattr__(
            self,
            "dual_stabilization_alpha",
            max(0.0, min(1.0, float(self.dual_stabilization_alpha))),
        )
        object.__setattr__(self, "dual_stabilization_window", max(1, int(self.dual_stabilization_window)))
        object.__setattr__(
            self,
            "support_overlap_threshold",
            max(0.0, min(1.0, float(self.support_overlap_threshold))),
        )
        object.__setattr__(
            self,
            "max_selected_jaccard",
            max(0.0, min(1.0, float(self.max_selected_jaccard))),
        )
        object.__setattr__(
            self,
            "max_selected_containment",
            max(0.0, min(1.0, float(self.max_selected_containment))),
        )
        object.__setattr__(self, "weak_replacement_cap", max(0, int(self.weak_replacement_cap)))
        object.__setattr__(
            self,
            "strong_replacement_threshold",
            float(self.strong_replacement_threshold),
        )
        object.__setattr__(
            self,
            "active_task_sets_for_exact_harvest",
            tuple(
                tuple(sorted(str(task_id) for task_id in row))
                for row in (self.active_task_sets_for_exact_harvest or tuple())
            ),
        )
        object.__setattr__(
            self,
            "support_continuation_max_seed_sets",
            max(0, int(self.support_continuation_max_seed_sets)),
        )
        object.__setattr__(
            self,
            "support_continuation_max_neighbors",
            max(1, int(self.support_continuation_max_neighbors)),
        )
        object.__setattr__(
            self,
            "support_continuation_protected_seed_count",
            max(0, int(self.support_continuation_protected_seed_count)),
        )

    @property
    def exact_mode(self) -> bool:
        return self.mode == EXACT_ELEMENTARY_MODE

    @property
    def relaxed_mode(self) -> bool:
        return self.mode == RELAXED_NG_ROUTE_MODE


def run_bpc_labeling_pricer(
    data: LunarIceData,
    true_duals: JourneyDuals,
    *,
    config: LabelingPricingConfig | None = None,
    branch_context: BranchContext | None = None,
    cut_context: CutContext | None = None,
    seed_task_sets: Iterable[Iterable[str]] = tuple(),
    seed_source_rows: Iterable[dict] = tuple(),
    existing_task_sets: Iterable[Iterable[str]] = tuple(),
    support_task_sets: Iterable[Iterable[str]] = tuple(),
    dual_history: Iterable[JourneyDuals] = tuple(),
    cache: DirectPricingCache | None = None,
) -> tuple[dict, tuple[JourneyColumn, ...]]:
    """Run the BPC resource-labeling pricer with fail-closed certificates."""

    cfg = config or LabelingPricingConfig()
    branch = branch_context or BranchContext()
    cuts = cut_context or CutContext()
    started_at = perf_counter()
    native_fallback_payload: dict = {}
    native_shadow_payload: dict = {}
    native_backend_id = str(
        os.getenv(NATIVE_EXACT_BACKEND_ENV, DEFAULT_EXACT_BACKEND_ID)
    )
    native_result = None
    native_shadow_backend_id = str(os.getenv(NATIVE_SHADOW_BACKEND_ENV, "") or "")
    if (
        cfg.exact_mode
        and native_backend_id == "python_reference"
        and native_shadow_backend_id
        and native_shadow_backend_id != "python_reference"
    ):
        shadow_started = perf_counter()
        try:
            shadow_result = _run_native_exact_backend(
                data,
                true_duals,
                cfg,
                branch_context=branch,
                cut_context=cuts,
                backend_id=native_shadow_backend_id,
            )
            native_shadow_payload = {
                "native_shadow_enabled": True,
                "native_shadow_backend_id": native_shadow_backend_id,
                "native_shadow_wall_time_sec": round(perf_counter() - shadow_started, 6),
                "native_shadow_result": shadow_result.to_payload(),
                "native_shadow_mutates_official_result": False,
            }
        except Exception as exc:
            native_shadow_payload = {
                "native_shadow_enabled": True,
                "native_shadow_backend_id": native_shadow_backend_id,
                "native_shadow_wall_time_sec": round(perf_counter() - shadow_started, 6),
                "native_shadow_error": repr(exc),
                "native_shadow_mutates_official_result": False,
            }
    if cfg.exact_mode and native_backend_id != "python_reference":
        native_result = _run_native_exact_backend(
            data,
            true_duals,
            cfg,
            branch_context=branch,
            cut_context=cuts,
            backend_id=native_backend_id,
        )
        if native_result.engine_status in {
            "UNSUPPORTED_FEATURE",
            "BACKEND_UNAVAILABLE",
            "BACKEND_ERROR",
            "BACKEND_CRASH",
        }:
            native_fallback_payload = {
                "native_backend_requested": native_backend_id,
                "native_backend_fallback_to_python": True,
                "native_backend_fallback_status": native_result.engine_status,
                "native_backend_fallback_blockers": list(native_result.certificate_blockers),
            }
            native_result = None
    if native_result is not None:
        payload, columns = _native_exact_backend_payload(
            native_result,
            cfg,
            backend_id=native_backend_id,
            true_duals=true_duals,
            cut_context=cuts,
        )
    elif cfg.exact_mode:
        payload, columns = _run_exact_elementary_labeling(
            data,
            true_duals,
            cfg,
            branch_context=branch,
            cut_context=cuts,
            cache=cache,
        )
    else:
        payload, columns = _run_worker_labeling(
            data,
            true_duals,
            cfg,
            branch_context=branch,
            cut_context=cuts,
            seed_task_sets=tuple(tuple(str(task_id) for task_id in row) for row in seed_task_sets),
            seed_source_rows=tuple(seed_source_rows or tuple()),
            existing_task_sets=tuple(tuple(str(task_id) for task_id in row) for row in existing_task_sets),
            support_task_sets=tuple(tuple(str(task_id) for task_id in row) for row in support_task_sets),
            dual_history=tuple(dual_history),
        )
    payload = dict(payload)
    payload["schema_version"] = LABELING_PRICER_SCHEMA_VERSION
    payload["labeling_pricer_wall_time_sec"] = round(perf_counter() - started_at, 6)
    payload["mode"] = cfg.mode
    payload["pricer_kind"] = "resource_constrained_shortest_path_labeling"
    payload["exact_elementary_mode"] = bool(cfg.exact_mode)
    payload["relaxed_ng_route_mode"] = bool(cfg.relaxed_mode)
    payload["ng_neighborhood_size"] = int(cfg.ng_neighborhood_size)
    payload["ng_neighborhood_sizes"] = [
        int(size) for size in (cfg.ng_neighborhood_sizes or (cfg.ng_neighborhood_size,))
    ]
    payload["ng_neighborhood_stage_count"] = len(cfg.ng_neighborhood_sizes or (cfg.ng_neighborhood_size,))
    payload["max_label_task_count"] = int(cfg.max_label_task_count)
    payload["harvest_target"] = int(cfg.harvest_target)
    payload["exact_negative_harvest_target"] = int(cfg.exact_negative_harvest_target)
    payload["active_task_sets_for_exact_harvest_count"] = len(cfg.active_task_sets_for_exact_harvest)
    payload["completion_bound_requested"] = bool(cfg.completion_bound_enabled)
    payload["branch_context_active"] = not branch.empty
    payload["branch_decision_count"] = len(branch.pair_decisions)
    payload["cut_context_active"] = not cuts.empty
    payload["cut_count"] = len(cuts.cuts)
    payload["certificate_boundary"] = (
        "exact elementary full-subset coverage can certify no-negative"
        if cfg.exact_mode
        else "worker/relaxed/ng-route candidate search only; no-column is uncertified"
    )
    payload["dual_stabilization_requested"] = bool(cfg.dual_stabilization_enabled)
    payload["dual_stabilization_scope"] = "worker_candidate_search_only"
    payload["dual_stabilization_used_for_official_certificate"] = False
    payload["dual_stabilization_ignored_for_exact_mode"] = bool(
        cfg.exact_mode and cfg.dual_stabilization_enabled
    )
    payload["official_pricing_dual_source"] = "current_true_rmp_dual"
    payload["stabilized_dual_no_column_can_certify"] = False
    payload.update(native_fallback_payload)
    payload.update(native_shadow_payload)
    payload.update(_status_semantics_contract(payload, exact_mode=cfg.exact_mode))
    return payload, columns


def _run_native_exact_backend(
    data: LunarIceData,
    true_duals: JourneyDuals,
    cfg: LabelingPricingConfig,
    *,
    branch_context: BranchContext,
    cut_context: CutContext,
    backend_id: str,
):
    from lunar_ice_bpc.exact.bpc.pricing.backends import (
        BACKEND_MODE_EXACT_PROOF,
        BACKEND_MODE_NEGATIVE_HARVEST,
        BackendPricingRequest,
        BackendRegistry,
    )
    from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import spprc_instance_hash

    try:
        memory_limit_gb = max(0.0, float(os.getenv(NATIVE_MEMORY_LIMIT_GB_ENV, "0") or 0.0))
    except ValueError:
        memory_limit_gb = 0.0
    return BackendRegistry.create(backend_id).solve(
        BackendPricingRequest(
            data=data,
            true_duals=true_duals,
            mode=(
                BACKEND_MODE_NEGATIVE_HARVEST
                if cfg.stop_at_first_negative
                else BACKEND_MODE_EXACT_PROOF
            ),
            branch_context=branch_context,
            cut_context=cut_context,
            harvest_target=cfg.exact_negative_harvest_target,
            wall_time_limit_sec=cfg.wall_time_limit_sec,
            memory_limit_gb=memory_limit_gb,
            negative_eps=cfg.negative_eps,
            completion_bound_enabled=bool(cfg.completion_bound_enabled)
            and str(os.getenv(NATIVE_COMPLETION_BOUND_ENV, "0")).strip().lower()
            in {"1", "true", "yes", "on"},
            subset_dominance_enabled=str(
                os.getenv(NATIVE_SUBSET_DOMINANCE_ENV, "0")
            ).strip().lower()
            in {"1", "true", "yes", "on"},
            instance_hash=spprc_instance_hash(data),
            config_hash=stable_payload_hash(cfg.__dict__),
            dual_binding_hash=true_dual_binding_hash(
                true_duals.cover,
                fleet_limit=true_duals.fleet_limit,
                cuts=true_duals.cuts,
            ),
            branch_context_hash=stable_payload_hash(branch_context.to_payload()),
            cut_context_hash=cut_context.active_cut_context_hash,
            cut_lineage_hash=cfg.cut_lineage_hash,
            live_cut_policy_hash=cfg.live_cut_policy_hash,
            rmp_iteration_id=cfg.rmp_iteration_id,
            separator_policy_version=cfg.separator_policy_version,
        )
    )


def _native_exact_backend_payload(
    result,
    cfg: LabelingPricingConfig,
    *,
    backend_id: str,
    true_duals: JourneyDuals,
    cut_context: CutContext,
) -> tuple[dict, tuple[JourneyColumn, ...]]:
    negative_columns = tuple(result.columns)
    proof_only_blockers = {
        "native_exact_search_incomplete",
        "native_frontier_not_empty",
    }
    column_audit_blockers = tuple(
        blocker
        for blocker in result.certificate_blockers
        if blocker not in proof_only_blockers
        and not str(blocker).startswith("native_result_binding_mismatch:")
        and blocker != "native_engine_build_hash_missing"
    )
    column_audit_pass = not column_audit_blockers
    has_negative = bool(
        result.best_found_rc is not None and result.best_found_rc < -cfg.negative_eps
    )
    certified = bool(
        not has_negative
        and result.can_enter_certificate_audit
        and result.proved_no_rc_below is not None
        and result.proved_no_rc_below >= -cfg.negative_eps
    )
    state = (
        PricingState.FOUND_NEGATIVE
        if has_negative
        else PricingState.CERTIFIED_NO_NEGATIVE
        if certified
        else PricingState.INCOMPLETE_LIMIT
    )
    proof_kind = (
        PROOF_KIND_EXHAUSTIVE_FOUND_NEGATIVE
        if has_negative and result.search_exhaustive
        else PROOF_KIND_EXHAUSTIVE_NO_NEGATIVE
        if certified
        else PROOF_KIND_EXHAUSTIVE_INCOMPLETE
    )
    payload = result.to_payload()
    payload.update(
        {
            "status": result.engine_status,
            "native_backend_id": backend_id,
            "native_backend_result": result.to_payload(),
            "labeling_algorithm": "native_rcspp_forward_elementary_multi_sortie",
            "resource_label_algorithm": "lab_core_rcspp_project_local_journey_resource",
            "resource_label_core_mode": "native_exact_elementary_full_space",
            "resource_dimensions": [
                "global_time",
                "sortie_demand",
                "sortie_energy",
                "sortie_shadow",
                "visited_bitset",
                "raw_operating_cost",
                "raw_risk",
                "raw_weighted_completion",
                "task_dual_reward",
            ],
            "dominance_policy": "same_visited_conservative_resource_and_true_rc",
            "elementarity_policy": "global_journey_visited_bitset_not_reset_between_sorties",
            "pricing_state": state.value,
            "pricing_proof_kind": proof_kind,
            "can_certify_no_negative": certified,
            "uses_true_dual_bpc_certificate": certified,
            "pricing_complete_for_all_task_subsets": bool(result.search_exhaustive),
            "pricing_complete_for_all_tasks": bool(result.search_exhaustive),
            "pricing_complete_for_branch_context": bool(result.search_exhaustive),
            "global_min_proof_complete": bool(result.search_exhaustive),
            "global_min_reduced_cost_source": (
                "native_exact_global_min"
                if result.global_min_rc_is_exact
                else "native_proved_no_rc_below_threshold"
                if result.proved_no_rc_below is not None
                else ""
            ),
            "global_min_reduced_cost_scope": "full_elementary_multi_sortie_journey_space",
            "global_remaining_rc_lb": (
                result.global_min_rc
                if result.global_min_rc_is_exact
                else result.proved_no_rc_below
            ),
            "global_remaining_rc_lb_valid": certified,
            "global_remaining_rc_lb_coverage_complete": bool(result.search_exhaustive),
            "proved_no_rc_below": result.proved_no_rc_below,
            "true_best_reduced_cost": result.best_found_rc,
            "best_reduced_cost": result.best_found_rc,
            "pricing_best_reduced_cost": result.best_found_rc,
            "true_audited_column_count": len(negative_columns),
            "true_negative_column_count": len(negative_columns),
            "returned_column_count": len(negative_columns),
            "returned_column_policy": "audited_true_rc_negative_columns_only",
            "returned_columns_are_complete_universe": False,
            "true_dual_reaudit_pass": bool(result.partial_columns_valid or not negative_columns),
            "branch_context_audit_pass": True,
            # Incomplete proof is a certificate blocker, not an RC-audit
            # failure for columns that were fully reconstructed and manually
            # checked before the stop condition.
            "pricing_rc_audit_pass": column_audit_pass,
            "manual_rc_audit_pass": column_audit_pass,
            "completion_bound": {"enabled": False, "can_certify_no_negative": False},
            "completion_bound_certificate_safe": True,
            "native_partial_negative_columns_retained": bool(
                negative_columns and not result.search_exhaustive
            ),
            "label_queue_push_count": int(result.telemetry.get("extended_labels") or 0),
            "dominance_pruned": int(result.telemetry.get("dominated_labels") or 0),
            "note": (
                "Native exact engine exhausted the full frontier and proved the configured threshold."
                if certified
                else "Native search returned true-dual audited negative columns."
                if negative_columns
                else "Native search is incomplete; fail closed for no-negative proof."
            ),
        }
    )
    cut_certificate_support = _cut_certificate_support_report(
        negative_columns,
        true_duals,
        cut_context,
        payload,
        negative_eps=cfg.negative_eps,
    )
    live_cut_supported = bool(
        cut_context.empty or cut_certificate_support["live_cut_certificate_supported"]
    )
    payload.update(
        {
            "cut_context_active": not cut_context.empty,
            "cut_count": len(cut_context.cuts),
            "live_cut_certificate_supported": live_cut_supported,
            "cut_certificate_support": cut_certificate_support,
        }
    )
    if certified and not live_cut_supported:
        payload.update(
            {
                "pricing_state": PricingState.INCOMPLETE_LIMIT.value,
                "pricing_proof_kind": PROOF_KIND_EXHAUSTIVE_INCOMPLETE,
                "can_certify_no_negative": False,
                "uses_true_dual_bpc_certificate": False,
                "global_remaining_rc_lb_valid": False,
                "note": "Native search exhausted, but the active cut certificate audit failed; fail closed.",
            }
        )
    return payload, negative_columns


def _run_exact_elementary_labeling(
    data: LunarIceData,
    true_duals: JourneyDuals,
    cfg: LabelingPricingConfig,
    *,
    branch_context: BranchContext,
    cut_context: CutContext,
    cache: DirectPricingCache | None,
) -> tuple[dict, tuple[JourneyColumn, ...]]:
    pricing, columns = run_resource_label_core(
        data,
        true_duals,
        config=ResourceLabelCoreConfig(
            mode=CORE_EXACT_ELEMENTARY_FULL_SPACE,
            max_task_count=cfg.max_exact_tasks,
            negative_eps=cfg.negative_eps,
            completion_bound_enabled=bool(cfg.completion_bound_enabled),
            exact_negative_harvest_target=cfg.exact_negative_harvest_target,
            active_task_sets_for_exact_harvest=cfg.active_task_sets_for_exact_harvest,
            stop_at_first_negative=bool(cfg.stop_at_first_negative),
            wall_time_limit_sec=cfg.wall_time_limit_sec,
        ),
        branch_context=branch_context,
        cut_context=cut_context,
        cache=cache,
    )
    audit = _audit_columns_with_true_dual(
        columns,
        true_duals,
        branch_context=branch_context,
        cut_context=cut_context,
        task_set_sources={},
        candidate_search_duals=true_duals,
        negative_eps=cfg.negative_eps,
        harvest_target=cfg.harvest_target,
    )
    complete = bool(pricing.get("pricing_complete_for_all_task_subsets"))
    pricing_best = _as_float_or_none(pricing.get("best_reduced_cost"))
    audit_best = _as_float_or_none(audit.get("true_best_reduced_cost"))
    rc_match = _rc_values_match(pricing_best, audit_best)
    ledger = _elementary_coverage_ledger(
        data,
        pricing,
        audit,
        max_exact_tasks=cfg.max_exact_tasks,
        rc_match=rc_match,
        negative_eps=cfg.negative_eps,
        branch_context=branch_context,
    )
    completion_bound_support = _completion_bound_support_report(pricing)
    if not completion_bound_support["completion_bound_certificate_safe"]:
        ledger = _downgrade_ledger_for_unsafe_completion_bound(
            ledger,
            completion_bound_support=completion_bound_support,
        )
        complete = False
    cut_certificate_support = _cut_certificate_support_report(
        columns,
        true_duals,
        cut_context,
        pricing,
        negative_eps=cfg.negative_eps,
    )
    if not cut_context.empty and not cut_certificate_support["live_cut_certificate_supported"]:
        ledger = _downgrade_ledger_for_unsupported_live_cuts(
            ledger,
            cut_context=cut_context,
            cut_certificate_support=cut_certificate_support,
        )
        complete = False
    certified = bool(
        ledger["coverage_complete"]
        and ledger["global_remaining_rc_lb_valid"]
        and rc_match
        and completion_bound_support["completion_bound_certificate_safe"]
        and audit["branch_context_audit_pass"]
        and audit["true_negative_column_count"] == 0
        and audit_best is not None
        and audit_best >= -cfg.negative_eps
    )
    manual_audit_pass = bool(
        audit.get("true_dual_reaudit_pass")
        and audit.get("branch_context_audit_pass")
    )
    if audit["true_negative_column_count"]:
        state = PricingState.FOUND_NEGATIVE
    elif certified:
        state = PricingState.CERTIFIED_NO_NEGATIVE
    elif complete:
        state = PricingState.INCOMPLETE_LIMIT
    else:
        state = PricingState.INCOMPLETE_LIMIT
    payload = dict(pricing)
    payload.update(audit)
    if not cut_context.empty and not cut_certificate_support["live_cut_certificate_supported"]:
        payload["pricing_complete_for_all_task_subsets"] = False
        payload["pricing_complete_for_all_tasks"] = False
    note = (
        "Exact elementary labeling over every nonempty task subset; may certify "
        "no-negative only when full coverage and true-dual RC audit pass."
    )
    if not cut_context.empty and cut_certificate_support["live_cut_certificate_supported"]:
        note = (
            "Exact elementary labeling used task-set-only live cuts with cut dominance, "
            "dual sign, and reduced-cost consistency audits."
        )
    elif not cut_context.empty:
        note = (
            "Exact elementary labeling found/audited columns under a live cut context, "
            "but cut-aware no-negative certification is not enabled; fail closed."
        )
    payload.update(
        {
            "labeling_algorithm": "elementary_resource_labeling_exhaustive_task_subsets",
            "pricing_state": state.value,
            "can_certify_no_negative": bool(certified),
            "uses_true_dual_bpc_certificate": bool(certified),
            "pricing_proof_kind": (
                PROOF_KIND_EXHAUSTIVE_NO_NEGATIVE
                if certified
                else PROOF_KIND_EXHAUSTIVE_FOUND_NEGATIVE
                if audit["true_negative_column_count"]
                else PROOF_KIND_EXHAUSTIVE_INCOMPLETE
            ),
            "elementary_coverage_ledger": ledger,
            "global_remaining_rc_lb": ledger["global_remaining_rc_lb"],
            "global_remaining_rc_lb_valid": ledger["global_remaining_rc_lb_valid"],
            "global_remaining_rc_lb_coverage_complete": ledger["coverage_complete"],
            "frontier_region_count": ledger["frontier_region_count"],
            "frontier_unsupported_region_count": ledger["unsupported_region_count"],
            "frontier_unsupported_task_count_regions": ledger[
                "unsupported_task_count_regions"
            ],
            "pricing_rc_audit_pass": bool(rc_match),
            "manual_rc_audit_pass": manual_audit_pass,
            "true_dual_candidate_audit_pass": manual_audit_pass,
            "pricing_best_reduced_cost": pricing_best,
            "worker_dual_stabilization_enabled": False,
            "worker_dual_used_for_candidate_search": False,
            "no_column_uncertified": not bool(certified),
            "completion_bound_certificate_safe": bool(
                completion_bound_support["completion_bound_certificate_safe"]
            ),
            "completion_bound_certificate_support": completion_bound_support,
            "live_cut_certificate_supported": bool(
                cut_context.empty or cut_certificate_support["live_cut_certificate_supported"]
            ),
            "cut_certificate_support": cut_certificate_support,
            "note": note,
        }
    )
    payload.pop("_selected_internal", None)
    return payload, tuple(columns)


def _run_worker_labeling(
    data: LunarIceData,
    true_duals: JourneyDuals,
    cfg: LabelingPricingConfig,
    *,
    branch_context: BranchContext,
    cut_context: CutContext,
    seed_task_sets: tuple[tuple[str, ...], ...],
    seed_source_rows: tuple[dict, ...],
    existing_task_sets: tuple[tuple[str, ...], ...],
    support_task_sets: tuple[tuple[str, ...], ...],
    dual_history: tuple[JourneyDuals, ...],
) -> tuple[dict, tuple[JourneyColumn, ...]]:
    center = build_tail_dual_center(dual_history, window=cfg.dual_stabilization_window)
    worker_duals, stabilization_payload = build_worker_duals_with_tail_center(
        true_duals,
        tail_dual_center=center,
        enabled=bool(cfg.dual_stabilization_enabled),
        alpha=cfg.dual_stabilization_alpha,
        window=cfg.dual_stabilization_window,
    )
    support_continuation_seed_sets = _support_continuation_seed_task_sets(
        data,
        worker_duals,
        support_task_sets=support_task_sets,
        max_label_task_count=cfg.max_label_task_count,
        max_seed_sets=cfg.support_continuation_max_seed_sets,
        max_neighbors=cfg.support_continuation_max_neighbors,
        enabled=bool(cfg.support_continuation_seed_enabled),
    )
    worker_seed_task_sets = _dedupe_task_sets((*seed_task_sets, *support_continuation_seed_sets))
    worker_seed_source_rows = (
        *seed_source_rows,
        *_support_continuation_seed_source_rows(support_continuation_seed_sets),
    )
    pricing, worker_columns = run_resource_label_core(
        data,
        worker_duals,
        config=ResourceLabelCoreConfig(
            mode=CORE_RELAXED_NG_ROUTE_WORKER,
            max_task_count=cfg.max_label_task_count,
            max_candidate_sets=cfg.max_candidate_sets,
            wall_time_limit_sec=cfg.wall_time_limit_sec,
            negative_eps=cfg.negative_eps,
            stop_at_first_negative=bool(cfg.stop_at_first_negative),
            negative_harvest_target=cfg.harvest_target,
            run_direct_portfolio=bool(cfg.relaxed_mode),
            resource_extension_seed_enabled=bool(cfg.resource_extension_seed_enabled),
            ng_neighborhood_size=cfg.ng_neighborhood_size,
            ng_neighborhood_sizes=cfg.ng_neighborhood_sizes,
            protected_support_continuation_seed_count=cfg.support_continuation_protected_seed_count,
        ),
        seed_task_sets=worker_seed_task_sets,
        seed_source_rows=worker_seed_source_rows,
        branch_context=branch_context,
        cut_context=cut_context,
    )
    audit = _audit_columns_with_true_dual(
        worker_columns,
        true_duals,
        branch_context=branch_context,
        cut_context=cut_context,
        task_set_sources=_seed_source_lookup(
            pricing.get("priced_candidate_task_set_sources")
            or pricing.get("active_seed_task_set_sources")
            or []
        ),
        candidate_search_duals=worker_duals,
        existing_task_sets=existing_task_sets,
        support_task_sets=support_task_sets,
        negative_eps=cfg.negative_eps,
        harvest_target=cfg.harvest_target,
        support_aware_harvest_enabled=bool(cfg.support_aware_harvest_enabled),
        support_overlap_threshold=cfg.support_overlap_threshold,
        max_selected_jaccard=cfg.max_selected_jaccard,
        max_selected_containment=cfg.max_selected_containment,
        weak_replacement_cap=cfg.weak_replacement_cap,
        strong_replacement_threshold=cfg.strong_replacement_threshold,
    )
    selected = tuple(audit_row["column"] for audit_row in audit["_selected_internal"])
    pricing_limit_hit = _pricing_payload_hit_limit(pricing)
    state = (
        PricingState.FOUND_NEGATIVE
        if selected
        else PricingState.INCOMPLETE_LIMIT
        if pricing_limit_hit
        else PricingState.LOCAL_NO_COLUMN_UNCERTIFIED
    )
    worker_audit_pass = bool(
        audit.get("true_dual_reaudit_pass")
        and audit.get("branch_context_audit_pass")
    )
    payload = dict(pricing)
    payload.update(audit)
    stabilization_enabled = bool(
        stabilization_payload.get("enabled")
        or stabilization_payload.get("tail_dual_stabilization_enabled")
    )
    payload.update(
        {
            "labeling_algorithm": (
                "ng_route_relaxed_resource_labeling_plus_direct_seed_portfolio"
                if cfg.relaxed_mode
                else "heuristic_resource_labeling"
            ),
            "resource_label_algorithm": pricing.get("resource_label_algorithm") or "",
            "resource_label_core_mode": pricing.get("resource_label_core_mode") or "",
            "resource_dimensions": pricing.get("resource_dimensions") or [],
            "dominance_policy": pricing.get("dominance_policy") or "",
            "elementarity_policy": pricing.get("elementarity_policy") or "",
            "pricing_state": state.value,
            "can_certify_no_negative": False,
            "uses_true_dual_bpc_certificate": False,
            "pricing_proof_kind": PROOF_KIND_RELAXED_WORKER_UNCERTIFIED,
            "elementary_coverage_ledger": {
                "coverage_complete": False,
                "unsupported_region_count": 1,
                "can_certify_no_negative": False,
                "note": "Relaxed/ng-route worker covers selected candidate sets only.",
            },
            "global_remaining_rc_lb": None,
            "global_remaining_rc_lb_valid": False,
            "global_remaining_rc_lb_coverage_complete": False,
            "frontier_unsupported_region_count": 1,
            "pricing_complete_for_all_task_subsets": False,
            "pricing_complete_for_all_tasks": False,
            "pricing_rc_audit_pass": worker_audit_pass,
            "manual_rc_audit_pass": worker_audit_pass,
            "worker_true_dual_candidate_audit_pass": worker_audit_pass,
            "worker_dual_stabilization": stabilization_payload,
            "worker_dual_stabilization_enabled": stabilization_enabled,
            "worker_dual_used_for_candidate_search": stabilization_enabled,
            "candidate_search_dual_is_true_dual": not stabilization_enabled,
            "ng_seed_task_set_count": int(pricing.get("ng_seed_task_set_count") or 0),
            "resource_extension_seed_enabled": bool(pricing.get("resource_extension_seed_enabled")),
            "resource_extension_seed_task_set_count": int(
                pricing.get("resource_extension_seed_task_set_count") or 0
            ),
            "active_resource_extension_seed_task_set_count": int(
                pricing.get("active_resource_extension_seed_task_set_count") or 0
            ),
            "resource_extension_seed_task_set_count_by_size": pricing.get(
                "resource_extension_seed_task_set_count_by_size"
            )
            or {},
            "resource_extension_label_column_worker_enabled": bool(
                pricing.get("resource_extension_label_column_worker_enabled")
            ),
            "resource_extension_label_column_count": int(
                pricing.get("resource_extension_label_column_count") or 0
            ),
            "resource_extension_label_column_task_set_count": int(
                pricing.get("resource_extension_label_column_task_set_count") or 0
            ),
            "resource_extension_label_column_task_sets": pricing.get(
                "resource_extension_label_column_task_sets"
            )
            or [],
            "resource_extension_label_column_policy": pricing.get(
                "resource_extension_label_column_policy"
            )
            or "",
            "resource_extension_label_columns_can_certify_no_negative": bool(
                pricing.get("resource_extension_label_columns_can_certify_no_negative")
            ),
            "resource_extension_label_path_variant_candidate_count": int(
                pricing.get("resource_extension_label_path_variant_candidate_count") or 0
            ),
            "resource_extension_label_path_variant_duplicate_count": int(
                pricing.get("resource_extension_label_path_variant_duplicate_count") or 0
            ),
            "resource_extension_label_path_variant_feasible_count": int(
                pricing.get("resource_extension_label_path_variant_feasible_count") or 0
            ),
            "resource_extension_label_path_variant_infeasible_count": int(
                pricing.get("resource_extension_label_path_variant_infeasible_count") or 0
            ),
            "seed_task_set_count": int(pricing.get("seed_task_set_count") or len(seed_task_sets)),
            "merged_seed_task_set_count": int(pricing.get("merged_seed_task_set_count") or len(seed_task_sets)),
            "active_seed_task_set_count": int(pricing.get("active_seed_task_set_count") or 0),
            "active_seed_task_set_source_counts": pricing.get("active_seed_task_set_source_counts") or {},
            "active_seed_task_set_source_task_count_counts": pricing.get(
                "active_seed_task_set_source_task_count_counts"
            )
            or {},
            "active_seed_task_set_sources": pricing.get("active_seed_task_set_sources") or [],
            "existing_master_task_set_count": len(_normalize_existing_task_sets(existing_task_sets)),
            "support_task_set_count": len(_normalize_existing_task_sets(support_task_sets)),
            "support_continuation_seed_enabled": bool(cfg.support_continuation_seed_enabled),
            "support_continuation_seed_count": len(support_continuation_seed_sets),
            "support_continuation_active_seed_count": _count_seed_intersection(
                pricing.get("active_seed_task_sets") or (),
                support_continuation_seed_sets,
            ),
            "support_continuation_max_seed_sets": int(cfg.support_continuation_max_seed_sets),
            "support_continuation_max_neighbors": int(cfg.support_continuation_max_neighbors),
            "support_continuation_protected_seed_count": int(
                cfg.support_continuation_protected_seed_count
            ),
            "support_continuation_active_protected_seed_count": int(
                pricing.get("active_protected_support_continuation_seed_task_set_count") or 0
            ),
            "support_continuation_seed_policy": (
                "rmp_support_add_drop_swap_by_worker_dual_worker_only_with_protected_front_budget"
            ),
            "support_continuation_can_certify_no_negative": False,
            "priced_candidate_task_set_source_counts": pricing.get(
                "priced_candidate_task_set_source_counts"
            )
            or {},
            "priced_candidate_task_set_source_task_count_counts": pricing.get(
                "priced_candidate_task_set_source_task_count_counts"
            )
            or {},
            "priced_candidate_task_set_sources": pricing.get("priced_candidate_task_set_sources") or [],
            "direct_candidate_task_set_count": int(pricing.get("direct_candidate_task_set_count") or 0),
            "candidate_seed_source_precedence": pricing.get("candidate_seed_source_precedence") or [],
            "active_ng_seed_task_set_count": int(pricing.get("active_ng_seed_task_set_count") or 0),
            "active_input_seed_task_set_count": int(pricing.get("active_input_seed_task_set_count") or 0),
            "ng_neighborhood_size": int(pricing.get("ng_neighborhood_size") or cfg.ng_neighborhood_size),
            "ng_neighborhood_sizes": pricing.get("ng_neighborhood_sizes")
            or [int(size) for size in (cfg.ng_neighborhood_sizes or (cfg.ng_neighborhood_size,))],
            "ng_neighborhood_stage_count": int(
                pricing.get("ng_neighborhood_stage_count")
                or len(cfg.ng_neighborhood_sizes or (cfg.ng_neighborhood_size,))
            ),
            "ng_seed_task_set_count_by_size": pricing.get("ng_seed_task_set_count_by_size") or {},
            "direct_seed_portfolio_enabled": bool(cfg.relaxed_mode),
            "direct_seed_portfolio_status": pricing.get("direct_seed_portfolio_status") or "",
            "direct_seed_portfolio_column_count": pricing.get("direct_seed_portfolio_column_count") or 0,
            "direct_seed_portfolio_negative_column_count": int(
                pricing.get("direct_seed_portfolio_negative_column_count") or 0
            ),
            "direct_seed_portfolio_best_reduced_cost": pricing.get("direct_seed_portfolio_best_reduced_cost"),
            "candidate_round_count": int(pricing.get("candidate_round_count") or 0),
            "sortie_attempt_count": int(pricing.get("sortie_attempt_count") or 0),
            "feasible_sortie_template_count": int(pricing.get("feasible_sortie_template_count") or 0),
            "pareto_label_count": int(pricing.get("pareto_label_count") or 0),
            "worker_pricing_limit_hit": bool(pricing_limit_hit),
            "worker_timeout_stage": str(pricing.get("timeout_stage") or ""),
            "no_column_uncertified": bool(not selected and not pricing_limit_hit),
            "note": (
                "Relaxed/ng-route labeling is a worker candidate generator. All selected "
                "columns are re-audited with the current true RMP dual; no-column is never "
                "a no-negative certificate."
            ),
        }
    )
    payload.pop("_selected_internal", None)
    return payload, selected


def _status_semantics_contract(payload: dict, *, exact_mode: bool) -> dict:
    """Machine-check the BPC_future status/proof separation contract."""

    state = str(payload.get("pricing_state") or PricingState.INCOMPLETE_LIMIT.value)
    proof_kind = str(payload.get("pricing_proof_kind") or PROOF_KIND_NONE)
    can_certify = bool(payload.get("can_certify_no_negative"))
    uses_true_dual = bool(payload.get("uses_true_dual_bpc_certificate"))
    limit_result = _pricing_payload_hit_limit(payload) or state == PricingState.INCOMPLETE_LIMIT.value
    issues: list[str] = []
    if can_certify and state != PricingState.CERTIFIED_NO_NEGATIVE.value:
        issues.append("certifying_payload_requires_certified_no_negative_state")
    if can_certify and proof_kind not in CERTIFYING_PROOF_KINDS:
        issues.append("certifying_payload_requires_certifying_proof_kind")
    if can_certify and not uses_true_dual:
        issues.append("certifying_payload_requires_true_dual")
    if can_certify and not bool(exact_mode):
        issues.append("worker_mode_cannot_certify_no_negative")
    if can_certify and not bool(payload.get("global_remaining_rc_lb_valid")):
        issues.append("certifying_payload_requires_valid_global_remaining_lb")
    if can_certify and bool(payload.get("dual_stabilization_used_for_official_certificate")):
        issues.append("certifying_payload_cannot_use_stabilized_dual")
    official_dual_source = str(payload.get("official_pricing_dual_source") or "current_true_rmp_dual")
    if can_certify and official_dual_source != "current_true_rmp_dual":
        issues.append("certifying_payload_requires_current_true_rmp_dual")
    if limit_result and can_certify:
        issues.append("incomplete_limit_cannot_certify")
    if state == PricingState.LOCAL_NO_COLUMN_UNCERTIFIED.value and can_certify:
        issues.append("local_no_column_uncertified_cannot_certify")
    if proof_kind == PROOF_KIND_RELAXED_WORKER_UNCERTIFIED and can_certify:
        issues.append("relaxed_worker_proof_kind_cannot_certify")
    return {
        "status_semantics_contract_version": STATUS_SEMANTICS_CONTRACT_VERSION,
        "required_pricing_state_vocabulary": [
            PricingState.FOUND_NEGATIVE.value,
            PricingState.LOCAL_NO_COLUMN_UNCERTIFIED.value,
            PricingState.CERTIFIED_NO_NEGATIVE.value,
            PricingState.INCOMPLETE_LIMIT.value,
            "DUPLICATE_ONLY",
        ],
        "only_certifying_pricing_state": PricingState.CERTIFIED_NO_NEGATIVE.value,
        "certifying_pricing_proof_kinds": sorted(CERTIFYING_PROOF_KINDS),
        "worker_no_column_can_certify": bool(
            not exact_mode and state == PricingState.LOCAL_NO_COLUMN_UNCERTIFIED.value and can_certify
        ),
        "limit_result": bool(limit_result),
        "limit_result_can_certify": bool(limit_result and can_certify),
        "worker_mode_certificate_allowed": bool(exact_mode),
        "certificate_semantics_pass": not issues,
        "certificate_semantics_issues": issues,
    }


def _pricing_payload_hit_limit(payload: dict) -> bool:
    status = str(payload.get("status") or "")
    timeout_stage = str(payload.get("timeout_stage") or "")
    return bool(
        "TIME_LIMIT" in status
        or "TIMEOUT" in status
        or bool(timeout_stage)
        or bool(payload.get("pricing_timeout"))
        or bool(payload.get("resource_extension_time_limit_hit"))
        or payload.get("pricing_state") == PricingState.INCOMPLETE_LIMIT.value
    )


def _audit_columns_with_true_dual(
    columns: Iterable[JourneyColumn],
    true_duals: JourneyDuals,
    *,
    branch_context: BranchContext,
    cut_context: CutContext,
    task_set_sources: dict[tuple[str, ...], tuple[str, ...]],
    candidate_search_duals: JourneyDuals | None = None,
    existing_task_sets: Iterable[Iterable[str]] = tuple(),
    support_task_sets: Iterable[Iterable[str]] = tuple(),
    negative_eps: float,
    harvest_target: int,
    support_aware_harvest_enabled: bool = True,
    support_overlap_threshold: float = 0.6,
    max_selected_jaccard: float = 0.5,
    max_selected_containment: float = 0.8,
    weak_replacement_cap: int = 8,
    strong_replacement_threshold: float = -1.0e-4,
) -> dict:
    rows = []
    seen = set()
    duplicate_signature_count = 0
    branch_invalid_count = 0
    cut_hash_column_count = 0
    search_duals = candidate_search_duals or true_duals
    existing_task_set_keys = _normalize_existing_task_sets(existing_task_sets)
    support_task_set_keys = _normalize_existing_task_sets(support_task_sets)
    for column in columns:
        signature = cut_aware_column_signature_from_journey(
            column,
            cut_context=cut_context,
            branch_context=branch_context,
        )
        if signature in seen:
            duplicate_signature_count += 1
            continue
        seen.add(signature)
        if signature.cut_coefficient_vector_hash:
            cut_hash_column_count += 1
        branch_allowed = journey_satisfies_branch_context(column, branch_context)
        if not branch_allowed:
            branch_invalid_count += 1
        rc = manual_journey_reduced_cost(
            column,
            true_duals,
            cut_coefficients=cut_context.coefficients_for(column),
        )
        search_rc = manual_journey_reduced_cost(
            column,
            search_duals,
            cut_coefficients=cut_context.coefficients_for(column),
        )
        task_set = tuple(sorted(str(task_id) for task_id in column.task_set))
        seed_sources, seed_source_match = _sources_for_task_set(task_set, task_set_sources)
        task_set_relation = "replacement" if task_set in existing_task_set_keys else "new_task_set"
        harvest_bucket = _support_aware_harvest_bucket(
            task_set,
            rc,
            existing_task_sets=existing_task_set_keys,
            support_task_sets=support_task_set_keys,
            support_aware=bool(support_aware_harvest_enabled),
            support_overlap_threshold=support_overlap_threshold,
            strong_replacement_threshold=strong_replacement_threshold,
        )
        rows.append(
            {
                "column": column,
                "true_reduced_cost": rc,
                "candidate_search_reduced_cost": search_rc,
                "task_set": task_set,
                "task_count": len(column.task_set),
                "sortie_count": len(column.sorties),
                "objective": round(float(column.objective), 6),
                "is_true_negative": bool(branch_allowed and rc < -abs(float(negative_eps))),
                "is_candidate_search_negative": bool(
                    branch_allowed and search_rc < -abs(float(negative_eps))
                ),
                "is_allowed_by_branch": bool(branch_allowed),
                "seed_sources": seed_sources,
                "seed_source_match": seed_source_match,
                "task_set_relation_to_existing": task_set_relation,
                "task_set_relation_to_support": (
                    "in_current_lp_support"
                    if task_set in support_task_set_keys
                    else "outside_current_lp_support"
                ),
                "task_set_harvest_bucket": harvest_bucket,
                "signature": signature,
                "cut_coefficient_vector_hash": signature.cut_coefficient_vector_hash,
                "branch_signature": signature.branch_signature,
            }
        )
    rows.sort(key=lambda row: (float(row["true_reduced_cost"]), row["task_set"], row["objective"]))
    negative_rows = [row for row in rows if row["is_true_negative"]]
    selected = _select_diverse_negative_rows(
        negative_rows,
        harvest_target=max(1, int(harvest_target)),
        existing_task_sets=existing_task_set_keys,
        support_task_sets=support_task_set_keys,
        support_aware=bool(support_aware_harvest_enabled),
        max_selected_jaccard=max_selected_jaccard,
        max_selected_containment=max_selected_containment,
        weak_replacement_cap=weak_replacement_cap,
    )
    sample_rows = rows[: max(len(selected), min(16, len(rows)))]
    serial_rows = [_serialize_audit_row(row) for row in sample_rows]
    selected_serial_rows = [_serialize_audit_row(row) for row in selected]
    selected_task_sets = [row["task_set"] for row in selected]
    selected_unique_task_sets = set(selected_task_sets)
    selected_new_task_set_count = sum(
        1 for row in selected if row.get("task_set_relation_to_existing") == "new_task_set"
    )
    selected_replacement_task_set_count = sum(
        1 for row in selected if row.get("task_set_relation_to_existing") == "replacement"
    )
    candidate_new_task_set_count = sum(
        1 for row in negative_rows if row.get("task_set_relation_to_existing") == "new_task_set"
    )
    candidate_replacement_task_set_count = sum(
        1 for row in negative_rows if row.get("task_set_relation_to_existing") == "replacement"
    )
    selected_support_changing_count = sum(
        1 for row in selected if row.get("task_set_harvest_bucket") == "support_changing"
    )
    selected_strong_replacement_count = sum(
        1 for row in selected if row.get("task_set_harvest_bucket") == "strong_replacement"
    )
    selected_weak_replacement_count = sum(
        1 for row in selected if row.get("task_set_harvest_bucket") == "weak_replacement"
    )
    candidate_support_changing_count = sum(
        1 for row in negative_rows if row.get("task_set_harvest_bucket") == "support_changing"
    )
    candidate_strong_replacement_count = sum(
        1 for row in negative_rows if row.get("task_set_harvest_bucket") == "strong_replacement"
    )
    candidate_weak_replacement_count = sum(
        1 for row in negative_rows if row.get("task_set_harvest_bucket") == "weak_replacement"
    )
    candidate_search_negative_rows = [row for row in rows if row["is_candidate_search_negative"]]
    candidate_search_negative_true_negative_count = sum(
        1 for row in candidate_search_negative_rows if row["is_true_negative"]
    )
    candidate_search_negative_true_nonnegative_count = (
        len(candidate_search_negative_rows) - candidate_search_negative_true_negative_count
    )
    candidate_search_false_positive_rows = [
        row for row in candidate_search_negative_rows if not row["is_true_negative"]
    ]
    true_negative_candidate_search_nonnegative_count = sum(
        1 for row in negative_rows if not row["is_candidate_search_negative"]
    )
    true_negative_candidate_search_nonnegative_rows = [
        row for row in negative_rows if not row["is_candidate_search_negative"]
    ]
    return {
        "true_audited_column_count": len(rows),
        "true_best_reduced_cost": rows[0]["true_reduced_cost"] if rows else None,
        "candidate_search_best_reduced_cost": (
            min(float(row["candidate_search_reduced_cost"]) for row in rows) if rows else None
        ),
        "true_negative_column_count": len(negative_rows),
        "candidate_search_negative_column_count": len(candidate_search_negative_rows),
        "candidate_search_negative_true_negative_count": candidate_search_negative_true_negative_count,
        "candidate_search_negative_true_nonnegative_count": candidate_search_negative_true_nonnegative_count,
        "true_negative_candidate_search_nonnegative_count": true_negative_candidate_search_nonnegative_count,
        "candidate_search_false_positive_rate": _safe_ratio(
            candidate_search_negative_true_nonnegative_count,
            len(candidate_search_negative_rows),
        ),
        "true_negative_candidate_search_miss_rate": _safe_ratio(
            true_negative_candidate_search_nonnegative_count,
            len(negative_rows),
        ),
        "candidate_search_false_positive_rows": [
            _serialize_audit_row(row) for row in candidate_search_false_positive_rows[:8]
        ],
        "true_negative_candidate_search_miss_rows": [
            _serialize_audit_row(row) for row in true_negative_candidate_search_nonnegative_rows[:8]
        ],
        "candidate_search_dual_matches_true_dual": _duals_match(search_duals, true_duals),
        "candidate_search_rc_recomputed_under_true_dual": True,
        "cut_aware_signature_used": True,
        "cut_aware_signature_cut_hash_column_count": int(cut_hash_column_count),
        "cut_aware_signature_branch_context_active": not branch_context.empty,
        "cut_aware_signature_cut_context_active": not cut_context.empty,
        "true_selected_negative_count": len(selected),
        "selected_negative_task_set_count": len({row["task_set"] for row in selected}),
        "true_dual_reaudit_pass": True,
        "branch_context_audit_pass": branch_invalid_count == 0,
        "branch_invalid_column_count": int(branch_invalid_count),
        "harvest_candidate_negative_count": len(negative_rows),
        "harvest_selected_count": len(selected),
        "harvest_candidate_new_task_set_count": int(candidate_new_task_set_count),
        "harvest_candidate_replacement_task_set_count": int(candidate_replacement_task_set_count),
        "harvest_selected_new_task_set_count": int(selected_new_task_set_count),
        "harvest_selected_replacement_task_set_count": int(selected_replacement_task_set_count),
        "harvest_candidate_support_changing_count": int(candidate_support_changing_count),
        "harvest_candidate_strong_replacement_count": int(candidate_strong_replacement_count),
        "harvest_candidate_weak_replacement_count": int(candidate_weak_replacement_count),
        "harvest_selected_support_changing_count": int(selected_support_changing_count),
        "harvest_selected_strong_replacement_count": int(selected_strong_replacement_count),
        "harvest_selected_weak_replacement_count": int(selected_weak_replacement_count),
        "harvest_selected_distinct_task_set_count": len(selected_unique_task_sets),
        "harvest_selected_duplicate_task_set_count": max(0, len(selected) - len(selected_unique_task_sets)),
        "harvest_existing_master_task_set_count": len(existing_task_set_keys),
        "harvest_support_task_set_count": len(support_task_set_keys),
        "harvest_support_aware_enabled": bool(support_aware_harvest_enabled),
        "harvest_support_overlap_threshold": round(float(support_overlap_threshold), 6),
        "harvest_max_selected_jaccard": round(float(max_selected_jaccard), 6),
        "harvest_max_selected_containment": round(float(max_selected_containment), 6),
        "harvest_weak_replacement_cap": int(weak_replacement_cap),
        "harvest_candidate_seed_source_counts": _seed_source_counts_for_rows(negative_rows),
        "harvest_selected_seed_source_counts": _seed_source_counts_for_rows(selected),
        "harvest_selection_policy": (
            "support_aware_new_then_support_changing_then_strong_replacement_then_capped_weak_replacement"
            if support_aware_harvest_enabled
            else "best_true_rc_first_then_min_overlap_distinct_task_sets_then_replacements"
        ),
        "harvest_rejected_duplicate_count": duplicate_signature_count,
        "harvest_rejected_same_task_set_count": max(
            0,
            len({row["signature"] for row in negative_rows}) - len(selected_unique_task_sets),
        ),
        "harvest_best_true_rc": selected[0]["true_reduced_cost"] if selected else None,
        "harvest_worst_selected_true_rc": selected[-1]["true_reduced_cost"] if selected else None,
        "harvest_avg_pairwise_jaccard": _avg_pairwise_task_set_jaccard(selected_task_sets),
        "harvest_max_pairwise_jaccard": _max_pairwise_task_set_jaccard(selected_task_sets),
        "selected_negative_rows": selected_serial_rows,
        "audit_sample_rows": serial_rows,
        "_selected_internal": selected,
    }


def _serialize_audit_row(row: dict) -> dict:
    return {
        "true_reduced_cost": round(float(row["true_reduced_cost"]), 9),
        "candidate_search_reduced_cost": round(float(row["candidate_search_reduced_cost"]), 9),
        "task_set": list(row["task_set"]),
        "task_count": int(row["task_count"]),
        "sortie_count": int(row["sortie_count"]),
        "objective": row["objective"],
        "is_true_negative": bool(row["is_true_negative"]),
        "is_candidate_search_negative": bool(row["is_candidate_search_negative"]),
        "is_allowed_by_branch": bool(row["is_allowed_by_branch"]),
        "seed_sources": list(row["seed_sources"]),
        "seed_source_match": row["seed_source_match"],
        "task_set_relation_to_existing": str(row.get("task_set_relation_to_existing") or ""),
        "task_set_relation_to_support": str(row.get("task_set_relation_to_support") or ""),
        "task_set_harvest_bucket": str(row.get("task_set_harvest_bucket") or ""),
        "cut_coefficient_vector_hash": str(row["cut_coefficient_vector_hash"]),
        "branch_signature": list(row["branch_signature"]),
        "signature_version": str(row["signature"].version),
    }


def _safe_ratio(numerator: int, denominator: int) -> float | None:
    if int(denominator) <= 0:
        return None
    return round(float(numerator) / float(denominator), 6)


def _elementary_coverage_ledger(
    data: LunarIceData,
    pricing: dict,
    audit: dict,
    *,
    max_exact_tasks: int,
    rc_match: bool,
    negative_eps: float,
    branch_context: BranchContext,
) -> dict:
    task_count = len(data.task_ids)
    expected = _expected_nonempty_subset_count(data, max_exact_tasks=max_exact_tasks)
    expected_by_task_count = _expected_nonempty_subset_count_by_task_count(
        data,
        max_exact_tasks=max_exact_tasks,
    )
    observed_by_task_count = _normalize_count_by_task_count(
        pricing.get("priced_candidate_set_count_by_task_count")
        or pricing.get("candidate_summary_count_by_task_count")
        or {}
    )
    observed = int(sum(observed_by_task_count.values()))
    if not observed:
        observed = int(
            pricing.get("priced_candidate_set_count")
            or pricing.get("candidate_round_count")
            or 0
        )
    pricing_complete = bool(pricing.get("pricing_complete_for_all_task_subsets"))
    branch_context_active = not branch_context.empty
    branch_context_complete = bool(
        pricing.get("pricing_complete_for_branch_context")
        if branch_context_active
        else True
    )
    coverage_complete_by_task_count = {
        key: bool(
            pricing_complete
            and branch_context_complete
            and observed_by_task_count.get(key, 0) == expected_count
        )
        for key, expected_count in expected_by_task_count.items()
    }
    unsupported_task_count_regions = [
        key for key, complete in coverage_complete_by_task_count.items() if not complete
    ]
    if task_count > int(max_exact_tasks):
        unsupported_task_count_regions = ["task_count_exceeds_max_exact_tasks"]
    search_coverage_complete = bool(
        task_count <= int(max_exact_tasks)
        and expected is not None
        and observed == int(expected)
        and pricing_complete
        and branch_context_complete
        and not unsupported_task_count_regions
    )
    global_min_source = str(pricing.get("global_min_reduced_cost_source") or "")
    global_min_scope = str(pricing.get("global_min_reduced_cost_scope") or "")
    global_min_proof_complete = bool(
        pricing.get("global_min_proof_complete")
        if pricing.get("global_min_proof_complete") is not None
        else search_coverage_complete
    )
    if search_coverage_complete and not global_min_proof_complete:
        unsupported_task_count_regions = [
            *unsupported_task_count_regions,
            "global_min_proof_incomplete",
        ]
    coverage_complete = bool(search_coverage_complete and global_min_proof_complete)
    true_best = _as_float_or_none(audit.get("true_best_reduced_cost"))
    lb_valid = bool(
        coverage_complete
        and rc_match
        and true_best is not None
    )
    unsupported = 0 if coverage_complete else max(1, len(unsupported_task_count_regions))
    audited_column_count = int(audit.get("true_audited_column_count") or 0)
    returned_column_semantics = (
        pricing.get("returned_column_semantics")
        or (
            "single_best_column_from_full_space_labeling"
            if bool(pricing.get("full_universe_incremental_label"))
            else "columns_returned_by_pricing_engine"
        )
    )
    can_certify = bool(
        lb_valid
        and int(audit.get("true_negative_column_count") or 0) == 0
        and true_best is not None
        and true_best >= -abs(float(negative_eps))
    )
    return {
        "schema_version": "lunar_ice_bpc.elementary_labeling_coverage_ledger.v2",
        "coverage_scope": (
            "branch_feasible_nonempty_task_subsets_up_to_max_tasks_per_trip"
            if branch_context_active
            else "all_nonempty_task_subsets_up_to_max_tasks_per_trip"
        ),
        "task_count": int(task_count),
        "max_exact_tasks": int(max_exact_tasks),
        "branch_context_active": bool(branch_context_active),
        "branch_decision_count": len(branch_context.pair_decisions),
        "expected_region_count": expected,
        "observed_region_count": int(observed),
        "search_region_count": int(observed),
        "search_region_count_by_task_count": observed_by_task_count,
        "search_region_count_semantics": (
            "pricing search coverage regions; not necessarily returned columns"
        ),
        "search_coverage_complete": bool(search_coverage_complete),
        "returned_column_count": audited_column_count,
        "returned_column_semantics": returned_column_semantics,
        "returned_column_policy": pricing.get("returned_column_policy") or "all_priced_columns",
        "returned_columns_are_complete_universe": bool(
            pricing.get("returned_columns_are_complete_universe")
            if pricing.get("returned_columns_are_complete_universe") is not None
            else not bool(pricing.get("full_universe_incremental_label"))
        ),
        "single_global_min_column_proof": bool(
            pricing.get("returned_column_policy") == "single_global_min_column"
        ),
        "true_dual_audited_column_count": audited_column_count,
        "true_dual_audit_scope": "all columns returned by pricing engine",
        "global_min_proof_complete": bool(global_min_proof_complete),
        "global_min_reduced_cost_source": global_min_source,
        "global_min_reduced_cost_scope": global_min_scope,
        "global_min_proof_requires_true_dual_reaudit": bool(
            pricing.get("global_min_proof_requires_true_dual_reaudit", True)
        ),
        "global_remaining_rc_lb_source": (
            "global_min_column_reaudited_under_true_dual"
            if bool(global_min_source)
            else "returned_columns_reaudited_under_true_dual"
        ),
        "expected_region_count_by_task_count": expected_by_task_count,
        "observed_region_count_by_task_count": observed_by_task_count,
        "coverage_complete_by_task_count": coverage_complete_by_task_count,
        "unsupported_task_count_regions": unsupported_task_count_regions,
        "frontier_region_count": len(expected_by_task_count),
        "coverage_complete": bool(coverage_complete),
        "unsupported_region_count": int(unsupported),
        "pricing_complete_for_all_task_subsets": bool(pricing_complete),
        "pricing_complete_for_branch_context": bool(branch_context_complete),
        "timeout_stage": str(pricing.get("timeout_stage") or ""),
        "rc_audit_match": bool(rc_match),
        "true_negative_column_count": int(audit.get("true_negative_column_count") or 0),
        "global_remaining_rc_lb": true_best if lb_valid else None,
        "global_remaining_rc_lb_valid": bool(lb_valid),
        "can_certify_no_negative": bool(can_certify),
        "note": (
            "Exact elementary branch-feasible resource-label coverage."
            if coverage_complete and branch_context_active
            else "Exact elementary full-subset resource-label coverage."
            if coverage_complete
            else "Coverage incomplete; fail closed for no-negative proof."
        ),
    }


def _completion_bound_support_report(pricing_payload: dict) -> dict:
    completion_bound = pricing_payload.get("completion_bound")
    if not isinstance(completion_bound, dict):
        return {
            "completion_bound_enabled": False,
            "completion_bound_certificate_safe": True,
            "note": "No completion-bound payload was present; no pruning support is needed.",
        }
    enabled = bool(completion_bound.get("enabled"))
    if not enabled:
        return {
            "completion_bound_enabled": False,
            "completion_bound_certificate_safe": True,
            "completion_bound_can_certify_no_negative": bool(
                completion_bound.get("can_certify_no_negative")
            ),
            "note": "Completion-bound pruning is disabled.",
        }
    unsupported_terms = [
        key
        for key in (
            "includes_fleet_dual",
            "includes_cut_duals",
            "includes_branch_duals",
            "includes_legacy_beta_journey_end_time",
        )
        if bool(completion_bound.get(key))
    ]
    safe = bool(
        completion_bound.get("bound_type") == "positive_cover_dual_optimistic_tail"
        and completion_bound.get("pruning_is_exact_safe") is True
        and not bool(completion_bound.get("can_certify_no_negative"))
        and not unsupported_terms
    )
    return {
        "completion_bound_enabled": True,
        "completion_bound_certificate_safe": bool(safe),
        "completion_bound_type": completion_bound.get("bound_type") or "",
        "completion_bound_pruning_is_exact_safe": bool(
            completion_bound.get("pruning_is_exact_safe")
        ),
        "completion_bound_can_certify_no_negative": bool(
            completion_bound.get("can_certify_no_negative")
        ),
        "completion_bound_unsupported_terms": unsupported_terms,
        "note": (
            "Completion-bound pruning is an exact-safe optimistic tail bound and does not certify by itself."
            if safe
            else "Completion-bound pruning is not certificate-safe; fail closed for no-negative proof."
        ),
    }


def _downgrade_ledger_for_unsafe_completion_bound(
    ledger: dict,
    *,
    completion_bound_support: dict,
) -> dict:
    downgraded = dict(ledger)
    unsupported_regions = list(downgraded.get("unsupported_task_count_regions") or [])
    if "completion_bound_certificate_unsafe" not in unsupported_regions:
        unsupported_regions.append("completion_bound_certificate_unsafe")
    downgraded.update(
        {
            "coverage_complete": False,
            "pricing_complete_for_all_task_subsets": False,
            "unsupported_region_count": max(1, int(downgraded.get("unsupported_region_count") or 0)),
            "unsupported_task_count_regions": unsupported_regions,
            "global_remaining_rc_lb": None,
            "global_remaining_rc_lb_valid": False,
            "can_certify_no_negative": False,
            "completion_bound_certificate_safe": False,
            "completion_bound_certificate_support": completion_bound_support,
            "note": "Coverage cannot certify because completion-bound pruning support failed.",
        }
    )
    return downgraded


def _cut_certificate_support_report(
    columns: tuple[JourneyColumn, ...],
    duals: JourneyDuals,
    cut_context: CutContext,
    pricing_payload: dict,
    *,
    negative_eps: float,
) -> dict:
    if cut_context.empty:
        return {
            "cut_context_active": False,
            "cut_count": 0,
            "live_cut_certificate_supported": True,
            "cut_dominance_compatibility": build_cut_dominance_compatibility_report(cut_context),
            "cut_reduced_cost_audit": {},
            "note": "No live cuts are active.",
        }
    dominance = build_cut_dominance_compatibility_report(cut_context)
    rc_audit = audit_cut_reduced_cost_consistency(
        columns,
        duals,
        cut_context,
        pricing_payload,
        negative_eps=negative_eps,
    )
    supported = bool(
        dominance.get("valid")
        and dominance.get("dominance_key_covers_active_cut_coefficients")
        and rc_audit.get("manual_rc_cut_consistency_pass")
        and rc_audit.get("cut_dual_sign_audit_pass")
    )
    return {
        "cut_context_active": True,
        "cut_count": len(cut_context.cuts),
        "live_cut_certificate_supported": bool(supported),
        "cut_dominance_compatibility": dominance,
        "cut_reduced_cost_audit": rc_audit,
        "note": (
            "Live cuts are task-set-only and passed dominance/reduced-cost audits."
            if supported
            else "At least one live cut is not supported for exact no-negative certification."
        ),
    }


def _downgrade_ledger_for_unsupported_live_cuts(
    ledger: dict,
    *,
    cut_context: CutContext,
    cut_certificate_support: dict,
) -> dict:
    downgraded = dict(ledger)
    unsupported_regions = list(downgraded.get("unsupported_task_count_regions") or [])
    if "live_cut_context_unsupported" not in unsupported_regions:
        unsupported_regions.append("live_cut_context_unsupported")
    downgraded.update(
        {
            "coverage_complete": False,
            "pricing_complete_for_all_task_subsets": False,
            "unsupported_region_count": max(1, int(downgraded.get("unsupported_region_count") or 0)),
            "unsupported_task_count_regions": unsupported_regions,
            "global_remaining_rc_lb": None,
            "global_remaining_rc_lb_valid": False,
            "can_certify_no_negative": False,
            "cut_context_active": True,
            "cut_count": len(cut_context.cuts),
            "live_cut_certificate_supported": False,
            "cut_certificate_support": cut_certificate_support,
            "note": (
                "Coverage may be complete for the task-subset search, but live cut no-negative "
                "certification is not enabled; fail closed."
            ),
        }
    )
    return downgraded


def _select_diverse_negative_rows(
    rows: list[dict],
    *,
    harvest_target: int,
    existing_task_sets: Iterable[Iterable[str]] = tuple(),
    support_task_sets: Iterable[Iterable[str]] = tuple(),
    support_aware: bool = True,
    max_selected_jaccard: float = 0.5,
    max_selected_containment: float = 0.8,
    weak_replacement_cap: int = 8,
) -> list[dict]:
    target = max(1, int(harvest_target))
    selected: list[dict] = []
    selected_signatures = set()
    selected_task_sets: set[tuple[str, ...]] = set()
    existing_keys = _normalize_existing_task_sets(existing_task_sets)
    weak_limit = max(0, int(weak_replacement_cap))
    jaccard_limit = max(0.0, min(1.0, float(max_selected_jaccard)))
    containment_limit = max(0.0, min(1.0, float(max_selected_containment)))

    def row_bucket(row: dict) -> str:
        bucket = str(row.get("task_set_harvest_bucket") or "")
        if bucket:
            return bucket
        task_set = tuple(row["task_set"])
        if task_set not in existing_keys:
            return "new_task_set"
        return "weak_replacement" if support_aware else "replacement"

    def bucket_rank(row: dict) -> int:
        if not support_aware:
            return 0
        bucket = row_bucket(row)
        if bucket == "new_task_set":
            return 0
        if bucket == "support_changing":
            return 1
        if bucket == "strong_replacement":
            return 2
        if bucket == "weak_replacement":
            return 3
        return 4

    def weak_replacement_count() -> int:
        return sum(1 for row in selected if row_bucket(row) == "weak_replacement")

    def weak_cap_reached(row: dict) -> bool:
        return bool(
            support_aware
            and row_bucket(row) == "weak_replacement"
            and weak_replacement_count() >= weak_limit
        )

    def diverse_enough(row: dict) -> bool:
        if not selected_task_sets:
            return True
        task_set = tuple(row["task_set"])
        return bool(
            _task_set_overlap_score(task_set, selected_task_sets) <= jaccard_limit
            and _task_set_containment_score(task_set, selected_task_sets) <= containment_limit
        )

    distinct_rows = [
        row
        for row in rows
        if tuple(row["task_set"]) not in selected_task_sets
        and row["signature"] not in selected_signatures
    ]
    while distinct_rows and len(selected) < target:
        if not selected:
            best = min(
                distinct_rows,
                key=lambda row: (
                    bucket_rank(row),
                    float(row["true_reduced_cost"]),
                    len(tuple(row["task_set"])),
                    tuple(row["task_set"]),
                    str(row["signature"]),
                ),
            )
        else:
            preferred_pool = [row for row in distinct_rows if not weak_cap_reached(row)]
            diverse_pool = [row for row in preferred_pool if diverse_enough(row)]
            candidate_pool = diverse_pool or preferred_pool or distinct_rows
            best = min(
                candidate_pool,
                key=lambda row: (
                    bucket_rank(row),
                    _task_set_overlap_score(tuple(row["task_set"]), selected_task_sets),
                    _task_set_containment_score(tuple(row["task_set"]), selected_task_sets),
                    float(row["true_reduced_cost"]),
                    len(tuple(row["task_set"])),
                    tuple(row["task_set"]),
                    str(row["signature"]),
                ),
            )
        selected.append(best)
        selected_task_sets.add(tuple(best["task_set"]))
        selected_signatures.add(best["signature"])
        distinct_rows = [
            row
            for row in distinct_rows
            if tuple(row["task_set"]) not in selected_task_sets
            and row["signature"] not in selected_signatures
        ]
        if len(selected) >= target:
            return selected
    for row in rows:
        signature = row["signature"]
        if signature in selected_signatures:
            continue
        if weak_cap_reached(row):
            continue
        selected.append(row)
        selected_signatures.add(signature)
        selected_task_sets.add(tuple(row["task_set"]))
        if len(selected) >= target:
            return selected
    return selected


def _support_continuation_seed_task_sets(
    data: LunarIceData,
    duals: JourneyDuals,
    *,
    support_task_sets: Iterable[Iterable[str]],
    max_label_task_count: int,
    max_seed_sets: int,
    max_neighbors: int,
    enabled: bool,
) -> tuple[tuple[str, ...], ...]:
    """Generate worker-only support-neighborhood seeds from the current LP support.

    These seeds implement the BPC_future "active-support continuation" lesson:
    when the tail keeps finding true negatives, try task-set add/drop/swap moves
    around the currently positive RMP support before spending the whole budget
    on unrelated neighborhoods.  This remains a candidate-search heuristic; all
    returned columns are still true-dual audited by the caller.
    """

    if not enabled or int(max_seed_sets) <= 0:
        return tuple()
    valid_tasks = {str(task_id) for task_id in data.task_ids}
    task_cap = max(1, min(int(max_label_task_count), int(data.max_tasks_per_trip), len(valid_tasks)))
    support_rows = _dedupe_task_sets(
        tuple(str(task_id) for task_id in row if str(task_id) in valid_tasks)
        for row in (support_task_sets or tuple())
    )
    if not support_rows:
        return tuple()
    max_neighbors = max(1, int(max_neighbors))
    generated: list[tuple[str, ...]] = []
    seen: set[tuple[str, ...]] = set()

    def add(row: Iterable[str]) -> None:
        if len(generated) >= int(max_seed_sets):
            return
        normalized = tuple(sorted({str(task_id) for task_id in row if str(task_id) in valid_tasks}))
        if not normalized or len(normalized) > task_cap or normalized in seen:
            return
        seen.add(normalized)
        generated.append(normalized)

    ranked_support = sorted(
        support_rows,
        key=lambda row: (
            _support_continuation_seed_score(data, duals, row),
            len(row),
            row,
        ),
    )
    for support in ranked_support:
        if len(generated) >= int(max_seed_sets):
            break
        base = tuple(task_id for task_id in support if task_id in valid_tasks)
        if not base:
            continue
        if len(base) > task_cap:
            projections = _support_continuation_project_large_support(
                data,
                duals,
                base,
                task_cap=task_cap,
                max_neighbors=max_neighbors,
            )
            for projection in projections:
                add(projection)
            for projection in projections[:max_neighbors]:
                inside_by_low_dual = sorted(
                    projection,
                    key=lambda task_id: (
                        float(duals.cover.get(task_id, 0.0)),
                        float(data.tasks[task_id].science_weight),
                        task_id,
                    ),
                )
                outside = _support_continuation_ranked_outside_tasks(
                    data,
                    duals,
                    projection,
                    max_neighbors=max_neighbors,
                )
                if len(projection) > 1:
                    for removed in inside_by_low_dual[:max_neighbors]:
                        add(task_id for task_id in projection if task_id != removed)
                for removed in inside_by_low_dual[:max_neighbors]:
                    for task_id in outside:
                        add((*tuple(row for row in projection if row != removed), task_id))
                        if len(generated) >= int(max_seed_sets):
                            break
                    if len(generated) >= int(max_seed_sets):
                        break
            continue
        if len(base) <= task_cap:
            add(base)
        inside_by_low_dual = sorted(
            base,
            key=lambda task_id: (
                float(duals.cover.get(task_id, 0.0)),
                float(data.tasks[task_id].science_weight),
                task_id,
            ),
        )
        outside = _support_continuation_ranked_outside_tasks(
            data,
            duals,
            base,
            max_neighbors=max_neighbors,
        )
        if len(base) > 1:
            for removed in inside_by_low_dual[:max_neighbors]:
                add(task_id for task_id in base if task_id != removed)
        if len(base) < task_cap:
            for task_id in outside:
                add((*base, task_id))
        for removed in inside_by_low_dual[:max_neighbors]:
            for task_id in outside:
                add((*tuple(row for row in base if row != removed), task_id))
                if len(generated) >= int(max_seed_sets):
                    break
            if len(generated) >= int(max_seed_sets):
                break
    return tuple(sorted(generated, key=lambda row: (_support_continuation_seed_score(data, duals, row), len(row), row)))


def _support_continuation_project_large_support(
    data: LunarIceData,
    duals: JourneyDuals,
    support: Iterable[str],
    *,
    task_cap: int,
    max_neighbors: int,
) -> tuple[tuple[str, ...], ...]:
    """Project an over-cap RMP support column into worker-sized neighborhoods."""

    base = tuple(str(task_id) for task_id in support)
    cap = max(1, min(int(task_cap), len(base)))
    if len(base) <= cap:
        return (tuple(sorted(base)),)
    ranked_by_dual = sorted(
        base,
        key=lambda task_id: (
            -float(duals.cover.get(task_id, 0.0)),
            -float(data.tasks[task_id].science_weight),
            task_id,
        ),
    )
    projected: list[tuple[str, ...]] = []
    seen: set[tuple[str, ...]] = set()

    def add(row: Iterable[str]) -> None:
        normalized = tuple(sorted({str(task_id) for task_id in row}))
        if not normalized or len(normalized) > cap or normalized in seen:
            return
        seen.add(normalized)
        projected.append(normalized)

    add(ranked_by_dual[:cap])
    for anchor in ranked_by_dual[: max(1, int(max_neighbors))]:
        nearest = sorted(
            (task_id for task_id in base if task_id != anchor),
            key=lambda task_id: (
                _task_xy_distance(data, anchor, task_id),
                -float(duals.cover.get(task_id, 0.0)),
                -float(data.tasks[task_id].science_weight),
                task_id,
            ),
        )
        add((anchor, *nearest[: max(0, cap - 1)]))
    return tuple(projected)


def _support_continuation_ranked_outside_tasks(
    data: LunarIceData,
    duals: JourneyDuals,
    base: Iterable[str],
    *,
    max_neighbors: int,
) -> tuple[str, ...]:
    base_row = tuple(str(task_id) for task_id in base)
    base_set = set(base_row)
    candidates = [str(task_id) for task_id in data.task_ids if str(task_id) not in base_set]
    ranked = sorted(
        candidates,
        key=lambda task_id: (
            -float(duals.cover.get(task_id, 0.0)),
            _min_distance_to_task_set(data, task_id, base_row),
            -float(data.tasks[task_id].science_weight),
            task_id,
        ),
    )
    return tuple(ranked[: max(1, int(max_neighbors))])


def _support_continuation_seed_score(
    data: LunarIceData,
    duals: JourneyDuals,
    task_set: Iterable[str],
) -> tuple[float, float]:
    row = tuple(str(task_id) for task_id in task_set)
    dual_gain = sum(float(duals.cover.get(task_id, 0.0)) for task_id in row)
    compactness = _task_set_mean_nearest_distance(data, row)
    return (-round(float(dual_gain), 9), round(float(compactness), 9))


def _support_continuation_seed_source_rows(
    seed_task_sets: Iterable[Iterable[str]],
) -> tuple[dict, ...]:
    return tuple(
        {
            "task_set": list(row),
            "sources": ["support_continuation"],
        }
        for row in _dedupe_task_sets(seed_task_sets)
    )


def _dedupe_task_sets(rows: Iterable[Iterable[str]]) -> tuple[tuple[str, ...], ...]:
    result: list[tuple[str, ...]] = []
    seen: set[tuple[str, ...]] = set()
    for row in rows or tuple():
        normalized = tuple(sorted({str(task_id) for task_id in row if str(task_id)}))
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return tuple(result)


def _count_seed_intersection(left: Iterable[Iterable[str]], right: Iterable[Iterable[str]]) -> int:
    left_set = set(_dedupe_task_sets(left))
    return sum(1 for row in _dedupe_task_sets(right) if row in left_set)


def _task_set_mean_nearest_distance(data: LunarIceData, task_set: Iterable[str]) -> float:
    row = tuple(str(task_id) for task_id in task_set)
    if len(row) < 2:
        return 0.0
    values = [
        _min_distance_to_task_set(
            data,
            task_id,
            tuple(other for other in row if other != task_id),
        )
        for task_id in row
    ]
    return sum(values) / max(1, len(values))


def _min_distance_to_task_set(
    data: LunarIceData,
    task_id: str,
    task_set: Iterable[str],
) -> float:
    candidates = tuple(str(other) for other in task_set if str(other) != str(task_id))
    if not candidates:
        return 0.0
    return min(_task_xy_distance(data, task_id, other) for other in candidates)


def _task_xy_distance(data: LunarIceData, left: str, right: str) -> float:
    left_xy = data.tasks[str(left)].xy_km
    right_xy = data.tasks[str(right)].xy_km
    return ((left_xy[0] - right_xy[0]) ** 2 + (left_xy[1] - right_xy[1]) ** 2) ** 0.5


def _task_set_overlap_score(
    task_set: tuple[str, ...],
    selected_task_sets: set[tuple[str, ...]],
) -> float:
    if not selected_task_sets:
        return 0.0
    candidate = set(task_set)
    if not candidate:
        return 0.0
    return max(
        (
            len(candidate & set(selected)) / len(candidate | set(selected))
            for selected in selected_task_sets
            if candidate | set(selected)
        ),
        default=0.0,
    )


def _task_set_containment_score(
    task_set: tuple[str, ...],
    selected_task_sets: set[tuple[str, ...]],
) -> float:
    if not selected_task_sets:
        return 0.0
    candidate = set(task_set)
    if not candidate:
        return 0.0
    return max(
        (
            len(candidate & set(selected)) / max(1, min(len(candidate), len(set(selected))))
            for selected in selected_task_sets
            if selected
        ),
        default=0.0,
    )


def _support_aware_harvest_bucket(
    task_set: tuple[str, ...],
    true_reduced_cost: float,
    *,
    existing_task_sets: set[tuple[str, ...]],
    support_task_sets: set[tuple[str, ...]],
    support_aware: bool,
    support_overlap_threshold: float,
    strong_replacement_threshold: float,
) -> str:
    if task_set not in existing_task_sets:
        return "new_task_set"
    if not support_aware:
        return "replacement"
    if support_task_sets and _max_task_set_jaccard(task_set, support_task_sets) <= float(
        support_overlap_threshold
    ):
        return "support_changing"
    if float(true_reduced_cost) <= float(strong_replacement_threshold):
        return "strong_replacement"
    return "weak_replacement"


def _max_task_set_jaccard(
    task_set: tuple[str, ...],
    other_task_sets: set[tuple[str, ...]],
) -> float:
    if not other_task_sets:
        return 0.0
    candidate = set(task_set)
    if not candidate:
        return 0.0
    return max(
        (
            len(candidate & set(other)) / len(candidate | set(other))
            for other in other_task_sets
            if candidate | set(other)
        ),
        default=0.0,
    )


def _normalize_existing_task_sets(task_sets: Iterable[Iterable[str]]) -> set[tuple[str, ...]]:
    normalized: set[tuple[str, ...]] = set()
    for task_set in task_sets or tuple():
        row = tuple(sorted(str(task_id) for task_id in task_set))
        if row:
            normalized.add(row)
    return normalized


def _avg_pairwise_task_set_jaccard(task_sets: list[tuple[str, ...]]) -> float | None:
    if len(task_sets) < 2:
        return None
    values: list[float] = []
    sets = [set(row) for row in task_sets]
    for left_index, left in enumerate(sets):
        for right in sets[left_index + 1 :]:
            union = left | right
            if not union:
                continue
            values.append(len(left & right) / len(union))
    if not values:
        return None
    return round(sum(values) / len(values), 6)


def _max_pairwise_task_set_jaccard(task_sets: list[tuple[str, ...]]) -> float | None:
    if len(task_sets) < 2:
        return None
    values: list[float] = []
    sets = [set(row) for row in task_sets]
    for left_index, left in enumerate(sets):
        for right in sets[left_index + 1 :]:
            union = left | right
            if not union:
                continue
            values.append(len(left & right) / len(union))
    if not values:
        return None
    return round(max(values), 6)


def _seed_source_lookup(rows: Iterable[dict]) -> dict[tuple[str, ...], tuple[str, ...]]:
    lookup: dict[tuple[str, ...], tuple[str, ...]] = {}
    for row in rows:
        task_set = tuple(sorted(str(task_id) for task_id in row.get("task_set") or ()))
        if not task_set:
            continue
        sources = tuple(str(source) for source in row.get("sources") or ("unknown",))
        lookup[task_set] = sources
    return lookup


def _sources_for_task_set(
    task_set: tuple[str, ...],
    lookup: dict[tuple[str, ...], tuple[str, ...]],
) -> tuple[tuple[str, ...], str]:
    if not lookup:
        return ("unknown",), "none"
    normalized = tuple(sorted(str(task_id) for task_id in task_set))
    exact = lookup.get(normalized)
    if exact:
        return exact, "exact"
    task_lookup = set(normalized)
    sources: set[str] = set()
    for seed_task_set, seed_sources in lookup.items():
        if task_lookup.issubset(set(seed_task_set)):
            sources.update(seed_sources)
    if sources:
        return tuple(sorted(sources)), "subset"
    return ("unknown",), "none"


def _seed_source_counts_for_rows(rows: Iterable[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        for source in row.get("seed_sources") or ("unknown",):
            source_key = str(source)
            counts[source_key] = counts.get(source_key, 0) + 1
    return dict(sorted(counts.items()))


def _duals_match(left: JourneyDuals, right: JourneyDuals, *, eps: float = 1.0e-9) -> bool:
    task_ids = set(left.cover) | set(right.cover)
    if any(abs(float(left.cover.get(task_id, 0.0)) - float(right.cover.get(task_id, 0.0))) > eps for task_id in task_ids):
        return False
    if abs(float(left.fleet_limit) - float(right.fleet_limit)) > eps:
        return False
    left_cuts = left.cuts or {}
    right_cuts = right.cuts or {}
    cut_ids = set(left_cuts) | set(right_cuts)
    return not any(abs(float(left_cuts.get(cut_id, 0.0)) - float(right_cuts.get(cut_id, 0.0))) > eps for cut_id in cut_ids)


def _expected_nonempty_subset_count(data: LunarIceData, *, max_exact_tasks: int) -> int | None:
    expected_by_task_count = _expected_nonempty_subset_count_by_task_count(
        data,
        max_exact_tasks=max_exact_tasks,
    )
    if not expected_by_task_count and len(data.task_ids) > int(max_exact_tasks):
        return None
    return int(sum(expected_by_task_count.values()))


def _expected_nonempty_subset_count_by_task_count(
    data: LunarIceData,
    *,
    max_exact_tasks: int,
) -> dict[str, int]:
    task_count = len(data.task_ids)
    if task_count > int(max_exact_tasks):
        return {}
    limit = min(task_count, int(data.max_tasks_per_trip))
    return {
        str(size): int(_comb(task_count, size))
        for size in range(1, limit + 1)
    }


def _normalize_count_by_task_count(value: object) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    normalized: dict[str, int] = {}
    for key, raw_count in value.items():
        try:
            task_count_key = str(int(key))
            count = int(raw_count)
        except (TypeError, ValueError):
            continue
        normalized[task_count_key] = max(0, count)
    return dict(sorted(normalized.items(), key=lambda item: int(item[0])))


def _comb(n: int, k: int) -> int:
    if k < 0 or k > n:
        return 0
    k = min(k, n - k)
    result = 1
    for i in range(1, k + 1):
        result = result * (n - k + i) // i
    return result


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


def _as_float_or_none(value: object) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _rc_values_match(left: float | None, right: float | None, *, eps: float = 1.0e-6) -> bool:
    if left is None or right is None:
        return left is None and right is None
    return abs(float(left) - float(right)) <= float(eps)
