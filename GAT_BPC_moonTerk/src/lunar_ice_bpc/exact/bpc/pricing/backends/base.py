"""Typed contract shared by Python and native SPPRC backends."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
import os
from typing import Mapping, Protocol

from lunar_ice_bpc.exact.bpc.guidance.contracts import (
    GUIDANCE_MODES,
    GUIDANCE_MODE_OFF,
    PricingOrderingHintsV2,
)
from lunar_ice_bpc.exact.core.branching import BranchContext
from lunar_ice_bpc.exact.core.cuts import (
    CUT_STATE_SCHEMA_VERSION,
    CutContext,
    stable_payload_hash,
)
from lunar_ice_bpc.exact.core.data import LunarIceData
from lunar_ice_bpc.exact.core.journey import JourneyColumn
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals


BACKEND_MODE_NEGATIVE_HARVEST = "negative_harvest"
BACKEND_MODE_EXACT_PROOF = "exact_proof"
BACKEND_MODES = frozenset({BACKEND_MODE_NEGATIVE_HARVEST, BACKEND_MODE_EXACT_PROOF})
BACKEND_OBJECTIVE_OFFICIAL = "official"
BACKEND_OBJECTIVE_PHASE_ONE = "phase_one"
BACKEND_OBJECTIVE_MODES = frozenset(
    {BACKEND_OBJECTIVE_OFFICIAL, BACKEND_OBJECTIVE_PHASE_ONE}
)
PRICING_LIFECYCLE_SCOPE_UNSPECIFIED = "unspecified"
PRICING_LIFECYCLE_SCOPE_ROOT_CG = "root_cg"
PRICING_LIFECYCLE_SCOPE_TREE_NODE = "tree_node"
PRICING_LIFECYCLE_SCOPES = frozenset(
    {
        PRICING_LIFECYCLE_SCOPE_UNSPECIFIED,
        PRICING_LIFECYCLE_SCOPE_ROOT_CG,
        PRICING_LIFECYCLE_SCOPE_TREE_NODE,
    }
)
PROOF_QUEUE_POLICY_Q0 = "Q0"
PROOF_QUEUE_POLICY_QC0 = "QC0"
PROOF_QUEUE_POLICY_QD1 = "QD1"
PROOF_QUEUE_POLICY_QB1 = "QB1"
PROOF_QUEUE_POLICY_QG1 = "QG1"
PROOF_QUEUE_POLICY_QG2 = "QG2"
PROOF_QUEUE_POLICY_QGR1 = "QGR1"
PROOF_QUEUE_POLICIES = frozenset(
    {
        PROOF_QUEUE_POLICY_Q0,
        PROOF_QUEUE_POLICY_QC0,
        PROOF_QUEUE_POLICY_QD1,
        PROOF_QUEUE_POLICY_QB1,
        PROOF_QUEUE_POLICY_QG1,
        PROOF_QUEUE_POLICY_QG2,
        PROOF_QUEUE_POLICY_QGR1,
    }
)
FRONTIER_PROBE_MODE_DISABLED = "disabled"
FRONTIER_PROBE_MODE_COLLECT_FORCE_Q0 = "collect_force_q0"
FRONTIER_PROBE_MODE_FORCE_QD1 = "force_qd1"
FRONTIER_PROBE_MODE_LEARNED = "learned"
FRONTIER_PROBE_MODE_COLLECT_TRIAL = "collect_trial"
FRONTIER_PROBE_MODE_FORCE_TRIAL_CONTINUE = "force_trial_continue"
FRONTIER_PROBE_MODE_FORCE_TRIAL_REVERT = "force_trial_revert"
FRONTIER_PROBE_MODE_LEARNED_AFTER_TRIAL = "learned_after_trial"
FRONTIER_TRIAL_MODES = frozenset(
    {
        FRONTIER_PROBE_MODE_COLLECT_TRIAL,
        FRONTIER_PROBE_MODE_FORCE_TRIAL_CONTINUE,
        FRONTIER_PROBE_MODE_FORCE_TRIAL_REVERT,
        FRONTIER_PROBE_MODE_LEARNED_AFTER_TRIAL,
    }
)
FRONTIER_PROBE_MODES = frozenset(
    {
        FRONTIER_PROBE_MODE_DISABLED,
        FRONTIER_PROBE_MODE_COLLECT_FORCE_Q0,
        FRONTIER_PROBE_MODE_FORCE_QD1,
        FRONTIER_PROBE_MODE_LEARNED,
        *FRONTIER_TRIAL_MODES,
    }
)
FRONTIER_PROBE_BOUNDARY_V7 = 4096
FRONTIER_TEMPORAL_BOUNDARIES_V10 = (4096, 8192, 16384)
FRONTIER_CONTEXT_FEATURE_COUNT_V7 = 28
COUNTERFACTUAL_PREFIX_MODE_DISABLED = "disabled"
COUNTERFACTUAL_PREFIX_MODE_Q0 = "counterfactual_q0_prefix"
COUNTERFACTUAL_PREFIX_MODE_QD1 = "counterfactual_qd1_prefix"
COUNTERFACTUAL_PREFIX_MODES = frozenset(
    {
        COUNTERFACTUAL_PREFIX_MODE_DISABLED,
        COUNTERFACTUAL_PREFIX_MODE_Q0,
        COUNTERFACTUAL_PREFIX_MODE_QD1,
    }
)
COUNTERFACTUAL_PREFIX_BOUNDARY_V8 = 4096
COUNTERFACTUAL_PREFIX_CHECKPOINTS_V8 = (128, 512, 2048)
COUNTERFACTUAL_LABEL_SAMPLE_CAP_V8 = 256
PROOF_QUEUE_EXPERIMENT_ENV = (
    "LUNAR_ICE_EXPERIMENTAL_PROOF_QUEUE_POLICY"
)
PROOF_QUEUE_EXPERIMENT_OFF = "off"
PROOF_QUEUE_EXPERIMENT_SCALE30_QD1 = "scale30_qd1_else_q0"
PROOF_QUEUE_EXPERIMENT_SCALE30_BRANCH_OR_CUT_QD1 = (
    "scale30_branch_or_cut_qd1_else_q0"
)
PROOF_QUEUE_EXPERIMENT_MODES = frozenset(
    {
        PROOF_QUEUE_EXPERIMENT_OFF,
        PROOF_QUEUE_POLICY_QC0,
        PROOF_QUEUE_POLICY_QD1,
        PROOF_QUEUE_EXPERIMENT_SCALE30_QD1,
        PROOF_QUEUE_EXPERIMENT_SCALE30_BRANCH_OR_CUT_QD1,
    }
)
DSSR_POLICY_VERSION_V1 = "multi_sortie_counterexample_refinement_v1"
DSSR_POLICY_VERSION_V2 = (
    "multi_sortie_counterexample_pressure_refinement_v2"
)
DSSR_POLICY_VERSION_NG_V3 = (
    "multi_sortie_ng_memory_counterexample_refinement_v3"
)
DSSR_POLICY_VERSIONS = frozenset(
    {
        DSSR_POLICY_VERSION_V1,
        DSSR_POLICY_VERSION_V2,
        DSSR_POLICY_VERSION_NG_V3,
    }
)
EXACT_NEGATIVE_ESCAPE_POLICY_V1 = (
    "diverse_raw_4x_then_p0v4_selector_v1"
)


def resolve_experimental_proof_queue_policy(
    *,
    requested_policy_id: str,
    mode: str,
    objective_mode: str,
    scale: int,
    branch_context_active: bool = False,
    cut_context_active: bool = False,
    environment: Mapping[str, str] | None = None,
) -> tuple[str, str]:
    """Resolve one pre-import, exact-only proof queue experiment.

    Explicit request policies always win.  The environment selector exists
    only for matched end-to-end experiments whose ordinary constructors still
    request Q0.  It never affects harvest or Phase-I pricing.
    """

    requested = str(requested_policy_id)
    values = os.environ if environment is None else environment
    selector = str(
        values.get(
            PROOF_QUEUE_EXPERIMENT_ENV,
            PROOF_QUEUE_EXPERIMENT_OFF,
        )
        or PROOF_QUEUE_EXPERIMENT_OFF
    )
    if selector not in PROOF_QUEUE_EXPERIMENT_MODES:
        raise ValueError(
            f"unsupported proof queue experiment {selector!r}"
        )
    if (
        requested != PROOF_QUEUE_POLICY_Q0
        or selector == PROOF_QUEUE_EXPERIMENT_OFF
        or str(mode) != BACKEND_MODE_EXACT_PROOF
        or str(objective_mode) != BACKEND_OBJECTIVE_OFFICIAL
    ):
        return requested, PROOF_QUEUE_EXPERIMENT_OFF
    if selector == PROOF_QUEUE_EXPERIMENT_SCALE30_QD1:
        return (
            PROOF_QUEUE_POLICY_QD1
            if int(scale) == 30
            else PROOF_QUEUE_POLICY_Q0,
            selector,
        )
    if selector == PROOF_QUEUE_EXPERIMENT_SCALE30_BRANCH_OR_CUT_QD1:
        return (
            PROOF_QUEUE_POLICY_QD1
            if int(scale) == 30
            and (
                bool(branch_context_active)
                or bool(cut_context_active)
            )
            else PROOF_QUEUE_POLICY_Q0,
            selector,
        )
    return selector, selector


@dataclass(frozen=True)
class BackendPricingRequest:
    data: LunarIceData
    true_duals: JourneyDuals
    mode: str = BACKEND_MODE_EXACT_PROOF
    objective_mode: str = BACKEND_OBJECTIVE_OFFICIAL
    pricing_lifecycle_scope: str = (
        PRICING_LIFECYCLE_SCOPE_UNSPECIFIED
    )
    branch_context: BranchContext = field(default_factory=BranchContext)
    cut_context: CutContext = field(default_factory=CutContext)
    harvest_target: int = 16
    exact_negative_escape_enabled: bool = False
    exact_admission_batch_size: int = 16
    exact_raw_negative_pool_size: int = 64
    exact_negative_escape_policy_id: str = (
        EXACT_NEGATIVE_ESCAPE_POLICY_V1
    )
    harvest_max_processed_labels: int = 0
    wall_time_limit_sec: float | None = None
    memory_limit_gb: float = 0.0
    negative_eps: float = 1.0e-6
    dominance_eps: float = 1.0e-12
    resource_eps: float = 1.0e-9
    reconstruction_eps: float = 2.0e-6
    completion_bound_enabled: bool = False
    subset_dominance_enabled: bool = False
    proof_queue_policy_id: str = PROOF_QUEUE_POLICY_Q0
    proof_queue_guidance_bucket_width: float = 0.01
    proof_tail_gat_enabled: bool = False
    proof_tail_queue_policy_id: str = PROOF_QUEUE_POLICY_QG2
    proof_tail_label_state_schema_version: str = ""
    proof_tail_gat_manifest_path: str = ""
    proof_tail_label_trace_enabled: bool = False
    proof_tail_label_trace_max_rows: int = 50_000
    proof_tail_label_trace_sampling_mode: str = "prefix_v1"
    proof_tail_label_trace_seed: int = 0
    proof_tail_preference_cap_per_family: int = 12_500
    proof_tail_surface_reservoir_count: int = 3_125
    proof_tail_surface_labels_per_bucket: int = 8
    proof_tail_witness_route_cap: int = 512
    proof_tail_witness_ancestor_cap: int = 25_000
    proof_tail_fallback_context: bool = False
    proof_tail_active_column_count: int | None = None
    proof_tail_active_task_sets: tuple[tuple[str, ...], ...] | None = None
    proof_tail_active_column_signature_hashes: tuple[str, ...] | None = None
    proof_tail_round_index: int | None = None
    proof_tail_previous_proof_wall_sec: float | None = None
    proof_tail_previous_processed_labels: int | None = None
    proof_tail_previous_queue_policy_id: str = ""
    proof_tail_previous_dominance_candidate_checks: int | None = None
    proof_tail_previous_dominance_wall_sec: float | None = None
    proof_tail_previous_max_visited_bucket_size: int | None = None
    proof_tail_dual_delta_l1: float | None = None
    proof_tail_v5_midpoint_wall_sec: float | None = None
    proof_tail_v5_midpoint_reason: str = ""
    proof_tail_frontier_probe_mode: str = FRONTIER_PROBE_MODE_DISABLED
    proof_tail_frontier_probe_boundary: int = FRONTIER_PROBE_BOUNDARY_V7
    proof_tail_frontier_trial_pop_budget: int = 0
    proof_tail_frontier_require_root_cg: bool = True
    proof_tail_frontier_fail_closed_on_ood: bool = True
    proof_tail_frontier_observation_boundaries: tuple[int, ...] = ()
    proof_tail_frontier_context_features: tuple[float, ...] = tuple(
        0.0 for _ in range(FRONTIER_CONTEXT_FEATURE_COUNT_V7)
    )
    proof_tail_frontier_gat_bundle: Mapping[str, object] | None = None
    proof_tail_frontier_manifest_path: str = ""
    proof_tail_frontier_manifest_sha256: str = ""
    proof_tail_frontier_bundle_sha256: str = ""
    proof_tail_counterfactual_prefix_mode: str = (
        COUNTERFACTUAL_PREFIX_MODE_DISABLED
    )
    proof_tail_counterfactual_prefix_boundary: int = (
        COUNTERFACTUAL_PREFIX_BOUNDARY_V8
    )
    proof_tail_counterfactual_rollout_checkpoints: tuple[int, ...] = (
        COUNTERFACTUAL_PREFIX_CHECKPOINTS_V8
    )
    proof_tail_counterfactual_max_rollout_budget: int = 2048
    proof_tail_counterfactual_label_sample_cap: int = (
        COUNTERFACTUAL_LABEL_SAMPLE_CAP_V8
    )
    proof_tail_counterfactual_sampling_seed: int = 0
    proof_tail_counterfactual_telemetry_only: bool = True
    proof_tail_counterfactual_public_routes_forbidden: bool = True
    proof_tail_counterfactual_certificate_forbidden: bool = True
    dssr_enabled: bool = False
    dssr_policy_version: str = ""
    dssr_negative_batch_target: int = 0
    dssr_pressure_refinement_enabled: bool = False
    dssr_pressure_max_bucket_size: int = 8192
    dssr_pressure_max_candidate_checks: int = 200_000_000
    ng_dssr_initial_neighborhood_size: int = 10
    cut_dual_projection_enabled: bool = True
    cut_state_enabled: bool = False
    instance_hash: str = ""
    config_hash: str = ""
    engine_hash: str = ""
    dual_binding_hash: str = ""
    branch_context_hash: str = ""
    cut_context_hash: str = ""
    cut_lineage_hash: str = ""
    live_cut_policy_hash: str = ""
    rmp_iteration_id: str = ""
    cut_state_schema_version: str = CUT_STATE_SCHEMA_VERSION
    separator_policy_version: str = ""
    guidance_mode: str = GUIDANCE_MODE_OFF
    guidance_hints: PricingOrderingHintsV2 | None = None
    guidance_feature_schema_version: str = ""
    guidance_normalization_version: str = ""
    guidance_checkpoint_id: str = ""
    guidance_ood_policy_version: str = ""
    guidance_lifecycle_telemetry: tuple[tuple[str, object], ...] = tuple()

    def __post_init__(self) -> None:
        mode = str(self.mode)
        if mode not in BACKEND_MODES:
            raise ValueError(f"unsupported backend pricing mode {mode!r}")
        object.__setattr__(self, "mode", mode)
        objective_mode = str(self.objective_mode)
        if objective_mode not in BACKEND_OBJECTIVE_MODES:
            raise ValueError(f"unsupported backend objective mode {objective_mode!r}")
        object.__setattr__(self, "objective_mode", objective_mode)
        pricing_lifecycle_scope = str(
            self.pricing_lifecycle_scope
        ).strip().lower()
        if pricing_lifecycle_scope not in PRICING_LIFECYCLE_SCOPES:
            raise ValueError(
                "unsupported pricing_lifecycle_scope "
                f"{pricing_lifecycle_scope!r}"
            )
        object.__setattr__(
            self,
            "pricing_lifecycle_scope",
            pricing_lifecycle_scope,
        )
        object.__setattr__(self, "harvest_target", max(1, int(self.harvest_target)))
        escape_enabled = bool(self.exact_negative_escape_enabled)
        admission_batch_size = int(self.exact_admission_batch_size)
        raw_pool_size = int(self.exact_raw_negative_pool_size)
        escape_policy_id = str(self.exact_negative_escape_policy_id)
        if admission_batch_size <= 0:
            raise ValueError(
                "exact_admission_batch_size must be positive"
            )
        if raw_pool_size < admission_batch_size:
            raise ValueError(
                "exact_raw_negative_pool_size must be at least "
                "exact_admission_batch_size"
            )
        if raw_pool_size > 4096:
            raise ValueError(
                "exact_raw_negative_pool_size cannot exceed 4096"
            )
        if escape_enabled:
            if mode != BACKEND_MODE_EXACT_PROOF:
                raise ValueError(
                    "exact negative escape is available only in exact-proof mode"
                )
            if escape_policy_id != EXACT_NEGATIVE_ESCAPE_POLICY_V1:
                raise ValueError(
                    "unsupported exact_negative_escape_policy_id "
                    f"{escape_policy_id!r}"
                )
        object.__setattr__(
            self, "exact_negative_escape_enabled", escape_enabled
        )
        object.__setattr__(
            self, "exact_admission_batch_size", admission_batch_size
        )
        object.__setattr__(
            self, "exact_raw_negative_pool_size", raw_pool_size
        )
        object.__setattr__(
            self, "exact_negative_escape_policy_id", escape_policy_id
        )
        object.__setattr__(
            self,
            "harvest_max_processed_labels",
            max(0, int(self.harvest_max_processed_labels)),
        )
        if (
            self.mode == BACKEND_MODE_EXACT_PROOF
            and self.harvest_max_processed_labels > 0
        ):
            raise ValueError(
                "harvest processed-label budget cannot truncate exact proof"
            )
        if self.wall_time_limit_sec is not None:
            object.__setattr__(self, "wall_time_limit_sec", max(0.0, float(self.wall_time_limit_sec)))
        object.__setattr__(self, "memory_limit_gb", max(0.0, float(self.memory_limit_gb)))
        object.__setattr__(self, "negative_eps", abs(float(self.negative_eps)))
        object.__setattr__(self, "dominance_eps", abs(float(self.dominance_eps)))
        object.__setattr__(self, "resource_eps", abs(float(self.resource_eps)))
        object.__setattr__(self, "reconstruction_eps", abs(float(self.reconstruction_eps)))
        object.__setattr__(self, "completion_bound_enabled", bool(self.completion_bound_enabled))
        object.__setattr__(self, "subset_dominance_enabled", bool(self.subset_dominance_enabled))
        requested_proof_queue_policy = str(
            self.proof_queue_policy_id
        )
        proof_queue_policy_id, proof_queue_selector = (
            resolve_experimental_proof_queue_policy(
                requested_policy_id=requested_proof_queue_policy,
                mode=mode,
                objective_mode=objective_mode,
                scale=int(self.data.scale),
                branch_context_active=not self.branch_context.empty,
                cut_context_active=not self.cut_context.empty,
            )
        )
        if proof_queue_policy_id not in PROOF_QUEUE_POLICIES:
            raise ValueError(
                f"unsupported proof_queue_policy_id {proof_queue_policy_id!r}"
            )
        if (
            proof_queue_policy_id != PROOF_QUEUE_POLICY_Q0
            and mode != BACKEND_MODE_EXACT_PROOF
        ):
            raise ValueError(
                "non-Q0 proof queue policies are exact-proof diagnostics only"
            )
        if proof_queue_policy_id in {
            PROOF_QUEUE_POLICY_QG2,
            PROOF_QUEUE_POLICY_QGR1,
        }:
            if int(self.data.scale) not in {30, 50}:
                raise ValueError("label-state GAT is restricted to scale30/50")
            if objective_mode != BACKEND_OBJECTIVE_OFFICIAL:
                raise ValueError("label-state GAT requires the official objective")
            if not bool(self.proof_tail_fallback_context):
                raise ValueError("label-state GAT requires a V5 fallback context")
        object.__setattr__(
            self,
            "proof_queue_policy_id",
            proof_queue_policy_id,
        )
        guidance_bucket_width = float(
            self.proof_queue_guidance_bucket_width
        )
        if (
            not isfinite(guidance_bucket_width)
            or guidance_bucket_width <= 0.0
        ):
            raise ValueError(
                "proof_queue_guidance_bucket_width must be finite and positive"
            )
        object.__setattr__(
            self,
            "proof_queue_guidance_bucket_width",
            guidance_bucket_width,
        )
        proof_tail_queue_policy_id = str(
            self.proof_tail_queue_policy_id
        )
        if proof_tail_queue_policy_id not in {
            PROOF_QUEUE_POLICY_QG2,
            PROOF_QUEUE_POLICY_QGR1,
        }:
            raise ValueError("proof-tail GAT action policy must be QG2 or QGR1")
        object.__setattr__(
            self, "proof_tail_queue_policy_id", proof_tail_queue_policy_id
        )
        object.__setattr__(
            self, "proof_tail_gat_enabled", bool(self.proof_tail_gat_enabled)
        )
        object.__setattr__(
            self,
            "proof_tail_label_state_schema_version",
            str(self.proof_tail_label_state_schema_version),
        )
        object.__setattr__(
            self,
            "proof_tail_gat_manifest_path",
            str(self.proof_tail_gat_manifest_path),
        )
        object.__setattr__(
            self,
            "proof_tail_label_trace_enabled",
            bool(self.proof_tail_label_trace_enabled),
        )
        trace_max_rows = int(self.proof_tail_label_trace_max_rows)
        if trace_max_rows <= 0 or trace_max_rows > 100_000:
            raise ValueError(
                "proof_tail_label_trace_max_rows must be in [1, 100000]"
            )
        object.__setattr__(
            self, "proof_tail_label_trace_max_rows", trace_max_rows
        )
        if self.proof_tail_label_trace_enabled and not self.exact_proof_mode:
            raise ValueError(
                "proof-tail label trace is exact-proof development telemetry"
            )
        sampling_mode = str(self.proof_tail_label_trace_sampling_mode)
        if sampling_mode not in {"prefix_v1", "qgr1_stratified_reservoir_v1"}:
            raise ValueError("unsupported proof-tail label trace sampling mode")
        object.__setattr__(
            self, "proof_tail_label_trace_sampling_mode", sampling_mode
        )
        seed = int(self.proof_tail_label_trace_seed)
        if seed < 0 or seed >= 2**64:
            raise ValueError("proof-tail label trace seed must be uint64")
        object.__setattr__(self, "proof_tail_label_trace_seed", seed)
        caps = {
            "proof_tail_preference_cap_per_family": int(
                self.proof_tail_preference_cap_per_family
            ),
            "proof_tail_surface_reservoir_count": int(
                self.proof_tail_surface_reservoir_count
            ),
            "proof_tail_surface_labels_per_bucket": int(
                self.proof_tail_surface_labels_per_bucket
            ),
            "proof_tail_witness_route_cap": int(
                self.proof_tail_witness_route_cap
            ),
            "proof_tail_witness_ancestor_cap": int(
                self.proof_tail_witness_ancestor_cap
            ),
        }
        if any(value <= 0 for value in caps.values()):
            raise ValueError("proof-tail label trace reservoir caps must be positive")
        if caps["proof_tail_surface_labels_per_bucket"] < 2:
            raise ValueError("surface label reservoir must retain at least two labels")
        for name, value in caps.items():
            object.__setattr__(self, name, value)
        object.__setattr__(
            self,
            "proof_tail_fallback_context",
            bool(self.proof_tail_fallback_context),
        )
        if self.proof_tail_active_task_sets is not None:
            legal_tasks = set(self.data.task_ids)
            active_task_sets = tuple(sorted({
                tuple(sorted(str(task_id) for task_id in task_set))
                for task_set in self.proof_tail_active_task_sets
            }))
            if any(
                not task_set or not set(task_set).issubset(legal_tasks)
                for task_set in active_task_sets
            ):
                raise ValueError(
                    "proof_tail_active_task_sets contain an invalid task set"
                )
            object.__setattr__(
                self,
                "proof_tail_active_task_sets",
                active_task_sets,
            )
        if self.proof_tail_active_column_signature_hashes is not None:
            signature_hashes = tuple(sorted({
                str(value).strip().lower()
                for value in self.proof_tail_active_column_signature_hashes
            }))
            if any(
                len(value) != 64
                or any(character not in "0123456789abcdef" for character in value)
                for value in signature_hashes
            ):
                raise ValueError(
                    "proof_tail_active_column_signature_hashes must be SHA-256 hex"
                )
            if (
                self.proof_tail_active_column_count is not None
                and len(signature_hashes) != int(self.proof_tail_active_column_count)
            ):
                raise ValueError(
                    "active signature count must equal proof_tail_active_column_count"
                )
            object.__setattr__(
                self,
                "proof_tail_active_column_signature_hashes",
                signature_hashes,
            )
        for field_name in (
            "proof_tail_active_column_count",
            "proof_tail_round_index",
            "proof_tail_previous_processed_labels",
            "proof_tail_previous_dominance_candidate_checks",
            "proof_tail_previous_max_visited_bucket_size",
        ):
            value = getattr(self, field_name)
            if value is not None:
                value = int(value)
                if value < 0:
                    raise ValueError(f"{field_name} must be non-negative")
                object.__setattr__(self, field_name, value)
        for field_name in (
            "proof_tail_previous_proof_wall_sec",
            "proof_tail_previous_dominance_wall_sec",
            "proof_tail_dual_delta_l1",
            "proof_tail_v5_midpoint_wall_sec",
        ):
            value = getattr(self, field_name)
            if value is not None:
                value = float(value)
                if not isfinite(value) or value < 0.0:
                    raise ValueError(
                        f"{field_name} must be finite and non-negative"
                    )
                object.__setattr__(self, field_name, value)
        previous_queue_policy = str(
            self.proof_tail_previous_queue_policy_id or ""
        )
        if (
            previous_queue_policy
            and previous_queue_policy not in PROOF_QUEUE_POLICIES
        ):
            raise ValueError(
                "proof_tail_previous_queue_policy_id is invalid"
            )
        object.__setattr__(
            self,
            "proof_tail_previous_queue_policy_id",
            previous_queue_policy,
        )
        if previous_queue_policy != PROOF_QUEUE_POLICY_Q0:
            # Previous-arm performance is intervention-dependent.  Keep it
            # out of the next selector input instead of creating a feedback
            # channel that was absent from the Q0-only training corpus.
            for field_name in (
                "proof_tail_previous_proof_wall_sec",
                "proof_tail_previous_processed_labels",
                "proof_tail_previous_dominance_candidate_checks",
                "proof_tail_previous_dominance_wall_sec",
                "proof_tail_previous_max_visited_bucket_size",
            ):
                object.__setattr__(self, field_name, None)
        object.__setattr__(
            self,
            "proof_tail_v5_midpoint_reason",
            str(self.proof_tail_v5_midpoint_reason),
        )
        frontier_mode = str(self.proof_tail_frontier_probe_mode).strip().lower()
        if frontier_mode not in FRONTIER_PROBE_MODES:
            raise ValueError(
                f"unsupported proof-tail frontier probe mode {frontier_mode!r}"
            )
        frontier_boundary = int(self.proof_tail_frontier_probe_boundary)
        observation_boundaries = tuple(
            int(value)
            for value in self.proof_tail_frontier_observation_boundaries
        )
        if observation_boundaries:
            expected_boundaries = tuple(
                value
                for value in FRONTIER_TEMPORAL_BOUNDARIES_V10
                if value <= frontier_boundary
            )
            if (
                frontier_mode == FRONTIER_PROBE_MODE_DISABLED
                or frontier_boundary not in FRONTIER_TEMPORAL_BOUNDARIES_V10
                or observation_boundaries != expected_boundaries
                or observation_boundaries[-1] != frontier_boundary
            ):
                raise ValueError(
                    "temporal frontier observations require an enabled probe "
                    "and the canonical 4096/8192/16384 prefix through the "
                    "decision boundary"
                )
        elif (
            frontier_boundary != FRONTIER_PROBE_BOUNDARY_V7
            and frontier_mode not in FRONTIER_TRIAL_MODES
        ):
            raise ValueError(
                "legacy frontier probe boundary must be exactly 4096"
            )
        frontier_context = tuple(
            float(value) for value in self.proof_tail_frontier_context_features
        )
        if (
            len(frontier_context) != FRONTIER_CONTEXT_FEATURE_COUNT_V7
            or any(not isfinite(value) for value in frontier_context)
        ):
            raise ValueError(
                "V7 frontier context must contain 28 finite features"
            )
        if frontier_mode != FRONTIER_PROBE_MODE_DISABLED:
            if proof_queue_policy_id != PROOF_QUEUE_POLICY_Q0:
                raise ValueError("V7 frontier probe requires literal Q0")
            if mode != BACKEND_MODE_EXACT_PROOF:
                raise ValueError("V7 frontier probe requires exact proof")
            if objective_mode != BACKEND_OBJECTIVE_OFFICIAL:
                raise ValueError("V7 frontier probe requires official objective")
            if int(self.data.scale) not in {30, 50}:
                raise ValueError("V7 frontier probe is restricted to scale30/50")
            if pricing_lifecycle_scope != PRICING_LIFECYCLE_SCOPE_ROOT_CG:
                raise ValueError("V7 frontier probe is root-CG only")
            if not bool(self.proof_tail_fallback_context):
                raise ValueError("V7 frontier probe requires a V5 fallback context")
            if (
                self.guidance_hints is not None
                or str(self.guidance_mode) != GUIDANCE_MODE_OFF
            ):
                raise ValueError("V7 frontier probe cannot combine with guidance")
            if self.dssr_enabled:
                raise ValueError("V7 frontier probe cannot run inside DSSR")
        trial_pop_budget = int(self.proof_tail_frontier_trial_pop_budget)
        if frontier_mode in FRONTIER_TRIAL_MODES:
            expected_boundary = 4096 if int(self.data.scale) == 30 else 16384
            if frontier_boundary != expected_boundary:
                raise ValueError(
                    "temporal trial boundary must be 4096 for scale30 and "
                    "16384 for scale50"
                )
            if trial_pop_budget not in COUNTERFACTUAL_PREFIX_CHECKPOINTS_V8:
                raise ValueError(
                    "temporal trial pop budget must be one of 128/512/2048"
                )
        elif trial_pop_budget != 0:
            raise ValueError(
                "frontier trial pop budget is allowed only in a trial mode"
            )
        bundle = self.proof_tail_frontier_gat_bundle
        if frontier_mode in {
            FRONTIER_PROBE_MODE_LEARNED,
            FRONTIER_PROBE_MODE_LEARNED_AFTER_TRIAL,
        }:
            if not isinstance(bundle, Mapping):
                raise ValueError("learned V7 frontier probe requires a bundle")
            bundle = dict(bundle)
        elif bundle is not None:
            raise ValueError("portable GAT bundle is allowed only in learned mode")
        object.__setattr__(self, "proof_tail_frontier_probe_mode", frontier_mode)
        object.__setattr__(self, "proof_tail_frontier_probe_boundary", frontier_boundary)
        object.__setattr__(
            self, "proof_tail_frontier_trial_pop_budget", trial_pop_budget
        )
        object.__setattr__(
            self,
            "proof_tail_frontier_observation_boundaries",
            observation_boundaries,
        )
        object.__setattr__(self, "proof_tail_frontier_context_features", frontier_context)
        object.__setattr__(self, "proof_tail_frontier_gat_bundle", bundle)
        object.__setattr__(
            self, "proof_tail_frontier_manifest_path",
            str(self.proof_tail_frontier_manifest_path),
        )
        object.__setattr__(
            self, "proof_tail_frontier_manifest_sha256",
            str(self.proof_tail_frontier_manifest_sha256),
        )
        object.__setattr__(
            self, "proof_tail_frontier_bundle_sha256",
            str(self.proof_tail_frontier_bundle_sha256),
        )
        counterfactual_mode = str(
            self.proof_tail_counterfactual_prefix_mode
        ).strip().lower()
        if counterfactual_mode not in COUNTERFACTUAL_PREFIX_MODES:
            raise ValueError(
                "unsupported counterfactual prefix mode "
                f"{counterfactual_mode!r}"
            )
        counterfactual_boundary = int(
            self.proof_tail_counterfactual_prefix_boundary
        )
        checkpoints = tuple(
            int(value)
            for value in self.proof_tail_counterfactual_rollout_checkpoints
        )
        maximum_rollout_budget = int(
            self.proof_tail_counterfactual_max_rollout_budget
        )
        sample_cap = int(
            self.proof_tail_counterfactual_label_sample_cap
        )
        sampling_seed = int(
            self.proof_tail_counterfactual_sampling_seed
        )
        if counterfactual_boundary != COUNTERFACTUAL_PREFIX_BOUNDARY_V8:
            raise ValueError("V8 counterfactual boundary must be exactly 4096")
        if checkpoints != COUNTERFACTUAL_PREFIX_CHECKPOINTS_V8:
            raise ValueError(
                "V8 counterfactual checkpoints must be (128, 512, 2048)"
            )
        if maximum_rollout_budget not in checkpoints:
            raise ValueError(
                "V8 maximum rollout budget must be one of 128/512/2048"
            )
        if sample_cap != COUNTERFACTUAL_LABEL_SAMPLE_CAP_V8:
            raise ValueError("V8 label sample cap must be exactly 256")
        if sampling_seed < 0 or sampling_seed >= 2**64:
            raise ValueError("V8 counterfactual sampling seed must be uint64")
        contract_flags = (
            bool(self.proof_tail_counterfactual_telemetry_only),
            bool(self.proof_tail_counterfactual_public_routes_forbidden),
            bool(self.proof_tail_counterfactual_certificate_forbidden),
        )
        if counterfactual_mode != COUNTERFACTUAL_PREFIX_MODE_DISABLED:
            if frontier_mode != FRONTIER_PROBE_MODE_DISABLED:
                raise ValueError("V8 prefix cannot combine with the V7 probe")
            if proof_queue_policy_id != PROOF_QUEUE_POLICY_Q0:
                raise ValueError("V8 prefix requires literal Q0")
            if mode != BACKEND_MODE_EXACT_PROOF:
                raise ValueError("V8 prefix requires exact-proof trajectory")
            if objective_mode != BACKEND_OBJECTIVE_OFFICIAL:
                raise ValueError("V8 prefix requires the official objective")
            if int(self.data.scale) not in {30, 50}:
                raise ValueError("V8 prefix is restricted to scale30/50")
            if pricing_lifecycle_scope != PRICING_LIFECYCLE_SCOPE_ROOT_CG:
                raise ValueError("V8 prefix is root-CG only")
            if not bool(self.proof_tail_fallback_context):
                raise ValueError("V8 prefix requires a V5 fallback context")
            if self.dssr_enabled:
                raise ValueError("V8 prefix cannot run inside DSSR")
            if not all(contract_flags):
                raise ValueError(
                    "V8 prefix must be telemetry-only with routes and certificate forbidden"
                )
        object.__setattr__(
            self, "proof_tail_counterfactual_prefix_mode", counterfactual_mode
        )
        object.__setattr__(
            self, "proof_tail_counterfactual_prefix_boundary",
            counterfactual_boundary,
        )
        object.__setattr__(
            self, "proof_tail_counterfactual_rollout_checkpoints", checkpoints
        )
        object.__setattr__(
            self, "proof_tail_counterfactual_max_rollout_budget",
            maximum_rollout_budget,
        )
        object.__setattr__(
            self, "proof_tail_counterfactual_label_sample_cap", sample_cap
        )
        object.__setattr__(
            self, "proof_tail_counterfactual_sampling_seed", sampling_seed
        )
        object.__setattr__(
            self, "proof_tail_counterfactual_telemetry_only", contract_flags[0]
        )
        object.__setattr__(
            self, "proof_tail_counterfactual_public_routes_forbidden",
            contract_flags[1],
        )
        object.__setattr__(
            self, "proof_tail_counterfactual_certificate_forbidden",
            contract_flags[2],
        )
        object.__setattr__(self, "dssr_enabled", bool(self.dssr_enabled))
        if self.dssr_enabled and proof_queue_policy_id in {
            PROOF_QUEUE_POLICY_QG2,
            PROOF_QUEUE_POLICY_QGR1,
        }:
            raise ValueError("label-state GAT cannot run inside DSSR")
        if self.dssr_enabled and self.exact_negative_escape_enabled:
            raise ValueError(
                "exact negative escape and DSSR cannot be enabled together"
            )
        if self.dssr_enabled and mode != BACKEND_MODE_EXACT_PROOF:
            raise ValueError(
                "DSSR relaxation is available only for exact-proof pricing"
            )
        dssr_policy_version = str(self.dssr_policy_version)
        if self.dssr_enabled and not dssr_policy_version:
            dssr_policy_version = DSSR_POLICY_VERSION_V1
        if (
            dssr_policy_version
            and dssr_policy_version not in DSSR_POLICY_VERSIONS
        ):
            raise ValueError(
                f"unsupported dssr_policy_version {dssr_policy_version!r}"
            )
        object.__setattr__(
            self,
            "dssr_policy_version",
            dssr_policy_version,
        )
        dssr_batch_target = int(self.dssr_negative_batch_target)
        if dssr_batch_target <= 0:
            dssr_batch_target = min(self.harvest_target, 64)
        object.__setattr__(
            self,
            "dssr_negative_batch_target",
            max(1, min(dssr_batch_target, 64)),
        )
        object.__setattr__(
            self,
            "dssr_pressure_refinement_enabled",
            bool(self.dssr_pressure_refinement_enabled),
        )
        object.__setattr__(
            self,
            "dssr_pressure_max_bucket_size",
            max(0, int(self.dssr_pressure_max_bucket_size)),
        )
        object.__setattr__(
            self,
            "dssr_pressure_max_candidate_checks",
            max(0, int(self.dssr_pressure_max_candidate_checks)),
        )
        object.__setattr__(
            self,
            "ng_dssr_initial_neighborhood_size",
            max(
                1,
                min(
                    int(self.ng_dssr_initial_neighborhood_size),
                    int(self.data.scale),
                ),
            ),
        )
        if (
            self.dssr_enabled
            and self.dssr_pressure_refinement_enabled
            and (
                self.dssr_pressure_max_bucket_size <= 0
                or self.dssr_pressure_max_candidate_checks <= 0
            )
        ):
            raise ValueError(
                "DSSR pressure thresholds must be positive when enabled"
            )
        if proof_queue_selector != PROOF_QUEUE_EXPERIMENT_OFF:
            object.__setattr__(
                self,
                "config_hash",
                stable_payload_hash(
                    {
                        "schema_version": (
                            "lunar_ice_bpc.proof_queue_experiment_config.v1"
                        ),
                        "source_config_hash": str(self.config_hash),
                        "selector_id": proof_queue_selector,
                        "resolved_policy_id": proof_queue_policy_id,
                    }
                ),
            )
        object.__setattr__(
            self,
            "cut_dual_projection_enabled",
            bool(self.cut_dual_projection_enabled),
        )
        # Cut state is a mathematical request requirement, not an independent
        # performance toggle. Empty-context calls remain on the no-cut path.
        object.__setattr__(self, "cut_state_enabled", not self.cut_context.empty)
        object.__setattr__(self, "cut_state_schema_version", str(self.cut_state_schema_version))
        guidance_mode = str(self.guidance_mode)
        if guidance_mode not in GUIDANCE_MODES:
            raise ValueError(f"unsupported guidance_mode {guidance_mode!r}")
        object.__setattr__(self, "guidance_mode", guidance_mode)
        object.__setattr__(
            self,
            "guidance_lifecycle_telemetry",
            tuple(
                (str(key), value)
                for key, value in self.guidance_lifecycle_telemetry
            ),
        )

    @property
    def exact_proof_mode(self) -> bool:
        return self.mode == BACKEND_MODE_EXACT_PROOF

    @property
    def cut_state_required(self) -> bool:
        return not self.cut_context.empty


@dataclass(frozen=True)
class BackendResult:
    backend_id: str
    engine_status: str
    best_found_rc: float | None = None
    global_min_rc: float | None = None
    global_min_rc_is_exact: bool = False
    proved_no_rc_below: float | None = None
    unexplored_rc_lower_bound: float | None = None
    search_exhaustive: bool = False
    frontier_empty: bool = False
    labels_dropped: bool = False
    partial_columns_valid: bool = False
    columns: tuple[JourneyColumn, ...] = tuple()
    certificate_blockers: tuple[str, ...] = tuple()
    telemetry: dict = field(default_factory=dict)

    @property
    def can_enter_certificate_audit(self) -> bool:
        threshold_proved = self.proved_no_rc_below is not None
        exact_min_known = self.global_min_rc_is_exact and self.global_min_rc is not None
        return bool(
            not self.certificate_blockers
            and not self.labels_dropped
            and self.search_exhaustive
            and self.frontier_empty
            and (threshold_proved or exact_min_known)
        )

    def to_payload(self) -> dict:
        return {
            "backend_id": self.backend_id,
            "engine_status": self.engine_status,
            "best_found_rc": self.best_found_rc,
            "global_min_rc": self.global_min_rc,
            "global_min_rc_is_exact": self.global_min_rc_is_exact,
            "proved_no_rc_below": self.proved_no_rc_below,
            "unexplored_rc_lower_bound": self.unexplored_rc_lower_bound,
            "search_exhaustive": self.search_exhaustive,
            "frontier_empty": self.frontier_empty,
            "labels_dropped": self.labels_dropped,
            "partial_columns_valid": self.partial_columns_valid,
            "column_count": len(self.columns),
            "certificate_blockers": list(self.certificate_blockers),
            "can_enter_certificate_audit": self.can_enter_certificate_audit,
            "telemetry": dict(self.telemetry),
        }


class PricingBackend(Protocol):
    backend_id: str

    def solve(self, request: BackendPricingRequest) -> BackendResult:
        """Price one journey subproblem without mutating the master problem."""
