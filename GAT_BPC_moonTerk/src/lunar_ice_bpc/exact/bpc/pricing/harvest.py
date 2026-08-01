"""B2 addability-aware harvesting."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from time import perf_counter
from typing import Any, Iterable, Mapping, Sequence

from lunar_ice_bpc.exact.bpc.core.column_pool import BpcColumn, ColumnPool
from lunar_ice_bpc.exact.bpc.core.column_signature import column_signature_from_journey
from lunar_ice_bpc.exact.bpc.cuts.cut_audit import cut_aware_column_signature_from_journey
from lunar_ice_bpc.exact.bpc.core.master_column_view import MasterColumnView
from lunar_ice_bpc.exact.bpc.pricing.profiling import PruningCounter
from lunar_ice_bpc.exact.bpc.guidance.contracts import (
    PricingOrderingHintsV2,
    canonical_harvest_candidate_id,
    canonical_universe_hash,
)
from lunar_ice_bpc.exact.core.branching import BranchContext, journey_satisfies_branch_context
from lunar_ice_bpc.exact.core.cuts import CutContext
from lunar_ice_bpc.exact.core.cuts import stable_payload_hash, true_dual_binding_hash
from lunar_ice_bpc.exact.core.data import LunarIceData
from lunar_ice_bpc.exact.core.journey import JourneyColumn
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals
from lunar_ice_bpc.exact.master.journey_rmp import (
    manual_journey_reduced_cost,
)


@dataclass(frozen=True)
class HarvestCandidateReport:
    candidate_id: str
    signature: object
    true_reduced_cost: float
    task_set: tuple[str, ...]
    is_negative: bool
    would_enter_master: bool
    addability_reason: str
    reject_reason: str
    pool_contains_signature: bool
    current_master_contains_signature: bool
    is_forbidden_signature: bool
    is_allowed_by_branch: bool
    is_allowed_by_cut_context: bool
    would_change_active_support: bool


@dataclass
class DeferredHarvestBuffer:
    """Node-local exact-safe storage for micro-batch admission.

    Entries omitted by an admission budget remain available and are repriced
    against the next true-dual context.  This buffer changes only when a legal
    column enters the master; it never authorizes permanent guidance filtering.
    """

    columns_by_candidate_id: dict[str, JourneyColumn]
    offered_count: int = 0
    activated_count: int = 0

    def __init__(self) -> None:
        self.columns_by_candidate_id = {}
        self.offered_count = 0
        self.activated_count = 0

    def repriced_candidates(
        self,
        *,
        duals: JourneyDuals,
        cut_context: CutContext,
    ) -> tuple[tuple[float, JourneyColumn], ...]:
        return tuple(
            (
                float(
                    manual_journey_reduced_cost(
                        column,
                        duals,
                        cut_coefficients=cut_context.coefficients_for(
                            column
                        ),
                    )
                ),
                column,
            )
            for _, column in sorted(
                self.columns_by_candidate_id.items()
            )
        )

    def offer(
        self, candidate_id: str, column: JourneyColumn
    ) -> None:
        if candidate_id not in self.columns_by_candidate_id:
            self.offered_count += 1
        self.columns_by_candidate_id[candidate_id] = column

    def mark_activated(self, candidate_ids: Iterable[str]) -> None:
        for candidate_id in candidate_ids:
            if self.columns_by_candidate_id.pop(
                str(candidate_id), None
            ) is not None:
                self.activated_count += 1

    @property
    def size(self) -> int:
        return len(self.columns_by_candidate_id)


def harvest_addable_negative_columns(
    candidates: Iterable[tuple[float, JourneyColumn]],
    *,
    pool: ColumnPool,
    view: MasterColumnView,
    node_id: str = "root",
    negative_eps: float = 1.0e-6,
    max_selected: int = 64,
    forbidden_signatures: set | None = None,
    active_task_sets: set[frozenset[str]] | None = None,
    branch_context: BranchContext | None = None,
    cut_context: CutContext | None = None,
    profiling: PruningCounter | None = None,
    source_phase: str = "addability_harvest",
    guidance_hints: PricingOrderingHintsV2 | None = None,
    canonical_binding_hash: str = "",
    guidance_enabled: bool = False,
    guidance_data: LunarIceData | None = None,
    guidance_duals: JourneyDuals | None = None,
    guidance_wall_time_limit_sec: float | None = None,
    guidance_memory_limit_gb: float = 0.0,
    guidance_rmp_iteration_id: str = "",
    guidance_cut_lineage_hash: str = "",
    guidance_live_cut_policy_hash: str = "",
    guidance_separator_policy_version: str = "",
    deferred_buffer: DeferredHarvestBuffer | None = None,
    micro_batch_size: int | None = None,
    one_deviation_candidate_id: str | None = None,
    one_deviation_allowed: bool = False,
    one_deviation_root_already_used: bool = False,
    one_deviation_memory_adverse_event: bool = False,
    counterfactual_state: Mapping[str, Any] | None = None,
    observation_only: bool = False,
    preserve_input_candidate_order: bool = False,
    p0_selected_candidate_ids_override: Sequence[str] | None = None,
    p0_override_is_exact_baseline: bool = False,
) -> tuple[tuple[JourneyColumn, ...], dict]:
    """Select true-RC negative candidates that can actually enter the master."""

    counter = profiling or PruningCounter()
    start = perf_counter()
    cuts = cut_context or CutContext()
    reports: list[HarvestCandidateReport] = []
    active_task_set_lookup = {
        frozenset(str(task_id) for task_id in row)
        for row in (active_task_sets or set())
    }
    addable: list[
        tuple[bool, float, tuple[str, ...], JourneyColumn, str]
    ] = []
    guidance_requested = bool(guidance_enabled)
    guidance_requested_mode = "harvest" if guidance_enabled else "off"
    guidance_runtime_telemetry: dict = {}
    guidance_runtime_diagnostics: dict = {}
    guidance_request = None
    candidate_columns: dict[str, JourneyColumn] = {}
    seen_signatures: set[object] = set()
    duplicate_signature_count = 0
    forbidden_count = 0
    branch_filtered_count = 0
    cut_filtered_count = 0
    duplicate_in_current_master_count = 0
    in_pool_not_master_count = 0
    dominance_filtered_count = 0
    negative_count = 0
    fresh_candidate_pairs = list(candidates)
    candidate_pairs = list(fresh_candidate_pairs)
    deferred_count_before = (
        0 if deferred_buffer is None else deferred_buffer.size
    )
    deferred_repriced_count = 0
    if deferred_buffer is not None:
        if guidance_duals is None:
            raise ValueError(
                "deferred harvest repricing requires current true duals"
            )
        deferred_pairs = deferred_buffer.repriced_candidates(
            duals=guidance_duals,
            cut_context=cuts,
        )
        deferred_repriced_count = len(deferred_pairs)
        merged_pairs: dict[
            str, tuple[float, JourneyColumn]
        ] = {}
        for true_rc, column in (
            *deferred_pairs,
            *fresh_candidate_pairs,
        ):
            signature = _column_signature_for_harvest(
                column,
                branch_context=branch_context,
                cut_context=cuts,
            )
            merged_pairs[
                canonical_harvest_candidate_id(signature)
            ] = (float(true_rc), column)
        candidate_pairs = list(merged_pairs.values())
    for true_rc, column in candidate_pairs:
        signature = _column_signature_for_harvest(
            column,
            branch_context=branch_context,
            cut_context=cuts,
        )
        candidate_id = canonical_harvest_candidate_id(signature)
        candidate_columns.setdefault(candidate_id, column)
        task_set = tuple(sorted(str(task_id) for task_id in column.task_set))
        is_negative = float(true_rc) < -abs(float(negative_eps))
        if not is_negative:
            continue
        negative_count += 1
        duplicate_candidate_signature = signature in seen_signatures
        if duplicate_candidate_signature:
            duplicate_signature_count += 1
        seen_signatures.add(signature)
        branch_allowed = journey_satisfies_branch_context(column, branch_context)
        bpc_column = BpcColumn(signature=signature, objective=column.objective, payload=column)
        report = pool.addability_check(
            bpc_column,
            {
                "master_view": view,
                "node_id": node_id,
                "forbidden_signatures": forbidden_signatures or set(),
                "active_task_sets": active_task_sets or set(),
                "is_allowed_by_branch": branch_allowed,
                "cut_coefficients": cuts.coefficients_for(column),
                "branch_signature": getattr(signature, "branch_signature", tuple()),
                "dominance_key": _column_dominance_key_for_harvest(signature),
            },
        )
        if report.is_forbidden_signature:
            forbidden_count += 1
        if not report.is_allowed_by_branch:
            branch_filtered_count += 1
        if not report.is_allowed_by_cut_context:
            cut_filtered_count += 1
        if not report.would_change_active_support:
            dominance_filtered_count += 1
        if report.current_master_contains_signature:
            duplicate_in_current_master_count += 1
        if report.pool_contains_signature and not report.current_master_contains_signature:
            in_pool_not_master_count += 1
        if report.pool_contains_signature or report.current_master_contains_signature:
            duplicate_signature_count += 1
        would_enter_master = bool(report.would_enter_master and not duplicate_candidate_signature)
        if would_enter_master:
            addable.append(
                (
                    report.would_change_active_support,
                    float(true_rc),
                    task_set,
                    column,
                    candidate_id,
                )
            )
        reports.append(
            HarvestCandidateReport(
                candidate_id=candidate_id,
                signature=signature,
                # Preserve the audited value used by the strict negative-eps
                # decision.  Rounding here could turn a legal
                # ``rc < -eps`` candidate into exactly ``-eps`` in the
                # replay snapshot and falsely invalidate opportunity data.
                true_reduced_cost=float(true_rc),
                task_set=task_set,
                is_negative=True,
                would_enter_master=would_enter_master,
                addability_reason="duplicate_candidate_signature" if duplicate_candidate_signature else report.reason,
                reject_reason="duplicate_candidate_signature" if duplicate_candidate_signature else report.reject_reason,
                pool_contains_signature=report.pool_contains_signature,
                current_master_contains_signature=report.current_master_contains_signature,
                is_forbidden_signature=report.is_forbidden_signature,
                is_allowed_by_branch=report.is_allowed_by_branch,
                is_allowed_by_cut_context=report.is_allowed_by_cut_context,
                would_change_active_support=report.would_change_active_support,
            )
        )
    if (
        guidance_hints is None
        and guidance_data is not None
        and guidance_duals is not None
        and (
            (
                bool(
                    str(
                        os.getenv(
                            "LUNAR_ICE_GAT_DEPLOYMENT_MANIFEST", ""
                        )
                    ).strip()
                )
                and bool(
                    str(
                        os.getenv("LUNAR_ICE_GAT_GUIDANCE_MODE", "")
                    ).strip()
                )
            )
            or bool(
                str(
                    os.getenv("LUNAR_ICE_GAT_TRAINING_ROWS_DIR", "")
                ).strip()
            )
            or bool(
                str(
                    os.getenv("LUNAR_ICE_ONE_DEVIATION_MANIFEST", "")
                ).strip()
            )
        )
    ):
        try:
            from lunar_ice_bpc.guidance.runtime import (
                prepare_guidance_request_from_environment,
            )

            guidance_request = _build_harvest_guidance_request(
                guidance_data,
                guidance_duals,
                node_id=node_id,
                source_phase=source_phase,
                negative_eps=negative_eps,
                max_selected=max_selected,
                branch_context=branch_context,
                cut_context=cuts,
                wall_time_limit_sec=guidance_wall_time_limit_sec,
                memory_limit_gb=guidance_memory_limit_gb,
                rmp_iteration_id=guidance_rmp_iteration_id,
                cut_lineage_hash=guidance_cut_lineage_hash,
                live_cut_policy_hash=guidance_live_cut_policy_hash,
                separator_policy_version=guidance_separator_policy_version,
            )
            prepared = prepare_guidance_request_from_environment(
                guidance_request,
                stage="harvest",
                harvest_candidates=(
                    {
                        "candidate_id": row[4],
                        "task_ids": row[2],
                        "context": (
                            float(row[1]),
                            1.0 if row[0] else 0.0,
                            (
                                0.0
                                if frozenset(row[2])
                                in active_task_set_lookup
                                else 1.0
                            ),
                            len(row[2])
                            / max(1.0, float(guidance_data.scale)),
                        ),
                    }
                    for row in addable
                ),
            )
            if prepared is not None:
                guidance_requested = True
                guidance_requested_mode = prepared.decision.requested_mode
                guidance_runtime_telemetry = dict(prepared.telemetry)
                guidance_runtime_diagnostics = dict(prepared.diagnostics)
                guidance_hints = prepared.request.guidance_hints
                if guidance_hints is not None:
                    from lunar_ice_bpc.exact.bpc.guidance.contracts import (
                        CanonicalSolveBindingV2,
                    )

                    canonical_binding_hash = (
                        CanonicalSolveBindingV2.from_backend_request(
                            prepared.request
                        ).binding_hash
                    )
        except Exception as exc:
            guidance_requested = True
            guidance_runtime_diagnostics = {
                "guidance_fallback_to_p0": True,
                "reason": "harvest_runtime_hook_failed",
                "error": repr(exc),
            }
    guidance_binding_match = bool(
        guidance_hints is not None
        and canonical_binding_hash
        and guidance_hints.binding_hash == canonical_binding_hash
        and not guidance_hints.ood
        and not guidance_hints.diagnostic_only
        and guidance_hints.queue_policy_id == "Q0"
    )
    guidance_effective = bool(guidance_requested and guidance_binding_match)
    harvest_priorities: Mapping[str, float] = (
        guidance_hints.priorities_for("harvest")
        if guidance_effective and guidance_hints is not None
        else {}
    )
    selection_limit = max_selected
    if micro_batch_size is not None:
        selection_limit = min(
            int(max_selected), max(1, int(micro_batch_size))
        )
    p0_selected_rows = _select_harvest_rows(
        addable,
        active_task_set_lookup=active_task_set_lookup,
        max_selected=selection_limit,
        priorities={},
        guidance_enabled=False,
    )
    p0_ordered_rows = (
        list(addable)
        if preserve_input_candidate_order
        else _select_harvest_rows(
            addable,
            active_task_set_lookup=active_task_set_lookup,
            max_selected=len(addable),
            priorities={},
            guidance_enabled=False,
        )
    )
    if p0_selected_candidate_ids_override is not None:
        row_by_id = {
            str(row[4]): row for row in p0_ordered_rows
        }
        requested_ids = tuple(
            str(candidate_id)
            for candidate_id in p0_selected_candidate_ids_override
        )
        p0_selected_rows = [
            row_by_id[candidate_id]
            for candidate_id in requested_ids
            if candidate_id in row_by_id
        ]
        if preserve_input_candidate_order:
            selected_id_set = {
                str(row[4]) for row in p0_selected_rows
            }
            p0_ordered_rows = [
                *p0_selected_rows,
                *(
                    row
                    for row in p0_ordered_rows
                    if str(row[4]) not in selected_id_set
                ),
            ]
    one_deviation_runtime_diagnostics: dict = {}
    if (
        not observation_only
        and one_deviation_candidate_id is None
        and str(node_id) == "root"
        and guidance_request is not None
        and bool(
            str(
                os.getenv("LUNAR_ICE_ONE_DEVIATION_MANIFEST", "")
            ).strip()
        )
    ):
        try:
            from lunar_ice_bpc.guidance.one_deviation_runtime import (
                infer_one_deviation_from_environment,
            )

            runtime_decision, one_deviation_runtime_diagnostics = (
                infer_one_deviation_from_environment(
                    request=guidance_request,
                    ordered_candidates=tuple(
                        {
                            "candidate_id": str(row[4]),
                            "task_ids": tuple(row[2]),
                            "context": (
                                float(row[1]),
                                1.0 if row[0] else 0.0,
                                (
                                    0.0
                                    if frozenset(row[2])
                                    in active_task_set_lookup
                                    else 1.0
                                ),
                                len(row[2])
                                / max(
                                    1.0,
                                    float(guidance_request.data.scale),
                                ),
                            ),
                        }
                        for row in p0_ordered_rows
                    ),
                    batch_size=selection_limit,
                    root_key=(
                        f"{guidance_request.data.instance_content_hash}:"
                        f"{node_id}"
                    ),
                    adverse_memory_event=bool(
                        one_deviation_memory_adverse_event
                    ),
                )
            )
            if runtime_decision.promotes:
                one_deviation_candidate_id = (
                    runtime_decision.promoted_candidate_id
                )
                one_deviation_allowed = True
            # The one-deviation product path is mutually exclusive with the
            # historical arbitrary harvest-priority guidance.
            guidance_effective = False
            harvest_priorities = {}
        except Exception as exc:
            one_deviation_runtime_diagnostics = {
                "one_deviation_fallback_to_noop": True,
                "one_deviation_runtime_error": repr(exc),
            }
    selected_rows = (
        list(p0_selected_rows)
        if observation_only or p0_override_is_exact_baseline
        else _select_harvest_rows(
            addable,
            active_task_set_lookup=active_task_set_lookup,
            max_selected=selection_limit,
            priorities=harvest_priorities,
            guidance_enabled=guidance_effective,
        )
    )
    one_deviation_requested = bool(
        one_deviation_allowed and one_deviation_candidate_id
    )
    one_deviation_executed = False
    one_deviation_reject_reason = ""
    if one_deviation_requested:
        ordered_by_id = {
            str(row[4]): (rank, row)
            for rank, row in enumerate(p0_ordered_rows, start=1)
        }
        promoted = ordered_by_id.get(
            str(one_deviation_candidate_id)
        )
        if str(node_id) != "root":
            one_deviation_reject_reason = "non_root_context"
        elif one_deviation_root_already_used:
            one_deviation_reject_reason = (
                "root_intervention_already_consumed"
            )
        elif promoted is None:
            one_deviation_reject_reason = (
                "candidate_not_in_audited_addable_universe"
            )
        elif not (
            selection_limit + 1
            <= promoted[0]
            <= selection_limit + 32
        ):
            one_deviation_reject_reason = (
                "candidate_outside_rank_k_plus_1_to_k_plus_32"
            )
        elif not p0_selected_rows:
            one_deviation_reject_reason = "empty_p0_batch"
        else:
            selected_rows = list(p0_selected_rows)
            selected_rows[-1] = promoted[1]
            one_deviation_executed = True
    selected = (
        tuple()
        if observation_only
        else tuple(row[3] for row in selected_rows)
    )
    selected_candidate_ids = tuple(str(row[4]) for row in selected_rows)
    p0_selected_candidate_ids = tuple(
        str(row[4]) for row in p0_selected_rows
    )
    guidance_order_changed = bool(
        guidance_effective
        and selected_candidate_ids != p0_selected_candidate_ids
    )
    guidance_admission_set_changed = bool(
        guidance_effective
        and set(selected_candidate_ids) != set(p0_selected_candidate_ids)
    )
    guidance_admission_set_symmetric_difference_count = len(
        set(selected_candidate_ids).symmetric_difference(
            p0_selected_candidate_ids
        )
    )
    deferred_offered_this_call = 0
    if deferred_buffer is not None:
        deferred_buffer.mark_activated(
            report.candidate_id
            for report in reports
            if report.current_master_contains_signature
        )
        for row in addable:
            candidate_id = str(row[4])
            size_before = deferred_buffer.size
            deferred_buffer.offer(candidate_id, row[3])
            deferred_offered_this_call += int(
                deferred_buffer.size > size_before
            )
    promoted_candidate_id = (
        None
        if not harvest_priorities
        else min(
            harvest_priorities,
            key=lambda candidate_id: (
                -float(harvest_priorities[candidate_id]),
                str(candidate_id),
            ),
        )
    )
    actual_execution_rank = (
        None
        if promoted_candidate_id not in selected_candidate_ids
        else selected_candidate_ids.index(promoted_candidate_id) + 1
    )
    promotion_requested = promoted_candidate_id is not None
    promotion_installed = bool(
        promotion_requested
        and guidance_binding_match
        and promoted_candidate_id in {str(row[4]) for row in addable}
    )
    promotion_executed = bool(
        promotion_installed and actual_execution_rank is not None
    )
    if not promotion_requested:
        treatment_compliance = "p0_noop"
        noncompliance_reason = ""
    elif not guidance_admission_set_changed:
        treatment_compliance = "installed_but_behaviorally_equivalent"
        noncompliance_reason = (
            "promotion_did_not_change_admitted_route_set"
        )
    elif actual_execution_rank == 1:
        treatment_compliance = "compliant"
        noncompliance_reason = ""
    elif promotion_executed:
        treatment_compliance = "executed_but_not_first"
        noncompliance_reason = (
            "harvest_new_task_set_partition_preceded_promoted_route"
        )
    else:
        treatment_compliance = "not_executed"
        noncompliance_reason = (
            "promotion_not_selected_within_harvest_budget"
        )
    selected_task_sets = tuple(row[2] for row in selected_rows)
    selected_new_task_set_count, selected_replacement_task_set_count = _selected_task_set_counts(
        selected_rows,
        active_task_set_lookup=active_task_set_lookup,
    )
    selected_true_rc_values = tuple(float(row[1]) for row in selected_rows)
    legal_universe_hash = canonical_universe_hash(
        (row[4] for row in addable),
        universe_kind="addable_harvest",
    )
    counter.candidate_addability_time += perf_counter() - start
    counter.candidate_duplicate_count += int(duplicate_signature_count)
    counter.candidate_addable_count += len(addable)
    payload = {
        "schema_version": "lunar_ice_bpc.b2_harvest.v1",
        "harvest_source_phase": str(source_phase),
        "cut_context_active": not cuts.empty,
        "cut_count": len(cuts.cuts),
        "candidate_negative_count": int(negative_count),
        "addable_negative_count": len(addable),
        "duplicate_in_current_master_count": int(duplicate_in_current_master_count),
        "in_pool_not_master_count": int(in_pool_not_master_count),
        "forbidden_signature_count": int(forbidden_count),
        "branch_filtered_count": int(branch_filtered_count),
        "cut_filtered_count": int(cut_filtered_count),
        "selected_count": len(selected),
        "selected_would_enter_master_count": len(selected),
        "selected_all_would_enter_master": True,
        "harvest_candidate_negative_count": int(negative_count),
        "harvest_addable_candidate_count": len(addable),
        "harvest_selected_count": len(selected),
        "harvest_selected_new_task_set_count": int(selected_new_task_set_count),
        "harvest_selected_replacement_task_set_count": int(selected_replacement_task_set_count),
        "harvest_rejected_duplicate_count": int(duplicate_signature_count),
        "harvest_rejected_not_addable_count": max(0, int(negative_count) - len(addable)),
        "harvest_best_true_rc": None if not selected_true_rc_values else round(float(min(selected_true_rc_values)), 9),
        "harvest_worst_selected_true_rc": None if not selected_true_rc_values else round(float(max(selected_true_rc_values)), 9),
        "harvest_avg_pairwise_jaccard": _avg_pairwise_jaccard(selected_task_sets),
        "harvest_priority": "prefer_new_task_set_then_true_rc_then_replacements",
        "guidance_mode": guidance_requested_mode,
        "guidance_requested": guidance_requested,
        "guidance_effective": guidance_effective,
        "guidance_binding_match": guidance_binding_match,
        "guidance_fallback_to_p0": bool(
            guidance_requested and not guidance_effective
        ),
        "p0_noop_available": bool(
            guidance_runtime_diagnostics.get(
                "p0_noop_available",
                True,
            )
        ),
        "p0_noop_score": guidance_runtime_diagnostics.get(
            "p0_noop_score"
        ),
        "learned_action_selected": guidance_runtime_diagnostics.get(
            "learned_action_selected"
        ),
        "abstained_to_p0": bool(
            guidance_runtime_diagnostics.get(
                "abstained_to_p0",
                not promotion_requested,
            )
        ),
        "abstention_reason": str(
            guidance_runtime_diagnostics.get("abstention_reason") or ""
        ),
        "promotion_requested": promotion_requested,
        "promotion_candidate_id": promoted_candidate_id,
        "promotion_installed": promotion_installed,
        "promotion_executed": promotion_executed,
        "actual_execution_rank": actual_execution_rank,
        "first_effective_action_id": (
            None
            if not selected_candidate_ids
            else selected_candidate_ids[0]
        ),
        "treatment_compliance": treatment_compliance,
        "noncompliance_reason": noncompliance_reason,
        "selected_candidate_ids_in_execution_order": list(
            selected_candidate_ids
        ),
        "p0_selected_candidate_ids_in_execution_order": list(
            p0_selected_candidate_ids
        ),
        "guidance_order_changed": guidance_order_changed,
        "guidance_admission_set_changed": (
            guidance_admission_set_changed
        ),
        "guidance_admission_set_symmetric_difference_count": (
            guidance_admission_set_symmetric_difference_count
        ),
        "route_admission_treatment_effective": bool(
            promotion_requested and guidance_admission_set_changed
        ),
        "one_deviation_requested": one_deviation_requested,
        "one_deviation_executed": one_deviation_executed,
        "one_deviation_candidate_id": (
            None
            if one_deviation_candidate_id is None
            else str(one_deviation_candidate_id)
        ),
        "one_deviation_reject_reason": one_deviation_reject_reason,
        "one_deviation_intervention_count_this_root": int(
            one_deviation_executed
        ),
        "one_deviation_next_round_policy": (
            "restore_frozen_exact_p0_order"
        ),
        "one_deviation_runtime": one_deviation_runtime_diagnostics,
        "route_admission_structural_zero": bool(
            len(addable) <= selection_limit
        ),
        "route_admission_structural_zero_reason": (
            "all_addable_routes_fit_p0_admission_budget"
            if len(addable) <= selection_limit
            else ""
        ),
        "observation_only": bool(observation_only),
        "preserve_input_candidate_order": bool(
            preserve_input_candidate_order
        ),
        "p0_override_is_exact_baseline": bool(
            p0_override_is_exact_baseline
        ),
        "legal_action_universe_hash_before_sort": legal_universe_hash,
        "legal_action_universe_hash_after_sort": legal_universe_hash,
        "guidance_filter_count": 0,
        "guidance_arc_drop_count": 0,
        "guidance_label_drop_count": 0,
        "guidance_branch_pair_drop_count": 0,
        "guidance_missing_harvest_hint_count": sum(
            1 for row in addable if row[4] not in harvest_priorities
        ),
        "selection_budget_omitted_count": max(0, len(addable) - len(selected)),
        "micro_batch_enabled": micro_batch_size is not None,
        "micro_batch_admission_limit": (
            None if micro_batch_size is None else selection_limit
        ),
        "deferred_buffer_count_before": deferred_count_before,
        "deferred_repriced_count": deferred_repriced_count,
        "deferred_offered_this_call": deferred_offered_this_call,
        "deferred_buffer_count_after": (
            0 if deferred_buffer is None else deferred_buffer.size
        ),
        "deferred_permanent_drop_count": 0,
        "deferred_reprice_policy": (
            "current_true_dual_before_each_admission"
            if deferred_buffer is not None
            else "disabled"
        ),
        "harvest_duplicate_signature_count": int(duplicate_signature_count),
        "harvest_forbidden_signature_count": int(forbidden_count),
        "harvest_branch_filtered_count": int(branch_filtered_count),
        "harvest_cut_filtered_count": int(cut_filtered_count),
        "harvest_duplicate_in_current_master_count": int(duplicate_in_current_master_count),
        "harvest_in_pool_not_master_count": int(in_pool_not_master_count),
        "harvest_dominance_filtered_count": int(dominance_filtered_count),
        "reports": [
            {
                "candidate_id": report.candidate_id,
                "true_reduced_cost": report.true_reduced_cost,
                "task_set": list(report.task_set),
                "would_enter_master": report.would_enter_master,
                "addability_reason": report.addability_reason,
                "reject_reason": report.reject_reason,
                "pool_contains_signature": report.pool_contains_signature,
                "current_master_contains_signature": report.current_master_contains_signature,
                "is_forbidden_signature": report.is_forbidden_signature,
                "is_allowed_by_branch": report.is_allowed_by_branch,
                "is_allowed_by_cut_context": report.is_allowed_by_cut_context,
                "would_change_active_support": report.would_change_active_support,
            }
            for report in reports
        ],
        "guidance_lifecycle": guidance_runtime_telemetry,
        "guidance_diagnostics": guidance_runtime_diagnostics,
        "profiling": counter.to_payload(),
    }
    training_recording = _maybe_record_harvest_training_rows(
        request=guidance_request,
        reports=reports,
        candidate_columns=candidate_columns,
        active_task_set_lookup=active_task_set_lookup,
        source_phase=source_phase,
        node_id=node_id,
        p0_selected_candidate_ids=p0_selected_candidate_ids,
        p0_ordered_candidate_ids=tuple(
            str(row[4]) for row in p0_ordered_rows
        ),
        selected_candidate_ids=selected_candidate_ids,
        selection_limit=selection_limit,
        pool=pool,
        view=view,
        counterfactual_state=counterfactual_state,
    )
    if training_recording:
        payload["guidance_training_recording"] = training_recording
    return selected, payload


def _build_harvest_guidance_request(
    data: LunarIceData,
    duals: JourneyDuals,
    *,
    node_id: str,
    source_phase: str,
    negative_eps: float,
    max_selected: int,
    branch_context: BranchContext | None,
    cut_context: CutContext,
    wall_time_limit_sec: float | None,
    memory_limit_gb: float,
    rmp_iteration_id: str,
    cut_lineage_hash: str,
    live_cut_policy_hash: str,
    separator_policy_version: str,
):
    """Create the exact request whose serializer owns the harvest binding."""

    from lunar_ice_bpc.exact.bpc.pricing.backends.base import (
        BACKEND_MODE_NEGATIVE_HARVEST,
        BackendPricingRequest,
    )
    from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import (
        spprc_engine_build_hash,
    )

    branch = branch_context or BranchContext()
    backend_id = str(
        os.getenv("LUNAR_ICE_SPPRC_EXACT_BACKEND", "native_rcspp_inprocess")
    )
    config_hash = stable_payload_hash(
        {
            "schema_version": "lunar_ice_bpc.harvest_guidance_config.v1",
            "source_phase": str(source_phase),
            "negative_eps": float(negative_eps),
            "max_selected": int(max_selected),
            "backend_id": backend_id,
        }
    )
    return BackendPricingRequest(
        data=data,
        true_duals=duals,
        mode=BACKEND_MODE_NEGATIVE_HARVEST,
        branch_context=branch,
        cut_context=cut_context,
        harvest_target=max(1, int(max_selected)),
        wall_time_limit_sec=wall_time_limit_sec,
        memory_limit_gb=max(0.0, float(memory_limit_gb)),
        negative_eps=negative_eps,
        instance_hash=data.instance_content_hash,
        config_hash=config_hash,
        engine_hash=spprc_engine_build_hash(backend_id),
        dual_binding_hash=true_dual_binding_hash(
            duals.cover,
            fleet_limit=duals.fleet_limit,
            cuts=duals.cuts,
        ),
        branch_context_hash=stable_payload_hash(branch.to_payload()),
        cut_context_hash=cut_context.active_cut_context_hash,
        cut_lineage_hash=str(cut_lineage_hash),
        live_cut_policy_hash=str(live_cut_policy_hash),
        rmp_iteration_id=(
            str(rmp_iteration_id)
            or f"harvest:{node_id}:{source_phase}"
        ),
        separator_policy_version=str(separator_policy_version),
    )


def _maybe_record_harvest_training_rows(
    *,
    request,
    reports: list[HarvestCandidateReport],
    candidate_columns: dict[str, JourneyColumn],
    active_task_set_lookup: set[frozenset[str]],
    source_phase: str,
    node_id: str,
    p0_selected_candidate_ids: tuple[str, ...],
    p0_ordered_candidate_ids: tuple[str, ...],
    selected_candidate_ids: tuple[str, ...],
    selection_limit: int,
    pool: ColumnPool,
    view: MasterColumnView,
    counterfactual_state: Mapping[str, Any] | None,
) -> dict:
    root_value = str(
        os.getenv("LUNAR_ICE_GAT_TRAINING_ROWS_DIR", "")
    ).strip()
    if not root_value or request is None or not reports:
        return {}
    try:
        from math import log1p

        from lunar_ice_bpc.exact.bpc.guidance.contracts import (
            CanonicalSolveBindingV2,
            canonical_arc_candidate_id,
        )
        from lunar_ice_bpc.guidance.tensorization import (
            build_static_graph_features,
            dynamic_node_features,
        )
        from lunar_ice_bpc.exact.core.objective import OBJECTIVE_SPEC_ID
        from lunar_ice_bpc.guidance.route_admission import (
            build_route_admission_snapshot,
        )

        binding = CanonicalSolveBindingV2.from_backend_request(request)
        static = build_static_graph_features(request.data)
        dynamic = dynamic_node_features(request)
        node_index = {
            node_id: index
            for index, node_id in enumerate(static.node_ids)
        }
        task_grade = {task_id: 0.0 for task_id in request.data.task_ids}
        task_observed = {
            task_id: False for task_id in request.data.task_ids
        }
        arc_grade = {
            candidate_id: 0.0
            for candidate_id in static.arc_candidate_ids
        }
        arc_observed = {
            candidate_id: False
            for candidate_id in static.arc_candidate_ids
        }
        harvest_masks = []
        harvest_context = []
        harvest_grades = []
        harvest_candidate_ids = []
        label_counts = {
            "addable_negative": 0,
            "duplicate_negative": 0,
            "invalid_negative": 0,
        }
        for report in reports:
            harvest_candidate_ids.append(str(report.candidate_id))
            if report.would_enter_master:
                grade = 3.0
                label = "addable_negative"
            elif (
                report.pool_contains_signature
                or report.current_master_contains_signature
                or "duplicate" in report.reject_reason
            ):
                grade = 1.0
                label = "duplicate_negative"
            else:
                grade = 0.0
                label = "invalid_negative"
            label_counts[label] += 1
            mask = [0.0] * len(static.node_ids)
            for task_id in report.task_set:
                mask[node_index[task_id]] = 1.0
            harvest_masks.append(mask)
            harvest_context.append(
                [
                    float(report.true_reduced_cost),
                    1.0 if report.would_change_active_support else 0.0,
                    (
                        0.0
                        if frozenset(report.task_set)
                        in active_task_set_lookup
                        else 1.0
                    ),
                    len(report.task_set)
                    / max(1.0, float(request.data.scale)),
                ]
            )
            harvest_grades.append(grade)
            column = candidate_columns.get(report.candidate_id)
            if column is None:
                continue
            for task_id in column.task_set:
                task_observed[str(task_id)] = True
                task_grade[str(task_id)] = max(
                    task_grade[str(task_id)], grade
                )
            for sortie in column.sorties:
                for leg in sortie.legs:
                    candidate_id = canonical_arc_candidate_id(
                        leg.source, leg.target, leg.path_type
                    )
                    arc_observed[candidate_id] = True
                    arc_grade[candidate_id] = max(
                        arc_grade[candidate_id], grade
                    )
        base = {
            "schema_version": (
                "lunar_ice_bpc.gat_harvest_training_row.v1"
            ),
            "scale": request.data.scale,
            "instance_content_hash": request.data.instance_content_hash,
            "node_phase": binding.phase,
            "rmp_context_hash": binding.binding_hash,
            "canonical_solve_binding": binding.to_payload(),
            "executed_objective_spec_id": OBJECTIVE_SPEC_ID,
            "candidate_id": "context",
            "source_phase": str(source_phase),
            "node_id": str(node_id),
            "node_features": [
                list(static_row) + list(dynamic_row)
                for static_row, dynamic_row in zip(
                    static.node_features, dynamic, strict=True
                )
            ],
            "edge_features": [
                list(values) for values in static.arc_features
            ],
            "edge_index": [
                list(static.arc_sources),
                list(static.arc_targets),
            ],
            "task_node_indices": list(range(1, len(static.node_ids))),
            "resource_context": [
                log1p(
                    max(0.0, request.memory_limit_gb) * (1024.0**3)
                ),
                log1p(
                    0.0
                    if request.wall_time_limit_sec is None
                    else max(0.0, request.wall_time_limit_sec)
                ),
                0.0,
                0.0,
            ],
        }
        rows = [
            {
                **base,
                "head": "exact_pricing",
                "task_grades": [
                    task_grade[task_id] for task_id in request.data.task_ids
                ],
                "task_candidate_ids": list(request.data.task_ids),
                "task_observed_mask": [
                    task_observed[task_id]
                    for task_id in request.data.task_ids
                ],
                "arc_grades": [
                    arc_grade[candidate_id]
                    for candidate_id in static.arc_candidate_ids
                ],
                "arc_candidate_ids": list(static.arc_candidate_ids),
                "arc_observed_mask": [
                    arc_observed[candidate_id]
                    for candidate_id in static.arc_candidate_ids
                ],
            },
            {
                **base,
                "schema_version": (
                    "lunar_ice_bpc.gat_harvest_training_row.v2"
                ),
                "head": "harvest",
                "harvest_context_schema": [
                    "true_reduced_cost",
                    "would_change_active_support",
                    "is_new_task_set",
                    "task_fraction",
                ],
                "harvest_task_masks": harvest_masks,
                "harvest_context": harvest_context,
                "harvest_grades": harvest_grades,
                "harvest_candidate_ids": harvest_candidate_ids,
                "harvest_p0_selected_candidate_ids": list(
                    p0_selected_candidate_ids
                ),
                "harvest_selected_candidate_ids": list(
                    selected_candidate_ids
                ),
                "harvest_selection_limit": int(selection_limit),
                "harvest_addable_candidate_count": int(
                    label_counts["addable_negative"]
                ),
                "harvest_selection_budget_omitted_count": max(
                    0,
                    int(label_counts["addable_negative"])
                    - int(selection_limit),
                ),
                "route_admission_structural_zero": bool(
                    int(label_counts["addable_negative"])
                    <= int(selection_limit)
                ),
            },
        ]
        output_dir = (
            Path(root_value)
            / request.data.instance_content_hash
            / binding.binding_hash
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        snapshot = None
        route_admission_boundary_active = bool(
            int(label_counts["addable_negative"])
            >= int(selection_limit) + 8
            and len(p0_selected_candidate_ids)
            == int(selection_limit)
        )
        route_admission_snapshot_eligible = bool(
            route_admission_boundary_active
            and str(binding.objective_mode) == "official"
        )
        if route_admission_snapshot_eligible:
            report_by_id = {
                str(report.candidate_id): report
                for report in reports
                if report.would_enter_master
            }
            candidate_rows = []
            for candidate_id in p0_ordered_candidate_ids:
                report = report_by_id.get(str(candidate_id))
                column = candidate_columns.get(str(candidate_id))
                if report is None or column is None:
                    raise ValueError(
                        "active route-admission boundary lacks a candidate "
                        "column payload"
                    )
                candidate_rows.append(
                    {
                        "candidate_id": str(candidate_id),
                        "true_reduced_cost": float(
                            report.true_reduced_cost
                        ),
                        "task_set": list(report.task_set),
                        "would_change_active_support": bool(
                            report.would_change_active_support
                        ),
                        "column_payload": column.to_solution_payload(
                            vehicle_id=(
                                "route_admission_candidate_"
                                f"{len(candidate_rows):06d}"
                            )
                        ),
                    }
                )
            active_column_payloads = []
            for signature in sorted(
                view.signatures_by_node.get(str(node_id), set()),
                key=repr,
            ):
                stored = pool.get(signature)
                column = None if stored is None else stored.payload
                if not isinstance(column, JourneyColumn):
                    raise ValueError(
                        "active route-admission RMP lacks a JourneyColumn "
                        "payload"
                    )
                active_column_payloads.append(
                    column.to_solution_payload(
                        vehicle_id=(
                            "route_admission_active_"
                            f"{len(active_column_payloads):06d}"
                        )
                    )
                )
            snapshot = build_route_admission_snapshot(
                canonical_solve_binding=binding.to_payload(),
                instance_content_hash=request.data.instance_content_hash,
                scale=request.data.scale,
                node_id=node_id,
                candidate_rows=candidate_rows,
                p0_ordered_candidate_ids=p0_ordered_candidate_ids,
                p0_selected_candidate_ids=p0_selected_candidate_ids,
                selection_limit=selection_limit,
                active_column_payloads=active_column_payloads,
                branch_context=request.branch_context.to_payload(),
                full_cut_context=request.cut_context.to_payload(),
                source_phase=source_phase,
                executed_objective_spec_id=OBJECTIVE_SPEC_ID,
                live_cut_policy_hash=request.live_cut_policy_hash,
                separator_policy_version=(
                    request.separator_policy_version
                ),
                candidate_pool_audit_complete=True,
                true_rc_audit_complete=True,
                remaining_solve_budget_sec=(
                    request.wall_time_limit_sec
                ),
                remaining_budget_observation_stage=(
                    "post_candidate_generation_pre_admission"
                ),
                memory_limit_gb=float(request.memory_limit_gb),
                counterfactual_state=counterfactual_state,
            )
        paths = []
        for row in rows:
            target = output_dir / f"{row['head']}.json"
            target.write_text(
                json.dumps(
                    row,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n",
                encoding="utf-8",
            )
            paths.append(str(target.resolve()))
        if snapshot is not None:
            snapshot_target = output_dir / "route_admission_snapshot.json"
            snapshot_target.write_text(
                json.dumps(
                    snapshot,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n",
                encoding="utf-8",
            )
            paths.append(str(snapshot_target.resolve()))
        return {
            "written": True,
            "paths": paths,
            "label_counts": label_counts,
            "route_admission_boundary_active": (
                route_admission_boundary_active
            ),
            "route_admission_snapshot_written": snapshot is not None,
            "route_admission_snapshot_skip_reason": (
                ""
                if snapshot is not None
                else (
                    "structural_zero_no_active_admission_boundary"
                    if not route_admission_boundary_active
                    else "nonofficial_rmp_objective_mode"
                )
            ),
            "unexplored_candidates_used_as_negative": False,
        }
    except Exception as exc:
        return {
            "written": False,
            "error": repr(exc),
            "unexplored_candidates_used_as_negative": False,
        }


def _column_signature_for_harvest(
    column: JourneyColumn,
    *,
    branch_context: BranchContext | None = None,
    cut_context: CutContext | None = None,
):
    context = cut_context or CutContext()
    if context.empty and (branch_context is None or branch_context.empty):
        return column_signature_from_journey(column)
    return cut_aware_column_signature_from_journey(
        column,
        cut_context=context,
        branch_context=branch_context,
    )


def _column_dominance_key_for_harvest(signature) -> tuple:
    key = tuple(signature.task_set)
    if getattr(signature, "branch_signature", tuple()) or getattr(
        signature,
        "cut_coefficient_vector_hash",
        "",
    ):
        return (
            tuple(signature.task_set),
            tuple(getattr(signature, "branch_signature", tuple())),
            str(getattr(signature, "cut_coefficient_vector_hash", "")),
        )
    return key


def _avg_pairwise_jaccard(task_sets: tuple[tuple[str, ...], ...]) -> float | None:
    if len(task_sets) < 2:
        return None
    total = 0.0
    count = 0
    for left_index, left in enumerate(task_sets):
        left_set = set(left)
        for right in task_sets[left_index + 1 :]:
            right_set = set(right)
            union = left_set | right_set
            total += 1.0 if not union else len(left_set & right_set) / len(union)
            count += 1
    return None if count == 0 else round(float(total / count), 9)


def _select_harvest_rows(
    rows: list[
        tuple[bool, float, tuple[str, ...], JourneyColumn, str]
    ],
    *,
    active_task_set_lookup: set[frozenset[str]],
    max_selected: int,
    priorities: Mapping[str, float] | None = None,
    guidance_enabled: bool = False,
) -> tuple[
    tuple[bool, float, tuple[str, ...], JourneyColumn, str], ...
]:
    limit = max(0, int(max_selected))
    if limit <= 0:
        return tuple()
    priority_lookup = priorities or {}
    ordered = sorted(
        rows,
        key=lambda item: (
            -float(priority_lookup.get(item[4], 0.0))
            if guidance_enabled
            else 0.0,
            item[1],
            item[2],
        ),
    )
    new_rows: list[
        tuple[bool, float, tuple[str, ...], JourneyColumn, str]
    ] = []
    replacement_rows: list[
        tuple[bool, float, tuple[str, ...], JourneyColumn, str]
    ] = []
    selected_new_task_sets: set[frozenset[str]] = set()
    for row in ordered:
        would_change_support, _true_rc, task_set, _column, _candidate_id = row
        key = frozenset(task_set)
        if would_change_support and key not in active_task_set_lookup and key not in selected_new_task_sets:
            new_rows.append(row)
            selected_new_task_sets.add(key)
        else:
            replacement_rows.append(row)
    return tuple((new_rows + replacement_rows)[:limit])


def _selected_task_set_counts(
    rows: tuple[
        tuple[bool, float, tuple[str, ...], JourneyColumn, str], ...
    ],
    *,
    active_task_set_lookup: set[frozenset[str]],
) -> tuple[int, int]:
    selected_new_task_sets: set[frozenset[str]] = set()
    new_count = 0
    replacement_count = 0
    for would_change_support, _true_rc, task_set, _column, _candidate_id in rows:
        key = frozenset(task_set)
        if would_change_support and key not in active_task_set_lookup and key not in selected_new_task_sets:
            new_count += 1
            selected_new_task_sets.add(key)
        else:
            replacement_count += 1
    return new_count, replacement_count
