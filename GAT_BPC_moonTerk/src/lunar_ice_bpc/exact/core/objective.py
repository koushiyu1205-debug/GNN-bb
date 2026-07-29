"""Normalized additive objective helpers for lunar-ice exact solvers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Iterable, Mapping
import weakref

from lunar_ice_bpc.domain.scenario import PATH_TYPES
from lunar_ice_bpc.exact.core.columns import build_timed_sortie
from lunar_ice_bpc.exact.core.data import LunarIceData


OBJECTIVE_SCHEMA_VERSION = "lunar_ice_bpc.normalized_additive_objective.v1"
OBJECTIVE_MODE = "normalized_operating_cost_risk_weighted_completion"
OBJECTIVE_SPEC_ID = (
    "normalized_operating_cost_1+risk_1+weighted_completion_0.4.v1"
)

_EPS = 1.0e-9
_REFERENCE_CACHE: dict[int, tuple[weakref.ReferenceType[LunarIceData], "ObjectiveReferences"]] = {}


@dataclass(frozen=True)
class ObjectiveReferences:
    reference_cost: float
    reference_risk: float
    reference_completion: float
    reference_makespan: float
    task_count: int
    infeasible_single_task_reference_count: int = 0

    def to_payload(self) -> dict:
        return {
            "schema_version": OBJECTIVE_SCHEMA_VERSION,
            "mode": OBJECTIVE_MODE,
            "objective_spec_id": OBJECTIVE_SPEC_ID,
            **asdict(self),
        }


@dataclass(frozen=True)
class ObjectiveBreakdown:
    raw_operating_cost: float
    raw_risk: float
    raw_weighted_completion_time: float
    raw_makespan: float
    normalized_operating_cost: float
    normalized_risk: float
    normalized_weighted_completion_time: float
    normalized_makespan: float
    weight_operating_cost: float
    weight_risk: float
    weight_completion: float
    objective: float

    def to_payload(self) -> dict:
        payload = asdict(self)
        raw_objective_unscaled = (
            float(self.weight_operating_cost) * float(self.raw_operating_cost)
            + float(self.weight_risk) * float(self.raw_risk)
            + float(self.weight_completion) * float(self.raw_weighted_completion_time)
        )
        return {
            "schema_version": OBJECTIVE_SCHEMA_VERSION,
            "mode": OBJECTIVE_MODE,
            "objective_spec_id": OBJECTIVE_SPEC_ID,
            **payload,
            "normalized_objective": self.objective,
            "official_objective": self.objective,
            "raw_objective_unscaled_weighted_sum": round(raw_objective_unscaled, 6),
            "makespan_enters_pricing_objective": False,
            "note": (
                "Official objective is normalized additive operating cost, risk, and weighted completion. "
                "Makespan is reported as an evaluation metric only."
            ),
        }


def operating_cost_value(*, service_cost: float, distance_km: float, energy_proxy: float) -> float:
    return float(service_cost) + float(distance_km) + float(energy_proxy)


def service_risk_value(task) -> float:
    return float(task.local_thermal_risk) * float(task.service_time) * 0.01


def objective_references(data: LunarIceData) -> ObjectiveReferences:
    cache_key = id(data)
    cached = _REFERENCE_CACHE.get(cache_key)
    if cached is not None:
        cached_data, refs = cached
        if cached_data() is data:
            return refs

    total_cost = 0.0
    total_risk = 0.0
    total_completion = 0.0
    reference_makespan = 0.0
    infeasible = 0

    for task_id in data.task_ids:
        single = _single_task_reference(data, task_id)
        if single is None:
            task = data.tasks[task_id]
            infeasible += 1
            fallback_completion = max(float(task.ready_time) + float(task.service_time), float(data.horizon))
            fallback_risk = service_risk_value(task)
            fallback_cost = operating_cost_value(
                service_cost=float(task.service_cost),
                distance_km=0.0,
                energy_proxy=float(task.service_energy),
            )
            total_cost += max(_EPS, fallback_cost)
            total_risk += max(_EPS, fallback_risk)
            total_completion += max(_EPS, float(task.science_weight) * fallback_completion)
            reference_makespan = max(reference_makespan, fallback_completion)
            continue
        total_cost += single["cost"]
        total_risk += single["risk"]
        total_completion += single["weighted_completion"]
        reference_makespan = max(reference_makespan, single["completion_time"])

    refs = ObjectiveReferences(
        reference_cost=round(max(_EPS, total_cost), 9),
        reference_risk=round(max(_EPS, total_risk), 9),
        reference_completion=round(max(_EPS, total_completion), 9),
        reference_makespan=round(max(_EPS, reference_makespan, float(data.horizon)), 9),
        task_count=len(data.task_ids),
        infeasible_single_task_reference_count=int(infeasible),
    )
    _REFERENCE_CACHE[cache_key] = (weakref.ref(data), refs)
    return refs


def additive_objective_value(
    data: LunarIceData,
    *,
    operating_cost: float,
    risk_integral: float,
    weighted_completion_time: float,
) -> float:
    return objective_breakdown(
        data,
        operating_cost=operating_cost,
        risk_integral=risk_integral,
        weighted_completion_time=weighted_completion_time,
        makespan=0.0,
    ).objective


def objective_breakdown(
    data: LunarIceData,
    *,
    operating_cost: float,
    risk_integral: float,
    weighted_completion_time: float,
    makespan: float,
) -> ObjectiveBreakdown:
    refs = objective_references(data)
    norm_cost = _safe_ratio(operating_cost, refs.reference_cost)
    norm_risk = _safe_ratio(risk_integral, refs.reference_risk)
    norm_completion = _safe_ratio(weighted_completion_time, refs.reference_completion)
    norm_makespan = _safe_ratio(makespan, refs.reference_makespan)
    objective = (
        float(data.objective.weight_operating_cost) * norm_cost
        + float(data.objective.weight_risk) * norm_risk
        + float(data.objective.weight_completion) * norm_completion
    )
    return ObjectiveBreakdown(
        raw_operating_cost=round(float(operating_cost), 6),
        raw_risk=round(float(risk_integral), 6),
        raw_weighted_completion_time=round(float(weighted_completion_time), 6),
        raw_makespan=round(float(makespan), 6),
        normalized_operating_cost=round(norm_cost, 9),
        normalized_risk=round(norm_risk, 9),
        normalized_weighted_completion_time=round(norm_completion, 9),
        normalized_makespan=round(norm_makespan, 9),
        weight_operating_cost=float(data.objective.weight_operating_cost),
        weight_risk=float(data.objective.weight_risk),
        weight_completion=float(data.objective.weight_completion),
        objective=round(objective, 6),
    )


def sortie_objective_value(data: LunarIceData, sortie) -> float:
    return sortie_objective_breakdown(data, sortie).objective


def sortie_objective_breakdown(data: LunarIceData, sortie) -> ObjectiveBreakdown:
    operating = operating_cost_value(
        service_cost=float(sortie.service_cost),
        distance_km=float(sortie.distance_km),
        energy_proxy=float(sortie.energy_proxy),
    )
    makespan = max((float(value) for value in getattr(sortie, "task_completion_times", {}).values()), default=0.0)
    return objective_breakdown(
        data,
        operating_cost=operating,
        risk_integral=float(sortie.risk_integral),
        weighted_completion_time=float(sortie.discovery_completion_term),
        makespan=makespan,
    )


def journey_objective_breakdown(data: LunarIceData, sorties: Iterable) -> ObjectiveBreakdown:
    rows = tuple(sorties)
    operating = sum(
        operating_cost_value(
            service_cost=float(row.service_cost),
            distance_km=float(row.distance_km),
            energy_proxy=float(row.energy_proxy),
        )
        for row in rows
    )
    risk = sum(float(row.risk_integral) for row in rows)
    completion = sum(float(row.discovery_completion_term) for row in rows)
    makespan = max(
        (float(value) for row in rows for value in getattr(row, "task_completion_times", {}).values()),
        default=0.0,
    )
    return objective_breakdown(
        data,
        operating_cost=operating,
        risk_integral=risk,
        weighted_completion_time=completion,
        makespan=makespan,
    )


def aggregate_journey_objective_breakdown(data: LunarIceData, journeys: Iterable) -> dict:
    rows = tuple(journeys)
    operating = sum(float(getattr(row, "operating_cost", 0.0)) for row in rows)
    risk = sum(float(row.risk_integral) for row in rows)
    completion = sum(float(row.discovery_completion_term) for row in rows)
    makespan = max((float(getattr(row, "makespan", row.end_time)) for row in rows), default=0.0)
    payload = objective_breakdown(
        data,
        operating_cost=operating,
        risk_integral=risk,
        weighted_completion_time=completion,
        makespan=makespan,
    ).to_payload()
    payload["reference"] = objective_references(data).to_payload()
    payload["official_objective"] = round(sum(float(row.objective) for row in rows), 6)
    return payload


def objective_metadata(data: LunarIceData) -> dict:
    return {
        "schema_version": OBJECTIVE_SCHEMA_VERSION,
        "mode": OBJECTIVE_MODE,
        "objective_spec_id": OBJECTIVE_SPEC_ID,
        "weights": {
            "operating_cost": float(data.objective.weight_operating_cost),
            "risk": float(data.objective.weight_risk),
            "weighted_completion": float(data.objective.weight_completion),
            "makespan": float(data.objective.weight_makespan_metric_only),
        },
        "reference": objective_references(data).to_payload(),
        "makespan_enters_pricing_objective": False,
        "legacy_source_coefficients_ignored_by_exact_objective": {
            "alpha_discovery_completion": float(
                data.objective.alpha_discovery_completion
            ),
            "beta_journey_end_time": float(
                data.objective.beta_journey_end_time
            ),
            "gamma_lunar_ice_risk": float(
                data.objective.gamma_lunar_ice_risk
            ),
            "delta_energy": float(data.objective.delta_energy),
        },
        "source_objective_mode_diagnostic_only": str(data.objective.mode),
    }


def flatten_objective_payload(payload: Mapping | None, *, prefix: str = "objective") -> dict:
    if not isinstance(payload, Mapping):
        return {}
    refs = payload.get("reference") if isinstance(payload.get("reference"), Mapping) else {}
    return {
        f"{prefix}_schema_version": payload.get("schema_version"),
        f"{prefix}_mode": payload.get("mode"),
        f"{prefix}_spec_id": payload.get("objective_spec_id"),
        f"{prefix}_raw_operating_cost": payload.get("raw_operating_cost"),
        f"{prefix}_raw_risk": payload.get("raw_risk"),
        f"{prefix}_raw_weighted_completion_time": payload.get("raw_weighted_completion_time"),
        f"{prefix}_raw_makespan": payload.get("raw_makespan"),
        f"{prefix}_raw_objective_unscaled_weighted_sum": payload.get("raw_objective_unscaled_weighted_sum"),
        f"{prefix}_normalized_operating_cost": payload.get("normalized_operating_cost"),
        f"{prefix}_normalized_risk": payload.get("normalized_risk"),
        f"{prefix}_normalized_weighted_completion_time": payload.get("normalized_weighted_completion_time"),
        f"{prefix}_normalized_makespan_metric": payload.get("normalized_makespan"),
        f"{prefix}_normalized_objective": payload.get("normalized_objective", payload.get("objective")),
        f"{prefix}_official_objective": payload.get("official_objective", payload.get("objective")),
        f"{prefix}_reference_cost": refs.get("reference_cost"),
        f"{prefix}_reference_risk": refs.get("reference_risk"),
        f"{prefix}_reference_completion": refs.get("reference_completion"),
        f"{prefix}_reference_makespan_metric": refs.get("reference_makespan"),
        f"{prefix}_makespan_enters_pricing_objective": payload.get("makespan_enters_pricing_objective"),
    }


def _single_task_reference(data: LunarIceData, task_id: str) -> dict[str, float] | None:
    task = data.tasks[str(task_id)]
    best_cost = float("inf")
    best_risk = float("inf")
    best_completion = float("inf")
    for out_type in PATH_TYPES:
        for back_type in PATH_TYPES:
            sortie = build_timed_sortie(
                data,
                (str(task_id),),
                (str(out_type), str(back_type)),
                start_time=0.0,
            )
            if not sortie.feasible:
                continue
            completion = float(sortie.task_completion_times[str(task_id)])
            cost = operating_cost_value(
                service_cost=float(sortie.service_cost),
                distance_km=float(sortie.distance_km),
                energy_proxy=float(sortie.energy_proxy),
            )
            best_cost = min(best_cost, cost)
            best_risk = min(best_risk, float(sortie.risk_integral))
            best_completion = min(best_completion, completion)
    if not all(isfinite(value) for value in (best_cost, best_risk, best_completion)):
        return None
    return {
        "cost": max(_EPS, best_cost),
        "risk": max(_EPS, best_risk),
        "weighted_completion": max(_EPS, float(task.science_weight) * best_completion),
        "completion_time": max(_EPS, best_completion),
    }


def _safe_ratio(value: float, reference: float) -> float:
    denominator = max(_EPS, float(reference))
    return float(value) / denominator
