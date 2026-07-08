"""Journey-column data structures."""

from __future__ import annotations

from dataclasses import dataclass

from lunar_ice_bpc.exact.core.columns import TimedSortie, build_timed_sortie
from lunar_ice_bpc.exact.core.data import LunarIceData
from lunar_ice_bpc.exact.core.objective import journey_objective_breakdown, operating_cost_value


@dataclass(frozen=True)
class JourneyColumn:
    sorties: tuple[TimedSortie, ...]
    task_set: frozenset[str]
    end_time: float
    discovery_completion_term: float
    risk_integral: float
    energy_proxy: float
    distance_km: float
    service_cost: float
    operating_cost: float
    makespan: float
    normalized_operating_cost: float
    normalized_risk: float
    normalized_weighted_completion_time: float
    normalized_makespan_metric: float
    objective_breakdown: dict
    task_completion_times: dict[str, float]
    objective: float

    def to_solution_payload(self, *, vehicle_id: str) -> dict:
        return {
            "vehicle_id": vehicle_id,
            "sorties": [
                {
                    "tasks": list(sortie.tasks),
                    "legs": [
                        {"from": leg.source, "to": leg.target, "path_type": leg.path_type}
                        for leg in sortie.legs
                    ],
                    "start_time": sortie.start_time,
                    "service_starts": sortie.service_starts,
                    "return_time": sortie.return_time,
                    "recharge_time": sortie.recharge_time,
                    "end_time": sortie.end_time,
                    "travel_time": sortie.travel_time,
                    "distance_km": sortie.distance_km,
                    "energy_proxy": sortie.energy_proxy,
                    "risk_integral": sortie.risk_integral,
                    "service_cost": sortie.service_cost,
                    "shadow_exposure_min": sortie.shadow_exposure_min,
                    "demand": sortie.demand,
                    "task_completion_times": sortie.task_completion_times,
                    "feasible": sortie.feasible,
                }
                for sortie in self.sorties
            ],
            "objective_breakdown": self.objective_breakdown,
        }


def journey_column_from_solution_payload(data: LunarIceData, payload: dict) -> JourneyColumn:
    """Rebuild a journey column from ``JourneyColumn.to_solution_payload`` output."""

    sorties = []
    for sortie_payload in payload.get("sorties", []):
        sequence = tuple(str(task_id) for task_id in sortie_payload.get("tasks", []))
        path_types = tuple(
            str(leg.get("path_type"))
            for leg in sortie_payload.get("legs", [])
        )
        if not sequence:
            raise ValueError("journey payload sortie has no tasks")
        if len(path_types) != len(sequence) + 1:
            raise ValueError("journey payload path_types must contain one leg per task plus return")
        sortie = build_timed_sortie(
            data,
            sequence,
            path_types,
            start_time=float(sortie_payload.get("start_time", 0.0)),
        )
        if not sortie.feasible:
            raise ValueError(f"journey payload sortie is infeasible: {sortie.infeasible_reason}")
        sorties.append(sortie)
    if not sorties:
        raise ValueError("journey payload has no sorties")
    return build_journey_column(data, tuple(sorties))


def build_journey_column(data: LunarIceData, sorties: tuple[TimedSortie, ...]) -> JourneyColumn:
    seen: set[str] = set()
    for sortie in sorties:
        if not sortie.feasible:
            raise ValueError("infeasible sortie cannot form a journey column")
        if seen.intersection(sortie.task_set):
            raise ValueError("journey sorties must have disjoint task sets")
        seen.update(sortie.task_set)
    end_time = max((sortie.end_time for sortie in sorties), default=0.0)
    completion = sum(sortie.discovery_completion_term for sortie in sorties)
    risk = sum(sortie.risk_integral for sortie in sorties)
    energy = sum(sortie.energy_proxy for sortie in sorties)
    distance = sum(sortie.distance_km for sortie in sorties)
    service_cost = sum(sortie.service_cost for sortie in sorties)
    operating_cost = operating_cost_value(
        service_cost=service_cost,
        distance_km=distance,
        energy_proxy=energy,
    )
    task_completion_times = {
        task_id: completion_time
        for sortie in sorties
        for task_id, completion_time in sortie.task_completion_times.items()
    }
    makespan = max((float(value) for value in task_completion_times.values()), default=0.0)
    breakdown = journey_objective_breakdown(data, sorties)
    return JourneyColumn(
        sorties=tuple(sorties),
        task_set=frozenset(seen),
        end_time=round(end_time, 6),
        discovery_completion_term=round(completion, 6),
        risk_integral=round(risk, 6),
        energy_proxy=round(energy, 6),
        distance_km=round(distance, 6),
        service_cost=round(service_cost, 6),
        operating_cost=round(operating_cost, 6),
        makespan=round(makespan, 6),
        normalized_operating_cost=breakdown.normalized_operating_cost,
        normalized_risk=breakdown.normalized_risk,
        normalized_weighted_completion_time=breakdown.normalized_weighted_completion_time,
        normalized_makespan_metric=breakdown.normalized_makespan,
        objective_breakdown=breakdown.to_payload(),
        task_completion_times={key: round(value, 6) for key, value in task_completion_times.items()},
        objective=round(breakdown.objective, 6),
    )
