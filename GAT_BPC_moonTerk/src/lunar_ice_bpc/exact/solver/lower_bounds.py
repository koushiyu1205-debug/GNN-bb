"""Relaxation lower bounds for lunar-ice routing instances."""

from __future__ import annotations

from dataclasses import dataclass
import heapq

from lunar_ice_bpc.domain.scenario import PATH_TYPES
from lunar_ice_bpc.exact.core.data import LunarIceData
from lunar_ice_bpc.exact.core.objective import additive_objective_value, operating_cost_value, service_risk_value


@dataclass(frozen=True)
class AnalyticLowerBound:
    status: str
    exact_status: str
    bound: float
    completion_term_bound: float
    service_energy_bound: float
    service_risk_bound: float
    task_count: int
    note: str

    def to_payload(self) -> dict:
        return {
            "status": self.status,
            "exact_status": self.exact_status,
            "bound": self.bound,
            "completion_term_bound": self.completion_term_bound,
            "service_energy_bound": self.service_energy_bound,
            "service_risk_bound": self.service_risk_bound,
            "task_count": self.task_count,
            "note": self.note,
        }


def compute_analytic_lower_bound(data: LunarIceData) -> AnalyticLowerBound:
    """Return a conservative relaxation lower bound.

    This bound relaxes routing, capacity, fleet, return, recharge, and shadow
    coupling. It keeps only per-task earliest possible completion from the
    shortest logical-graph travel time, plus mandatory service energy and
    service thermal-risk terms.
    """

    shortest = _shortest_travel_from_depot(data)
    completion_term = 0.0
    service_energy = 0.0
    service_risk = 0.0
    for task_id in data.task_ids:
        task = data.tasks[task_id]
        earliest_arrival = shortest.get(task_id, 0.0)
        earliest_start = max(float(task.ready_time), float(earliest_arrival))
        completion_term += float(task.science_weight) * (earliest_start + float(task.service_time))
        service_energy += float(task.service_energy)
        service_risk += service_risk_value(task)
    bound = additive_objective_value(
        data,
        operating_cost=operating_cost_value(
            service_cost=sum(float(data.tasks[task_id].service_cost) for task_id in data.task_ids),
            distance_km=0.0,
            energy_proxy=service_energy,
        ),
        risk_integral=service_risk,
        weighted_completion_time=completion_term,
    )
    return AnalyticLowerBound(
        status="ANALYTIC_RELAXATION_BOUND",
        exact_status="RELAXATION_LOWER_BOUND",
        bound=round(bound, 6),
        completion_term_bound=round(completion_term, 6),
        service_energy_bound=round(service_energy, 6),
        service_risk_bound=round(service_risk, 6),
        task_count=len(data.task_ids),
        note=(
            "Conservative non-BPC relaxation lower bound; ignores nonnegative routing, return, recharge, "
            "fleet, capacity, shadow, and all makespan/report-only terms."
        ),
    )


def relative_gap(incumbent: float | None, lower_bound: float | None) -> float | None:
    if incumbent is None or lower_bound is None:
        return None
    incumbent_value = float(incumbent)
    if incumbent_value <= 1.0e-9:
        return None
    gap = max(0.0, incumbent_value - float(lower_bound)) / abs(incumbent_value)
    return round(gap, 9)


def _shortest_travel_from_depot(data: LunarIceData) -> dict[str, float]:
    nodes = ("depot", *data.task_ids)
    adjacency: dict[str, list[tuple[str, float]]] = {node: [] for node in nodes}
    for source in nodes:
        for target in nodes:
            if source == target:
                continue
            best = min(float(data.option(source, target, path_type).travel_time_min) for path_type in PATH_TYPES)
            adjacency[source].append((target, best))
    distance: dict[str, float] = {"depot": 0.0}
    heap: list[tuple[float, str]] = [(0.0, "depot")]
    while heap:
        value, node = heapq.heappop(heap)
        if value > distance.get(node, float("inf")) + 1.0e-9:
            continue
        for target, cost in adjacency[node]:
            new_value = value + cost
            if new_value < distance.get(target, float("inf")) - 1.0e-9:
                distance[target] = new_value
                heapq.heappush(heap, (new_value, target))
    return distance
