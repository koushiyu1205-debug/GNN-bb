"""B4.3 SPPRC pricing facade.

This module is the stable BPC-facing API for the large-scale SPPRC labeling
pricer.  The first implementation deliberately wraps the in-repo
resource-labeling engine instead of binding an external C++ library directly:
that keeps the certificate semantics auditable while leaving a narrow adapter
surface for a future bucket-graph sidecar.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from time import perf_counter
from typing import Iterable

from lunar_ice_bpc.exact.bpc.pricing.labeling_pricer import (
    EXACT_ELEMENTARY_MODE,
    RELAXED_NG_ROUTE_MODE,
    LabelingPricingConfig,
    run_bpc_labeling_pricer,
)
from lunar_ice_bpc.exact.core.branching import BranchContext
from lunar_ice_bpc.exact.core.cuts import CutContext
from lunar_ice_bpc.exact.core.data import LunarIceData
from lunar_ice_bpc.exact.core.journey import JourneyColumn
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals
from lunar_ice_bpc.exact.pricing.journey_pricing import DirectPricingCache


SPPRC_PRICER_SCHEMA_VERSION = "lunar_ice_bpc.b4_3_spprc_pricer.v1"
SPPRC_MODEL_ID = "B4_3_SPPRC_LABELING_V1"
SPPRC_OBJECTIVE_VERSION = "normalized_cost_risk_weighted_completion_v1"
SPPRC_WORKER_MODE = "RELAXED_NG_WORKER"
SPPRC_EXACT_MODE = "EXACT_ELEMENTARY_PROOF"
SPPRC_ENGINE_SOURCE = "internal_resource_label_core"
SPPRC_ENGINE_LICENSE = "project_internal"


@dataclass(frozen=True)
class SpprcPricingRequest:
    """Stable request contract for B4.3 SPPRC pricing.

    ``RELAXED_NG_WORKER`` is candidate-search only.  ``EXACT_ELEMENTARY_PROOF``
    may certify only when the wrapped labeling payload reports full coverage and
    the true-dual audits close.
    """

    mode: str
    instance_hash: str
    config_hash: str
    objective_version: str = SPPRC_OBJECTIVE_VERSION
    branch_context_hash: str = "empty"
    cut_context_hash: str = "empty"
    max_exact_tasks: int = 30
    max_label_task_count: int = 30
    max_candidate_sets: int | None = 480
    harvest_target: int = 64
    exact_negative_harvest_target: int = 8
    ng_neighborhood_sizes: tuple[int, ...] = (6, 10, 14, 30)
    wall_time_limit_sec: float | None = None
    negative_eps: float = 1.0e-6
    dual_stabilization_enabled: bool = False
    tail_dual_alpha: float = 0.7
    tail_dual_window: int = 5

    def __post_init__(self) -> None:
        mode = str(self.mode)
        if mode not in {SPPRC_WORKER_MODE, SPPRC_EXACT_MODE}:
            raise ValueError(f"unsupported SPPRC mode {mode!r}")
        object.__setattr__(self, "mode", mode)
        object.__setattr__(self, "max_exact_tasks", max(1, int(self.max_exact_tasks)))
        object.__setattr__(self, "max_label_task_count", max(1, int(self.max_label_task_count)))
        if self.max_candidate_sets is not None:
            object.__setattr__(self, "max_candidate_sets", max(0, int(self.max_candidate_sets)))
        object.__setattr__(self, "harvest_target", max(1, int(self.harvest_target)))
        object.__setattr__(
            self,
            "exact_negative_harvest_target",
            max(1, int(self.exact_negative_harvest_target)),
        )
        object.__setattr__(
            self,
            "ng_neighborhood_sizes",
            _normalize_ng_sizes(self.ng_neighborhood_sizes, self.max_label_task_count),
        )
        if self.wall_time_limit_sec is not None:
            object.__setattr__(self, "wall_time_limit_sec", max(0.0, float(self.wall_time_limit_sec)))
        object.__setattr__(self, "negative_eps", abs(float(self.negative_eps)))
        object.__setattr__(self, "tail_dual_alpha", max(0.0, min(1.0, float(self.tail_dual_alpha))))
        object.__setattr__(self, "tail_dual_window", max(1, int(self.tail_dual_window)))


@dataclass(frozen=True)
class SpprcPricingResult:
    schema_version: str
    model_id: str
    mode: str
    engine_source: str
    engine_build_hash: str
    request_hash: str
    status: str
    pricing_state: str
    pricing_proof_kind: str
    can_certify_no_negative: bool
    uses_true_dual_bpc_certificate: bool
    no_column_can_certify: bool
    exact_coverage_complete: bool
    global_min_rc: float | None
    worker_sec: float
    exact_sec: float
    wall_time_sec: float
    label_count: int
    dominance_pruned: int
    ng_size_final: int
    dssr_iterations: int
    payload: dict
    columns: tuple[JourneyColumn, ...]

    def to_payload(self) -> dict:
        payload = dict(self.payload)
        payload.update(
            {
                "schema_version": self.schema_version,
                "model_id": self.model_id,
                "spprc_mode": self.mode,
                "spprc_engine_source": self.engine_source,
                "spprc_engine_build_hash": self.engine_build_hash,
                "spprc_request_hash": self.request_hash,
                "spprc_status": self.status,
                "spprc_pricing_state": self.pricing_state,
                "spprc_pricing_proof_kind": self.pricing_proof_kind,
                "spprc_can_certify_no_negative": self.can_certify_no_negative,
                "spprc_uses_true_dual_bpc_certificate": self.uses_true_dual_bpc_certificate,
                "spprc_no_column_can_certify": self.no_column_can_certify,
                "spprc_exact_coverage_complete": self.exact_coverage_complete,
                "spprc_global_min_rc": self.global_min_rc,
                "spprc_worker_sec": self.worker_sec,
                "spprc_exact_sec": self.exact_sec,
                "spprc_wall_time_sec": self.wall_time_sec,
                "spprc_label_count": self.label_count,
                "spprc_dominance_pruned": self.dominance_pruned,
                "spprc_ng_size_final": self.ng_size_final,
                "spprc_dssr_iterations": self.dssr_iterations,
                "spprc_column_count": len(self.columns),
                "spprc_engine_license": SPPRC_ENGINE_LICENSE,
            }
        )
        return payload


def run_spprc_pricer(
    data: LunarIceData,
    true_duals: JourneyDuals,
    request: SpprcPricingRequest,
    *,
    branch_context: BranchContext | None = None,
    cut_context: CutContext | None = None,
    seed_task_sets: Iterable[Iterable[str]] = tuple(),
    seed_source_rows: Iterable[dict] = tuple(),
    existing_task_sets: Iterable[Iterable[str]] = tuple(),
    support_task_sets: Iterable[Iterable[str]] = tuple(),
    dual_history: Iterable[JourneyDuals] = tuple(),
    cache: DirectPricingCache | None = None,
) -> SpprcPricingResult:
    """Run B4.3 SPPRC pricing through the current exact-safe labeler."""

    start = perf_counter()
    if request.mode == SPPRC_EXACT_MODE:
        config = LabelingPricingConfig(
            mode=EXACT_ELEMENTARY_MODE,
            max_exact_tasks=request.max_exact_tasks,
            harvest_target=request.harvest_target,
            exact_negative_harvest_target=request.exact_negative_harvest_target,
            wall_time_limit_sec=request.wall_time_limit_sec,
            negative_eps=request.negative_eps,
            dual_stabilization_enabled=False,
            stop_at_first_negative=False,
        )
    else:
        config = LabelingPricingConfig(
            mode=RELAXED_NG_ROUTE_MODE,
            max_label_task_count=request.max_label_task_count,
            max_candidate_sets=request.max_candidate_sets,
            harvest_target=request.harvest_target,
            wall_time_limit_sec=request.wall_time_limit_sec,
            negative_eps=request.negative_eps,
            dual_stabilization_enabled=request.dual_stabilization_enabled,
            dual_stabilization_alpha=request.tail_dual_alpha,
            dual_stabilization_window=request.tail_dual_window,
            ng_neighborhood_size=request.ng_neighborhood_sizes[-1],
            ng_neighborhood_sizes=request.ng_neighborhood_sizes,
            stop_at_first_negative=False,
        )
    payload, columns = run_bpc_labeling_pricer(
        data,
        true_duals,
        config=config,
        branch_context=branch_context or BranchContext(),
        cut_context=cut_context or CutContext(),
        seed_task_sets=seed_task_sets,
        seed_source_rows=seed_source_rows,
        existing_task_sets=existing_task_sets,
        support_task_sets=support_task_sets,
        dual_history=dual_history,
        cache=cache,
    )
    elapsed = round(perf_counter() - start, 6)
    exact_mode = request.mode == SPPRC_EXACT_MODE
    return SpprcPricingResult(
        schema_version=SPPRC_PRICER_SCHEMA_VERSION,
        model_id=SPPRC_MODEL_ID,
        mode=request.mode,
        engine_source=SPPRC_ENGINE_SOURCE,
        engine_build_hash=spprc_engine_build_hash(),
        request_hash=spprc_request_hash(request),
        status=str(payload.get("status") or payload.get("pricing_state") or ""),
        pricing_state=str(payload.get("pricing_state") or ""),
        pricing_proof_kind=str(payload.get("pricing_proof_kind") or ""),
        can_certify_no_negative=bool(payload.get("can_certify_no_negative")),
        uses_true_dual_bpc_certificate=bool(payload.get("uses_true_dual_bpc_certificate")),
        no_column_can_certify=False,
        exact_coverage_complete=bool(payload.get("global_remaining_rc_lb_coverage_complete")),
        global_min_rc=_optional_float(
            payload.get("global_remaining_rc_lb")
            if payload.get("global_remaining_rc_lb") is not None
            else payload.get("true_best_reduced_cost")
        ),
        worker_sec=0.0 if exact_mode else elapsed,
        exact_sec=elapsed if exact_mode else 0.0,
        wall_time_sec=elapsed,
        label_count=_label_count(payload),
        dominance_pruned=_dominance_pruned_count(payload),
        ng_size_final=int(request.ng_neighborhood_sizes[-1]),
        dssr_iterations=len(request.ng_neighborhood_sizes) if not exact_mode else 0,
        payload=payload,
        columns=tuple(columns),
    )


def build_spprc_request(
    data: LunarIceData,
    *,
    mode: str,
    config_hash: str,
    branch_context: BranchContext | None = None,
    cut_context: CutContext | None = None,
    **kwargs,
) -> SpprcPricingRequest:
    return SpprcPricingRequest(
        mode=mode,
        instance_hash=spprc_instance_hash(data),
        config_hash=str(config_hash),
        branch_context_hash=_stable_hash((branch_context or BranchContext()).to_payload()),
        cut_context_hash=_stable_hash((cut_context or CutContext()).to_payload()),
        **kwargs,
    )


def spprc_instance_hash(data: LunarIceData) -> str:
    payload = {
        "instance_id": data.instance_id,
        "task_ids": list(data.task_ids),
        "fleet_size": data.fleet_size,
        "max_tasks_per_trip": data.max_tasks_per_trip,
        "capacity": data.capacity,
        "energy_limit": data.energy_limit,
        "horizon": data.horizon,
        "path_option_policy_id": data.path_option_policy_id,
        "objective": data.objective.mode,
    }
    return _stable_hash(payload)


def spprc_request_hash(request: SpprcPricingRequest) -> str:
    return _stable_hash(asdict(request))


def spprc_engine_build_hash() -> str:
    try:
        content = Path(__file__).read_bytes()
    except OSError:
        content = SPPRC_ENGINE_SOURCE.encode("utf-8")
    return hashlib.sha256(content).hexdigest()[:16]


def _stable_hash(payload) -> str:
    raw = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _normalize_ng_sizes(values: Iterable[int], max_label_task_count: int) -> tuple[int, ...]:
    seen: set[int] = set()
    sizes: list[int] = []
    for raw in values:
        size = max(1, min(int(max_label_task_count), int(raw)))
        if size in seen:
            continue
        seen.add(size)
        sizes.append(size)
    if not sizes:
        sizes.append(max(1, int(max_label_task_count)))
    if sizes[-1] != max(1, int(max_label_task_count)):
        cap = max(1, int(max_label_task_count))
        if cap not in seen:
            sizes.append(cap)
    return tuple(sizes)


def _label_count(payload: dict) -> int:
    for key in (
        "resource_extension_label_attempt_count",
        "label_queue_push_count",
        "pareto_label_count",
        "true_audited_column_count",
    ):
        value = payload.get(key)
        if value is not None:
            try:
                return int(value)
            except (TypeError, ValueError):
                pass
    return 0


def _dominance_pruned_count(payload: dict) -> int:
    total = 0
    for key in (
        "resource_extension_label_dominance_rejected_count",
        "resource_extension_label_dominance_replaced_count",
        "dominance_pruned",
        "dominance_filtered_count",
    ):
        try:
            total += int(payload.get(key) or 0)
        except (TypeError, ValueError):
            pass
    return total


def _optional_float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
