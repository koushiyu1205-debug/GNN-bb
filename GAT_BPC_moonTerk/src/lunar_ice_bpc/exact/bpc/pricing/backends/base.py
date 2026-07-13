"""Typed contract shared by Python and native SPPRC backends."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from lunar_ice_bpc.exact.core.branching import BranchContext
from lunar_ice_bpc.exact.core.cuts import CutContext
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
    cut_state_enabled: bool = False
    instance_hash: str = ""
    config_hash: str = ""
    dual_binding_hash: str = ""
    branch_context_hash: str = ""
    cut_context_hash: str = ""

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
        object.__setattr__(self, "cut_state_enabled", bool(self.cut_state_enabled))

    @property
    def exact_proof_mode(self) -> bool:
        return self.mode == BACKEND_MODE_EXACT_PROOF


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
