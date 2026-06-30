"""Journey-column data structures."""

from __future__ import annotations

from dataclasses import dataclass

from lunar_ice_bpc.exact.core.columns import TimedSortie
from lunar_ice_bpc.exact.core.data import LunarIceData


@dataclass(frozen=True)
class JourneyColumn:
    sorties: tuple[TimedSortie, ...]
    task_set: frozenset[str]
    end_time: float
    discovery_completion_term: float
    risk_integral: float
    energy_proxy: float
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
                    "shadow_exposure_min": sortie.shadow_exposure_min,
                    "demand": sortie.demand,
                    "feasible": sortie.feasible,
                }
                for sortie in self.sorties
            ],
        }


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
    objective = (
        data.objective.alpha_discovery_completion * completion
        + data.objective.beta_journey_end_time * end_time
        + data.objective.gamma_lunar_ice_risk * risk
        + data.objective.delta_energy * energy
    )
    return JourneyColumn(
        sorties=tuple(sorties),
        task_set=frozenset(seen),
        end_time=round(end_time, 6),
        discovery_completion_term=round(completion, 6),
        risk_integral=round(risk, 6),
        energy_proxy=round(energy, 6),
        objective=round(objective, 6),
    )

