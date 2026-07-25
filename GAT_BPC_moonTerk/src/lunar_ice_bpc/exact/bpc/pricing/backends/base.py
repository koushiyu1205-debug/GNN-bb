"""Typed contract shared by Python and native SPPRC backends."""

from __future__ import annotations

from dataclasses import dataclass, field
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
PROOF_QUEUE_POLICY_Q0 = "Q0"
PROOF_QUEUE_POLICY_QC0 = "QC0"
PROOF_QUEUE_POLICY_QD1 = "QD1"
PROOF_QUEUE_POLICY_QB1 = "QB1"
PROOF_QUEUE_POLICIES = frozenset(
    {
        PROOF_QUEUE_POLICY_Q0,
        PROOF_QUEUE_POLICY_QC0,
        PROOF_QUEUE_POLICY_QD1,
        PROOF_QUEUE_POLICY_QB1,
    }
)
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
    branch_context: BranchContext = field(default_factory=BranchContext)
    cut_context: CutContext = field(default_factory=CutContext)
    harvest_target: int = 16
    wall_time_limit_sec: float | None = None
    memory_limit_gb: float = 0.0
    negative_eps: float = 1.0e-6
    dominance_eps: float = 1.0e-12
    resource_eps: float = 1.0e-9
    reconstruction_eps: float = 2.0e-6
    completion_bound_enabled: bool = False
    subset_dominance_enabled: bool = False
    proof_queue_policy_id: str = PROOF_QUEUE_POLICY_Q0
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
        object.__setattr__(self, "harvest_target", max(1, int(self.harvest_target)))
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
        object.__setattr__(
            self,
            "proof_queue_policy_id",
            proof_queue_policy_id,
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
