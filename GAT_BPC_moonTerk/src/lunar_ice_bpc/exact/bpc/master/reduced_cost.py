"""Immutable reduced-cost context for BPC pricing and audits."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping


def _freeze_float_mapping(values: Mapping[object, object]) -> Mapping[str, float]:
    return MappingProxyType({str(key): float(value) for key, value in values.items()})


@dataclass(frozen=True)
class ReducedCostContext:
    task_duals: Mapping[str, float]
    fleet_dual: float
    cut_duals: Mapping[str, float] = field(default_factory=dict)
    branch_context: object | None = None
    cut_context: object | None = None
    dual_fingerprint: str = ""
    rmp_iteration_id: str = ""
    objective_mode: str = "official"
    true_dual_binding_hash: str = ""
    branch_context_hash: str = ""
    active_cut_context_hash: str = ""
    cut_lineage_hash: str = ""
    live_cut_policy_hash: str = ""
    separator_policy_version: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "task_duals", _freeze_float_mapping(self.task_duals))
        object.__setattr__(self, "fleet_dual", float(self.fleet_dual))
        object.__setattr__(self, "cut_duals", _freeze_float_mapping(self.cut_duals))
        object.__setattr__(self, "objective_mode", str(self.objective_mode))
